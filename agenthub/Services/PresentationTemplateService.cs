using System.Text.Json;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;
using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;

namespace AIAgentManagement.Services;

public class PresentationTemplateService : IPresentationTemplateService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly IPptxTemplateParser _templateParser;
    private readonly IFileService _fileService;
    private readonly IAiProxyService _aiProxyService;
    private readonly ILogger<PresentationTemplateService> _logger;
    private readonly IConfiguration _configuration;
    private readonly string _templatePath;

    public PresentationTemplateService(
        AIAgentManagementDbContext context,
        IPptxTemplateParser templateParser,
        IFileService fileService,
        IAiProxyService aiProxyService,
        ILogger<PresentationTemplateService> logger,
        IConfiguration configuration)
    {
        _context = context;
        _templateParser = templateParser;
        _fileService = fileService;
        _aiProxyService = aiProxyService;
        _logger = logger;
        _configuration = configuration;
        _templatePath = Path.Combine(
            _configuration["FileUploadSettings:UploadPath"] ?? "wwwroot/uploads",
            "templates"
        );

        if (!Directory.Exists(_templatePath))
        {
            Directory.CreateDirectory(_templatePath);
        }
    }

    public async Task<PresentationTemplateDto> UploadTemplateAsync(int userId, IFormFile templateFile, TemplateUploadRequestDto request, CancellationToken cancellationToken = default)
    {
        try
        {
            // 파일 확장자 확인
            var extension = Path.GetExtension(templateFile.FileName).ToLowerInvariant();
            if (extension != ".pptx")
            {
                throw new InvalidOperationException("Only PPTX files are supported for templates");
            }

            // 템플릿 파일 저장
            using var fileStream = templateFile.OpenReadStream();
            var filePath = await _fileService.SaveFileAsync(fileStream, templateFile.FileName, "templates");

            // 템플릿 구조 파싱
            fileStream.Position = 0;
            var templateStructure = await _templateParser.ParseTemplateAsync(fileStream, cancellationToken);

            // 데이터베이스에 저장
            var template = new PresentationTemplate
            {
                TemplateName = request.TemplateName,
                Description = request.Description,
                TemplateFilePath = filePath,
                TemplateStructure = JsonSerializer.Serialize(templateStructure),
                Category = request.Category,
                IsPublic = request.IsPublic,
                CreatedBy = userId,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            };

            _context.PresentationTemplates.Add(template);
            await _context.SaveChangesAsync(cancellationToken);

            return await GetTemplateAsync(template.TemplateId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error uploading template");
            throw;
        }
    }

    public async Task<List<PresentationTemplateDto>> GetTemplatesAsync(int? userId = null, string? category = null, bool? isPublic = null)
    {
        var query = _context.PresentationTemplates.AsQueryable();

        if (userId.HasValue)
        {
            query = query.Where(t => t.CreatedBy == userId || t.IsPublic);
        }
        else if (isPublic.HasValue)
        {
            query = query.Where(t => t.IsPublic == isPublic.Value);
        }

        if (!string.IsNullOrEmpty(category))
        {
            query = query.Where(t => t.Category == category);
        }

        var templates = await query
            .OrderByDescending(t => t.CreatedAt)
            .ToListAsync();

        return templates.Select(t => MapToDto(t)).ToList();
    }

    public async Task<PresentationTemplateDto> GetTemplateAsync(int templateId)
    {
        var template = await _context.PresentationTemplates
            .Include(t => t.Creator)
            .FirstOrDefaultAsync(t => t.TemplateId == templateId);

        if (template == null)
        {
            throw new InvalidOperationException("Template not found");
        }

        return MapToDto(template);
    }

    public async Task<(Stream Stream, string FileName)?> GetTemplateFileAsync(int templateId)
    {
        var template = await _context.PresentationTemplates
            .FirstOrDefaultAsync(t => t.TemplateId == templateId);
        if (template == null || string.IsNullOrEmpty(template.TemplateFilePath))
            return null;

        var stream = await _fileService.GetFileAsync(template.TemplateFilePath);
        if (stream == null)
            return null;

        var fileName = template.TemplateName?.Trim();
        if (string.IsNullOrEmpty(fileName))
            fileName = "template";
        if (!fileName.EndsWith(".pptx", StringComparison.OrdinalIgnoreCase))
            fileName += ".pptx";

        return (stream, fileName);
    }

    public async Task<bool> DeleteTemplateAsync(int templateId, int userId)
    {
        var template = await _context.PresentationTemplates
            .FirstOrDefaultAsync(t => t.TemplateId == templateId);

        if (template == null)
        {
            return false;
        }

        // 권한 확인 (생성자만 삭제 가능)
        if (template.CreatedBy != userId)
        {
            throw new UnauthorizedAccessException("You don't have permission to delete this template");
        }

        // 파일 삭제
        try
        {
            if (!string.IsNullOrEmpty(template.TemplateFilePath))
            {
                await _fileService.DeleteFileAsync(template.TemplateFilePath);
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to delete template file: {FilePath}", template.TemplateFilePath);
        }

        _context.PresentationTemplates.Remove(template);
        await _context.SaveChangesAsync();

        return true;
    }

    public async Task<PresentationDto> GenerateFromTemplateAsync(int templateId, PresentationGenerationRequestDto request, CancellationToken cancellationToken = default)
    {
        var template = await GetTemplateAsync(templateId);
        if (template.TemplateStructure == null)
        {
            throw new InvalidOperationException("Template structure is not available");
        }

        // 템플릿 구조를 기반으로 AI 프롬프트 생성
        var slides = await GenerateSlidesFromTemplateAsync(template, request, cancellationToken);

        // 프레젠테이션 저장
        var presentation = new Presentation
        {
            UserId = request.UserId ?? 0,
            Title = ExtractTitleFromPrompt(request.Prompt),
            Slides = JsonSerializer.Serialize(slides),
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };

        _context.Presentations.Add(presentation);
        await _context.SaveChangesAsync(cancellationToken);

        return new PresentationDto
        {
            PresentationId = presentation.PresentationId,
            UserId = presentation.UserId,
            Title = presentation.Title,
            Slides = slides,
            CreatedAt = presentation.CreatedAt,
            UpdatedAt = presentation.UpdatedAt
        };
    }

    private async Task<List<SlideDto>> GenerateSlidesFromTemplateAsync(PresentationTemplateDto template, PresentationGenerationRequestDto request, CancellationToken cancellationToken)
    {
        var slides = new List<SlideDto>();
        var templateStructure = template.TemplateStructure!;

        // 템플릿의 각 슬라이드에 대해 AI로 내용 생성
        foreach (var templateSlide in templateStructure.Slides)
        {
            var slidePrompt = GenerateSlidePrompt(templateSlide, request.Prompt, templateStructure.SlideCount);
            
            var chatRequest = new ChatMessageRequestDto
            {
                Messages = new List<ChatMessageDto>
                {
                    new ChatMessageDto
                    {
                        Role = "system",
                        Content = $@"You are a professional presentation slide generator. 
Generate content for slide {templateSlide.SlideNumber} of {templateStructure.SlideCount} slides.

**SLIDE INFORMATION:**
- Layout: {templateSlide.LayoutType}
- Placeholders: {string.Join(", ", templateSlide.Placeholders.Select(p => $"{p.Type}({p.Index})"))}

**REQUIREMENTS:**
- Topic: {request.Prompt}
- Style: {request.Style}
- Generate content that fits the slide layout
- Use bullet points for body content
- Keep content concise and focused

**RESPONSE FORMAT (JSON only):**
{{
  ""title"": ""Slide title related to the topic"",
  ""content"": ""• First point\n• Second point\n• Third point"",
  ""layout"": ""{templateSlide.LayoutType}""
}}

Return ONLY valid JSON, no additional text."
                    },
                    new ChatMessageDto
                    {
                        Role = "user",
                        Content = slidePrompt
                    }
                },
                Temperature = 0.3m,
                MaxTokens = 2048
            };

            try
            {
                var model = request.Model ?? "gpt-4-turbo";
                var aiResponse = await _aiProxyService.SendChatMessageAsync(
                    request.ServiceId, 
                    model, 
                    chatRequest, 
                    cancellationToken);

                var slideContent = ParseSlideFromAIResponse(aiResponse.Content, templateSlide);
                slideContent.SlideNumber = templateSlide.SlideNumber;
                slides.Add(slideContent);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error generating content for slide {SlideNumber}", templateSlide.SlideNumber);
                // 에러 발생 시 기본 슬라이드 추가
                slides.Add(new SlideDto
                {
                    SlideId = Guid.NewGuid().ToString(),
                    SlideNumber = templateSlide.SlideNumber,
                    Title = $"Slide {templateSlide.SlideNumber}",
                    Content = "Content generation failed",
                    Layout = templateSlide.LayoutType
                });
            }
        }

        return slides;
    }

    private string GenerateSlidePrompt(TemplateSlideInfoDto templateSlide, string topic, int totalSlides)
    {
        return $"Create content for slide {templateSlide.SlideNumber} of {totalSlides} about: {topic}\n\n" +
               $"Layout: {templateSlide.LayoutType}\n" +
               $"Placeholders: {string.Join(", ", templateSlide.Placeholders.Select(p => p.Type))}";
    }

    private SlideDto ParseSlideFromAIResponse(string aiResponse, TemplateSlideInfoDto templateSlide)
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

            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
            var slide = JsonSerializer.Deserialize<SlideDto>(jsonText, options);

            if (slide == null)
            {
                throw new InvalidOperationException("Failed to parse slide from AI response");
            }

            slide.SlideId = Guid.NewGuid().ToString();
            slide.Layout = templateSlide.LayoutType;

            return slide;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing slide from AI response");
            return new SlideDto
            {
                SlideId = Guid.NewGuid().ToString(),
                SlideNumber = templateSlide.SlideNumber,
                Title = $"Slide {templateSlide.SlideNumber}",
                Content = "Content parsing failed",
                Layout = templateSlide.LayoutType
            };
        }
    }

    private string ExtractTitleFromPrompt(string prompt)
    {
        if (string.IsNullOrEmpty(prompt))
            return "New Presentation";

        var title = prompt.Length > 50 ? prompt.Substring(0, 50) + "..." : prompt;
        return title;
    }

    private PresentationTemplateDto MapToDto(PresentationTemplate template)
    {
        var dto = new PresentationTemplateDto
        {
            TemplateId = template.TemplateId,
            TemplateName = template.TemplateName,
            Description = template.Description,
            TemplateFilePath = template.TemplateFilePath,
            Category = template.Category,
            IsPublic = template.IsPublic,
            CreatedBy = template.CreatedBy,
            CreatedByName = template.Creator?.FullName ?? template.Creator?.Email ?? "Unknown",
            CreatedAt = template.CreatedAt,
            UpdatedAt = template.UpdatedAt
        };

        if (!string.IsNullOrEmpty(template.TemplateStructure))
        {
            try
            {
                dto.TemplateStructure = JsonSerializer.Deserialize<TemplateStructureDto>(template.TemplateStructure);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to deserialize template structure for template {TemplateId}", template.TemplateId);
            }
        }

        return dto;
    }
}
