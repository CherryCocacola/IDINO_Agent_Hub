using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.EntityFrameworkCore;
using System.Security.Claims;
using System.Text.Json;
using AIAgentManagement.Attributes;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

/// <summary>
/// OpenAI 호환 API 엔드포인트.
///
/// 외부 클라이언트(OpenAI SDK, LangChain, Cursor 등)가 Agent Hub 에이전트를
/// OpenAI API 형식 그대로 호출할 수 있도록 합니다.
///
/// 인증 방법 (기존 API Key 그대로 사용):
///   Authorization: Bearer {agent-api-key}
///   또는 X-API-Key: {agent-api-key}
///
/// 모델 ID = agentCode (예: "abc123ef")
///
/// 예시:
///   client = OpenAI(api_key="sk-...", base_url="https://yourdomain/v1")
///   client.chat.completions.create(model="abc123ef", messages=[...])
/// </summary>
[ApiController]
[Route("v1")]
[ApiKeyAuthorize]
[EnableRateLimiting("ip-openai")]
public class OpenAICompatController : ControllerBase
{
    private readonly AIAgentManagementDbContext _context;
    private readonly IChatService _chatService;
    private readonly IBannedWordService _bannedWordService;
    private readonly IPiiDetectionService _piiDetectionService;
    private readonly ILogger<OpenAICompatController> _logger;

    private static readonly JsonSerializerOptions _snakeCase = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower
    };

    public OpenAICompatController(
        AIAgentManagementDbContext context,
        IChatService chatService,
        IBannedWordService bannedWordService,
        IPiiDetectionService piiDetectionService,
        ILogger<OpenAICompatController> logger)
    {
        _context = context;
        _chatService = chatService;
        _bannedWordService = bannedWordService;
        _piiDetectionService = piiDetectionService;
        _logger = logger;
    }

    // ════════════════════════════════════════════════════════════════════════════
    // GET /v1/models
    // ════════════════════════════════════════════════════════════════════════════

    /// <summary>
    /// API 키 소유자가 접근 가능한 에이전트 목록을 OpenAI 모델 형식으로 반환합니다.
    /// </summary>
    [HttpGet("models")]
    public async Task<IActionResult> ListModels()
    {
        if (!TryGetUserId(out var userId))
            return Unauthorized(ErrorBody("authentication_error", "Unauthorized"));

        // API 키가 특정 에이전트에 연결된 경우 해당 에이전트만 노출
        var agentIdClaim = User.FindFirst("AgentId")?.Value;
        int.TryParse(agentIdClaim, out var linkedAgentId);

        var query = _context.Agents
            .Where(a => a.IsActive && (a.CreatedBy == userId || a.IsPublic));

        if (linkedAgentId > 0)
            query = query.Where(a => a.AgentId == linkedAgentId);

        var agents = await query
            .OrderByDescending(a => a.UpdatedAt)
            .ToListAsync();

        var models = agents.Select(a => new OpenAIModelDto
        {
            Id          = a.AgentCode,
            Created     = new DateTimeOffset(a.CreatedAt, TimeSpan.Zero).ToUnixTimeSeconds(),
            OwnedBy     = "agent-hub",
            Description = string.IsNullOrEmpty(a.Description)
                ? a.AgentName
                : $"{a.AgentName} — {a.Description}"
        }).ToList();

        return Ok(new OpenAIModelListResponse { Data = models });
    }

    // ════════════════════════════════════════════════════════════════════════════
    // GET /v1/models/{model}
    // ════════════════════════════════════════════════════════════════════════════

    /// <summary>
    /// 특정 에이전트 정보를 OpenAI 모델 형식으로 반환합니다.
    /// </summary>
    [HttpGet("models/{model}")]
    public async Task<IActionResult> GetModel(string model)
    {
        var agent = await _context.Agents
            .AsNoTracking()
            .FirstOrDefaultAsync(a => a.AgentCode == model && a.IsActive);

        if (agent == null)
            return NotFound(ErrorBody("model_not_found", $"The model '{model}' does not exist."));

        return Ok(new OpenAIModelDto
        {
            Id          = agent.AgentCode,
            Created     = new DateTimeOffset(agent.CreatedAt, TimeSpan.Zero).ToUnixTimeSeconds(),
            OwnedBy     = "agent-hub",
            Description = string.IsNullOrEmpty(agent.Description)
                ? agent.AgentName
                : $"{agent.AgentName} — {agent.Description}"
        });
    }

    // ════════════════════════════════════════════════════════════════════════════
    // POST /v1/chat/completions
    // ════════════════════════════════════════════════════════════════════════════

    /// <summary>
    /// OpenAI 형식 채팅 완성.
    /// stream: false → JSON 단일 응답
    /// stream: true  → SSE (text/event-stream), data: [...] \n\n 형식
    /// </summary>
    [HttpPost("chat/completions")]
    public async Task ChatCompletions(
        [FromBody] OpenAIChatCompletionRequest request,
        CancellationToken cancellationToken)
    {
        // ── 인증 ────────────────────────────────────────────────────────────────
        if (!TryGetUserId(out var userId))
        {
            Response.StatusCode = 401;
            await Response.WriteAsJsonAsync(ErrorBody("authentication_error", "Unauthorized"), _snakeCase, cancellationToken);
            return;
        }

        // ── 요청 유효성 ─────────────────────────────────────────────────────────
        if (string.IsNullOrWhiteSpace(request.Model))
        {
            Response.StatusCode = 400;
            await Response.WriteAsJsonAsync(ErrorBody("invalid_request_error", "'model' is required."), _snakeCase, cancellationToken);
            return;
        }

        var userMessage = request.Messages.LastOrDefault(m =>
            string.Equals(m.Role, "user", StringComparison.OrdinalIgnoreCase))?.Content;

        if (string.IsNullOrWhiteSpace(userMessage))
        {
            Response.StatusCode = 400;
            await Response.WriteAsJsonAsync(ErrorBody("invalid_request_error", "At least one 'user' message is required."), _snakeCase, cancellationToken);
            return;
        }

        // ── 에이전트 조회 ────────────────────────────────────────────────────────
        var agent = await _context.Agents
            .Include(a => a.ApiService)
            .FirstOrDefaultAsync(a => a.AgentCode == request.Model && a.IsActive, cancellationToken);

        if (agent == null)
        {
            Response.StatusCode = 404;
            await Response.WriteAsJsonAsync(ErrorBody("model_not_found", $"The model '{request.Model}' does not exist."), _snakeCase, cancellationToken);
            return;
        }

        if (!agent.IsPublic && agent.CreatedBy != userId)
        {
            Response.StatusCode = 403;
            await Response.WriteAsJsonAsync(ErrorBody("permission_denied", "You do not have access to this model."), _snakeCase, cancellationToken);
            return;
        }

        // ── 금칙어 검사 ──────────────────────────────────────────────────────────
        var bannedCheck = await _bannedWordService.CheckBannedWordsAsync(userMessage, agent.AgentId);
        if (bannedCheck.IsBlocked)
        {
            Response.StatusCode = 400;
            await Response.WriteAsJsonAsync(ErrorBody("content_policy_violation", "Message blocked by content policy."), _snakeCase, cancellationToken);
            return;
        }

        // ── PII 검사 ─────────────────────────────────────────────────────────────
        var messageToSend = userMessage;
        var piiSettings = await _piiDetectionService.GetAgentSettingsAsync(agent.AgentId);
        if (piiSettings.Enabled)
        {
            var piiResult = await _piiDetectionService.DetectPiiAsync(userMessage, piiSettings.DetectionTypes);
            if (piiResult.HasPii)
            {
                if (piiSettings.Mode == "Block")
                {
                    Response.StatusCode = 400;
                    await Response.WriteAsJsonAsync(ErrorBody("content_policy_violation", "Message contains personal information."), _snakeCase, cancellationToken);
                    return;
                }
                if (piiSettings.Mode == "Mask")
                    messageToSend = piiResult.MaskedMessage;
            }
        }

        // ── DirectSendMessageRequestDto 구성 ─────────────────────────────────────
        // OpenAI messages 배열에서 대화 히스토리를 그대로 전달 (system 제외)
        var chatMessages = request.Messages
            .Where(m => !string.Equals(m.Role, "system", StringComparison.OrdinalIgnoreCase))
            .Select(m => new ChatMessageItemDto { Role = m.Role, Content = m.Content })
            .ToList();

        // 마지막 user 메시지를 PII 처리된 값으로 교체
        if (chatMessages.Count > 0 &&
            string.Equals(chatMessages[^1].Role, "user", StringComparison.OrdinalIgnoreCase))
        {
            chatMessages[^1] = new ChatMessageItemDto { Role = "user", Content = messageToSend };
        }

        var directRequest = new DirectSendMessageRequestDto
        {
            AgentId     = agent.AgentId,
            ServiceId   = agent.ServiceId,
            Model       = agent.DefaultModel ?? agent.ApiService?.DefaultModel,
            Temperature = request.Temperature ?? agent.Temperature ?? 0.7m,
            MaxTokens   = request.MaxTokens ?? agent.MaxTokens ?? 2048,
            EnableRag   = agent.EnableRag,
            Language    = "auto",
            Messages    = chatMessages
        };

        var completionId = $"chatcmpl-{Guid.NewGuid():N}";
        var createdAt    = DateTimeOffset.UtcNow.ToUnixTimeSeconds();

        if (request.Stream)
            await SendStreaming(directRequest, userId, request.Model, completionId, createdAt, cancellationToken);
        else
            await SendNonStreaming(directRequest, userId, request.Model, completionId, createdAt, cancellationToken);
    }

    // ════════════════════════════════════════════════════════════════════════════
    // 내부: 비스트리밍 응답
    // ════════════════════════════════════════════════════════════════════════════

    private async Task SendNonStreaming(
        DirectSendMessageRequestDto directRequest,
        int userId,
        string modelId,
        string completionId,
        long createdAt,
        CancellationToken cancellationToken)
    {
        var response = await _chatService.SendDirectMessageAsync(directRequest, userId);

        // 비스트리밍 분기: SendDirectMessageAsync 가 prompt/completion 분리 토큰을 노출하지 않으므로
        // 0.65 휴리스틱으로 대략 추정한다. (TODO Phase 5+) DirectSendMessageResponseDto 에 prompt/completion 분리 필드 추가 시 정확한 값 반영.
        // 진짜 SSE 분기는 OpenAI stream_options.include_usage:true 로 실제 값을 받으므로 추정 불필요.
        OpenAIUsage? usage = null;
        if (response.TokensUsed.HasValue)
        {
            var total      = response.TokensUsed.Value;
            var completion = (int)(total * 0.65);
            usage = new OpenAIUsage
            {
                TotalTokens      = total,
                CompletionTokens = completion,
                PromptTokens     = total - completion
            };
        }

        var result = new OpenAIChatCompletionResponse
        {
            Id      = completionId,
            Created = createdAt,
            Model   = modelId,
            Choices = new List<OpenAIChoice>
            {
                new()
                {
                    Index        = 0,
                    Message      = new OpenAIChatMessage { Role = "assistant", Content = response.Content },
                    FinishReason = "stop"
                }
            },
            Usage = usage
        };

        Response.ContentType = "application/json";
        await Response.WriteAsJsonAsync(result, _snakeCase, cancellationToken);
    }

    // ════════════════════════════════════════════════════════════════════════════
    // 내부: 진짜 SSE 스트리밍 응답 (OpenAI 호환 chat.completion.chunk 포맷)
    // - 가짜 SSE(C9) 제거: ChatService.SendDirectMessageAsync(전체 응답 await + Split + Task.Delay) 패턴 폐기
    // - H5 해소: AiProxyService.SendChatMessageStreamChunksAsync 가 ApiKeyPool/Cooldown 적용
    // - usage: stream_options.include_usage:true 로 OpenAI가 보낸 실제 토큰 수를 그대로 반영
    // ════════════════════════════════════════════════════════════════════════════

    private async Task SendStreaming(
        DirectSendMessageRequestDto directRequest,
        int userId,
        string modelId,
        string completionId,
        long createdAt,
        CancellationToken cancellationToken)
    {
        Response.ContentType = "text/event-stream; charset=utf-8";
        Response.Headers["Cache-Control"]      = "no-cache";
        Response.Headers["X-Accel-Buffering"]  = "no";  // IIS InProcess + nginx/Apache reverse proxy buffering 방지
        Response.Headers["Connection"]          = "keep-alive";
        // IIS InProcess 호스팅에서 chunked transfer 강제: Content-Length 헤더 미설정 + 즉시 첫 Flush

        async Task WriteSseChunk(string? role, string? content, string? finishReason)
        {
            if (cancellationToken.IsCancellationRequested) return;
            var delta = new OpenAIChunkDelta { Role = role, Content = content };
            var chunk = new OpenAIChatCompletionChunk
            {
                Id      = completionId,
                Created = createdAt,
                Model   = modelId,
                Choices = new List<OpenAIChunkChoice>
                {
                    new() { Index = 0, Delta = delta, FinishReason = finishReason }
                }
            };
            // OpenAI 표준 chat.completion.chunk JSON
            // (usage 필드는 finish_reason 청크 이후 별도 usage chunk로 보내는 OpenAI 최신 동작을 따른다)
            var json = JsonSerializer.Serialize(chunk, _snakeCase);
            await Response.WriteAsync($"data: {json}\n\n", cancellationToken);
            await Response.Body.FlushAsync(cancellationToken);
        }

        // OpenAI는 stream_options.include_usage:true 일 때 finish_reason 청크 다음에
        // choices 빈 배열 + usage 가 채워진 별도 청크를 추가로 흘려보낸다. 우리도 동일 포맷으로 한 번 더 yield.
        async Task WriteSseUsageChunk(int promptTokens, int completionTokens, int totalTokens)
        {
            if (cancellationToken.IsCancellationRequested) return;
            var payload = new
            {
                id = completionId,
                @object = "chat.completion.chunk",
                created = createdAt,
                model = modelId,
                choices = Array.Empty<object>(),
                usage = new
                {
                    prompt_tokens = promptTokens,
                    completion_tokens = completionTokens,
                    total_tokens = totalTokens
                }
            };
            var json = JsonSerializer.Serialize(payload);
            await Response.WriteAsync($"data: {json}\n\n", cancellationToken);
            await Response.Body.FlushAsync(cancellationToken);
        }

        try
        {
            // (1) 역할 선언 청크 — 클라이언트가 즉시 메시지 시작을 인지
            await WriteSseChunk(role: "assistant", content: null, finishReason: null);

            // (2) ChatService streaming wrapper — PII/BannedWord 검사 + AiProxy 진짜 SSE → ChatChunk
            string? finalFinishReason = null;
            int finalPrompt = 0, finalCompletion = 0, finalTotal = 0;

            await foreach (var chunk in _chatService
                .SendDirectMessageStreamChunksAsync(directRequest, userId, cancellationToken)
                .WithCancellation(cancellationToken))
            {
                // delta content
                if (!string.IsNullOrEmpty(chunk.Content))
                {
                    await WriteSseChunk(role: null, content: chunk.Content, finishReason: null);
                }

                // usage 누적 (마지막 chunk에 동봉되어 옴)
                if (chunk.PromptTokens.HasValue) finalPrompt = chunk.PromptTokens.Value;
                if (chunk.CompletionTokens.HasValue) finalCompletion = chunk.CompletionTokens.Value;
                if (chunk.TotalTokens.HasValue) finalTotal = chunk.TotalTokens.Value;

                if (!string.IsNullOrEmpty(chunk.FinishReason))
                {
                    finalFinishReason = chunk.FinishReason;
                }
            }

            // (3) 종료 청크 — finish_reason 명시
            await WriteSseChunk(role: null, content: null, finishReason: finalFinishReason ?? "stop");

            // (4) usage 청크 — stream_options.include_usage:true 동작 모사 (OpenAI SDK 호환)
            if (finalTotal > 0)
            {
                await WriteSseUsageChunk(finalPrompt, finalCompletion, finalTotal);
            }

            // (5) OpenAI 스트리밍 종료 신호
            await Response.WriteAsync("data: [DONE]\n\n", cancellationToken);
            await Response.Body.FlushAsync(cancellationToken);
        }
        catch (OperationCanceledException)
        {
            _logger.LogInformation("OpenAI 호환 스트리밍 클라이언트 연결 종료: model={Model}", modelId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "OpenAI 호환 스트리밍 오류: model={Model}", modelId);
            // 스트림이 이미 시작된 상태라 HTTP status를 변경할 수 없음 — error chunk 한 건 흘리고 종료
            try
            {
                var errorPayload = new
                {
                    error = new { type = "internal_error", message = "스트리밍 처리 중 오류가 발생했습니다." }
                };
                await Response.WriteAsync($"data: {JsonSerializer.Serialize(errorPayload)}\n\n", cancellationToken);
                await Response.WriteAsync("data: [DONE]\n\n", cancellationToken);
                await Response.Body.FlushAsync(cancellationToken);
            }
            catch
            {
                // 응답이 이미 닫혔거나 클라이언트 disconnect — 무시
            }
        }
    }

    // ════════════════════════════════════════════════════════════════════════════
    // 헬퍼
    // ════════════════════════════════════════════════════════════════════════════

    private bool TryGetUserId(out int userId)
    {
        var claim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        return int.TryParse(claim, out userId);
    }

    private static OpenAIErrorResponse ErrorBody(string type, string message, string? code = null) =>
        new() { Error = new OpenAIErrorDetail { Type = type, Message = message, Code = code } };
}
