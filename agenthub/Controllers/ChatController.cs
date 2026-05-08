using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using System.Text.Json;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;
using AIAgentManagement.Exceptions;
using AIAgentManagement.Hubs;
using Microsoft.AspNetCore.SignalR;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class ChatController : ControllerBase
{
    private readonly IChatService _chatService;
    private readonly IHubContext<ChatHub> _chatHub;
    private readonly ILogger<ChatController> _logger;

    public ChatController(
        IChatService chatService,
        IHubContext<ChatHub> chatHub,
        ILogger<ChatController> logger)
    {
        _chatService = chatService;
        _chatHub = chatHub;
        _logger = logger;
    }

    [HttpGet("conversations")]
    public async Task<ActionResult<List<ConversationDto>>> GetConversations([FromQuery] bool? isArchived)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var conversations = await _chatService.GetConversationsAsync(userId, isArchived);
            return Ok(conversations);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting conversations");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("conversations/{id}")]
    public async Task<ActionResult<ConversationDto>> GetConversation(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var conversation = await _chatService.GetConversationByIdAsync(id, userId);
            if (conversation == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(conversation);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting conversation {ConversationId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost("conversations")]
    public async Task<ActionResult<ConversationDto>> CreateConversation([FromBody] CreateConversationRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var conversation = await _chatService.CreateConversationAsync(request, userId);
            return CreatedAtAction(nameof(GetConversation), new { id = conversation.ConversationId }, conversation);
        }
        catch (ArgumentException ex)
        {
            // ServiceId/AgentId 누락 또는 존재하지 않는 AgentId — 400 으로 사용자에게 한국어 안내.
            _logger.LogWarning(ex, "대화 생성 입력값 검증 실패");
            return BadRequest(new ErrorResponseDto(ex.Message, "VALIDATION_ERROR", null));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating conversation");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPut("conversations/{id}")]
    public async Task<ActionResult<ConversationDto>> UpdateConversation(int id, [FromBody] UpdateConversationRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var conversation = await _chatService.UpdateConversationAsync(id, request, userId);
            if (conversation == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(conversation);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating conversation {ConversationId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpDelete("conversations/{id}")]
    public async Task<ActionResult> DeleteConversation(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var result = await _chatService.DeleteConversationAsync(id, userId);
            if (!result)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting conversation {ConversationId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("conversations/{id}/messages")]
    public async Task<ActionResult<List<ChatMessageDto>>> GetMessages(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var messages = await _chatService.GetMessagesAsync(id, userId);
            return Ok(messages);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting messages for conversation {ConversationId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost("conversations/{id}/messages")]
    public async Task<ActionResult<ChatMessageDto>> SendMessage(int id, [FromBody] SendMessageRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var message = await _chatService.SendMessageAsync(id, request, userId);

            // Send SignalR notification
            await _chatHub.Clients.Group($"conversation_{id}").SendAsync("ReceiveMessage", message);

            return Ok(message);
        }
        catch (BannedWordException ex)
        {
            var errorResponse = ErrorResponseDto.FromBannedWordException(ex);
            return BadRequest(errorResponse);
        }
        catch (PiiDetectionException ex)
        {
            var errorResponse = ErrorResponseDto.FromPiiDetectionException(ex);
            return BadRequest(errorResponse);
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ErrorResponseDto.BadRequest(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error sending message to conversation {ConversationId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost("conversations/{id}/archive")]
    public async Task<ActionResult> ArchiveConversation(int id, [FromBody] bool archive)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var result = await _chatService.ArchiveConversationAsync(id, userId, archive);
            if (!result)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(new { message = archive ? "Conversation archived" : "Conversation unarchived" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error archiving conversation {ConversationId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost("send")]
    public async Task<ActionResult> SendDirectMessage([FromBody] DirectSendMessageRequestDto request)
    {
        try
        {
            // 요청 데이터 로깅 (디버깅용)
            _logger.LogInformation("Received SendDirectMessage request: ServiceId={ServiceId}, AgentId={AgentId}, MessagesCount={MessagesCount}",
                request?.ServiceId, request?.AgentId, request?.Messages?.Count ?? 0);

            if (!ModelState.IsValid)
            {
                var errors = ModelState.Values.SelectMany(v => v.Errors.Select(e => e.ErrorMessage));
                _logger.LogWarning("Invalid model state: {Errors}", string.Join(", ", errors));
                
                // ModelState의 키와 에러 상세 정보 로깅
                foreach (var key in ModelState.Keys)
                {
                    var state = ModelState[key];
                    if (state?.Errors != null && state.Errors.Count > 0)
                    {
                        _logger.LogWarning("ModelState error for key '{Key}': {Errors}", 
                            key, string.Join(", ", state.Errors.Select(e => e.ErrorMessage)));
                    }
                }
                
                return BadRequest(ErrorResponseDto.BadRequest("Invalid request"));
            }

            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            // Validation
            if (request == null)
            {
                return BadRequest(ErrorResponseDto.BadRequest("Request body is required"));
            }

            if (request.Messages == null || request.Messages.Count == 0)
            {
                return BadRequest(ErrorResponseDto.BadRequest("Messages array is required and cannot be empty"));
            }

            // 각 메시지 검증: Content 또는 Contents 중 하나는 있어야 함
            foreach (var msg in request.Messages)
            {
                // Role 검증
                if (string.IsNullOrWhiteSpace(msg.Role))
                {
                    return BadRequest(ErrorResponseDto.BadRequest("Message Role is required"));
                }

                // Content 또는 Contents 검증
                var hasContent = !string.IsNullOrWhiteSpace(msg.Content);
                var hasContents = msg.Contents != null && msg.Contents.Count > 0;

                if (!hasContent && !hasContents)
                {
                    return BadRequest(ErrorResponseDto.BadRequest($"Message with role '{msg.Role}' must have either Content or Contents"));
                }

                // Contents가 있으면 각 항목 검증
                if (hasContents && msg.Contents != null)
                {
                    foreach (var content in msg.Contents)
                    {
                        if (string.IsNullOrWhiteSpace(content.Type))
                        {
                            return BadRequest(ErrorResponseDto.BadRequest($"Content item in message with role '{msg.Role}' must have a Type"));
                        }

                        // Type에 따라 필수 필드 검증
                        switch (content.Type.ToLower())
                        {
                            case "text":
                                if (string.IsNullOrWhiteSpace(content.Text))
                                {
                                    return BadRequest(ErrorResponseDto.BadRequest($"Text content in message with role '{msg.Role}' must have Text"));
                                }
                                break;
                            case "image_url":
                                if (string.IsNullOrWhiteSpace(content.ImageUrl))
                                {
                                    return BadRequest(ErrorResponseDto.BadRequest($"Image content in message with role '{msg.Role}' must have ImageUrl"));
                                }
                                break;
                            case "audio_url":
                                if (string.IsNullOrWhiteSpace(content.AudioUrl))
                                {
                                    return BadRequest(ErrorResponseDto.BadRequest($"Audio content in message with role '{msg.Role}' must have AudioUrl"));
                                }
                                break;
                            case "file":
                                if (string.IsNullOrWhiteSpace(content.FileUrl))
                                {
                                    return BadRequest(ErrorResponseDto.BadRequest($"File content in message with role '{msg.Role}' must have FileUrl"));
                                }
                                break;
                        }
                    }
                }
            }

            if (!request.ServiceId.HasValue)
            {
                return BadRequest(ErrorResponseDto.BadRequest("ServiceId is required"));
            }

            var result = await _chatService.SendDirectMessageAsync(request, userId);
            return Ok(result);
        }
        catch (BannedWordException ex)
        {
            _logger.LogWarning(ex, "Banned word detected: {BlockedWords}", string.Join(", ", ex.BlockedWords));
            var errorResponse = ErrorResponseDto.FromBannedWordException(ex);
            return BadRequest(errorResponse);
        }
        catch (PiiDetectionException ex)
        {
            _logger.LogWarning(ex, "PII detected: {DetectedTypes}", string.Join(", ", ex.DetectedTypes));
            var errorResponse = ErrorResponseDto.FromPiiDetectionException(ex);
            return BadRequest(errorResponse);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogWarning(ex, "Invalid operation: {Message}", ex.Message);
            return BadRequest(ErrorResponseDto.BadRequest(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error sending direct message");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred: " + ex.Message));
        }
    }

    // ════════════════════════════════════════════════════════════════════════════
    // Phase 3.5b — Vue UI 전용 진짜 SSE 스트리밍
    //
    // 흐름: SendDirectMessage 와 동일한 검증을 통과 → IChatService.SendDirectMessageStreamEventsAsync
    // 호출 → ChatStreamEvent 를 SSE frame 으로 변환하여 즉시 flush.
    //
    // 응답 명세 (camelCase JSON):
    //   data: {"type":"delta","content":"<token>"}\n\n
    //   data: {"type":"usage","promptTokens":10,"completionTokens":20,"totalTokens":30,"cost":0.0001}\n\n
    //   data: {"type":"meta","conversationId":123,"messageId":456,"model":"gpt-4o-mini"}\n\n
    //   data: [DONE]\n\n
    // 에러:
    //   data: {"type":"error","code":"BANNED_WORD_DETECTED|...","message":"한국어 메시지"}\n\n
    //   data: [DONE]\n\n
    //
    // 사용자 보고 "Vue UI에서 5~10초 대기 후 일괄 출력" 직접 해소.
    // 기존 비스트리밍 [POST] /api/chat/send 는 호환을 위해 유지.
    // OpenAI 호환 [POST] /v1/chat/completions(stream:true) 는 별도 SSE 형식으로 유지(ChatChunk 기반, 회귀 0).
    // ════════════════════════════════════════════════════════════════════════════
    [HttpPost("send/stream")]
    public async Task SendDirectMessageStream([FromBody] DirectSendMessageRequestDto request, CancellationToken cancellationToken)
    {
        // ── 인증 확인 (SSE 시작 전이므로 401/400 일반 응답 사용) ─────────────────
        var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
        {
            Response.StatusCode = StatusCodes.Status401Unauthorized;
            Response.ContentType = "application/json; charset=utf-8";
            await Response.WriteAsJsonAsync(ErrorResponseDto.Unauthorized(), cancellationToken);
            return;
        }

        // ── ModelState / Validation (SendDirectMessage 와 동일한 정책) ──────────
        if (!ModelState.IsValid)
        {
            Response.StatusCode = StatusCodes.Status400BadRequest;
            Response.ContentType = "application/json; charset=utf-8";
            await Response.WriteAsJsonAsync(ErrorResponseDto.BadRequest("Invalid request"), cancellationToken);
            return;
        }

        if (request == null)
        {
            Response.StatusCode = StatusCodes.Status400BadRequest;
            Response.ContentType = "application/json; charset=utf-8";
            await Response.WriteAsJsonAsync(ErrorResponseDto.BadRequest("Request body is required"), cancellationToken);
            return;
        }

        if (request.Messages == null || request.Messages.Count == 0)
        {
            Response.StatusCode = StatusCodes.Status400BadRequest;
            Response.ContentType = "application/json; charset=utf-8";
            await Response.WriteAsJsonAsync(ErrorResponseDto.BadRequest("Messages array is required and cannot be empty"), cancellationToken);
            return;
        }

        foreach (var msg in request.Messages)
        {
            if (string.IsNullOrWhiteSpace(msg.Role))
            {
                Response.StatusCode = StatusCodes.Status400BadRequest;
                Response.ContentType = "application/json; charset=utf-8";
                await Response.WriteAsJsonAsync(ErrorResponseDto.BadRequest("Message Role is required"), cancellationToken);
                return;
            }

            var hasContent = !string.IsNullOrWhiteSpace(msg.Content);
            var hasContents = msg.Contents != null && msg.Contents.Count > 0;
            if (!hasContent && !hasContents)
            {
                Response.StatusCode = StatusCodes.Status400BadRequest;
                Response.ContentType = "application/json; charset=utf-8";
                await Response.WriteAsJsonAsync(ErrorResponseDto.BadRequest($"Message with role '{msg.Role}' must have either Content or Contents"), cancellationToken);
                return;
            }
        }

        if (!request.ServiceId.HasValue && !request.AgentId.HasValue)
        {
            // ServiceId 는 ChatService 가 AgentId 로부터 보충하므로 둘 중 하나만 있으면 통과
            Response.StatusCode = StatusCodes.Status400BadRequest;
            Response.ContentType = "application/json; charset=utf-8";
            await Response.WriteAsJsonAsync(ErrorResponseDto.BadRequest("ServiceId or AgentId is required"), cancellationToken);
            return;
        }

        // ── SSE 헤더 (IIS InProcess + reverse proxy buffering 방지) ────────────
        Response.ContentType = "text/event-stream; charset=utf-8";
        Response.Headers["Cache-Control"]      = "no-cache";
        Response.Headers["X-Accel-Buffering"]  = "no";
        Response.Headers["Connection"]          = "keep-alive";
        // Content-Length 미설정 + 첫 frame flush 로 chunked transfer 강제

        try
        {
            await foreach (var evt in _chatService
                .SendDirectMessageStreamEventsAsync(request, userId, cancellationToken)
                .WithCancellation(cancellationToken))
            {
                await WriteSseFrameAsync(evt, cancellationToken);
            }

            await Response.WriteAsync("data: [DONE]\n\n", cancellationToken);
            await Response.Body.FlushAsync(cancellationToken);
        }
        catch (BannedWordException ex)
        {
            _logger.LogWarning(ex, "Banned word detected (stream): {BlockedWords}", string.Join(", ", ex.BlockedWords));
            await WriteSseErrorAsync("BANNED_WORD_DETECTED", ex.Message ?? "금칙어가 포함되어 있습니다.", cancellationToken);
        }
        catch (PiiDetectionException ex)
        {
            _logger.LogWarning(ex, "PII detected (stream): {DetectedTypes}", string.Join(", ", ex.DetectedTypes));
            await WriteSseErrorAsync("PII_DETECTED", ex.Message ?? "개인정보가 포함되어 있습니다.", cancellationToken);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogWarning(ex, "Invalid operation (stream): {Message}", ex.Message);
            await WriteSseErrorAsync("VALIDATION_ERROR", ex.Message, cancellationToken);
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            // 클라이언트 disconnect — 정상 종료
            _logger.LogInformation("Vue UI 스트리밍 클라이언트 연결 종료: UserId={UserId}", userId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Streaming chat error: UserId={UserId}", userId);
            await WriteSseErrorAsync("INTERNAL_ERROR", "서버 처리 중 오류가 발생했습니다.", cancellationToken);
        }
    }

    /// <summary>
    /// ChatStreamEvent → SSE frame (data: {...}\n\n) 변환 + 즉시 flush.
    /// camelCase JSON (Program.cs 의 JsonNamingPolicy.CamelCase 와 일치).
    /// </summary>
    private async Task WriteSseFrameAsync(object payload, CancellationToken cancellationToken)
    {
        if (cancellationToken.IsCancellationRequested) return;
        var json = JsonSerializer.Serialize(payload, _sseJsonOptions);
        await Response.WriteAsync($"data: {json}\n\n", cancellationToken);
        await Response.Body.FlushAsync(cancellationToken);
    }

    /// <summary>
    /// SSE 에러 frame + [DONE] 종료. 스트림 시작 후 발생한 예외 처리용
    /// (이미 200 OK + text/event-stream 헤더가 흘러간 상태에서 상태 코드 변경 불가).
    /// </summary>
    private async Task WriteSseErrorAsync(string code, string message, CancellationToken cancellationToken)
    {
        try
        {
            await WriteSseFrameAsync(new { type = "error", code, message }, cancellationToken);
            await Response.WriteAsync("data: [DONE]\n\n", cancellationToken);
            await Response.Body.FlushAsync(cancellationToken);
        }
        catch (Exception writeEx)
        {
            // 클라이언트 연결이 이미 끊어진 경우 — 무시하고 종료
            _logger.LogDebug(writeEx, "SSE error frame 전송 실패 (클라이언트 연결 종료 추정)");
        }
    }

    private static readonly JsonSerializerOptions _sseJsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull,
    };
}
