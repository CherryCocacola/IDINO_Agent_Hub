namespace AIAgentManagement.DTOs;

/// <summary>
/// 진짜 SSE 스트리밍에서 한 chunk를 표현합니다.
/// IAiProxyService.SendChatMessageStreamChunksAsync 가 반환하는 IAsyncEnumerable&lt;ChatChunk&gt;의 단위.
///
/// 사용 패턴:
///   - delta(부분 텍스트): Content 채움, FinishReason 은 null
///   - 종료 이벤트: Content 는 null/빈문자, FinishReason 채움 (예: "stop")
///   - usage 동봉: 마지막 chunk에 PromptTokens/CompletionTokens/TotalTokens 채움 (Provider가 지원할 때만)
///
/// 가짜 SSE(C9)와 H5(키 풀 우회) 동시 해소를 목표로 도입된 타입입니다.
/// TECHSPEC §15.4 / §16 C9 / H5 참조.
/// </summary>
public sealed record ChatChunk(
    string? Content,
    string? FinishReason,
    int? PromptTokens,
    int? CompletionTokens,
    int? TotalTokens
)
{
    /// <summary>delta 텍스트만 담은 chunk를 만듭니다.</summary>
    public static ChatChunk Delta(string content) =>
        new(content, null, null, null, null);

    /// <summary>종료 chunk를 만듭니다 (FinishReason 만 채움).</summary>
    public static ChatChunk Stop(string finishReason = "stop") =>
        new(null, finishReason, null, null, null);

    /// <summary>usage 정보를 담은 마지막 chunk를 만듭니다.</summary>
    public static ChatChunk Usage(int promptTokens, int completionTokens, int totalTokens) =>
        new(null, null, promptTokens, completionTokens, totalTokens);
}
