namespace AIAgentManagement.DTOs;

/// <summary>
/// Vue UI(`/api/chat/send/stream`) 전용 SSE 이벤트 단위.
///
/// OpenAI 호환 엔드포인트(`/v1/chat/completions`)의 표준 chat.completion.chunk 포맷과는
/// 별개로, AgentHub Vue 채팅 UI가 소비하기 쉬운 discriminator 기반 형식으로 표현됩니다.
///
/// 흐름:
///   - delta: AI 토큰이 흐를 때마다 yield (Type="delta", Content 채움)
///   - usage: 마지막 chunk에 동봉된 토큰 사용량 yield (Type="usage")
///   - meta : 영속화 완료 후 conversationId / messageId / model / cost yield (Type="meta")
///
/// SSE 응답 명세 (camelCase JSON):
///   data: {"type":"delta","content":"<token>"}\n\n
///   data: {"type":"usage","promptTokens":10,"completionTokens":20,"totalTokens":30,"cost":0.0001}\n\n
///   data: {"type":"meta","conversationId":123,"messageId":456,"model":"gpt-4o-mini"}\n\n
///   data: [DONE]\n\n
///
/// Phase 3.5b에서 도입 — 사용자 보고 "Vue UI에서 5~10초 대기 후 일괄 출력" 직접 해소.
/// 기존 ChatChunk / SendDirectMessageStreamChunksAsync 는 OpenAI 호환 SSE 전용으로 유지(불변).
/// </summary>
public sealed record ChatStreamEvent(
    string Type,
    string? Content = null,
    int? ConversationId = null,
    long? MessageId = null,
    string? Model = null,
    decimal? Cost = null,
    int? PromptTokens = null,
    int? CompletionTokens = null,
    int? TotalTokens = null
)
{
    /// <summary>delta 텍스트 chunk.</summary>
    public static ChatStreamEvent Delta(string content) =>
        new("delta", Content: content);

    /// <summary>usage chunk — 토큰 사용량 + 계산된 비용 동봉.</summary>
    public static ChatStreamEvent UsageEvent(int promptTokens, int completionTokens, int totalTokens, decimal? cost) =>
        new("usage",
            PromptTokens: promptTokens,
            CompletionTokens: completionTokens,
            TotalTokens: totalTokens,
            Cost: cost);

    /// <summary>meta chunk — 영속화 후 회수된 conversationId / messageId / model.</summary>
    public static ChatStreamEvent Meta(int? conversationId, long? messageId, string? model, decimal? cost) =>
        new("meta",
            ConversationId: conversationId,
            MessageId: messageId,
            Model: model,
            Cost: cost);
}
