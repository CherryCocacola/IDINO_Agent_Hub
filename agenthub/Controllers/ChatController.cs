using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
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
}
