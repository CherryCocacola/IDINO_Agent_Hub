using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.RateLimiting;
using System.Security.Claims;
using QRCoder;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;
using AIAgentManagement.Attributes;
using AIAgentManagement.Data;
using AIAgentManagement.Utils;
using AIAgentManagement.Exceptions;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class AgentsController : ControllerBase
{
    private readonly IAgentService _agentService;
    private readonly IChatService _chatService;
    private readonly IApiKeyService _apiKeyService;
    private readonly IBannedWordService _bannedWordService;
    private readonly IPiiDetectionService _piiDetectionService;
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<AgentsController> _logger;

    public AgentsController(
        IAgentService agentService,
        IChatService chatService,
        IApiKeyService apiKeyService,
        IBannedWordService bannedWordService,
        IPiiDetectionService piiDetectionService,
        AIAgentManagementDbContext context,
        ILogger<AgentsController> logger)
    {
        _agentService = agentService;
        _chatService = chatService;
        _apiKeyService = apiKeyService;
        _bannedWordService = bannedWordService;
        _piiDetectionService = piiDetectionService;
        _context = context;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<List<AgentDto>>> GetAgents([FromQuery] int? userId, [FromQuery] bool? isPublic, [FromQuery] string? search)
    {
        try
        {
            // Admin이 아니면 현재 로그인 사용자의 Agent + Public Agent만 조회
            if (!User.IsInRole("Admin"))
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (int.TryParse(userIdClaim, out var currentUserId))
                {
                    userId = currentUserId;
                }
            }

            var agents = await _agentService.GetAgentsAsync(userId, isPublic, search);
            return Ok(agents);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting agents. UserId: {UserId}, IsPublic: {IsPublic}, Search: {Search}", userId, isPublic, search);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<AgentDto>> GetAgent(int id)
    {
        try
        {
            var agent = await _agentService.GetAgentByIdAsync(id);
            if (agent == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(agent);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting agent {AgentId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    /// <summary>
    /// AgentCode로 Agent 정보 조회 (로그인 필요). 내부 테스트 페이지용.
    /// </summary>
    [HttpGet("bycode/{code}")]
    public async Task<ActionResult<AgentDto>> GetAgentByCode(string code)
    {
        try
        {
            var agent = await _context.Agents
                .Include(a => a.ApiService)
                .Include(a => a.Creator)
                .FirstOrDefaultAsync(a => a.AgentCode == code && a.IsActive);

            if (agent == null)
                return NotFound(ErrorResponseDto.NotFound("Agent를 찾을 수 없습니다."));

            var dto = new AgentDto
            {
                AgentId = agent.AgentId,
                AgentCode = agent.AgentCode,
                AgentName = agent.AgentName,
                Description = agent.Description,
                ServiceId = agent.ServiceId,
                ServiceName = agent.ApiService?.ServiceName ?? "",
                SystemPrompt = agent.SystemPrompt,
                IconClass = agent.IconClass,
                ColorCode = agent.ColorCode,
                Temperature = agent.Temperature,
                MaxTokens = agent.MaxTokens,
                DefaultModel = agent.DefaultModel,
                IsPublic = agent.IsPublic,
                EnableRag = agent.EnableRag,
                PiiProtectionEnabled = agent.PiiProtectionEnabled,
                PiiProtectionMode = agent.PiiProtectionMode,
                WelcomeMessage = agent.WelcomeMessage,
                PlaceholderText = agent.PlaceholderText,
                ChatTheme = agent.ChatTheme,
                AllowGuestChat = agent.AllowGuestChat,
                CreatedBy = agent.CreatedBy,
                CreatedByName = agent.Creator?.FullName ?? "Unknown",
                IsActive = agent.IsActive,
                CreatedAt = agent.CreatedAt,
                UpdatedAt = agent.UpdatedAt
            };

            return Ok(dto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting agent by code {AgentCode}", code);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost]
    public async Task<ActionResult<AgentDto>> CreateAgent([FromBody] CreateAgentRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var agent = await _agentService.CreateAgentAsync(request, userId);
            return CreatedAtAction(nameof(GetAgent), new { id = agent.AgentId }, agent);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating agent: {Message}", ex.Message);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPut("{id}")]
    public async Task<ActionResult<AgentDto>> UpdateAgent(int id, [FromBody] UpdateAgentRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            // Admin은 모든 Agent 수정 가능
            var isAdmin = User.IsInRole("Admin");
            var agent = await _agentService.UpdateAgentAsync(id, request, userId, isAdmin);
            if (agent == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(agent);
        }
        catch (UnauthorizedAccessException ex)
        {
            return StatusCode(403, ErrorResponseDto.Forbidden(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating agent {AgentId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpDelete("{id}")]
    public async Task<ActionResult> DeleteAgent(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var isAdmin = User.IsInRole("Admin");
            var result = await _agentService.DeleteAgentAsync(id, userId, isAdmin);
            if (!result)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return NoContent();
        }
        catch (UnauthorizedAccessException ex)
        {
            return StatusCode(403, ErrorResponseDto.Forbidden(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting agent {AgentId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost("{id}/chat")]
    [ApiKeyAuthorize]
    public async Task<ActionResult<AgentChatResponseDto>> ChatWithAgent(int id, [FromBody] AgentChatRequestDto request)
    {
        try
        {
            // 사용자 ID 가져오기 (JWT 또는 API Key)
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized("User authentication required"));
            }

            // Agent 조회 및 검증
            var agent = await _context.Agents
                .Include(a => a.ApiService)
                .FirstOrDefaultAsync(a => a.AgentId == id && a.IsActive);

            if (agent == null)
            {
                return NotFound(ErrorResponseDto.NotFound("Agent not found or inactive"));
            }

            // Agent 접근 권한 확인 (비공개 Agent는 소유자만 접근 가능)
            if (!agent.IsPublic && agent.CreatedBy != userId)
            {
                return Forbid();
            }

            // 금칙어 검사
            var bannedWordCheck = await _bannedWordService.CheckBannedWordsAsync(request.Message, agent.AgentId);
            if (bannedWordCheck.IsBlocked)
            {
                var errorResponse = ErrorResponseDto.FromBannedWordException(new BannedWordException(bannedWordCheck.BlockedWords));
                return BadRequest(errorResponse);
            }

            // 개인정보 검사 및 처리
            var piiSettings = await _piiDetectionService.GetAgentSettingsAsync(agent.AgentId);
            var messageToProcess = request.Message;
            
            if (piiSettings.Enabled)
            {
                var piiResult = await _piiDetectionService.DetectPiiAsync(request.Message, piiSettings.DetectionTypes);
                
                if (piiResult.HasPii)
                {
                    if (piiSettings.Mode == "Block")
                    {
                        var detectedTypes = piiResult.DetectedItems.Select(i => PiiTypeHelper.GetPiiTypeName(i.Type)).Distinct().ToList();
                        var errorResponse = ErrorResponseDto.FromPiiDetectionException(new PiiDetectionException(piiResult, detectedTypes));
                        return BadRequest(errorResponse);
                    }
                    else if (piiSettings.Mode == "Mask")
                    {
                        // 마스킹 처리된 메시지 사용
                        messageToProcess = piiResult.MaskedMessage;
                        _logger.LogInformation("PII detected and masked in ChatWithAgent. AgentId: {AgentId}, Types: {Types}", 
                            id, string.Join(", ", piiResult.DetectedItems.Select(i => i.Type).Distinct()));
                    }
                }
            }

            // Agent 설정을 적용하여 DirectSendMessageRequestDto 생성
            var directRequest = new DirectSendMessageRequestDto
            {
                AgentId = agent.AgentId,
                ServiceId = agent.ServiceId,
                Model = request.Model ?? agent.DefaultModel ?? agent.ApiService?.DefaultModel,
                Temperature = request.Temperature ?? agent.Temperature ?? 0.7m,
                MaxTokens = request.MaxTokens ?? agent.MaxTokens ?? 2048,
                EnableRag = request.EnableRag ?? agent.EnableRag,
                EnableWebSearch = request.EnableWebSearch ?? false,
                Language = request.Language ?? "auto",
                RagTopK = request.RagTopK,
                DocumentIds = request.DocumentIds,
                Messages = new List<ChatMessageItemDto>
                {
                    new ChatMessageItemDto
                    {
                        Role = "user",
                        Content = request.Message
                    }
                }
            };

            // 기존 대화가 있으면 conversationId 설정
            if (request.ConversationId.HasValue)
            {
                var conversation = await _context.ChatConversations
                    .FirstOrDefaultAsync(c => c.ConversationId == request.ConversationId.Value 
                        && c.UserId == userId 
                        && c.AgentId == agent.AgentId);
                
                if (conversation != null)
                {
                    // conversationId는 ChatService에서 자동으로 처리됨
                }
            }

            // ChatService를 통해 메시지 전송
            var response = await _chatService.SendDirectMessageAsync(directRequest, userId);

            // AgentChatResponseDto로 변환
            var agentResponse = new AgentChatResponseDto
            {
                MessageId = response.MessageId,
                ConversationId = response.ConversationId,
                Content = response.Content,
                Model = response.Model,
                TokensUsed = response.TokensUsed,
                Cost = response.Cost,
                ResponseTime = response.ResponseTime,
                Citations = response.Citations
            };

            return Ok(agentResponse);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogWarning(ex, "Invalid operation in ChatWithAgent for AgentId {AgentId}", id);
            return BadRequest(ErrorResponseDto.BadRequest(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error in ChatWithAgent for AgentId {AgentId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost("code/{code}/chat")]
    [ApiKeyAuthorize]
    public async Task<ActionResult<AgentChatResponseDto>> ChatWithAgentByCode(string code, [FromBody] AgentChatRequestDto request)
    {
        try
        {
            // 사용자 ID 가져오기 (JWT 또는 API Key)
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized("User authentication required"));
            }

            // AgentCode로 Agent 조회 및 검증
            var agent = await _context.Agents
                .Include(a => a.ApiService)
                .FirstOrDefaultAsync(a => a.AgentCode == code && a.IsActive);

            if (agent == null)
            {
                return NotFound(ErrorResponseDto.NotFound("Agent not found or inactive"));
            }

            // Agent 접근 권한 확인 (비공개 Agent는 소유자만 접근 가능)
            if (!agent.IsPublic && agent.CreatedBy != userId)
            {
                return Forbid();
            }

            // 금칙어 검사
            var bannedWordCheck = await _bannedWordService.CheckBannedWordsAsync(request.Message, agent.AgentId);
            if (bannedWordCheck.IsBlocked)
            {
                var errorResponse = ErrorResponseDto.FromBannedWordException(new BannedWordException(bannedWordCheck.BlockedWords));
                return BadRequest(errorResponse);
            }

            // 개인정보 검사 및 처리
            var piiSettings = await _piiDetectionService.GetAgentSettingsAsync(agent.AgentId);
            var messageToProcess = request.Message;
            
            if (piiSettings.Enabled)
            {
                var piiResult = await _piiDetectionService.DetectPiiAsync(request.Message, piiSettings.DetectionTypes);
                
                if (piiResult.HasPii)
                {
                    if (piiSettings.Mode == "Block")
                    {
                        var detectedTypes = piiResult.DetectedItems.Select(i => PiiTypeHelper.GetPiiTypeName(i.Type)).Distinct().ToList();
                        var errorResponse = ErrorResponseDto.FromPiiDetectionException(new PiiDetectionException(piiResult, detectedTypes));
                        return BadRequest(errorResponse);
                    }
                    else if (piiSettings.Mode == "Mask")
                    {
                        // 마스킹 처리된 메시지 사용
                        messageToProcess = piiResult.MaskedMessage;
                        _logger.LogInformation("PII detected and masked in ChatWithAgentByCode. AgentCode: {AgentCode}, Types: {Types}", 
                            code, string.Join(", ", piiResult.DetectedItems.Select(i => i.Type).Distinct()));
                    }
                }
            }

            // Agent 설정을 적용하여 DirectSendMessageRequestDto 생성
            var directRequest = new DirectSendMessageRequestDto
            {
                AgentId = agent.AgentId,
                ServiceId = agent.ServiceId,
                Model = request.Model ?? agent.DefaultModel ?? agent.ApiService?.DefaultModel,
                Temperature = request.Temperature ?? agent.Temperature ?? 0.7m,
                MaxTokens = request.MaxTokens ?? agent.MaxTokens ?? 2048,
                EnableRag = request.EnableRag ?? agent.EnableRag,
                EnableWebSearch = request.EnableWebSearch ?? false,
                Language = request.Language ?? "auto",
                RagTopK = request.RagTopK,
                DocumentIds = request.DocumentIds,
                Messages = new List<ChatMessageItemDto>
                {
                    new ChatMessageItemDto
                    {
                        Role = "user",
                        Content = request.Message
                    }
                }
            };

            // 기존 대화가 있으면 conversationId 설정
            if (request.ConversationId.HasValue)
            {
                var conversation = await _context.ChatConversations
                    .FirstOrDefaultAsync(c => c.ConversationId == request.ConversationId.Value 
                        && c.UserId == userId 
                        && c.AgentId == agent.AgentId);
                
                if (conversation != null)
                {
                    // conversationId는 ChatService에서 자동으로 처리됨
                }
            }

            // ChatService를 통해 메시지 전송
            var response = await _chatService.SendDirectMessageAsync(directRequest, userId);

            // AgentChatResponseDto로 변환
            var agentResponse = new AgentChatResponseDto
            {
                MessageId = response.MessageId,
                ConversationId = response.ConversationId,
                Content = response.Content,
                Model = response.Model,
                TokensUsed = response.TokensUsed,
                Cost = response.Cost,
                ResponseTime = response.ResponseTime,
                Citations = response.Citations
            };

            return Ok(agentResponse);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogWarning(ex, "Invalid operation in ChatWithAgentByCode for AgentCode {AgentCode}", code);
            return BadRequest(ErrorResponseDto.BadRequest(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error in ChatWithAgentByCode for AgentCode {AgentCode}", code);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost("{id}/api-keys")]
    public async Task<ActionResult<CreateAgentApiKeyResponseDto>> CreateAgentApiKey(int id, [FromBody] CreateAgentApiKeyRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var agent = await _context.Agents.AsNoTracking().FirstOrDefaultAsync(a => a.AgentId == id && a.IsActive);
            if (agent == null)
            {
                return NotFound(ErrorResponseDto.NotFound("Agent not found or inactive"));
            }
            if (agent.CreatedBy != userId)
            {
                return Forbid();
            }

            var result = await _apiKeyService.GenerateAgentApiKeyAsync(id, userId, request ?? new CreateAgentApiKeyRequestDto());
            return CreatedAtAction(nameof(GetAgentApiKeys), new { id }, result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating Agent API key for AgentId {AgentId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("{id}/api-keys")]
    public async Task<ActionResult<List<ApiKeyDto>>> GetAgentApiKeys(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var agent = await _context.Agents.AsNoTracking().FirstOrDefaultAsync(a => a.AgentId == id && a.IsActive);
            if (agent == null)
            {
                return NotFound(ErrorResponseDto.NotFound("Agent not found or inactive"));
            }
            if (agent.CreatedBy != userId)
            {
                return Forbid();
            }

            var keys = await _apiKeyService.GetAgentApiKeysAsync(id, userId);
            return Ok(keys);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting Agent API keys for AgentId {AgentId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpDelete("{id}/api-keys/{apiKeyId}")]
    public async Task<ActionResult> DeleteAgentApiKey(int id, int apiKeyId)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var agent = await _context.Agents.AsNoTracking().FirstOrDefaultAsync(a => a.AgentId == id && a.IsActive);
            if (agent == null)
            {
                return NotFound(ErrorResponseDto.NotFound("Agent not found or inactive"));
            }
            if (agent.CreatedBy != userId)
            {
                return Forbid();
            }

            var deleted = await _apiKeyService.DeleteAgentApiKeyAsync(id, apiKeyId, userId);
            if (!deleted)
            {
                return NotFound(ErrorResponseDto.NotFound("API key not found or not associated with this agent"));
            }
            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting Agent API key {ApiKeyId} for AgentId {AgentId}", apiKeyId, id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    // ════════════════════════════════════════════════════════════════
    // 외부 시스템 연동 전용 엔드포인트 (API Key 인증)
    // ════════════════════════════════════════════════════════════════

    /// <summary>
    /// SSE(Server-Sent Events) 스트리밍 채팅.
    /// Content-Type: text/event-stream으로 응답합니다.
    /// 필요 Scope: stream
    /// </summary>
    [HttpPost("{id}/chat/stream")]
    [ApiKeyAuthorize("stream")]
    public async Task ChatWithAgentStream(int id, [FromBody] AgentChatRequestDto request, CancellationToken cancellationToken)
    {
        var httpContext = HttpContext;
        httpContext.Response.ContentType = "text/event-stream; charset=utf-8";
        httpContext.Response.Headers["Cache-Control"] = "no-cache";
        httpContext.Response.Headers["X-Accel-Buffering"] = "no";
        httpContext.Response.Headers["Connection"] = "keep-alive";

        async Task WriteEvent(string eventType, object data)
        {
            if (cancellationToken.IsCancellationRequested) return;
            var json = System.Text.Json.JsonSerializer.Serialize(data,
                new System.Text.Json.JsonSerializerOptions
                {
                    PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase
                });
            await httpContext.Response.WriteAsync($"event: {eventType}\ndata: {json}\n\n", cancellationToken);
            await httpContext.Response.Body.FlushAsync(cancellationToken);
        }

        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                await WriteEvent("error", new { message = "Unauthorized" });
                return;
            }

            var agent = await _context.Agents
                .Include(a => a.ApiService)
                .FirstOrDefaultAsync(a => a.AgentId == id && a.IsActive, cancellationToken);

            if (agent == null)
            {
                await WriteEvent("error", new { message = "Agent not found or inactive" });
                return;
            }

            if (!agent.IsPublic && agent.CreatedBy != userId)
            {
                await WriteEvent("error", new { message = "Access denied" });
                return;
            }

            // 금칙어 검사
            var bannedWordCheck = await _bannedWordService.CheckBannedWordsAsync(request.Message, agent.AgentId);
            if (bannedWordCheck.IsBlocked)
            {
                await WriteEvent("error", new { message = "Message blocked by content policy" });
                return;
            }

            // 개인정보 검사
            var piiSettings = await _piiDetectionService.GetAgentSettingsAsync(agent.AgentId);
            var messageToProcess = request.Message;
            if (piiSettings.Enabled)
            {
                var piiResult = await _piiDetectionService.DetectPiiAsync(request.Message, piiSettings.DetectionTypes);
                if (piiResult.HasPii)
                {
                    if (piiSettings.Mode == "Block")
                    {
                        await WriteEvent("error", new { message = "Message blocked: contains personal information" });
                        return;
                    }
                    else if (piiSettings.Mode == "Mask")
                    {
                        messageToProcess = piiResult.MaskedMessage;
                    }
                }
            }

            // 시작 이벤트
            await WriteEvent("start", new { agentId = id, agentName = agent.AgentName });

            // ChatService 호출
            var directRequest = new DirectSendMessageRequestDto
            {
                AgentId         = agent.AgentId,
                ServiceId       = agent.ServiceId,
                Model           = request.Model ?? agent.DefaultModel ?? agent.ApiService?.DefaultModel,
                Temperature     = request.Temperature ?? agent.Temperature ?? 0.7m,
                MaxTokens       = request.MaxTokens ?? agent.MaxTokens ?? 2048,
                EnableRag       = request.EnableRag ?? agent.EnableRag,
                EnableWebSearch = request.EnableWebSearch ?? false,
                Language        = request.Language ?? "auto",
                RagTopK         = request.RagTopK,
                DocumentIds     = request.DocumentIds,
                Messages        = new List<ChatMessageItemDto>
                {
                    new ChatMessageItemDto { Role = "user", Content = messageToProcess }
                }
            };

            var response = await _chatService.SendDirectMessageAsync(directRequest, userId);

            // 응답을 단어 단위로 분할하여 청크 전송 (스트리밍 효과)
            if (!string.IsNullOrEmpty(response.Content))
            {
                var words = response.Content.Split(' ');
                foreach (var word in words)
                {
                    if (cancellationToken.IsCancellationRequested) break;
                    await WriteEvent("chunk", new { content = word + " " });
                    await Task.Delay(15, cancellationToken);
                }
            }

            // 완료 이벤트
            await WriteEvent("done", new
            {
                messageId      = response.MessageId,
                conversationId = response.ConversationId,
                totalTokens    = response.TokensUsed,
                cost           = response.Cost,
                responseTime   = response.ResponseTime,
                model          = response.Model
            });
        }
        catch (OperationCanceledException)
        {
            _logger.LogInformation("SSE 스트리밍 클라이언트 연결 종료: AgentId={AgentId}", id);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "SSE 스트리밍 오류: AgentId={AgentId}", id);
            try { await WriteEvent("error", new { message = "Internal server error" }); } catch { /* 클라이언트 연결 끊김 */ }
        }
    }

    /// <summary>
    /// Agent 공개 메타데이터 조회 (API Key 인증).
    /// 외부 시스템이 Agent 정보를 확인할 때 사용합니다.
    /// 필요 Scope: info
    /// </summary>
    [HttpGet("{id}/info")]
    [ApiKeyAuthorize("info")]
    public async Task<ActionResult<AgentPublicInfoDto>> GetAgentPublicInfo(int id)
    {
        try
        {
            var agent = await _context.Agents
                .Include(a => a.ApiService)
                .AsNoTracking()
                .FirstOrDefaultAsync(a => a.AgentId == id && a.IsActive);

            if (agent == null)
                return NotFound(ErrorResponseDto.NotFound("Agent not found or inactive"));

            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            int.TryParse(userIdClaim, out var userId);

            if (!agent.IsPublic && agent.CreatedBy != userId)
                return Forbid();

            var capabilities = new List<string> { "chat", "stream" };
            if (agent.EnableRag) capabilities.Add("rag");

            var dto = new AgentPublicInfoDto
            {
                AgentId      = agent.AgentId,
                AgentName    = agent.AgentName,
                AgentCode    = agent.AgentCode,
                Description  = agent.Description,
                IsPublic     = agent.IsPublic,
                DefaultModel = agent.DefaultModel ?? agent.ApiService?.DefaultModel,
                EnableRag    = agent.EnableRag,
                Capabilities = capabilities
            };

            return Ok(dto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting public info for AgentId {AgentId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    // ════════════════════════════════════════════════════════════════
    // 퍼블릭 엔드포인트 (비로그인 게스트 접근 - AllowGuestChat=true 인 공개 Agent)
    // ════════════════════════════════════════════════════════════════

    /// <summary>
    /// 퍼블릭 Agent 정보 조회 (비로그인 허용).
    /// /chatbot/{code} 페이지, /embed/{code} 페이지에서 사용.
    /// </summary>
    [HttpGet("public/{code}/info")]
    [AllowAnonymous]
    [EnableRateLimiting("ip-guest")]
    public async Task<ActionResult<AgentPublicInfoDto>> GetPublicAgentInfo(string code)
    {
        var agent = await _context.Agents
            .Include(a => a.ApiService)
            .AsNoTracking()
            .FirstOrDefaultAsync(a => a.AgentCode == code && a.IsActive && a.IsPublic && a.AllowGuestChat);

        if (agent == null)
            return NotFound(ErrorResponseDto.NotFound("Agent를 찾을 수 없습니다."));

        if (!IsEmbedOriginAllowed(agent.AllowedEmbedDomains))
            return StatusCode(403, ErrorResponseDto.Forbidden("이 도메인에서는 임베드가 허용되지 않습니다."));

        var capabilities = new List<string> { "chat", "stream" };
        if (agent.EnableRag) capabilities.Add("rag");

        return Ok(new AgentPublicInfoDto
        {
            AgentId      = agent.AgentId,
            AgentName    = agent.AgentName,
            AgentCode    = agent.AgentCode,
            Description  = agent.Description,
            IconClass    = agent.IconClass,
            ColorCode    = agent.ColorCode,
            IsPublic     = agent.IsPublic,
            DefaultModel = agent.DefaultModel ?? agent.ApiService?.DefaultModel,
            EnableRag    = agent.EnableRag,
            WelcomeMessage  = agent.WelcomeMessage,
            PlaceholderText = agent.PlaceholderText,
            ChatTheme       = agent.ChatTheme ?? "light",
            Capabilities = capabilities
        });
    }

    /// <summary>
    /// 퍼블릭 채팅 (비로그인 허용, AllowGuestChat=true 인 공개 Agent만).
    /// Rate Limit: IP당 분당 30회.
    /// </summary>
    [HttpPost("public/{code}/chat")]
    [AllowAnonymous]
    [EnableRateLimiting("ip-guest")]
    public async Task<ActionResult> PublicChat(string code, [FromBody] PublicChatRequestDto request)
    {
        var agent = await _context.Agents
            .Include(a => a.ApiService)
            .AsNoTracking()
            .FirstOrDefaultAsync(a => a.AgentCode == code && a.IsActive && a.IsPublic && a.AllowGuestChat);

        if (agent == null)
            return NotFound(ErrorResponseDto.NotFound("Agent를 찾을 수 없습니다."));

        if (!IsEmbedOriginAllowed(agent.AllowedEmbedDomains))
            return StatusCode(403, ErrorResponseDto.Forbidden("이 도메인에서는 임베드가 허용되지 않습니다."));

        // 금칙어 검사
        var bannedWordCheck = await _bannedWordService.CheckBannedWordsAsync(request.Message, agent.AgentId);
        if (bannedWordCheck.IsBlocked)
            return BadRequest(ErrorResponseDto.BadRequest("메시지에 금칙어가 포함되어 있습니다."));

        // Agent 소유자 ID로 사용량 기록
        var directRequest = new DirectSendMessageRequestDto
        {
            AgentId     = agent.AgentId,
            ServiceId   = agent.ServiceId,
            Model       = agent.DefaultModel ?? agent.ApiService?.DefaultModel,
            Temperature = agent.Temperature ?? 0.7m,
            MaxTokens   = agent.MaxTokens ?? 2000,
            EnableRag   = agent.EnableRag,
            Language    = "auto",
            Messages    = request.Messages?.Select(m => new ChatMessageItemDto
            {
                Role    = m.Role,
                Content = m.Content
            }).ToList() ?? new List<ChatMessageItemDto>
            {
                new ChatMessageItemDto { Role = "user", Content = request.Message }
            }
        };

        try
        {
            var response = await _chatService.SendDirectMessageAsync(directRequest, agent.CreatedBy);
            return Ok(new
            {
                content  = response.Content,
                model    = response.Model,
                tokensUsed = response.TokensUsed
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "PublicChat error. AgentCode={Code}", code);
            return StatusCode(500, ErrorResponseDto.InternalError("응답 생성 중 오류가 발생했습니다."));
        }
    }

    /// <summary>
    /// 퍼블릭 SSE 스트리밍 채팅 (비로그인 허용).
    /// </summary>
    [HttpPost("public/{code}/stream")]
    [AllowAnonymous]
    [EnableRateLimiting("ip-guest")]
    public async Task PublicChatStream(string code, [FromBody] PublicChatRequestDto request, CancellationToken cancellationToken)
    {
        HttpContext.Response.ContentType = "text/event-stream; charset=utf-8";
        HttpContext.Response.Headers["Cache-Control"] = "no-cache";
        HttpContext.Response.Headers["X-Accel-Buffering"] = "no";
        HttpContext.Response.Headers["Connection"] = "keep-alive";

        async Task WriteEvent(string eventType, object data)
        {
            if (cancellationToken.IsCancellationRequested) return;
            var json = System.Text.Json.JsonSerializer.Serialize(data,
                new System.Text.Json.JsonSerializerOptions { PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase });
            await HttpContext.Response.WriteAsync($"event: {eventType}\ndata: {json}\n\n", cancellationToken);
            await HttpContext.Response.Body.FlushAsync(cancellationToken);
        }

        var agent = await _context.Agents
            .Include(a => a.ApiService)
            .FirstOrDefaultAsync(a => a.AgentCode == code && a.IsActive && a.IsPublic && a.AllowGuestChat, cancellationToken);

        if (agent == null)
        {
            await WriteEvent("error", new { message = "Agent를 찾을 수 없습니다." });
            return;
        }

        if (!IsEmbedOriginAllowed(agent.AllowedEmbedDomains))
        {
            await WriteEvent("error", new { message = "이 도메인에서는 임베드가 허용되지 않습니다." });
            return;
        }

        // 금칙어 검사
        var bannedWordCheck = await _bannedWordService.CheckBannedWordsAsync(request.Message, agent.AgentId);
        if (bannedWordCheck.IsBlocked)
        {
            await WriteEvent("error", new { message = "메시지에 금칙어가 포함되어 있습니다." });
            return;
        }

        try
        {
            await WriteEvent("start", new { agentId = agent.AgentId, agentName = agent.AgentName });

            var directRequest = new DirectSendMessageRequestDto
            {
                AgentId     = agent.AgentId,
                ServiceId   = agent.ServiceId,
                Model       = agent.DefaultModel ?? agent.ApiService?.DefaultModel,
                Temperature = agent.Temperature ?? 0.7m,
                MaxTokens   = agent.MaxTokens ?? 2000,
                EnableRag   = agent.EnableRag,
                Language    = "auto",
                Messages    = request.Messages?.Select(m => new ChatMessageItemDto
                {
                    Role    = m.Role,
                    Content = m.Content
                }).ToList() ?? new List<ChatMessageItemDto>
                {
                    new ChatMessageItemDto { Role = "user", Content = request.Message }
                }
            };

            var response = await _chatService.SendDirectMessageAsync(directRequest, agent.CreatedBy);

            if (!string.IsNullOrEmpty(response.Content))
            {
                var words = response.Content.Split(' ');
                foreach (var word in words)
                {
                    if (cancellationToken.IsCancellationRequested) break;
                    await WriteEvent("chunk", new { content = word + " " });
                    await Task.Delay(15, cancellationToken);
                }
            }

            await WriteEvent("done", new { totalTokens = response.TokensUsed, model = response.Model });
        }
        catch (OperationCanceledException) { /* 클라이언트 연결 종료 */ }
        catch (Exception ex)
        {
            _logger.LogError(ex, "PublicChatStream error. AgentCode={Code}", code);
            try { await WriteEvent("error", new { message = "응답 생성 중 오류가 발생했습니다." }); } catch { }
        }
    }

    /// <summary>
    /// API 키 사용량 및 Rate Limit 잔여량 조회 (API Key 인증).
    /// 필요 Scope: usage
    /// </summary>
    [HttpGet("{id}/usage")]
    [ApiKeyAuthorize("usage")]
    public async Task<ActionResult<AgentApiUsageDto>> GetAgentApiUsage(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                return Unauthorized(ErrorResponseDto.Unauthorized());

            var agent = await _context.Agents.AsNoTracking()
                .FirstOrDefaultAsync(a => a.AgentId == id && a.IsActive);

            if (agent == null)
                return NotFound(ErrorResponseDto.NotFound("Agent not found or inactive"));

            if (!agent.IsPublic && agent.CreatedBy != userId)
                return Forbid();

            // HttpContext.Items에서 인증된 API Key 정보 가져오기
            var validation = HttpContext.Items["ApiKeyValidation"] as DTOs.ApiKeyValidationResult;

            Models.ApiKey? apiKey = null;
            if (validation?.ApiKeyId > 0)
            {
                apiKey = await _context.ApiKeys.AsNoTracking()
                    .FirstOrDefaultAsync(k => k.ApiKeyId == validation.ApiKeyId);
            }
            else
            {
                apiKey = await _context.ApiKeys.AsNoTracking()
                    .Where(k => k.UserId == userId && k.AgentId == id && k.ServiceCode == "agent-api" && k.IsActive)
                    .OrderByDescending(k => k.LastUsedAt)
                    .FirstOrDefaultAsync();
            }

            if (apiKey == null)
                return NotFound(ErrorResponseDto.NotFound("No active API key found for this agent"));

            var dto = new AgentApiUsageDto
            {
                AgentId            = id,
                ApiKeyId           = apiKey.ApiKeyId,
                KeyName            = apiKey.KeyName,
                TotalRequests      = apiKey.UsageCount,
                LastUsedAt         = apiKey.LastUsedAt,
                RateLimitPerMinute = apiKey.RateLimitPerMinute,
                RateLimitPerDay    = apiKey.RateLimitPerDay,
                Scopes             = apiKey.Scopes,
                ExpiresAt          = apiKey.ExpiresAt
            };

            return Ok(dto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting API usage for AgentId {AgentId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 헬퍼: 임베드 Origin 허용 여부 확인
    // ──────────────────────────────────────────────────────────────────────────

    /// <summary>
    /// Request의 Origin/Referer 헤더가 에이전트의 허용 도메인 목록에 포함되는지 확인합니다.
    /// allowedDomains가 null이면 전체 허용(직접 접속 포함).
    /// </summary>
    private bool IsEmbedOriginAllowed(string? allowedDomains)
    {
        // 도메인 화이트리스트 미설정 = 전체 허용
        if (string.IsNullOrWhiteSpace(allowedDomains))
            return true;

        var origin = Request.Headers["Origin"].FirstOrDefault()
                  ?? Request.Headers["Referer"].FirstOrDefault();

        // Origin 헤더 없음 = 직접 접속(브라우저 주소창) → 허용
        if (string.IsNullOrWhiteSpace(origin))
            return true;

        // Referer는 경로까지 포함하므로 Origin 부분만 추출
        if (Uri.TryCreate(origin, UriKind.Absolute, out var uri))
            origin = $"{uri.Scheme}://{uri.Host}{(uri.IsDefaultPort ? "" : $":{uri.Port}")}";

        var allowed = allowedDomains.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
        return allowed.Any(d => string.Equals(d.TrimEnd('/'), origin.TrimEnd('/'), StringComparison.OrdinalIgnoreCase));
    }

    // ──────────────────────────────────────────────────────────────────────────
    // GET /api/agents/public/{code}/qr   — QR 코드 이미지 반환 (PNG)
    // ──────────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 에이전트 퍼블릭 채팅 URL을 QR 코드 PNG로 반환합니다. (인증 불필요)
    /// </summary>
    [HttpGet("public/{code}/qr")]
    [AllowAnonymous]
    [EnableRateLimiting("ip-guest")]
    public async Task<IActionResult> GetAgentQrCode(string code, [FromQuery] int size = 300)
    {
        var agent = await _context.Agents
            .AsNoTracking()
            .FirstOrDefaultAsync(a => a.AgentCode == code && a.IsActive);

        if (agent == null)
            return NotFound(ErrorResponseDto.NotFound("Agent not found"));

        if (!agent.IsPublic && !agent.AllowGuestChat)
            return Forbid();

        // 클라이언트 Origin 기반으로 URL 구성 (없으면 Request 기반)
        var baseUrl = $"{Request.Scheme}://{Request.Host}";
        var chatUrl = $"{baseUrl}/chatbot/{code}";

        // QR 코드 생성
        using var qrGenerator = new QRCodeGenerator();
        var qrData = qrGenerator.CreateQrCode(chatUrl, QRCodeGenerator.ECCLevel.M);
        using var qrCode = new PngByteQRCode(qrData);

        // 픽셀당 포인트 크기 계산 (요청 size를 25개 모듈 기준으로 나눔, 최소 1)
        var pixelsPerModule = Math.Max(1, size / 25);
        var pngBytes = qrCode.GetGraphic(pixelsPerModule);

        return File(pngBytes, "image/png");
    }

}
