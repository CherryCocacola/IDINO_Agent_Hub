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

    /// <summary>
    /// 진짜 SSE 스트리밍 — DirectSendMessageRequestDto 기반.
    /// 흐름: PII / BannedWord 검사 → AiProxyService.SendChatMessageStreamChunksAsync → ChatChunk yield →
    /// 완료 후 ChatMessage / ApiUsage / Quota 기록.
    /// usage chunk 도달 시점에 quota/cost 기록을 수행합니다 (마지막에 RecordUsageAsync).
    /// 비스트리밍 SendDirectMessageAsync 와 동일한 보안/로깅 정책을 유지합니다.
    /// 가짜 SSE(C9)와 H5(키 풀 우회) 동시 해소를 위해 도입된 streaming 진입점입니다.
    /// </summary>
    IAsyncEnumerable<ChatChunk> SendDirectMessageStreamChunksAsync(DirectSendMessageRequestDto request, int userId, CancellationToken cancellationToken = default);
}
