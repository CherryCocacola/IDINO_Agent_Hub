namespace AIAgentManagement.Services;

public interface IEmbeddingService
{
    /// <summary>
    /// 단일 텍스트를 임베딩 벡터로 변환
    /// </summary>
    Task<float[]> GetEmbeddingAsync(string text, CancellationToken cancellationToken = default);

    /// <summary>
    /// 여러 텍스트를 배치로 임베딩 벡터로 변환
    /// </summary>
    Task<List<float[]>> GetEmbeddingsAsync(IEnumerable<string> texts, CancellationToken cancellationToken = default);

    /// <summary>
    /// 임베딩 벡터를 JSON 문자열로 직렬화
    /// </summary>
    string SerializeEmbedding(float[] embedding);

    /// <summary>
    /// JSON 문자열에서 임베딩 벡터로 역직렬화
    /// </summary>
    float[]? DeserializeEmbedding(string? json);

    /// <summary>
    /// 두 임베딩 벡터 간의 코사인 유사도를 계산
    /// </summary>
    float CalculateCosineSimilarity(float[] embedding1, float[] embedding2);
}
