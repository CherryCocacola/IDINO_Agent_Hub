using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;
using AIAgentManagement.Data;
using Microsoft.EntityFrameworkCore;
using System.Net.Http;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/image-generation")]
[Authorize]
public class ImageGenerationController : ControllerBase
{
    private readonly IAiProxyService _aiProxyService;
    private readonly IQuotaService _quotaService;
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<ImageGenerationController> _logger;
    private readonly IHttpClientFactory _httpClientFactory;

    private readonly IConfiguration _configuration;

    public ImageGenerationController(
        IAiProxyService aiProxyService,
        IQuotaService quotaService,
        AIAgentManagementDbContext context,
        ILogger<ImageGenerationController> logger,
        IHttpClientFactory httpClientFactory,
        IConfiguration configuration)
    {
        _aiProxyService = aiProxyService;
        _quotaService = quotaService;
        _context = context;
        _logger = logger;
        _httpClientFactory = httpClientFactory;
        _configuration = configuration;
    }

    [HttpPost("generate")]
    public async Task<ActionResult<ImageGenerationResponseDto>> GenerateImage([FromBody] ImageGenerationRequestDto? request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            if (request == null)
            {
                return BadRequest(ErrorResponseDto.BadRequest("요청 데이터가 없습니다."));
            }

            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            if (request.UserId.HasValue)
            {
                userId = request.UserId.Value;
            }

            // 서비스 정보 가져오기 (ImageGeneration 또는 Both 타입 지원)
            var service = await _context.ApiServices
                .FirstOrDefaultAsync(s => s.ServiceId == request.ServiceId 
                    && (s.ServiceType == "ImageGeneration" || s.ServiceType == "Both") 
                    && s.IsActive);
            
            if (service == null)
            {
                return BadRequest(ErrorResponseDto.BadRequest("Image generation service not found"));
            }

            // 할당량 체크
            var quotaCheck = await _quotaService.CheckQuotaAsync(userId, service.ServiceId);
            if (!quotaCheck.CanUse)
            {
                return BadRequest(ErrorResponseDto.BadRequest($"Quota exceeded: {quotaCheck.Message}"));
            }

            // Conversation 찾기 또는 생성 (이미지 생성 전에 수행하여 대화 히스토리 가져오기)
            Models.ChatConversation? conversation = null;
            int? conversationId = null;
            
            if (request.ConversationId.HasValue)
            {
                // 기존 Conversation 사용
                conversation = await _context.ChatConversations
                    .FirstOrDefaultAsync(c => c.ConversationId == request.ConversationId.Value && c.UserId == userId);
                conversationId = conversation?.ConversationId;
            }
            else if (request.AgentId.HasValue)
            {
                // Agent 기반 대화 찾기 또는 생성
                conversation = await _context.ChatConversations
                    .FirstOrDefaultAsync(c => 
                        c.UserId == userId && 
                        c.AgentId == request.AgentId.Value && 
                        !c.IsArchived);
                
                if (conversation == null)
                {
                    var agent = await _context.Agents
                        .FirstOrDefaultAsync(a => a.AgentId == request.AgentId.Value);
                    
                    conversation = new Models.ChatConversation
                    {
                        UserId = userId,
                        AgentId = request.AgentId,
                        ServiceId = service.ServiceId,
                        Title = agent?.AgentName ?? "이미지 생성",
                        Model = request.Model ?? service.DefaultModel ?? "dall-e-3",
                        Temperature = 0.7m,
                        MaxTokens = 2048,
                        MessageCount = 0,
                        TotalTokens = 0,
                        TotalCost = 0,
                        IsArchived = false,
                        IsPinned = false,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    };
                    _context.ChatConversations.Add(conversation);
                    await _context.SaveChangesAsync();
                }
                conversationId = conversation.ConversationId;
            }

            // conversationId가 있고 Messages가 없으면 이전 대화 메시지 가져오기 (Gemini Image 등 채팅 API 사용 모델용)
            if (conversationId.HasValue && (request.Messages == null || request.Messages.Count == 0))
            {
                var previousMessages = await _context.ChatMessages
                    .Where(m => m.ConversationId == conversationId.Value)
                    .OrderBy(m => m.CreatedAt)
                    .Select(m => new ChatMessageDto
                    {
                        Role = m.Role,
                        Content = m.Content
                    })
                    .ToListAsync();
                
                if (previousMessages.Any())
                {
                    request.Messages = previousMessages;
                    _logger.LogInformation("Loaded {Count} previous messages for conversation {ConversationId}", 
                        previousMessages.Count, conversationId.Value);
                }
            }

            // conversationId를 request에 설정 (이후 저장 로직에서 사용)
            request.ConversationId = conversationId;

            // 웹 검색 활성화 시 프롬프트에서 URL 감지 및 웹 검색 수행
            if (request.EnableWebSearch && !string.IsNullOrEmpty(request.Prompt))
            {
                // URL 패턴 감지 (http://, https://, www. 등)
                var urlPattern = new System.Text.RegularExpressions.Regex(
                    @"(https?://[^\s]+|www\.[^\s]+|instagram\.com/[^\s]+|facebook\.com/[^\s]+|twitter\.com/[^\s]+|x\.com/[^\s]+)",
                    System.Text.RegularExpressions.RegexOptions.IgnoreCase);
                
                var urlMatches = urlPattern.Matches(request.Prompt);
                if (urlMatches.Count > 0)
                {
                    _logger.LogInformation("URL detected in image generation prompt, performing web search. URLs: {Urls}", 
                        string.Join(", ", urlMatches.Cast<System.Text.RegularExpressions.Match>().Select(m => m.Value)));
                    
                    // URL을 포함한 검색 쿼리 생성
                    var searchQuery = request.Prompt;
                    var webSearchResults = await PerformWebSearchForImageGenerationAsync(searchQuery);
                    
                    if (!string.IsNullOrEmpty(webSearchResults))
                    {
                        // 웹 검색 결과를 프롬프트에 포함
                        request.Prompt = $"{request.Prompt}\n\n[웹 검색 결과]\n{webSearchResults}\n\n위 검색 결과를 참고하여 이미지를 생성해주세요.";
                        _logger.LogInformation("Web search results added to image generation prompt. Results length: {Length}", webSearchResults.Length);
                    }
                }
                else
                {
                    // URL이 없어도 일반 웹 검색 수행
                    _logger.LogInformation("Performing general web search for image generation prompt");
                    var webSearchResults = await PerformWebSearchForImageGenerationAsync(request.Prompt);
                    
                    if (!string.IsNullOrEmpty(webSearchResults))
                    {
                        request.Prompt = $"{request.Prompt}\n\n[웹 검색 결과]\n{webSearchResults}\n\n위 검색 결과를 참고하여 이미지를 생성해주세요.";
                        _logger.LogInformation("Web search results added to image generation prompt. Results length: {Length}", webSearchResults.Length);
                    }
                }
            }

            // 이미지 생성 요청 (API 키 사전 검증으로 명확한 오류 메시지 제공)
            var model = request.Model ?? service.DefaultModel ?? "dall-e-3";
            var serviceCode = service.ServiceCode?.Trim().ToLowerInvariant() ?? "";
            if (serviceCode is "dalle" or "openai")
            {
                var openaiKey = _configuration["AiApiSettings:OpenAI:ApiKey"];
                if (string.IsNullOrWhiteSpace(openaiKey))
                {
                    return BadRequest(ErrorResponseDto.BadRequest("OpenAI API 키가 설정되지 않았습니다. 설정 > API 설정에서 OpenAI API 키를 등록해 주세요."));
                }
            }
            var response = await _aiProxyService.SendImageGenerationAsync(service.ServiceId, model, request);

            // Conversation이 아직 생성되지 않은 경우에만 새로 생성
            if (!conversationId.HasValue)
            {
                // 새 Conversation 생성 (AgentId가 없는 경우)
                var conversationTitle = request.Prompt?.Length > 50 
                    ? request.Prompt.Substring(0, 50) + "..." 
                    : request.Prompt ?? "이미지 생성";
                
                conversation = new Models.ChatConversation
                {
                    UserId = userId,
                    AgentId = null,
                    ServiceId = service.ServiceId,
                    Title = conversationTitle,
                    Model = model,
                    Temperature = 0.7m,
                    MaxTokens = 2048,
                    MessageCount = 0,
                    TotalTokens = 0,
                    TotalCost = 0,
                    IsArchived = false,
                    IsPinned = false,
                    CreatedAt = DateTime.UtcNow,
                    UpdatedAt = DateTime.UtcNow
                };
                _context.ChatConversations.Add(conversation);
                await _context.SaveChangesAsync();
                conversationId = conversation.ConversationId;
            }

            // 사용자 메시지 저장 (프롬프트)
            if (conversationId.HasValue && !string.IsNullOrEmpty(request.Prompt))
            {
                var userMessage = new Models.ChatMessage
                {
                    ConversationId = conversationId.Value,
                    Role = "user",
                    Content = request.Prompt,
                    CreatedAt = DateTime.UtcNow
                };
                _context.ChatMessages.Add(userMessage);
            }

            // Assistant 메시지 저장 (이미지 생성 결과)
            if (conversationId.HasValue && response.ImageUrls != null && response.ImageUrls.Count > 0)
            {
                var imageUrlsJson = System.Text.Json.JsonSerializer.Serialize(response.ImageUrls);
                var assistantContent = $"이미지 생성 완료 ({response.ImageUrls.Count}개)";
                
                var assistantMessage = new Models.ChatMessage
                {
                    ConversationId = conversationId.Value,
                    Role = "assistant",
                    Content = assistantContent,
                    Attachments = imageUrlsJson,
                    Model = response.Model,
                    CreatedAt = DateTime.UtcNow
                };
                _context.ChatMessages.Add(assistantMessage);

                // Conversation 업데이트
                if (conversation != null)
                {
                    var messageCount = await _context.ChatMessages
                        .Where(m => m.ConversationId == conversationId.Value)
                        .CountAsync();
                    
                    conversation.MessageCount = messageCount;
                    conversation.TotalCost += response.Cost;
                    conversation.LastMessageAt = DateTime.UtcNow;
                    conversation.UpdatedAt = DateTime.UtcNow;
                }
            }

            // 사용량 기록 및 할당량 업데이트
            try
            {
                var usage = new Models.ApiUsage
                {
                    UserId = userId,
                    ServiceId = service.ServiceId,
                    ConversationId = conversationId,
                    Model = response.Model,
                    RequestCost = response.Cost,
                    RequestTime = DateTime.UtcNow,
                    ResponseTime = response.ResponseTime,
                    StatusCode = 200, // 이미지 생성 성공 — UsageHistory에서 "성공"으로 표시
                    CreatedAt = DateTime.UtcNow
                };
                _context.ApiUsages.Add(usage);
                
                // 모든 변경사항을 한 번에 저장 (트랜잭션 보장)
                await _context.SaveChangesAsync();

                // 할당량 업데이트 (이미지 생성은 토큰이 없으므로 0으로 전달)
                await _quotaService.RecordUsageAsync(userId, service.ServiceId, 0, response.Cost);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to record API usage for image generation");
                // 사용량 기록 실패해도 응답은 반환
            }

            // 응답에 conversationId 포함
            response.ConversationId = conversationId;

            return Ok(response);
        }
        catch (Exception ex)
        {
            var serviceId = request?.ServiceId ?? 0;
            var model = request?.Model ?? "(null)";
            var promptPreview = request?.Prompt != null 
                ? request.Prompt.Length > 100 ? request.Prompt.Substring(0, 100) + "..." : request.Prompt 
                : "(null)";
            
            _logger.LogError(ex, "Error generating image. ServiceId: {ServiceId}, Model: {Model}, Prompt: {Prompt}, Error: {Message}", 
                serviceId, model, promptPreview, ex.Message);
            
            var innerMsg = ex.InnerException?.Message ?? "";
            var fullMsg = string.IsNullOrEmpty(innerMsg) ? ex.Message : $"{ex.Message} ({innerMsg})";
            
            // 사용자 친화적 메시지로 변환
            var userMessage = fullMsg;
            if (fullMsg.Contains("API key is not configured", StringComparison.OrdinalIgnoreCase))
                userMessage = "API 키가 설정되지 않았습니다. 설정 > API 설정에서 해당 서비스의 API 키를 등록해 주세요.";
            else if (fullMsg.Contains("401") || fullMsg.Contains("Unauthorized") || fullMsg.Contains("Invalid API key"))
                userMessage = "API 키가 유효하지 않거나 만료되었습니다. OpenAI/서비스 설정에서 API 키를 확인해 주세요.";
            else if (fullMsg.Contains("429") || fullMsg.Contains("rate limit"))
                userMessage = "요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요.";
            else if (fullMsg.Contains("is not supported"))
                userMessage = $"선택한 서비스(ServiceId: {serviceId})가 이미지 생성을 지원하지 않습니다. DALL-E, Gemini Image 등 ImageGeneration 타입 서비스를 선택해 주세요.";
            else if (fullMsg.Contains("content policy", StringComparison.OrdinalIgnoreCase) || fullMsg.Contains("safety", StringComparison.OrdinalIgnoreCase) || fullMsg.Contains("inappropriate", StringComparison.OrdinalIgnoreCase))
                userMessage = "프롬프트가 콘텐츠 정책에 위배됩니다. 다른 표현으로 시도해 주세요.";
            
            var errorResponse = new
            {
                message = $"이미지 생성 실패: {userMessage}",
                error = ex.Message,
                innerError = ex.InnerException?.Message,
                serviceId,
                model
            };
            
            return StatusCode(500, errorResponse);
        }
    }

    [HttpGet("download")]
    public async Task<IActionResult> DownloadImage([FromQuery] string imageUrl, [FromQuery] string? filename = null)
    {
        try
        {
            if (string.IsNullOrEmpty(imageUrl))
            {
                return BadRequest(ErrorResponseDto.BadRequest("Image URL is required"));
            }

            var httpClient = _httpClientFactory.CreateClient();
            httpClient.Timeout = TimeSpan.FromSeconds(60);
            httpClient.DefaultRequestHeaders.Add("User-Agent", "Mozilla/5.0 (compatible; AIAgentManagement/1.0)");

            var response = await httpClient.GetAsync(imageUrl);
            response.EnsureSuccessStatusCode();

            var imageBytes = await response.Content.ReadAsByteArrayAsync();
            var contentType = response.Content.Headers.ContentType?.MediaType ?? "image/png";
            
            var downloadFilename = filename ?? $"generated-image-{DateTime.UtcNow:yyyyMMddHHmmss}.png";
            
            return File(imageBytes, contentType, downloadFilename);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error downloading image from URL: {ImageUrl}", imageUrl != null && imageUrl.Length > 100 ? imageUrl.Substring(0, 100) + "..." : imageUrl);
            return StatusCode(500, ErrorResponseDto.InternalError($"이미지 다운로드 실패: {ex.Message}"));
        }
    }

    [HttpGet("estimate-cost")]
    public async Task<ActionResult<object>> EstimateCost(
        [FromQuery] int serviceId,
        [FromQuery] string? model,
        [FromQuery] string size = "1024x1024",
        [FromQuery] string quality = "standard",
        [FromQuery] int numberOfImages = 1)
    {
        try
        {
            var service = await _context.ApiServices
                .FirstOrDefaultAsync(s => s.ServiceId == serviceId && (s.ServiceType == "ImageGeneration" || s.ServiceType == "Both") && s.IsActive);
            if (service == null)
            {
                return BadRequest(ErrorResponseDto.BadRequest("Image generation service not found"));
            }

            var estimatedCost = await _aiProxyService.CalculateImageGenerationCostAsync(
                serviceId, model ?? string.Empty, size, quality, numberOfImages);
            return Ok(new { estimatedCost });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error estimating image generation cost. ServiceId: {ServiceId}", serviceId);
            return StatusCode(500, ErrorResponseDto.InternalError($"Failed to estimate cost: {ex.Message}"));
        }
    }

    private async Task<string?> PerformWebSearchForImageGenerationAsync(string query)
    {
        try
        {
            var tavilyApiKey = _configuration["AiApiSettings:Tavily:ApiKey"];
            var tavilyBaseUrl = _configuration["AiApiSettings:Tavily:BaseUrl"] ?? "https://api.tavily.com";

            if (string.IsNullOrEmpty(tavilyApiKey))
            {
                _logger.LogWarning("Tavily API key is not configured for image generation web search");
                return null;
            }

            var client = _httpClientFactory.CreateClient();
            client.DefaultRequestHeaders.Add("api-key", tavilyApiKey);
            client.Timeout = TimeSpan.FromSeconds(30);

            var payload = new
            {
                api_key = tavilyApiKey,
                query = query,
                search_depth = "advanced", // 이미지 생성을 위해 더 깊은 검색
                include_answer = true,
                include_images = false,
                include_raw_content = true, // 이미지 생성을 위해 원본 콘텐츠 포함
                max_results = 10 // 더 많은 결과
            };

            var json = System.Text.Json.JsonSerializer.Serialize(payload);
            var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");

            var response = await client.PostAsync($"{tavilyBaseUrl}/search", content);
            
            if (!response.IsSuccessStatusCode)
            {
                var errorContent = await response.Content.ReadAsStringAsync();
                _logger.LogWarning("Tavily API error for image generation. Status: {StatusCode}, Response: {Response}", 
                    response.StatusCode, errorContent);
                return null;
            }

            var responseJson = await response.Content.ReadAsStringAsync();
            var jsonOptions = new System.Text.Json.JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            };

            var tavilyResponse = System.Text.Json.JsonSerializer.Deserialize<TavilySearchResponse>(responseJson, jsonOptions);

            if (tavilyResponse == null || tavilyResponse.Results == null || tavilyResponse.Results.Count == 0)
            {
                _logger.LogInformation("Tavily search returned no results for image generation");
                return null;
            }

            // 검색 결과를 포맷팅 (이미지 생성에 최적화)
            var searchResults = new System.Text.StringBuilder();
            
            if (!string.IsNullOrEmpty(tavilyResponse.Answer))
            {
                searchResults.AppendLine($"검색 요약: {tavilyResponse.Answer}");
            }

            searchResults.AppendLine("\n주요 정보:");
            foreach (var result in tavilyResponse.Results.Take(5)) // 상위 5개 결과만 사용
            {
                if (!string.IsNullOrEmpty(result.Title))
                {
                    searchResults.AppendLine($"- {result.Title}");
                }
                if (!string.IsNullOrEmpty(result.Content))
                {
                    // 이미지 생성을 위해 더 긴 콘텐츠 포함
                    var contentPreview = result.Content.Length > 500 
                        ? result.Content.Substring(0, 500) + "..." 
                        : result.Content;
                    searchResults.AppendLine($"  {contentPreview}");
                }
                if (!string.IsNullOrEmpty(result.Url))
                {
                    searchResults.AppendLine($"  출처: {result.Url}");
                }
                searchResults.AppendLine();
            }

            return searchResults.ToString();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error performing web search for image generation");
            return null;
        }
    }

    private class TavilySearchResponse
    {
        public string? Answer { get; set; }
        public List<TavilySearchResult>? Results { get; set; }
    }

    private class TavilySearchResult
    {
        public string? Title { get; set; }
        public string? Url { get; set; }
        public string? Content { get; set; }
    }
}
