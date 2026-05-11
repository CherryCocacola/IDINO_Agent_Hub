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
    // POST /v1/embeddings  (Phase 7.5)
    //
    // OpenAI Embeddings API 호환 엔드포인트.
    // DocUtil/career 의 직접 OpenAI 호출(P1 위반)을 본 게이트웨이로 흡수한다.
    //
    // model 파싱 우선순위:
    //   1) AgentCode 가 Agents 테이블에 존재하면 → 그 Agent 의 ApiService + DefaultModel 사용
    //   2) 그렇지 않으면 → "embedding-default" Agent 로 자동 폴백 (OpenAI 모델명 호환)
    //
    // input 파싱:
    //   - string  → 단건 임베딩
    //   - string[] → 배치 임베딩
    //   - 그 외   → 400
    // ════════════════════════════════════════════════════════════════════════════

    [HttpPost("embeddings")]
    public async Task<IActionResult> EmbeddingsAsync(
        [FromBody] EmbeddingsRequestDto request,
        [FromServices] IAiProxyService aiProxy,
        CancellationToken cancellationToken)
    {
        // ── 인증 ────────────────────────────────────────────────────────────────
        if (!TryGetUserId(out var userId))
            return Unauthorized(ErrorBody("authentication_error", "Unauthorized"));

        // ── 요청 유효성 ─────────────────────────────────────────────────────────
        if (string.IsNullOrWhiteSpace(request?.Model))
            return BadRequest(ErrorBody("invalid_request_error", "'model' is required."));

        if (request.Input == null)
            return BadRequest(ErrorBody("invalid_request_error", "'input' is required."));

        // input 정규화: string / string[] / JsonElement 모두 허용
        var inputs = NormalizeEmbeddingInputs(request.Input);
        if (inputs == null || inputs.Length == 0)
        {
            return BadRequest(ErrorBody("invalid_request_error",
                "'input' must be a non-empty string or array of strings."));
        }
        if (inputs.Any(s => s == null))
        {
            return BadRequest(ErrorBody("invalid_request_error",
                "'input' array entries must be non-null strings."));
        }

        // encoding_format 은 float 만 지원 (Phase 7.5)
        if (!string.IsNullOrEmpty(request.EncodingFormat)
            && !string.Equals(request.EncodingFormat, "float", StringComparison.OrdinalIgnoreCase))
        {
            return BadRequest(ErrorBody("invalid_request_error",
                $"encoding_format '{request.EncodingFormat}' is not supported. Use 'float'."));
        }

        // ── Agent 룩업 ──────────────────────────────────────────────────────────
        // 우선 model 그대로 AgentCode 시도 → 실패 시 embedding-default 폴백.
        var agent = await _context.Agents
            .Include(a => a.ApiService)
            .FirstOrDefaultAsync(
                a => a.AgentCode == request.Model && a.IsActive, cancellationToken);

        if (agent == null)
        {
            // OpenAI 호환 SDK 가 "text-embedding-3-small" 같은 모델명을 보내는 경우 처리.
            agent = await _context.Agents
                .Include(a => a.ApiService)
                .FirstOrDefaultAsync(
                    a => a.AgentCode == "embedding-default" && a.IsActive, cancellationToken);

            if (agent == null)
            {
                _logger.LogWarning(
                    "/v1/embeddings 요청 model='{Model}' AgentCode 미일치 + embedding-default Agent 미시드",
                    request.Model);
                return NotFound(ErrorBody(
                    "model_not_found",
                    $"The model '{request.Model}' does not exist and 'embedding-default' fallback is not seeded."));
            }
        }

        // ApiKey 가 특정 Agent 에 묶인 경우 권한 검사 (chat 과 동일 패턴).
        if (!agent.IsPublic && agent.CreatedBy != userId)
            return StatusCode(403, ErrorBody("permission_denied", "You do not have access to this model."));

        if (agent.ApiService == null)
        {
            _logger.LogError(
                "Embeddings Agent '{AgentCode}' 가 ApiService 를 보유하지 않음 — 시드 누락 가능성",
                agent.AgentCode);
            return StatusCode(500, ErrorBody("internal_error",
                "Agent 의 ApiService 매핑이 누락되었습니다."));
        }

        // ── 실제 모델명 결정 ────────────────────────────────────────────────────
        // Agent.DefaultModel 이 우선 (예: "text-embedding-3-small") — 미설정 시 ApiService.DefaultModel.
        // 단, request.Model 이 OpenAI 모델 prefix("text-embedding-") 로 시작하면 그 값을 우선 — 외부 SDK 호환.
        string actualModel;
        if (request.Model.StartsWith("text-embedding-", StringComparison.OrdinalIgnoreCase))
        {
            actualModel = request.Model;
        }
        else
        {
            actualModel = agent.DefaultModel
                ?? agent.ApiService.DefaultModel
                ?? "text-embedding-3-small";
        }

        // ── AiProxyService 위임 ────────────────────────────────────────────────
        EmbeddingResultDto result;
        try
        {
            result = await aiProxy.GenerateEmbeddingAsync(
                agent.ApiService, actualModel, inputs!, cancellationToken);
        }
        catch (NotSupportedException ex)
        {
            _logger.LogWarning(ex, "/v1/embeddings 미지원 프로바이더: {ServiceCode}",
                agent.ApiService.ServiceCode);
            return BadRequest(ErrorBody("invalid_request_error", ex.Message));
        }
        catch (HttpRequestException ex) when (ex.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
        {
            _logger.LogWarning(ex, "/v1/embeddings 외부 LLM 429");
            return StatusCode(429, ErrorBody("rate_limit_exceeded", "외부 LLM Rate Limit 초과 — 잠시 후 재시도하세요."));
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "/v1/embeddings 외부 LLM 호출 실패");
            return StatusCode(502, ErrorBody("upstream_error", "임베딩 외부 호출에 실패했습니다."));
        }

        // ── 응답 구성 (OpenAI 호환 schema) ────────────────────────────────────
        var data = new List<EmbeddingItemDto>(result.Embeddings.Length);
        for (int i = 0; i < result.Embeddings.Length; i++)
        {
            data.Add(new EmbeddingItemDto
            {
                Index = i,
                Embedding = result.Embeddings[i] ?? Array.Empty<float>(),
            });
        }

        var response = new EmbeddingsResponseDto
        {
            Object = "list",
            Data = data,
            // 외부 SDK 가 model 을 echo 받기를 기대 — 실제 호출 모델 우선.
            Model = string.IsNullOrEmpty(result.Model) ? actualModel : result.Model,
            Usage = new EmbeddingUsageDto
            {
                PromptTokens = result.PromptTokens,
                TotalTokens = result.TotalTokens > 0 ? result.TotalTokens : result.PromptTokens,
            },
        };

        return Ok(response);
    }

    /// <summary>
    /// OpenAI 호환을 위해 input(object) 을 string[] 로 정규화.
    /// 허용: string / string[] / JsonElement(String|Array of String).
    /// </summary>
    private static string[]? NormalizeEmbeddingInputs(object? raw)
    {
        if (raw == null) return null;

        // 직접 string
        if (raw is string s)
            return string.IsNullOrEmpty(s) ? Array.Empty<string>() : new[] { s };

        // 직접 string[]
        if (raw is string[] arr) return arr;

        // List<string>
        if (raw is List<string> list) return list.ToArray();

        // System.Text.Json deserialization 결과 — JsonElement
        if (raw is JsonElement elem)
        {
            if (elem.ValueKind == JsonValueKind.String)
            {
                var v = elem.GetString();
                return v == null ? Array.Empty<string>() : new[] { v };
            }
            if (elem.ValueKind == JsonValueKind.Array)
            {
                var result = new List<string>(elem.GetArrayLength());
                foreach (var item in elem.EnumerateArray())
                {
                    if (item.ValueKind != JsonValueKind.String) return null; // 비-문자열 entry 거부
                    var v = item.GetString();
                    if (v != null) result.Add(v);
                }
                return result.ToArray();
            }
            return null;
        }

        return null;
    }

    // ════════════════════════════════════════════════════════════════════════════
    // POST /v1/images/generations  (Phase 7 — DU-14 R2 강제)
    //
    // OpenAI Images API 호환 엔드포인트.
    // DocUtil/career 의 직접 OpenAI/Unsplash 이미지 호출(P1 위반)을 본 게이트웨이로 흡수한다.
    //
    // 인증: ApiKey (chat 컨트롤러와 동일). agent-docutil-image-generator 같이 ServiceCode=dalle 인
    //   Agent 가 ApiKey 의 AgentId 와 일치하거나 ApiKey 가 unbound (모든 Agent 접근) 이어야 함.
    //
    // model 파싱 우선순위:
    //   1) AgentCode 가 Agents 테이블에 존재 → 그 Agent 의 ApiService + DefaultModel 사용
    //   2) "dall-e-3"/"dall-e-2" 같은 OpenAI 모델명 → docutil-image-generator Agent 로 폴백
    //
    // LlmRouting 분기:
    //   - External  → AiProxyService.SendImageGenerationAsync 로 외부 LLM 호출
    //   - Internal  → Nexus 는 이미지 미지원 — 400 한국어 안내 + permission_denied
    //   - Hybrid    → 현재 Phase 에서 정책 평가 미구현 — External 로 처리하되 X-Policy-Note 헤더로 안내
    //
    // 응답 형식:
    //   - response_format=url   (기본) — 외부 LLM 의 url 그대로 전달
    //   - response_format=b64_json    — AgentHub 가 url 을 GET 으로 다운로드 후 base64 인코딩 (DocUtil bytes 사용 경로)
    // ════════════════════════════════════════════════════════════════════════════

    [HttpPost("images/generations")]
    public async Task<IActionResult> ImagesGenerationsAsync(
        [FromBody] OpenAIImagesRequestDto request,
        [FromServices] IAiProxyService aiProxy,
        [FromServices] IHttpClientFactory httpClientFactory,
        CancellationToken cancellationToken)
    {
        // ── 인증 ────────────────────────────────────────────────────────────────
        if (!TryGetUserId(out var userId))
            return Unauthorized(ErrorBody("authentication_error", "Unauthorized"));

        // ── 요청 유효성 ─────────────────────────────────────────────────────────
        if (request == null)
            return BadRequest(ErrorBody("invalid_request_error", "요청 본문이 비어 있습니다."));

        if (string.IsNullOrWhiteSpace(request.Model))
            return BadRequest(ErrorBody("invalid_request_error", "'model' 필드는 필수입니다."));

        if (string.IsNullOrWhiteSpace(request.Prompt))
            return BadRequest(ErrorBody("invalid_request_error", "'prompt' 필드는 필수입니다."));

        if (request.Prompt.Length > 4000)
            return BadRequest(ErrorBody("invalid_request_error", "프롬프트는 최대 4000자까지 입력 가능합니다."));

        var n = request.N ?? 1;
        if (n < 1 || n > 10)
            return BadRequest(ErrorBody("invalid_request_error", "'n' 은 1~10 범위여야 합니다."));

        var responseFormat = string.IsNullOrWhiteSpace(request.ResponseFormat)
            ? "url"
            : request.ResponseFormat.ToLowerInvariant();
        if (responseFormat != "url" && responseFormat != "b64_json")
        {
            return BadRequest(ErrorBody("invalid_request_error",
                $"'response_format' 은 'url' 또는 'b64_json' 만 지원합니다 (현재: '{request.ResponseFormat}')."));
        }

        // ── Agent 룩업 ──────────────────────────────────────────────────────────
        // 우선 model 그대로 AgentCode 시도 → 실패 시 docutil-image-generator 폴백 (Phase 7.1 시드).
        var agent = await _context.Agents
            .Include(a => a.ApiService)
            .FirstOrDefaultAsync(
                a => a.AgentCode == request.Model && a.IsActive, cancellationToken);

        if (agent == null)
        {
            // OpenAI 호환 SDK 가 "dall-e-3" 같은 모델명을 보내는 경우 처리.
            agent = await _context.Agents
                .Include(a => a.ApiService)
                .FirstOrDefaultAsync(
                    a => a.AgentCode == "docutil-image-generator" && a.IsActive, cancellationToken);

            if (agent == null)
            {
                _logger.LogWarning(
                    "/v1/images/generations 요청 model='{Model}' AgentCode 미일치 + docutil-image-generator Agent 미시드",
                    request.Model);
                return NotFound(ErrorBody(
                    "model_not_found",
                    $"모델 '{request.Model}' 을 찾을 수 없으며 docutil-image-generator 폴백도 미시드 상태입니다."));
            }
        }

        // ── 권한 검사 (chat 과 동일 패턴) ──────────────────────────────────────
        // ApiKey 가 특정 Agent 에 묶인 경우, 키의 AgentId 가 본 Agent 와 일치하거나
        // Agent 가 IsPublic 이거나 사용자가 소유자여야 함.
        var agentIdClaim = User.FindFirst("AgentId")?.Value;
        if (int.TryParse(agentIdClaim, out var linkedAgentId) && linkedAgentId > 0 && linkedAgentId != agent.AgentId)
        {
            return StatusCode(403, ErrorBody("permission_denied",
                "이 API 키는 해당 이미지 생성 Agent에 접근 권한이 없습니다."));
        }
        if (!agent.IsPublic && agent.CreatedBy != userId)
            return StatusCode(403, ErrorBody("permission_denied", "이 Agent 에 접근할 수 없습니다."));

        if (agent.ApiService == null)
        {
            _logger.LogError(
                "Images Agent '{AgentCode}' 가 ApiService 를 보유하지 않음 — 시드 누락 가능성",
                agent.AgentCode);
            return StatusCode(500, ErrorBody("internal_error",
                "Agent 의 ApiService 매핑이 누락되었습니다."));
        }

        // ── LlmRouting 분기 ────────────────────────────────────────────────────
        // Nexus 는 이미지 생성 미지원 → Internal 라우팅은 400 한국어 안내 후 종료.
        // Hybrid 는 현 Phase 에서 별도 정책 평가 없이 External 로 처리.
        var llmRouting = (agent.LlmRouting ?? "External").Trim();
        if (string.Equals(llmRouting, "Internal", StringComparison.OrdinalIgnoreCase))
        {
            _logger.LogWarning(
                "/v1/images/generations Agent={AgentCode} 의 LlmRouting=Internal 차단 — Nexus 이미지 미지원",
                agent.AgentCode);
            return BadRequest(ErrorBody("invalid_request_error",
                "내부망 LLM(Nexus)은 이미지 생성을 지원하지 않습니다. Agent 의 LlmRouting 을 External 또는 Hybrid 로 설정하세요."));
        }

        // ── 실제 모델명 결정 ────────────────────────────────────────────────────
        // Agent.DefaultModel 우선 (예: "dall-e-3") — 미설정 시 ApiService.DefaultModel.
        // 단, request.Model 이 OpenAI 이미지 모델명("dall-e-") 으로 시작하면 그 값을 우선 — 외부 SDK 호환.
        string actualModel;
        if (!string.IsNullOrEmpty(request.Model)
            && request.Model.StartsWith("dall-e-", StringComparison.OrdinalIgnoreCase))
        {
            actualModel = request.Model;
        }
        else
        {
            actualModel = agent.DefaultModel
                ?? agent.ApiService.DefaultModel
                ?? "dall-e-3";
        }

        // ── 내부 ImageGenerationRequestDto 로 변환 ─────────────────────────────
        // 기존 IAiProxyService.SendImageGenerationAsync 분기(CallDallEAsync/CallGeminiImage/Imagen4/Gen4/Flux2)를
        // 그대로 재활용한다. 코드 중복 0.
        var internalRequest = new ImageGenerationRequestDto
        {
            Prompt = request.Prompt,
            Model = actualModel,
            Size = string.IsNullOrEmpty(request.Size) ? "1024x1024" : request.Size,
            Quality = string.IsNullOrEmpty(request.Quality) ? "standard" : request.Quality,
            Style = request.Style,
            NumberOfImages = n,
            UserId = userId,
            ServiceId = agent.ApiService.ServiceId,
            AgentId = agent.AgentId,
            EnableWebSearch = false, // OpenAI 호환 표면에서는 미지원
        };

        // ── AiProxyService 위임 ────────────────────────────────────────────────
        ImageGenerationResponseDto result;
        try
        {
            result = await aiProxy.SendImageGenerationAsync(
                agent.ApiService.ServiceId, actualModel, internalRequest, cancellationToken);
        }
        catch (NotSupportedException ex)
        {
            _logger.LogWarning(ex, "/v1/images/generations 미지원 프로바이더: {ServiceCode}",
                agent.ApiService.ServiceCode);
            return BadRequest(ErrorBody("invalid_request_error", ex.Message));
        }
        catch (HttpRequestException ex) when (ex.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
        {
            _logger.LogWarning(ex, "/v1/images/generations 외부 LLM 429");
            return StatusCode(429, ErrorBody("rate_limit_exceeded",
                "외부 LLM Rate Limit 초과 — 잠시 후 재시도하세요."));
        }
        catch (InvalidOperationException ex)
        {
            // OpenAI API key 미설정 / 응답 파싱 실패 등.
            _logger.LogError(ex, "/v1/images/generations 외부 LLM 호출 실패: {ServiceCode}",
                agent.ApiService.ServiceCode);
            return StatusCode(502, ErrorBody("upstream_error", "이미지 생성 외부 호출에 실패했습니다."));
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "/v1/images/generations 외부 LLM HTTP 오류: {ServiceCode}",
                agent.ApiService.ServiceCode);
            return StatusCode(502, ErrorBody("upstream_error", "이미지 생성 외부 호출 중 네트워크 오류가 발생했습니다."));
        }

        if (result?.ImageUrls == null || result.ImageUrls.Count == 0)
        {
            _logger.LogError("/v1/images/generations 결과에 ImageUrls 없음: agent={AgentCode}", agent.AgentCode);
            return StatusCode(502, ErrorBody("upstream_error", "외부 LLM 이 이미지 URL 을 반환하지 않았습니다."));
        }

        // ── 응답 구성 ──────────────────────────────────────────────────────────
        // response_format=b64_json 인 경우 외부 LLM 의 URL 을 GET 으로 받아 base64 인코딩.
        // (CallDallEAsync 가 response_format="url" 로 고정 호출하므로 본 경로가 b64 변환을 수행한다.)
        var items = new List<OpenAIImageItemDto>(result.ImageUrls.Count);
        if (responseFormat == "b64_json")
        {
            // 외부 CDN 접근에 별도의 인증이 필요 없도록 기본 HttpClient 사용 (named pool 불요).
            var downloader = httpClientFactory.CreateClient();
            downloader.Timeout = TimeSpan.FromSeconds(60);

            foreach (var url in result.ImageUrls)
            {
                if (string.IsNullOrWhiteSpace(url)) continue;
                try
                {
                    var bytes = await downloader.GetByteArrayAsync(url, cancellationToken);
                    items.Add(new OpenAIImageItemDto
                    {
                        B64Json = Convert.ToBase64String(bytes),
                    });
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex,
                        "/v1/images/generations b64_json 변환 실패: agent={AgentCode}, url(prefix)={UrlPrefix}",
                        agent.AgentCode, url.Length > 80 ? url[..80] : url);
                    return StatusCode(502, ErrorBody("upstream_error",
                        "외부 LLM URL 에서 이미지 바이트를 받아 base64 로 변환하는 중 오류가 발생했습니다."));
                }
            }

            if (items.Count == 0)
            {
                return StatusCode(502, ErrorBody("upstream_error",
                    "b64_json 변환할 유효한 이미지 URL 이 없습니다."));
            }
        }
        else
        {
            foreach (var url in result.ImageUrls)
            {
                if (string.IsNullOrWhiteSpace(url)) continue;
                items.Add(new OpenAIImageItemDto { Url = url });
            }
        }

        var response = new OpenAIImagesResponseDto
        {
            Created = DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
            Data = items,
        };

        return Ok(response);
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
