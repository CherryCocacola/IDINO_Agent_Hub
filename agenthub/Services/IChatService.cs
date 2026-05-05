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
    ///
    /// OpenAI 호환 엔드포인트(`/v1/chat/completions`)가 소비합니다. Vue UI 전용 분기는
    /// SendDirectMessageStreamEventsAsync 를 사용합니다.
    /// </summary>
    IAsyncEnumerable<ChatChunk> SendDirectMessageStreamChunksAsync(DirectSendMessageRequestDto request, int userId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Vue UI 전용 진짜 SSE 스트리밍 — DirectSendMessageRequestDto 기반.
    /// 흐름: PII / BannedWord 검사 → AiProxyService.SendChatMessageStreamChunksAsync → delta/usage event yield →
    /// 영속화(ChatMessage / ApiUsage / Conversation 통계 / Quota) 후 meta event yield.
    ///
    /// SendDirectMessageStreamChunksAsync 와 거의 동일한 흐름이지만, 마지막에 Vue UI가 활용할 수 있도록
    /// conversationId / messageId / model / cost 를 담은 meta 이벤트를 추가로 yield 합니다.
    /// (기존 wrapper는 OpenAI 호환 SSE 표준에 맞춰 ChatChunk 만 yield 하므로 분리)
    ///
    /// Phase 3.5b — 사용자 보고 "Vue UI에서 5~10초 대기 후 일괄 출력" 직접 해소.
    /// </summary>
    IAsyncEnumerable<ChatStreamEvent> SendDirectMessageStreamEventsAsync(DirectSendMessageRequestDto request, int userId, CancellationToken cancellationToken = default);
}
