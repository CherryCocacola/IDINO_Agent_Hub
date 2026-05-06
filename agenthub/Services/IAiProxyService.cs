using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IAiProxyService
{
    Task<AiResponseDto> SendChatMessageAsync(int serviceId, string model, ChatMessageRequestDto request, CancellationToken cancellationToken = default);

    /// <summary>
    /// (deprecated, 호출처 0건) 원본 Stream을 그대로 반환합니다.
    /// ApiKeyPool 라운드로빈/Cooldown 적용 누락(H5) 및 진짜 streaming 미보장 문제로
    /// SendChatMessageStreamChunksAsync 로 대체되었습니다. 신규 호출은 ChatChunk 기반 메서드를 사용합니다.
    /// TECHSPEC §16 H5 참조.
    /// </summary>
    [Obsolete("Use SendChatMessageStreamChunksAsync. This method bypasses ApiKeyPool/Cooldown and does not guarantee real-time streaming.")]
    Task<Stream> SendChatMessageStreamAsync(int serviceId, string model, ChatMessageRequestDto request, CancellationToken cancellationToken = default);

    /// <summary>
    /// 진짜 SSE 스트리밍 — provider별 native streaming 응답을 ChatChunk 단위로 yield 합니다.
    /// OpenAI는 stream_options.include_usage:true 옵션으로 마지막 chunk에 usage를 포함시킵니다.
    /// 다른 provider(claude/gemini/perplexity/mistral/copilot/azure-openai)는 현재 비스트리밍 호출 결과를
    /// 단일 chunk로 폴백 yield합니다 — Phase 5+ 에서 native streaming 정식 구현 예정.
    /// ApiKeyPool 라운드로빈 + 429 Cooldown은 본 메서드 내부에서 적용됩니다(H5 해결).
    /// </summary>
    IAsyncEnumerable<ChatChunk> SendChatMessageStreamChunksAsync(int serviceId, string model, ChatMessageRequestDto request, CancellationToken cancellationToken = default);

    Task<decimal> CalculateCostAsync(int serviceId, string model, int promptTokens, int completionTokens);
    Task<List<string>> GetAvailableModelsAsync(int serviceId, CancellationToken cancellationToken = default);
    Task<bool> TestServiceConnectionAsync(int serviceId, CancellationToken cancellationToken = default);
    Task<ImageGenerationResponseDto> SendImageGenerationAsync(int serviceId, string model, ImageGenerationRequestDto request, CancellationToken cancellationToken = default);
    Task<decimal> CalculateImageGenerationCostAsync(int serviceId, string model, string size, string quality, int numberOfImages);

    /// <summary>
    /// Phase 7.5 — Embeddings 위임 (OpenAI 호환).
    /// AgentHub 는 ApiService.ServiceCode 분기로 OpenAI/Azure OpenAI Embeddings API 를 호출한다.
    /// 외부 SDK 호환을 위해 OpenAI Embeddings API 와 동일한 응답 schema 를 그대로 반환한다.
    /// </summary>
    /// <param name="service">조회된 ApiService (Embeddings 호환 프로바이더만 허용).</param>
    /// <param name="model">실제 LLM 모델명 (예: "text-embedding-3-small").</param>
    /// <param name="inputs">임베딩 대상 텍스트 배열 (단건도 길이 1 배열로 전달).</param>
    /// <returns>임베딩 벡터 배열 + 토큰 사용량.</returns>
    Task<EmbeddingResultDto> GenerateEmbeddingAsync(
        Models.ApiService service,
        string model,
        string[] inputs,
        CancellationToken cancellationToken = default);
}

/// <summary>
/// Phase 7.5 — 내부용 임베딩 결과 컨테이너. OpenAICompatController 가 OpenAI 호환 응답으로 매핑한다.
/// </summary>
public class EmbeddingResultDto
{
    /// <summary>입력 순서를 보존한 임베딩 벡터 배열. inputs.Length == Embeddings.Length.</summary>
    public float[][] Embeddings { get; set; } = Array.Empty<float[]>();

    /// <summary>실제 호출된 모델명 (프로바이더가 echo 한 값 우선, 없으면 요청 model).</summary>
    public string Model { get; set; } = string.Empty;

    public int PromptTokens { get; set; }
    public int TotalTokens { get; set; }
}
