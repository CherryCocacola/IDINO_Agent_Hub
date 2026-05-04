using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IChatService
{
    Task<List<ConversationDto>> GetConversationsAsync(int userId, bool? isArchived = null);
    Task<ConversationDto?> GetConversationByIdAsync(int conversationId, int userId);
    Task<ConversationDto> CreateConversationAsync(CreateConversationRequestDto request, int userId);
    Task<ConversationDto?> UpdateConversationAsync(int conversationId, UpdateConversationRequestDto request, int userId);
    Task<bool> DeleteConversationAsync(int conversationId, int userId);
    Task<List<ChatMessageDto>> GetMessagesAsync(int conversationId, int userId);
    Task<ChatMessageDto> SendMessageAsync(int conversationId, SendMessageRequestDto request, int userId);
    Task<bool> ArchiveConversationAsync(int conversationId, int userId, bool archive);
    Task<DirectSendMessageResponseDto> SendDirectMessageAsync(DirectSendMessageRequestDto request, int userId);
}
