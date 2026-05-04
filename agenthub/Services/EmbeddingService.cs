using System.Numerics;
using System.Text;
using System.Text.Json;

namespace AIAgentManagement.Services;

public class EmbeddingService : IEmbeddingService
{
    private readonly IConfiguration _configuration;
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<EmbeddingService> _logger;
    private readonly string _model;
    private readonly int _dimension;
    private readonly int _batchSize;

    public EmbeddingService(
        IConfiguration configuration,
        IHttpClientFactory httpClientFactory,
        ILogger<EmbeddingService> logger)
    {
        _configuration = configuration;
        _httpClientFactory = httpClientFactory;
        _logger = logger;
        _model = _configuration["EmbeddingSettings:Model"] ?? "text-embedding-3-small";
        _dimension = _configuration.GetValue<int>("EmbeddingSettings:Dimension", 1536);
        _batchSize = _configuration.GetValue<int>("EmbeddingSettings:BatchSize", 100);
    }

    public async Task<float[]> GetEmbeddingAsync(string text, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            throw new ArgumentException("Text cannot be null or empty", nameof(text));
        }

        var embeddings = await GetEmbeddingsAsync(new[] { text }, cancellationToken);
        return embeddings.FirstOrDefault() ?? Array.Empty<float>();
    }

    public async Task<List<float[]>> GetEmbeddingsAsync(IEnumerable<string> texts, CancellationToken cancellationToken = default)
    {
        var textList = texts.ToList();
        if (!textList.Any())
        {
            return new List<float[]>();
        }

        var apiKey = _configuration["AiApiSettings:OpenAI:ApiKey"];
        var baseUrl = _configuration["AiApiSettings:OpenAI:BaseUrl"] ?? "https://api.openai.com/v1";

        if (string.IsNullOrEmpty(apiKey))
        {
            throw new InvalidOperationException("OpenAI API key is not configured");
        }

        var client = _httpClientFactory.CreateClient();
        client.Timeout = TimeSpan.FromSeconds(60);
        client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);

        var results = new List<float[]>();

        // 배치 처리
        for (int i = 0; i < textList.Count; i += _batchSize)
        {
            var batch = textList.Skip(i).Take(_batchSize).ToList();
            
            var requestBody = new
            {
                model = _model,
                input = batch,
                dimensions = _dimension
            };

            var json = JsonSerializer.Serialize(requestBody);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            try
            {
                var response = await client.PostAsync($"{baseUrl}/embeddings", content, cancellationToken);
                response.EnsureSuccessStatusCode();

                var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);
                var embeddingResponse = JsonSerializer.Deserialize<EmbeddingResponse>(responseJson, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });

                if (embeddingResponse?.Data == null)
                {
                    _logger.LogError("Invalid embedding response: {Response}", responseJson);
                    throw new InvalidOperationException("Invalid embedding response");
                }

                foreach (var item in embeddingResponse.Data)
                {
                    if (item.Embedding != null)
                    {
                        results.Add(item.Embedding);
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error generating embeddings for batch {BatchIndex}", i / _batchSize);
                throw;
            }
        }

        return results;
    }

    public string SerializeEmbedding(float[] embedding)
    {
        if (embedding == null || embedding.Length == 0)
        {
            return "[]";
        }

        return JsonSerializer.Serialize(embedding);
    }

    public float[]? DeserializeEmbedding(string? json)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            return null;
        }

        try
        {
            return JsonSerializer.Deserialize<float[]>(json);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to deserialize embedding: {Json}", json);
            return null;
        }
    }

    public float CalculateCosineSimilarity(float[] embedding1, float[] embedding2)
    {
        if (embedding1 == null || embedding2 == null)
            throw new ArgumentNullException("Embeddings cannot be null");

        if (embedding1.Length != embedding2.Length)
            throw new ArgumentException($"Embedding dimensions must match. Got {embedding1.Length} and {embedding2.Length}");

        if (embedding1.Length == 0)
            return 0f;

        // SIMD(Vector<float>)로 병렬 연산 — CPU 벡터 레지스터 활용 (4~8배 빠름)
        int simdWidth = Vector<float>.Count;
        int i = 0;
        var vDot = Vector<float>.Zero;
        var vNorm1 = Vector<float>.Zero;
        var vNorm2 = Vector<float>.Zero;

        // SIMD 처리 가능한 구간
        for (; i <= embedding1.Length - simdWidth; i += simdWidth)
        {
            var v1 = new Vector<float>(embedding1, i);
            var v2 = new Vector<float>(embedding2, i);
            vDot += v1 * v2;
            vNorm1 += v1 * v1;
            vNorm2 += v2 * v2;
        }

        float dotProduct = Vector.Dot(vDot, Vector<float>.One);
        float norm1 = Vector.Dot(vNorm1, Vector<float>.One);
        float norm2 = Vector.Dot(vNorm2, Vector<float>.One);

        // 나머지 스칼라 처리
        for (; i < embedding1.Length; i++)
        {
            dotProduct += embedding1[i] * embedding2[i];
            norm1 += embedding1[i] * embedding1[i];
            norm2 += embedding2[i] * embedding2[i];
        }

        float denominator = MathF.Sqrt(norm1) * MathF.Sqrt(norm2);
        return denominator == 0f ? 0f : dotProduct / denominator;
    }

    private class EmbeddingResponse
    {
        public List<EmbeddingDataItem>? Data { get; set; }
    }

    private class EmbeddingDataItem
    {
        public float[]? Embedding { get; set; }
    }
}
