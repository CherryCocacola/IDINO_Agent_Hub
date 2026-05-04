using System.Text.Json;
using System.Linq;
using System.Diagnostics;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Infrastructure;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using AIAgentManagement.Settings;

namespace AIAgentManagement.Services;

public class PresentationService : IPresentationService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly IAiProxyService _aiProxyService;
    private readonly PptxGenerationService _pptxGenerationService;
    private readonly ITextExtractionService _textExtractionService;
    private readonly ILogger<PresentationService> _logger;
    private readonly IConfiguration _configuration;

    public PresentationService(
        AIAgentManagementDbContext context,
        IAiProxyService aiProxyService,
        PptxGenerationService pptxGenerationService,
        ITextExtractionService textExtractionService,
        ILogger<PresentationService> logger,
        IConfiguration configuration)
    {
        _context = context;
        _aiProxyService = aiProxyService;
        _pptxGenerationService = pptxGenerationService;
        _textExtractionService = textExtractionService;
        _logger = logger;
        _configuration = configuration;
    }

    public async Task<PresentationDto> GeneratePresentationAsync(PresentationGenerationRequestDto request, CancellationToken cancellationToken = default)
    {
        try
        {
            // 입력 검증
            if (request == null)
                throw new ArgumentNullException(nameof(request));

            var sourceType = (request.SourceType ?? "topic").Trim().ToLowerInvariant();
            if (sourceType != "topic" && sourceType != "paste" && sourceType != "import")
                sourceType = "topic";

            if (sourceType == "topic" && string.IsNullOrWhiteSpace(request.Prompt))
                throw new ArgumentException("주제(Prompt)를 입력해 주세요.", nameof(request));
            if (sourceType == "paste" && string.IsNullOrWhiteSpace(request.PasteContent))
                throw new ArgumentException("붙여넣을 텍스트(PasteContent)를 입력해 주세요.", nameof(request));
            if (sourceType == "import" && string.IsNullOrWhiteSpace(request.ImportUrl))
                throw new ArgumentException("가져올 URL(ImportUrl)을 입력해 주세요.", nameof(request));

            if (request.SlideCount <= 0 || request.SlideCount > 50)
                throw new ArgumentException("SlideCount must be between 1 and 50", nameof(request));
            if (request.ServiceId <= 0)
                throw new ArgumentException("ServiceId must be greater than 0", nameof(request));

            // Import 시 URL에서 텍스트 추출
            string contentForSlides = request.Prompt ?? string.Empty;
            string titleForSave = ExtractTitleFromPrompt(request.Prompt ?? string.Empty);
            if (sourceType == "paste" && !string.IsNullOrWhiteSpace(request.PasteContent))
            {
                contentForSlides = request.PasteContent!;
                titleForSave = ExtractTitleFromPrompt(contentForSlides);
            }
            else if (sourceType == "import" && !string.IsNullOrWhiteSpace(request.ImportUrl))
            {
                contentForSlides = await _textExtractionService.ExtractTextFromUrlAsync(request.ImportUrl!, cancellationToken);
                if (string.IsNullOrWhiteSpace(contentForSlides))
                    throw new InvalidOperationException("URL에서 추출한 텍스트가 없습니다.");
                titleForSave = ExtractTitleFromPrompt(contentForSlides);
            }

            _logger.LogInformation("Generating presentation: SourceType={SourceType}, SlideCount={SlideCount}, ServiceId={ServiceId}", 
                sourceType, request.SlideCount, request.ServiceId);

            if (request.TemplateId.HasValue)
                throw new InvalidOperationException("Template-based generation should use PresentationTemplateService.GenerateFromTemplateAsync");

            List<SlideDto> slides = await GenerateSlidesWithAIAsync(request, sourceType, contentForSlides, cancellationToken);

            if (slides == null || slides.Count == 0)
            {
                _logger.LogWarning("No slides generated, creating default slides");
                slides = GenerateDefaultSlides(request.SlideCount);
            }

            // Phase 3: AI 이미지 포함 시 슬라이드별 이미지 생성
            if (request.IncludeAiImages && request.ImageServiceId.HasValue && request.ImageServiceId.Value > 0)
            {
                var imageModel = request.ImageModel ?? "dall-e-3";
                var imageStyleSuffix = GetImageStyleSuffix(request.Style ?? "business");
                foreach (var slide in slides)
                {
                    var prompt = !string.IsNullOrWhiteSpace(slide.ImageDescription)
                        ? slide.ImageDescription
                        : $"{slide.Title}. {slide.Content}".Trim();
                    if (string.IsNullOrWhiteSpace(prompt)) continue;
                    if (prompt.Length > 1000) prompt = prompt.Substring(0, 1000);
                    if (!string.IsNullOrEmpty(imageStyleSuffix))
                        prompt = prompt.TrimEnd() + ". " + imageStyleSuffix;
                    try
                    {
                        var imageRequest = new ImageGenerationRequestDto
                        {
                            Prompt = prompt,
                            ServiceId = request.ImageServiceId.Value,
                            Model = imageModel,
                            Size = "1024x1024",
                            NumberOfImages = 1,
                            UserId = request.UserId
                        };
                        var imageResponse = await _aiProxyService.SendImageGenerationAsync(
                            request.ImageServiceId.Value, imageModel, imageRequest, cancellationToken);
                        if (imageResponse?.ImageUrls != null && imageResponse.ImageUrls.Count > 0)
                        {
                            slide.ImageUrl = imageResponse.ImageUrls[0];
                            slide.ImagePrompt = prompt;
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning(ex, "AI image generation failed for slide {SlideId}", slide.SlideId);
                    }
                }
            }

            // UserId 필수 (FK to Users)
            var userId = request.UserId ?? 0;
            if (userId <= 0)
            {
                throw new InvalidOperationException("UserId is required and must be a valid user. Please sign in again.");
            }

            // ThemeId: 미지정 시 스타일별 기본 테마 매핑
            var themeId = string.IsNullOrWhiteSpace(request.ThemeId)
                ? GetDefaultThemeIdForStyle(request.Style)
                : request.ThemeId.Trim();
            if (string.IsNullOrWhiteSpace(themeId))
                themeId = null;

            // 프레젠테이션 저장 (Slides는 PresentationSlides 테이블에 별도 저장 — 잘림 오류 없음)
            var slideSize = (request.SlideSize ?? "16:9").Trim();
            if (slideSize.Length > 20) slideSize = "16:9";
            var presentation = new Presentation
            {
                UserId = userId,
                Title = titleForSave.Length > 200 ? titleForSave.Substring(0, 200) : titleForSave,
                Slides = null, // PresentationSlides 테이블 사용, JSON 컬럼 미사용
                ThemeId = themeId,
                SlideSize = slideSize,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            };

            _context.Presentations.Add(presentation);
            try
            {
                await _context.SaveChangesAsync(cancellationToken);
            }
            catch (Microsoft.EntityFrameworkCore.DbUpdateException dbEx)
            {
                var inner = dbEx.InnerException?.Message ?? dbEx.Message;
                _logger.LogError(dbEx, "Presentation save failed: {InnerMessage}", inner);
                if (inner.Contains("ThemeId", StringComparison.OrdinalIgnoreCase) || inner.Contains("'ThemeId'"))
                    throw new InvalidOperationException(
                        "프레젠테이션 저장에 실패했습니다. DB에 ThemeId 컬럼이 없습니다. " +
                        "Data/Scripts/AddPresentationThemeId.sql 스크립트를 DB에 실행한 뒤 다시 시도해 주세요.",
                        dbEx);
                if (inner.Contains("FK_") || inner.Contains("foreign key"))
                    throw new InvalidOperationException(
                        "프레젠테이션 저장에 실패했습니다. 사용자 정보를 확인해 주세요. 다시 로그인 후 시도해 보세요.",
                        dbEx);
                throw new InvalidOperationException("프레젠테이션 저장에 실패했습니다. " + inner, dbEx);
            }

            // PresentationSlides 테이블에 슬라이드 저장
            var slideEntities = slides
                .Select((s, idx) => SlideDtoToEntity(s, presentation.PresentationId, idx + 1))
                .ToList();
            _context.PresentationSlides.AddRange(slideEntities);
            await _context.SaveChangesAsync(cancellationToken);

            return new PresentationDto
            {
                PresentationId = presentation.PresentationId,
                UserId = presentation.UserId,
                Title = presentation.Title,
                Slides = slides,
                ThemeId = presentation.ThemeId,
                SlideSize = presentation.SlideSize ?? "16:9",
                FontHeading = request.FontHeading,
                FontBody = request.FontBody,
                CreatedAt = presentation.CreatedAt,
                UpdatedAt = presentation.UpdatedAt
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating presentation: {Message}, StackTrace: {StackTrace}", ex.Message, ex.StackTrace);
            throw;
        }
    }

    private async Task<List<SlideDto>> GenerateSlidesWithAIAsync(
        PresentationGenerationRequestDto request,
        string sourceType,
        string contentForSlides,
        CancellationToken cancellationToken)
    {
        try
        {
            _logger.LogInformation("Generating slides with AI: SourceType={SourceType}, ServiceId={ServiceId}, Model={Model}", 
                sourceType, request.ServiceId, request.Model);

            string systemPrompt;
            string userMessage;

            var styleGuidance = GetStyleGuidance(request.Style ?? "business");

            if (sourceType == "paste" || sourceType == "import")
            {
                systemPrompt = $@"You are a presentation slide generator. Split the given text into EXACTLY {request.SlideCount} slides.

**STRUCTURE RULES:**
- Slide 1 MUST be a title slide: use layout ""title-only"" or ""title-content"" with the main title (and optional subtitle). One clear title for the whole presentation.
- Slide {request.SlideCount} (last) SHOULD be a closing: use layout ""thank-you"" with a short closing message, or ""title-only"" for summary/key takeaways.
- Middle slides: one main idea per slide. Choose layout by content: ""comparison"" for A vs B/pros-cons; ""two-column"" for parallel concepts; ""image-title"" when visuals are central; ""title-content"" for standard bullets.

**CONTENT RULES:**
- Each slide = ONE main message. Use bullet points or short phrases; 5-7 bullets max per slide, one line each.
- Use line breaks (\n) to separate bullets or sections. No long paragraphs.
- Keep titles clear and concise (5-10 words). Use subheadings to break long content into sections where needed.
- Do NOT add content that is not from or implied by the source text. Do NOT use generic placeholders (e.g. ""Slide 1"", ""Content goes here""). Extract and summarize only from the provided text.

**TEXT FORMATTING (use in content):**
- Use **bold** for key terms or emphasis. Use *italic* for subtle emphasis.
- Keep bullet points with • or -

**CHARTS & TABLES (optional):**
- For numeric data (Q1: 100, Q2: 150...): add ""charts"" array with chartType ""bar""/""line""/""pie"", title, data as {{""Q1"": 100, ""Q2"": 150}}.
- For comparisons (제품 vs 가격 vs 평점): add ""tables"" array with headerRow: true, rows: [[""제품"",""가격""], [""A"",""10만원""]].

**OUTPUT:**
- Output ONLY valid JSON. No explanations, no markdown, no code blocks.
- Use the exact JSON format with ""slides"" array. Each slide MUST have: ""title"", ""content"", ""layout"", and optionally ""imageDescription"", ""charts"", ""tables"".
- Layouts: title-content, title-only, two-column, image-title, section-header, comparison, quote, thank-you.

**STYLE: {request.Style}**
{styleGuidance}";
                userMessage = $"Split the following text into exactly {request.SlideCount} slides. First slide = title, last slide = thank-you or summary. Use only information from the text below; do not add off-topic or generic content. Respond with ONLY the JSON object.\n\n---\n{contentForSlides}";
            }
            else
            {
                systemPrompt = $@"You are a professional presentation slide generator and designer.

**CRITICAL INSTRUCTIONS:**
- You MUST generate a presentation with EXACTLY {request.SlideCount} slides about the topic: ""{contentForSlides}""
- ALL slides MUST be directly and solely related to this topic. Do NOT add slides or content that are off-topic, generic, or unrelated.
- Do NOT use generic placeholders (e.g. ""Slide 1"", ""Content goes here"", ""Key point 1""). Every title and every bullet must be specific and meaningful for the given topic.
- You MUST respond with ONLY valid JSON - no explanations, no markdown, no code blocks
- The JSON must follow the exact format specified below. EVERY slide MUST have a ""layout"" field.

**STRUCTURE RULES:**
- Slide 1 MUST be the title slide: use layout ""title-only"" or ""title-content"" with the presentation title (and optional subtitle).
- Slide {request.SlideCount} (last) MUST be a closing slide: use layout ""thank-you"" with a short closing (e.g. Thank you, Q&A, Next steps) or ""title-only"" for final summary.
- Middle slides: use ""title-content"", ""two-column"", ""comparison"", ""image-title"", ""section-header"", ""quote"" as appropriate.

**DESIGN PRINCIPLES:**
- Keep content concise and focused - each slide should convey ONE main idea
- Use bullet points or short phrases instead of long paragraphs
- Create visual hierarchy: important information should stand out
- Ensure readability: use clear, simple language

**CONTENT GUIDELINES:**
- Titles: clear, concise, engaging (5-10 words max)
- Content: bullet points or short sentences; keywords and phrases rather than full sentences
- Each bullet = one idea (max 1 line). Limit 5-7 bullet points per slide
- Use line breaks (\n) to separate sections or ideas

**TEXT FORMATTING (use in content):**
- Use **bold** for key terms or emphasis: **핵심 포인트**
- Use *italic* for subtle emphasis or terms
- Keep bullet points with • or -

**LAYOUT (assign to EVERY slide) - choose based on content type:**
- ""title-only"": Title slide, section dividers, or impactful single statement
- ""title-content"": Standard slide with title and body (most common)
- ""two-column"": Two concepts or related info side-by-side
- ""image-title"": When an image is central to the message (visual-heavy content)
- ""comparison"": Use for A vs B, pros/cons, before/after, advantages/disadvantages
- ""section-header"": Section divider with optional subtitle
- ""quote"": Key quote or testimonial
- ""thank-you"": Closing slide only
**Layout selection rules:** Use ""comparison"" for contrast (vs, 장점/단점, 비교). Use ""image-title"" when visuals are central. Use ""two-column"" for parallel concepts.

**IMAGE DESCRIPTIONS:**
- Provide specific, descriptive image suggestions that enhance understanding
- Be specific: e.g. ""A modern office workspace with people collaborating"" not ""office""

**CHARTS (optional):** For numeric/trend data (Q1~Q4 매출, 성장률 등), add ""charts"" array:
  {{ ""chartType"": ""bar""|""line""|""pie"", ""title"": ""분기별 매출"", ""data"": {{""Q1"": 100, ""Q2"": 150}} }}

**TABLES (optional):** For comparisons (제품/가격/평점, 장단점 비교), add ""tables"" array:
  {{ ""headerRow"": true, ""rows"": [[""제품"",""가격"",""평점""], [""A"",""10만원"",""4.5""]] }}

**STYLE: {request.Style}**
{styleGuidance}

**REQUIRED JSON FORMAT (you MUST follow this exactly):**
{{
  ""slides"": [
    {{
      ""title"": ""Clear and engaging slide title"",
      ""content"": ""• First key point\n• Second key point\n• Third key point"",
      ""layout"": ""title-content"",
      ""imageDescription"": ""Specific description (optional)"",
      ""charts"": [{{ ""chartType"": ""bar"", ""title"": ""Chart title"", ""data"": {{""A"": 10, ""B"": 20}} }}],
      ""tables"": [{{ ""headerRow"": true, ""rows"": [[""Col1"",""Col2""], [""A"",""B""]] }}]
    }}
  ]
}}

**CRITICAL REMINDERS:**
- Topic: {contentForSlides}
- Number of slides: {request.SlideCount}
- Response format: ONLY JSON, no other text. Every slide must have ""layout"".
- Every slide title and content must be specifically about the topic above. No generic or off-topic content.";
                userMessage = $"Create a {request.SlideCount}-slide presentation. The topic (you must stick to this only): {contentForSlides}\n\n" +
                    "Requirements: Every slide must be strictly about this topic. Use specific titles and bullets, not placeholders like \"Slide 1\" or \"Content goes here\". Respond with ONLY a valid JSON object in the exact format specified. No explanatory text or markdown.";
            }

        var chatRequest = new ChatMessageRequestDto
        {
            Messages = new List<ChatMessageDto>
            {
                new ChatMessageDto
                {
                    Role = "system",
                    Content = systemPrompt
                },
                new ChatMessageDto
                {
                    Role = "user",
                    Content = userMessage
                }
            },
            Temperature = 0.3m, // 더 일관된 응답을 위해 낮은 temperature 사용
            MaxTokens = 4096
        };

            var model = request.Model ?? "gpt-4-turbo";
            
            _logger.LogInformation("Calling AI service for presentation generation: ServiceId={ServiceId}, Model={Model}, PromptLength={PromptLength}", 
                request.ServiceId, model, request.Prompt?.Length ?? 0);
            
            AiResponseDto? aiResponse = null;
            try
            {
                aiResponse = await _aiProxyService.SendChatMessageAsync(request.ServiceId, model, chatRequest, cancellationToken);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error calling AI service for presentation generation: ServiceId={ServiceId}, Model={Model}, Error={Error}", 
                    request.ServiceId, model, ex.Message);
                throw; // 예외를 다시 던져서 상위에서 처리하도록
            }

            if (aiResponse == null || string.IsNullOrEmpty(aiResponse.Content))
            {
                _logger.LogWarning("AI response is empty or null, generating default slides. ServiceId={ServiceId}, Model={Model}", 
                    request.ServiceId, model);
                return GenerateDefaultSlides(request.SlideCount);
            }
            
            _logger.LogInformation("AI response received successfully: ContentLength={Length}, Model={Model}", 
                aiResponse.Content.Length, aiResponse.Model);

            _logger.LogDebug("AI response received, length={Length}", aiResponse.Content.Length);

            // AI 응답에서 JSON 파싱
            var slides = ParseSlidesFromAIResponse(aiResponse.Content, request.SlideCount);

            // 슬라이드 번호 할당
            for (int i = 0; i < slides.Count; i++)
            {
                slides[i].SlideNumber = i + 1;
            }

            _logger.LogInformation("Successfully generated {Count} slides", slides.Count);
            return slides;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error in GenerateSlidesWithAIAsync: {Message}", ex.Message);
            // 에러 발생 시 기본 슬라이드 반환
            return GenerateDefaultSlides(request.SlideCount);
        }
    }

    private List<SlideDto> ParseSlidesFromAIResponse(string aiResponse, int expectedSlideCount)
    {
        try
        {
            // JSON 코드 블록 제거
            var jsonText = aiResponse;
            if (jsonText.Contains("```json"))
            {
                var startIndex = jsonText.IndexOf("```json") + 7;
                var endIndex = jsonText.IndexOf("```", startIndex);
                if (endIndex > startIndex)
                {
                    jsonText = jsonText.Substring(startIndex, endIndex - startIndex).Trim();
                }
            }
            else if (jsonText.Contains("```"))
            {
                var startIndex = jsonText.IndexOf("```") + 3;
                var endIndex = jsonText.IndexOf("```", startIndex);
                if (endIndex > startIndex)
                {
                    jsonText = jsonText.Substring(startIndex, endIndex - startIndex).Trim();
                }
            }

            var options = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            };

            var response = JsonSerializer.Deserialize<Dictionary<string, object>>(jsonText, options);
            if (response == null || !response.ContainsKey("slides"))
            {
                _logger.LogWarning("AI response does not contain 'slides' key. Response: {Response}", aiResponse);
                return GenerateDefaultSlides(expectedSlideCount);
            }

            var slidesJson = response["slides"].ToString();
            if (string.IsNullOrEmpty(slidesJson))
            {
                return GenerateDefaultSlides(expectedSlideCount);
            }

            var slides = JsonSerializer.Deserialize<List<SlideDto>>(slidesJson, options);
            if (slides == null || slides.Count == 0)
            {
                _logger.LogWarning("Failed to deserialize slides from AI response");
                return GenerateDefaultSlides(expectedSlideCount);
            }

            // SlideId가 없는 경우 생성
            foreach (var slide in slides)
            {
                if (string.IsNullOrEmpty(slide.SlideId))
                    slide.SlideId = Guid.NewGuid().ToString();
                if (string.IsNullOrWhiteSpace(slide.Layout))
                    slide.Layout = "title-content";
            }

            // 슬라이드 수 보정: 초과 시 앞 N장만, 부족 시 기본 슬라이드로 채움
            if (slides.Count > expectedSlideCount)
            {
                slides = slides.Take(expectedSlideCount).ToList();
                _logger.LogInformation("Trimmed slides to {Count}", expectedSlideCount);
            }
            else while (slides.Count < expectedSlideCount)
            {
                slides.Add(new SlideDto
                {
                    SlideId = Guid.NewGuid().ToString(),
                    Title = $"Slide {slides.Count + 1}",
                    Content = "Content goes here",
                    Layout = slides.Count == expectedSlideCount - 1 ? "thank-you" : "title-content",
                    SlideNumber = slides.Count + 1
                });
            }

            // 첫 슬라이드: 제목 슬라이드로 layout 통일
            if (slides.Count > 0)
            {
                var first = slides[0];
                var firstLayout = (first.Layout ?? "").Trim().ToLowerInvariant();
                if (firstLayout != "title-only" && firstLayout != "title-content")
                    first.Layout = "title-content";
            }

            // 마지막 슬라이드: thank-you 권장
            if (slides.Count > 1)
            {
                var last = slides[slides.Count - 1];
                var lastLayout = (last.Layout ?? "").Trim().ToLowerInvariant();
                if (string.IsNullOrEmpty(lastLayout) || lastLayout == "title-content")
                    last.Layout = "thank-you";
            }

            return slides;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing slides from AI response: {Response}", aiResponse);
            return GenerateDefaultSlides(expectedSlideCount);
        }
    }

    private List<SlideDto> GenerateDefaultSlides(int count)
    {
        var slides = new List<SlideDto>();
        for (int i = 1; i <= count; i++)
        {
            slides.Add(new SlideDto
            {
                SlideId = Guid.NewGuid().ToString(),
                Title = $"Slide {i}",
                Content = "Content goes here",
                Layout = "title-content",
                SlideNumber = i
            });
        }
        return slides;
    }

    private static string? GetImageStyleSuffix(string? style)
    {
        if (string.IsNullOrWhiteSpace(style)) return null;
        var s = style.Trim().ToLowerInvariant();
        return s switch
        {
            "business" => "Professional, clean, business presentation style.",
            "education" => "Clear, educational illustration style.",
            "marketing" => "Modern, high-impact, marketing visual.",
            "creative" => "Creative, visually striking, memorable.",
            _ => null
        };
    }

    private static string? GetDefaultThemeIdForStyle(string? style)
    {
        if (string.IsNullOrWhiteSpace(style)) return null;
        var s = style.Trim().ToLowerInvariant();
        return s switch
        {
            "business" => PresentationThemes.BusinessBlue,
            "education" => PresentationThemes.Education,
            "marketing" => PresentationThemes.Marketing,
            "creative" => PresentationThemes.Minimal,
            _ => null
        };
    }

    private static string GetStyleGuidance(string style)
    {
        var s = (style ?? "business").Trim().ToLowerInvariant();
        return s switch
        {
            "education" => "- Education style: Use clear definitions, step-by-step explanations, and examples. Structure content for learning (intro → concept → example → summary).",
            "marketing" => "- Marketing style: Emphasize value proposition, benefits, and call-to-action. Use persuasive, benefit-focused language. End with impact or next step.",
            "creative" => "- Creative style: Use storytelling, analogies, and visual descriptions. One strong idea per slide. Prefer memorable phrases and image-friendly content.",
            _ => "- Business style: Be concise and data-oriented. Clear conclusions and takeaways. Professional tone. Prefer facts and structure over decorative content."
        };
    }

    private string ExtractTitleFromPrompt(string prompt)
    {
        if (string.IsNullOrEmpty(prompt))
            return "New Presentation";

        // 프롬프트의 첫 부분을 제목으로 사용 (최대 50자)
        var title = prompt.Length > 50 ? prompt.Substring(0, 50) + "..." : prompt;
        return title;
    }

    public async Task<PresentationDto> GetPresentationAsync(int presentationId, int userId)
    {
        var presentation = await _context.Presentations
            .FirstOrDefaultAsync(p => p.PresentationId == presentationId && p.UserId == userId);

        if (presentation == null)
            throw new InvalidOperationException("Presentation not found");

        // PresentationSlides 테이블에서 슬라이드 로드
        var slideEntities = await _context.PresentationSlides
            .Where(s => s.PresentationId == presentationId)
            .OrderBy(s => s.SlideNumber)
            .ToListAsync();

        List<SlideDto> slides;
        if (slideEntities.Count > 0)
        {
            slides = slideEntities.Select(EntityToSlideDto).ToList();
        }
        else if (!string.IsNullOrEmpty(presentation.Slides))
        {
            // 레거시 JSON 폴백 (마이그레이션 전 데이터)
            try
            {
                slides = JsonSerializer.Deserialize<List<SlideDto>>(presentation.Slides) ?? new List<SlideDto>();
                _logger.LogInformation("Presentation {PresentationId}: loaded {Count} slides from legacy JSON column", presentationId, slides.Count);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error deserializing legacy slides for presentation {PresentationId}", presentationId);
                slides = new List<SlideDto>();
            }
        }
        else
        {
            slides = new List<SlideDto>();
        }

        return new PresentationDto
        {
            PresentationId = presentation.PresentationId,
            UserId = presentation.UserId,
            Title = presentation.Title,
            Slides = slides,
            ThemeId = presentation.ThemeId,
            SlideSize = presentation.SlideSize ?? "16:9",
            CreatedAt = presentation.CreatedAt,
            UpdatedAt = presentation.UpdatedAt
        };
    }

    public async Task<PresentationDto> UpdatePresentationAsync(int presentationId, int userId, PresentationDto presentation)
    {
        // AnyAsync — Presentations.Slides 컬럼을 로드하지 않음 (잘림 오류 근본 방지)
        var exists = await _context.Presentations
            .AnyAsync(p => p.PresentationId == presentationId && p.UserId == userId);
        if (!exists)
            throw new InvalidOperationException("Presentation not found");

        var title = (presentation.Title ?? string.Empty);
        if (title.Length > 200) title = title.Substring(0, 200);

        var themeId = presentation.ThemeId?.Trim();
        if (!string.IsNullOrEmpty(themeId) && themeId.Length > 50) themeId = themeId.Substring(0, 50);
        if (string.IsNullOrWhiteSpace(themeId)) themeId = null;

        var slideSize = presentation.SlideSize?.Trim();
        if (string.IsNullOrWhiteSpace(slideSize)) slideSize = "16:9";
        if (slideSize.Length > 20) slideSize = "16:9";

        // ExecuteUpdateAsync — Slides 컬럼을 절대 건드리지 않는 직접 SQL UPDATE
        await _context.Presentations
            .Where(p => p.PresentationId == presentationId && p.UserId == userId)
            .ExecuteUpdateAsync(s => s
                .SetProperty(p => p.Title, title)
                .SetProperty(p => p.ThemeId, themeId)
                .SetProperty(p => p.SlideSize, slideSize)
                .SetProperty(p => p.UpdatedAt, DateTime.UtcNow));

        // PresentationSlides 테이블 — 기존 슬라이드 전체 삭제 후 재삽입
        var existingSlides = await _context.PresentationSlides
            .Where(s => s.PresentationId == presentationId)
            .ToListAsync();
        _context.PresentationSlides.RemoveRange(existingSlides);

        var incomingSlides = presentation.Slides ?? new List<SlideDto>();
        var newSlideEntities = incomingSlides
            .Select((s, idx) => SlideDtoToEntity(s, presentationId, idx + 1))
            .ToList();
        _context.PresentationSlides.AddRange(newSlideEntities);

        try
        {
            await _context.SaveChangesAsync();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error saving presentation {PresentationId} to PresentationSlides", presentationId);
            throw new InvalidOperationException($"Failed to save presentation: {ex.InnerException?.Message ?? ex.Message}", ex);
        }

        return await GetPresentationAsync(presentationId, userId);
    }

    public async Task<PresentationDto> AddSlideAsync(int presentationId, int userId, SlideDto slide)
    {
        // 소유자 확인
        var exists = await _context.Presentations
            .AnyAsync(p => p.PresentationId == presentationId && p.UserId == userId);
        if (!exists)
            throw new InvalidOperationException("Presentation not found");

        var maxSlideNumber = await _context.PresentationSlides
            .Where(s => s.PresentationId == presentationId)
            .MaxAsync(s => (int?)s.SlideNumber) ?? 0;

        slide.SlideNumber = maxSlideNumber + 1;
        var entity = SlideDtoToEntity(slide, presentationId, slide.SlideNumber);
        _context.PresentationSlides.Add(entity);

        await _context.Presentations
            .Where(p => p.PresentationId == presentationId)
            .ExecuteUpdateAsync(s => s.SetProperty(p => p.UpdatedAt, DateTime.UtcNow));

        await _context.SaveChangesAsync();
        return await GetPresentationAsync(presentationId, userId);
    }

    /// <summary>직렬화 전 전체 슬라이드 목록 정규화 (PUT presentation / PUT slide 공통). 문자열 잘림 방지를 위해 긴 필드 절단.</summary>
    /// <param name="maxContentPerSlide">슬라이드당 Content 최대 길이. 0이면 기본값 사용. aggressive 모드에서는 더 작은 값 사용.</param>
    private static List<SlideDto> NormalizeSlidesForSerialization(List<SlideDto> slides, int maxContentPerSlide = 0)
    {
        const int DefaultMaxContent = 20000;
        int MaxContent = maxContentPerSlide > 0 ? maxContentPerSlide : DefaultMaxContent;
        const int MaxTitle = 2000;
        const int MaxImageUrl = 2000;
        const int MaxImageDesc = 2000;
        const int MaxImagePrompt = 2000;
        const int MaxImageItem = 2000;

        if (slides == null || slides.Count == 0) return new List<SlideDto>();
        var list = new List<SlideDto>(slides.Count);
        foreach (var s in slides)
        {
            if (s == null) continue;
            var title = s.Title ?? "";
            var content = s.Content ?? "";
            var imgUrl = s.ImageUrl;
            if (!string.IsNullOrEmpty(imgUrl))
            {
                if (imgUrl.StartsWith("data:", StringComparison.OrdinalIgnoreCase))
                    imgUrl = null; // base64 data URL은 DB에 저장하지 않음 (문자열 잘림 방지)
                else if (imgUrl.Length > MaxImageUrl)
                    imgUrl = imgUrl.Substring(0, MaxImageUrl);
            }
            var imgDesc = s.ImageDescription;
            if (!string.IsNullOrEmpty(imgDesc) && imgDesc.Length > MaxImageDesc)
                imgDesc = imgDesc.Substring(0, MaxImageDesc);
            var imgPrompt = s.ImagePrompt;
            if (!string.IsNullOrEmpty(imgPrompt) && imgPrompt.Length > MaxImagePrompt)
                imgPrompt = imgPrompt.Substring(0, MaxImagePrompt);

            list.Add(new SlideDto
            {
                SlideId = s.SlideId ?? Guid.NewGuid().ToString(),
                SlideNumber = s.SlideNumber,
                Title = title.Length > MaxTitle ? title.Substring(0, MaxTitle) : title,
                Content = content.Length > MaxContent ? content.Substring(0, MaxContent) : content,
                Layout = s.Layout ?? "title-content",
                Images = NormalizeImagesList(s.Images, MaxImageItem),
                Charts = NormalizeChartsList(s.Charts),
                Tables = NormalizeTablesList(s.Tables),
                ImageDescription = imgDesc,
                ImageUrl = imgUrl,
                ImagePrompt = imgPrompt
            });
        }
        return list;
    }

    private static List<string> NormalizeImagesList(List<string>? images, int maxPerItem = 2000)
    {
        if (images == null) return new List<string>();
        var list = new List<string>(images.Count);
        foreach (var item in images)
        {
            if (item == null) continue;
            var s = item is string str ? str : item.ToString() ?? "";
            if (s.StartsWith("data:", StringComparison.OrdinalIgnoreCase))
                continue; // base64 data URL은 DB에 저장하지 않음
            if (s.Length > maxPerItem)
                s = s.Substring(0, maxPerItem);
            list.Add(s);
        }
        return list;
    }

    /// <summary>JSON 직렬화 결과가 maxChars 이하가 되도록 Content를 반복 절단.</summary>
    private static List<SlideDto> TruncateSlidesToFitMaxSize(List<SlideDto> slides, int maxChars, JsonSerializerOptions jsonOptions)
    {
        var list = new List<SlideDto>(slides);
        for (int round = 0; round < 20; round++)
        {
            var json = JsonSerializer.Serialize(list, jsonOptions);
            if (json.Length <= maxChars) return list;
            int excess = json.Length - maxChars;
            int perSlide = Math.Max(100, excess / Math.Max(1, list.Count));
            var next = new List<SlideDto>(list.Count);
            foreach (var s in list)
            {
                var content = s.Content ?? "";
                if (content.Length > perSlide)
                    content = content.Substring(0, Math.Max(0, content.Length - perSlide));
                next.Add(new SlideDto
                {
                    SlideId = s.SlideId,
                    SlideNumber = s.SlideNumber,
                    Title = s.Title,
                    Content = content,
                    Layout = s.Layout,
                    Images = s.Images,
                    Charts = s.Charts,
                    Tables = s.Tables,
                    ImageDescription = s.ImageDescription,
                    ImageUrl = s.ImageUrl,
                    ImagePrompt = s.ImagePrompt
                });
            }
            list = next;
        }
        return list;
    }

    private const int MaxChartDataValueLength = 500;
    private const int MaxChartDataKeys = 50;

    private static List<ChartDto> NormalizeChartsList(List<ChartDto>? charts)
    {
        if (charts == null) return new List<ChartDto>();
        var list = new List<ChartDto>(charts.Count);
        foreach (var c in charts)
        {
            if (c == null) continue;
            var data = new Dictionary<string, object>();
            if (c.Data != null)
            {
                int keyCount = 0;
                foreach (var kv in c.Data)
                {
                    if (kv.Key == null || keyCount >= MaxChartDataKeys) continue;
                    var val = kv.Value;
                    if (val != null)
                    {
                        var str = val.ToString();
                        if (!string.IsNullOrEmpty(str) && str.Length > MaxChartDataValueLength)
                            val = str.Substring(0, MaxChartDataValueLength);
                    }
                    data[kv.Key] = val!;
                    keyCount++;
                }
            }
            var chartTitle = c.Title ?? "";
            if (chartTitle.Length > 500) chartTitle = chartTitle.Substring(0, 500);
            list.Add(new ChartDto
            {
                ChartId = c.ChartId ?? Guid.NewGuid().ToString(),
                ChartType = c.ChartType ?? "bar",
                Title = chartTitle,
                Data = data
            });
        }
        return list;
    }

    private const int MaxTableRows = 50;
    private const int MaxTableCellsPerRow = 20;
    private const int MaxTableCellLength = 500;

    private static List<TableDto> NormalizeTablesList(List<TableDto>? tables)
    {
        if (tables == null) return new List<TableDto>();
        var list = new List<TableDto>(Math.Min(tables.Count, 10));
        foreach (var t in tables.Take(10))
        {
            if (t == null || t.Rows == null || t.Rows.Count == 0) continue;
            var rows = new List<List<string>>();
            foreach (var row in t.Rows.Take(MaxTableRows))
            {
                if (row == null) continue;
                var cells = new List<string>();
                foreach (var cell in row.Take(MaxTableCellsPerRow))
                {
                    var s = cell?.ToString()?.Trim() ?? "";
                    if (s.Length > MaxTableCellLength) s = s.Substring(0, MaxTableCellLength);
                    cells.Add(s);
                }
                if (cells.Count > 0) rows.Add(cells);
            }
            if (rows.Count > 0)
                list.Add(new TableDto { HeaderRow = t.HeaderRow, Rows = rows });
        }
        return list;
    }

    // ──────────────────────────────────────────────────────────────────────
    // PresentationSlide 엔티티 ↔ SlideDto 변환 헬퍼
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>JSON 직렬화 옵션 — ChartDto.Data 등 Dictionary serialization 지원</summary>
    private static readonly JsonSerializerOptions _slideJsonOptions = new()
    {
        WriteIndented = false,
        DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
    };

    private static SlideDto EntityToSlideDto(PresentationSlide entity)
    {
        List<ChartDto>? charts = null;
        if (!string.IsNullOrEmpty(entity.ChartsJson))
        {
            try { charts = JsonSerializer.Deserialize<List<ChartDto>>(entity.ChartsJson, _slideJsonOptions); } catch { /* 무시 */ }
        }
        List<TableDto>? tables = null;
        if (!string.IsNullOrEmpty(entity.TablesJson))
        {
            try { tables = JsonSerializer.Deserialize<List<TableDto>>(entity.TablesJson, _slideJsonOptions); } catch { /* 무시 */ }
        }
        List<string>? images = null;
        if (!string.IsNullOrEmpty(entity.ImagesJson))
        {
            try { images = JsonSerializer.Deserialize<List<string>>(entity.ImagesJson, _slideJsonOptions); } catch { /* 무시 */ }
        }
        return new SlideDto
        {
            SlideId = entity.SlideId,
            SlideNumber = entity.SlideNumber,
            Title = entity.Title,
            Content = entity.Content,
            Layout = entity.Layout,
            ImageUrl = entity.ImageUrl,
            ImageDescription = entity.ImageDescription,
            ImagePrompt = entity.ImagePrompt,
            Charts = charts ?? new List<ChartDto>(),
            Tables = tables ?? new List<TableDto>(),
            Images = images ?? new List<string>()
        };
    }

    private PresentationSlide SlideDtoToEntity(SlideDto dto, int presentationId, int slideNumber)
    {
        var now = DateTime.UtcNow;

        var title = dto.Title ?? "";
        if (title.Length > 500) title = title.Substring(0, 500);

        var imageUrl = dto.ImageUrl;
        if (!string.IsNullOrEmpty(imageUrl) && imageUrl.StartsWith("data:", StringComparison.OrdinalIgnoreCase))
            imageUrl = null;
        if (!string.IsNullOrEmpty(imageUrl) && imageUrl.Length > 2000)
            imageUrl = imageUrl.Substring(0, 2000);

        var imageDesc = dto.ImageDescription;
        if (!string.IsNullOrEmpty(imageDesc) && imageDesc.Length > 2000)
            imageDesc = imageDesc.Substring(0, 2000);

        var imagePrompt = dto.ImagePrompt;
        if (!string.IsNullOrEmpty(imagePrompt) && imagePrompt.Length > 2000)
            imagePrompt = imagePrompt.Substring(0, 2000);

        var normalizedCharts = NormalizeChartsList(dto.Charts);
        var normalizedTables = NormalizeTablesList(dto.Tables);
        var normalizedImages = NormalizeImagesList(dto.Images);

        var slideId = string.IsNullOrEmpty(dto.SlideId) ? Guid.NewGuid().ToString() : dto.SlideId;
        if (slideId.Length > 50) slideId = Guid.NewGuid().ToString();

        var layout = dto.Layout ?? "title-content";
        if (layout.Length > 50) layout = "title-content";

        return new PresentationSlide
        {
            SlideId = slideId,
            PresentationId = presentationId,
            SlideNumber = slideNumber,
            Title = title,
            Content = dto.Content ?? "",
            Layout = layout,
            ImageUrl = imageUrl,
            ImageDescription = imageDesc,
            ImagePrompt = imagePrompt,
            ChartsJson = normalizedCharts.Count > 0 ? JsonSerializer.Serialize(normalizedCharts, _slideJsonOptions) : null,
            TablesJson = normalizedTables.Count > 0 ? JsonSerializer.Serialize(normalizedTables, _slideJsonOptions) : null,
            ImagesJson = normalizedImages.Count > 0 ? JsonSerializer.Serialize(normalizedImages, _slideJsonOptions) : null,
            CreatedAt = now,
            UpdatedAt = now
        };
    }

    public async Task<PresentationDto> UpdateSlideAsync(int presentationId, int userId, string slideId, SlideDto slide)
    {
        // 소유자 확인 — AnyAsync: Presentations.Slides 컬럼 로드 안 함
        var exists = await _context.Presentations
            .AnyAsync(p => p.PresentationId == presentationId && p.UserId == userId);
        if (!exists)
            throw new InvalidOperationException("Presentation not found");

        var slideExists = await _context.PresentationSlides
            .AnyAsync(s => s.PresentationId == presentationId && s.SlideId == slideId);
        if (!slideExists)
            throw new InvalidOperationException($"Slide not found: {slideId}");

        // 필드 길이 보호
        var title = slide?.Title ?? "";
        if (title.Length > 500) title = title.Substring(0, 500);

        var content = slide?.Content ?? "";

        var layout = slide?.Layout ?? "title-content";
        if (layout.Length > 50) layout = "title-content";

        var imageUrl = slide?.ImageUrl;
        if (!string.IsNullOrEmpty(imageUrl) && imageUrl.StartsWith("data:", StringComparison.OrdinalIgnoreCase))
            imageUrl = null;
        if (!string.IsNullOrEmpty(imageUrl) && imageUrl.Length > 2000)
            imageUrl = imageUrl.Substring(0, 2000);

        var imgDesc = slide?.ImageDescription;
        if (!string.IsNullOrEmpty(imgDesc) && imgDesc.Length > 2000)
            imgDesc = imgDesc.Substring(0, 2000);

        var imgPrompt = slide?.ImagePrompt;
        if (!string.IsNullOrEmpty(imgPrompt) && imgPrompt.Length > 2000)
            imgPrompt = imgPrompt.Substring(0, 2000);

        var normalizedCharts = NormalizeChartsList(slide?.Charts);
        var normalizedTables = NormalizeTablesList(slide?.Tables);
        var normalizedImages = NormalizeImagesList(slide?.Images);

        var chartsJson = normalizedCharts.Count > 0 ? JsonSerializer.Serialize(normalizedCharts, _slideJsonOptions) : null;
        var tablesJson = normalizedTables.Count > 0 ? JsonSerializer.Serialize(normalizedTables, _slideJsonOptions) : null;
        var imagesJson = normalizedImages.Count > 0 ? JsonSerializer.Serialize(normalizedImages, _slideJsonOptions) : null;

        var now = DateTime.UtcNow;

        // ExecuteUpdateAsync — PresentationSlide를 EF Core 변경 추적 없이 직접 SQL UPDATE
        // (SaveChangesAsync를 사용하지 않으므로 Presentations.Slides 컬럼이 개입될 여지 없음)
        await _context.PresentationSlides
            .Where(s => s.PresentationId == presentationId && s.SlideId == slideId)
            .ExecuteUpdateAsync(s => s
                .SetProperty(p => p.Title, title)
                .SetProperty(p => p.Content, content)
                .SetProperty(p => p.Layout, layout)
                .SetProperty(p => p.ImageUrl, imageUrl)
                .SetProperty(p => p.ImageDescription, imgDesc)
                .SetProperty(p => p.ImagePrompt, imgPrompt)
                .SetProperty(p => p.ChartsJson, chartsJson)
                .SetProperty(p => p.TablesJson, tablesJson)
                .SetProperty(p => p.ImagesJson, imagesJson)
                .SetProperty(p => p.UpdatedAt, now));

        await _context.Presentations
            .Where(p => p.PresentationId == presentationId)
            .ExecuteUpdateAsync(s => s.SetProperty(p => p.UpdatedAt, now));

        return await GetPresentationAsync(presentationId, userId);
    }

    public async Task<PresentationDto> DeleteSlideAsync(int presentationId, int userId, string slideId)
    {
        // 소유자 확인
        var exists = await _context.Presentations
            .AnyAsync(p => p.PresentationId == presentationId && p.UserId == userId);
        if (!exists)
            throw new InvalidOperationException("Presentation not found");

        var entity = await _context.PresentationSlides
            .FirstOrDefaultAsync(s => s.PresentationId == presentationId && s.SlideId == slideId);
        if (entity == null)
            throw new InvalidOperationException("Slide not found");

        _context.PresentationSlides.Remove(entity);
        await _context.SaveChangesAsync();

        // 슬라이드 번호 재정렬
        var remaining = await _context.PresentationSlides
            .Where(s => s.PresentationId == presentationId)
            .OrderBy(s => s.SlideNumber)
            .ToListAsync();
        for (int i = 0; i < remaining.Count; i++)
            remaining[i].SlideNumber = i + 1;

        await _context.Presentations
            .Where(p => p.PresentationId == presentationId)
            .ExecuteUpdateAsync(s => s.SetProperty(p => p.UpdatedAt, DateTime.UtcNow));

        await _context.SaveChangesAsync();
        return await GetPresentationAsync(presentationId, userId);
    }

    public async Task<PresentationDto> ReorderSlidesAsync(int presentationId, int userId, List<string> slideIds)
    {
        // 소유자 확인
        var exists = await _context.Presentations
            .AnyAsync(p => p.PresentationId == presentationId && p.UserId == userId);
        if (!exists)
            throw new InvalidOperationException("Presentation not found");

        var entities = await _context.PresentationSlides
            .Where(s => s.PresentationId == presentationId)
            .ToListAsync();

        // slideIds 순서대로 SlideNumber 재할당
        var slideIdSet = new HashSet<string>(slideIds);
        for (int i = 0; i < slideIds.Count; i++)
        {
            var entity = entities.FirstOrDefault(s => s.SlideId == slideIds[i]);
            if (entity != null)
                entity.SlideNumber = i + 1;
        }
        // slideIds에 없는 슬라이드는 마지막에 추가
        int next = slideIds.Count + 1;
        foreach (var e in entities.Where(s => !slideIdSet.Contains(s.SlideId)).OrderBy(s => s.SlideNumber))
            e.SlideNumber = next++;

        await _context.Presentations
            .Where(p => p.PresentationId == presentationId)
            .ExecuteUpdateAsync(s => s.SetProperty(p => p.UpdatedAt, DateTime.UtcNow));

        await _context.SaveChangesAsync();
        return await GetPresentationAsync(presentationId, userId);
    }

    public async Task<Stream> ExportToPptxAsync(int presentationId, int userId, string? themeIdOverride = null)
    {
        var presentation = await GetPresentationAsync(presentationId, userId);
        if (!string.IsNullOrWhiteSpace(themeIdOverride))
            presentation.ThemeId = themeIdOverride.Trim();
        return await _pptxGenerationService.GeneratePptxAsync(presentation);
    }

    /// <summary>DB 저장 없이 클라이언트 데이터로 PPTX 생성. 문자열 잘림 오류 우회용.</summary>
    public Task<Stream> ExportToPptxFromDtoAsync(PresentationDto presentation)
    {
        return _pptxGenerationService.GeneratePptxAsync(presentation);
    }

    /// <summary>DB 저장 없이 클라이언트 데이터로 PDF 생성. 문자열 잘림 오류 우회용.</summary>
    public async Task<Stream> ExportToPdfFromDtoAsync(PresentationDto presentation)
    {
        Stream? pptxStream = null;
        string? tempPptxFile = null;
        string? tempPdfFile = null;
        try
        {
            pptxStream = await _pptxGenerationService.GeneratePptxAsync(presentation);
            if (pptxStream.CanSeek && pptxStream.Position > 0)
                pptxStream.Position = 0;
            var tempDir = Path.Combine(Path.GetTempPath(), "presentation_export");
            if (!Directory.Exists(tempDir))
                Directory.CreateDirectory(tempDir);
            tempPptxFile = Path.Combine(tempDir, $"temp_{Guid.NewGuid()}.pptx");
            tempPdfFile = Path.Combine(tempDir, $"temp_{Guid.NewGuid()}.pdf");
            using (var fileStream = new FileStream(tempPptxFile, FileMode.Create))
                await pptxStream.CopyToAsync(fileStream);
            pptxStream.Dispose();
            pptxStream = null;
            var pdfStream = await ConvertPptxToPdfAsync(tempPptxFile, tempPdfFile);
            try { if (File.Exists(tempPptxFile)) File.Delete(tempPptxFile); } catch { /* ignore */ }
            return pdfStream;
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "LibreOffice PDF conversion failed for inline export");
            if (pptxStream != null && pptxStream.CanRead)
            {
                try
                {
                    if (pptxStream.CanSeek) pptxStream.Position = 0;
                    return pptxStream;
                }
                catch { pptxStream?.Dispose(); }
            }
            throw new InvalidOperationException("LibreOffice PDF 변환 실패. PPTX를 다운로드하여 수동으로 PDF로 변환해 주세요.", ex);
        }
    }

    public async Task<PresentationDto> UpdateThemeAsync(int presentationId, int userId, string themeId)
    {
        var existing = await _context.Presentations
            .FirstOrDefaultAsync(p => p.PresentationId == presentationId && p.UserId == userId);
        if (existing == null)
            throw new InvalidOperationException("Presentation not found");
        existing.ThemeId = themeId;
        existing.UpdatedAt = DateTime.UtcNow;
        await _context.SaveChangesAsync();
        return await GetPresentationAsync(presentationId, userId);
    }

    public async Task<Stream> ExportToPdfAsync(int presentationId, int userId, string? themeIdOverride = null)
    {
        Stream? pptxStream = null;
        string? tempPptxFile = null;
        string? tempPdfFile = null;
        
        try
        {
            // PPTX를 먼저 생성한 후 LibreOffice를 통해 PDF로 변환
            pptxStream = await ExportToPptxAsync(presentationId, userId, themeIdOverride);
            
            // 스트림 위치 확인 및 재설정
            if (pptxStream.CanSeek && pptxStream.Position > 0)
            {
                pptxStream.Position = 0;
            }
            
            // PPTX를 임시 파일로 저장
            var tempDir = Path.Combine(Path.GetTempPath(), "presentation_export");
            if (!Directory.Exists(tempDir))
            {
                Directory.CreateDirectory(tempDir);
            }
            
            tempPptxFile = Path.Combine(tempDir, $"temp_{Guid.NewGuid()}.pptx");
            tempPdfFile = Path.Combine(tempDir, $"temp_{Guid.NewGuid()}.pdf");
            
            // PPTX 스트림을 파일로 저장
            using (var fileStream = new FileStream(tempPptxFile, FileMode.Create))
            {
                await pptxStream.CopyToAsync(fileStream);
            }
            
            // PPTX 스트림 닫기
            pptxStream.Dispose();
            pptxStream = null;
            
            // LibreOffice를 사용하여 PDF로 변환
            var pdfStream = await ConvertPptxToPdfAsync(tempPptxFile, tempPdfFile);
            
            // 임시 PPTX 파일 정리 (PDF 파일은 스트림이 닫힐 때 정리)
            try
            {
                if (File.Exists(tempPptxFile))
                {
                    File.Delete(tempPptxFile);
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to delete temporary PPTX file: {File}", tempPptxFile);
            }
            
            return pdfStream;
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "LibreOffice PDF conversion failed");
            
            // PPTX 스트림이 아직 열려있고 사용 가능한 경우 반환
            if (pptxStream != null && pptxStream.CanRead)
            {
                try
                {
                    if (pptxStream.CanSeek)
                    {
                        pptxStream.Position = 0;
                    }
                    return pptxStream;
                }
                catch
                {
                    pptxStream?.Dispose();
                }
            }
            
            // PPTX 스트림도 사용할 수 없으면 예외 재발생
            throw new InvalidOperationException($"PDF conversion failed: {ex.Message}", ex);
        }
        finally
        {
            // 정리되지 않은 리소스 정리
            if (pptxStream != null)
            {
                try
                {
                    pptxStream.Dispose();
                }
                catch { }
            }
        }
    }

    private string? GetLibreOfficePath()
    {
        // 설정에서 경로 가져오기
        var configuredPath = _configuration["FileUploadSettings:LibreOfficePath"];
        if (!string.IsNullOrEmpty(configuredPath) && File.Exists(configuredPath))
        {
            return configuredPath;
        }

        // 기본 경로 시도 (Windows)
        var windowsPaths = new[]
        {
            @"C:\Program Files\LibreOffice\program\soffice.exe",
            @"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            @"C:\Program Files\LibreOffice 7\program\soffice.exe",
            @"C:\Program Files\LibreOffice 6\program\soffice.exe"
        };

        foreach (var path in windowsPaths)
        {
            if (File.Exists(path))
            {
                return path;
            }
        }

        // Linux/Mac 기본 경로
        var unixPaths = new[]
        {
            "/usr/bin/libreoffice",
            "/usr/bin/soffice",
            "/usr/local/bin/libreoffice",
            "/opt/libreoffice/program/soffice"
        };

        foreach (var path in unixPaths)
        {
            if (File.Exists(path))
            {
                return path;
            }
        }

        return null;
    }

    private async Task<Stream> ConvertPptxToPdfAsync(string pptxPath, string pdfPath)
    {
        // LibreOffice 경로 가져오기 (자동 탐지)
        var libreOfficePath = GetLibreOfficePath();
        
        if (string.IsNullOrEmpty(libreOfficePath))
        {
            var errorMessage = "LibreOffice를 찾을 수 없습니다. PDF 변환을 사용하려면:\n\n" +
                             "1. LibreOffice를 설치하세요: https://www.libreoffice.org/download/\n" +
                             "2. 또는 appsettings.json에 LibreOfficePath를 설정하세요:\n" +
                             "   \"FileUploadSettings\": {\n" +
                             "     \"LibreOfficePath\": \"C:\\\\Program Files\\\\LibreOffice\\\\program\\\\soffice.exe\"\n" +
                             "   }";
            
            _logger.LogWarning("LibreOffice not found. Please install LibreOffice or configure the path in appsettings.json");
            throw new InvalidOperationException(errorMessage);
        }

        var processInfo = new ProcessStartInfo
        {
            FileName = libreOfficePath,
            Arguments = $"--headless --convert-to pdf --outdir \"{Path.GetDirectoryName(pdfPath)}\" \"{pptxPath}\"",
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true,
            WorkingDirectory = Path.GetDirectoryName(pdfPath)
        };

        using (var process = Process.Start(processInfo))
        {
            if (process == null)
            {
                throw new InvalidOperationException("Failed to start LibreOffice process");
            }

            // stdout/stderr를 WaitForExitAsync와 동시에 읽어 버퍼 데드락 방지
            var stdoutTask = process.StandardOutput.ReadToEndAsync();
            var stderrTask = process.StandardError.ReadToEndAsync();

            await process.WaitForExitAsync();
            await Task.WhenAll(stdoutTask, stderrTask);

            if (process.ExitCode != 0)
            {
                var error = stderrTask.Result;
                throw new InvalidOperationException($"LibreOffice conversion failed: {error}");
            }
        }

        // 변환된 PDF 파일 읽기
        var expectedPdfPath = Path.Combine(Path.GetDirectoryName(pdfPath)!, Path.GetFileNameWithoutExtension(pptxPath) + ".pdf");
        if (!File.Exists(expectedPdfPath))
        {
            throw new InvalidOperationException("PDF file was not created by LibreOffice");
        }

        // PDF 파일을 메모리 스트림으로 읽기
        var pdfBytes = await File.ReadAllBytesAsync(expectedPdfPath);
        var pdfStream = new MemoryStream(pdfBytes);
        
        // 임시 PDF 파일 정리 (비동기적으로)
        _ = Task.Run(async () =>
        {
            try
            {
                await Task.Delay(1000); // 스트림이 완전히 생성된 후 삭제
                if (File.Exists(expectedPdfPath))
                {
                    File.Delete(expectedPdfPath);
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to delete temporary PDF file: {File}", expectedPdfPath);
            }
        });
        
        return pdfStream;
    }
}
