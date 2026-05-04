using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;
using System.Security.Cryptography;
using System.Text;

namespace AIAgentManagement.Services;

public class RagService : IRagService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly IEmbeddingService _embeddingService;
    private readonly CachingService _cachingService;
    private readonly ILogger<RagService> _logger;

    public RagService(
        AIAgentManagementDbContext context,
        IEmbeddingService embeddingService,
        CachingService cachingService,
        ILogger<RagService> logger)
    {
        _context = context;
        _embeddingService = embeddingService;
        _cachingService = cachingService;
        _logger = logger;
    }

    public async Task<List<RagSearchResultDto>> RetrieveAsync(
        string query,
        int topK = 5,
        int? userId = null,
        int? agentId = null,
        List<int>? documentIds = null,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(query))
            return new List<RagSearchResultDto>();

        // 쿼리 해시 (캐시 키 공통 사용)
        var queryHash = ComputeQueryHash(query);

        // [B] RAG 결과 캐싱 - 동일 조건이면 DB/API 호출 없이 반환
        var ragCacheKey = _cachingService.GetRagResultKey(queryHash, agentId, userId);
        var cachedResult = await _cachingService.GetAsync<List<RagSearchResultDto>>(ragCacheKey);
        if (cachedResult != null)
        {
            _logger.LogDebug("RAG cache hit for query hash {Hash}", queryHash);
            return cachedResult;
        }

        // [A] 쿼리 임베딩 캐싱 - 같은 질문이면 OpenAI API 호출 스킵
        float[] queryEmbedding;
        var embeddingCacheKey = _cachingService.GetEmbeddingKey(queryHash);
        var cachedEmbedding = await _cachingService.GetAsync<float[]>(embeddingCacheKey);
        if (cachedEmbedding != null)
        {
            _logger.LogDebug("Embedding cache hit for query hash {Hash}", queryHash);
            queryEmbedding = cachedEmbedding;
        }
        else
        {
            try
            {
                queryEmbedding = await _embeddingService.GetEmbeddingAsync(query, cancellationToken);
                if (queryEmbedding.Length == 0)
                {
                    _logger.LogWarning("Query embedding is empty for query: {Query}", query);
                    return new List<RagSearchResultDto>();
                }
                // 임베딩은 질문이 같으면 결과도 같으므로 1시간 캐시
                await _cachingService.SetAsync(embeddingCacheKey, queryEmbedding, TimeSpan.FromHours(1));
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to generate embedding for query: {Query}", query);
                return new List<RagSearchResultDto>();
            }
        }

        // [C] 필요한 컬럼만 SELECT - Document 전체 로드 제거
        var queryDb = _context.DocumentChunks
            .AsNoTracking()
            .Where(dc => dc.Embedding != null && dc.Embedding != "");

        // documentIds가 명시적으로 지정된 경우: 지정된 문서만 검색 (최우선)
        if (documentIds != null && documentIds.Count > 0)
        {
            _logger.LogInformation("RAG search with explicit documentIds: {DocumentIds}", string.Join(", ", documentIds));
            queryDb = queryDb.Where(dc => documentIds.Contains(dc.DocumentId));
        }
        // AgentId가 있는 경우: Agent에 연결된 문서만 검색
        else if (agentId.HasValue)
        {
            var agentDocumentIds = await _context.Agents
                .AsNoTracking()
                .Where(a => a.AgentId == agentId.Value && a.EnableRag)
                .SelectMany(a => a.AgentDocuments.Select(ad => ad.DocumentId))
                .ToListAsync(cancellationToken);

            if (agentDocumentIds.Count == 0)
                return new List<RagSearchResultDto>();

            queryDb = queryDb.Where(dc => agentDocumentIds.Contains(dc.DocumentId));
        }
        else if (userId.HasValue)
        {
            queryDb = queryDb.Where(dc => dc.Document != null && dc.Document.UserId == userId);
        }

        // [C] 임베딩·컨텐츠·메타만 SELECT (Document 전체 Include 제거)
        var chunkProjections = await queryDb
            .Select(dc => new
            {
                dc.ChunkId,
                dc.DocumentId,
                dc.Content,
                dc.Embedding,
                dc.Metadata,
                DocumentTitle = dc.Document != null ? dc.Document.Title : "Untitled Document",
                DocumentSourceId = dc.Document != null ? dc.Document.SourceId : null
            })
            .ToListAsync(cancellationToken);

        // 유사도 계산 (SIMD는 D 단계에서 EmbeddingService에 적용)
        var scored = new List<(long chunkId, int documentId, string content, string? metadata, string title, string source, float similarity)>(chunkProjections.Count);

        foreach (var chunk in chunkProjections)
        {
            try
            {
                var chunkEmbedding = _embeddingService.DeserializeEmbedding(chunk.Embedding);
                if (chunkEmbedding == null || chunkEmbedding.Length == 0) continue;

                var similarity = _embeddingService.CalculateCosineSimilarity(queryEmbedding, chunkEmbedding);
                scored.Add((
                    chunk.ChunkId,
                    chunk.DocumentId,
                    chunk.Content,
                    chunk.Metadata,
                    chunk.DocumentTitle ?? "Untitled Document",
                    chunk.DocumentTitle ?? chunk.DocumentSourceId ?? "Unknown Source",
                    similarity
                ));
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to calculate similarity for chunk {ChunkId}", chunk.ChunkId);
            }
        }

        // Top-K 결과
        var results = scored
            .OrderByDescending(x => x.similarity)
            .Take(topK)
            .Select(x => new RagSearchResultDto
            {
                DocumentId = x.documentId,
                ChunkId = x.chunkId,
                Title = x.title,
                Content = x.content,
                Similarity = x.similarity,
                Source = x.source,
                Metadata = x.metadata
            })
            .ToList();

        // [B] RAG 결과 캐싱 (10분 - 문서가 변경될 수 있으므로 짧게)
        await _cachingService.SetAsync(ragCacheKey, results, TimeSpan.FromMinutes(10));

        return results;
    }

    private static string ComputeQueryHash(string query)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(query.Trim().ToLowerInvariant()));
        return Convert.ToBase64String(bytes).Replace("/", "_").Replace("+", "-")[..16];
    }
}
