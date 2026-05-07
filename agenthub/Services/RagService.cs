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
    private readonly IDocUtilClient _docUtilClient;
    private readonly IQueryRewriter _queryRewriter;
    private readonly ILogger<RagService> _logger;

    // RRF (Reciprocal Rank Fusion) 상수 — Cormack et al. 2009 표준값
    private const int RrfK = 60;

    public RagService(
        AIAgentManagementDbContext context,
        IEmbeddingService embeddingService,
        CachingService cachingService,
        IDocUtilClient docUtilClient,
        IQueryRewriter queryRewriter,
        ILogger<RagService> logger)
    {
        _context = context;
        _embeddingService = embeddingService;
        _cachingService = cachingService;
        _docUtilClient = docUtilClient;
        _queryRewriter = queryRewriter;
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

        // ── Phase 6.2 (ADR-2): KnowledgeBaseSource 권위 시스템 분기 ─────────
        // Agent.KnowledgeBaseSource="DocUtil" 인 경우 자체 임베딩/유사도 계산을
        // 건너뛰고 DocUtil 의 하이브리드 검색(/api/v1/search) 으로 위임한다.
        // 자체 KB(AgentHub) 폴백은 본 분기 이후 기존 흐름 그대로 유지.
        // ----------------------------------------------------------------
        if (agentId.HasValue)
        {
            var agentRouting = await _context.Agents
                .AsNoTracking()
                .Where(a => a.AgentId == agentId.Value)
                .Select(a => new { a.KnowledgeBaseSource, a.KnowledgeBaseRef })
                .FirstOrDefaultAsync(cancellationToken);

            if (agentRouting != null
                && string.Equals(agentRouting.KnowledgeBaseSource, "DocUtil", StringComparison.OrdinalIgnoreCase))
            {
                try
                {
                    // ── 다국어 query rewrite + RRF (Reciprocal Rank Fusion) ─────
                    // 한국어 query 가 DocUtil 검색에서 results=0 으로 나오는 케이스를
                    // 보강하기 위해 LLM 으로 영문 변환 후 양쪽 검색 → 순위 결합.
                    // 실패 시 원본 query 만 사용(graceful).
                    var queries = await _queryRewriter.RewriteAsync(query, cancellationToken);

                    _logger.LogInformation(
                        "RAG 위임 - AgentId={AgentId}, KnowledgeBaseSource=DocUtil, CollectionRef={Ref}, TopK={TopK}, QueryCount={Count}",
                        agentId.Value, agentRouting.KnowledgeBaseRef ?? "(global)", topK, queries.Count);

                    // hit 식별 키: ChunkId 우선, 없으면 Content 해시 — 동일 청크의 RRF 누적
                    var rrfScores = new Dictionary<string, (DocUtilSearchHit hit, double score)>();

                    foreach (var q in queries)
                    {
                        var search = await _docUtilClient.SearchAsync(
                            q, agentRouting.KnowledgeBaseRef, topK, cancellationToken);

                        for (int rank = 0; rank < search.Results.Length; rank++)
                        {
                            var hit = search.Results[rank];
                            var key = !string.IsNullOrEmpty(hit.Id)
                                ? hit.Id
                                : Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(hit.Content ?? string.Empty)), 0, 16);
                            var rrf = 1.0 / (RrfK + rank);

                            if (rrfScores.TryGetValue(key, out var existing))
                            {
                                rrfScores[key] = (existing.hit, existing.score + rrf);
                            }
                            else
                            {
                                rrfScores[key] = (hit, rrf);
                            }
                        }
                    }

                    var docutilResults = rrfScores.Values
                        .OrderByDescending(x => x.score)
                        .Take(topK)
                        .Select(x => MapDocUtilHitToDto(x.hit))
                        .ToList();

                    _logger.LogInformation(
                        "RAG 결과 - DistinctChunks={Distinct}, TopK 반환={Count}",
                        rrfScores.Count, docutilResults.Count);

                    // RAG 결과 캐싱(10분) — AgentHub 자체 KB 분기와 TTL 동일.
                    await _cachingService.SetAsync(ragCacheKey, docutilResults, TimeSpan.FromMinutes(10));
                    return docutilResults;
                }
                catch (Exception ex)
                {
                    // DocUtil 응답 실패는 사용자 화면에 의미 있는 메시지로 노출되어야 한다.
                    // RagService 의 외부 시그니처는 빈 리스트 반환이지만, 운영자가 원인을
                    // 파악할 수 있도록 ERROR 레벨로 기록한 뒤 빈 결과를 반환한다.
                    _logger.LogError(
                        ex,
                        "DocUtil RAG 위임 실패 - AgentId={AgentId}, CollectionRef={Ref}. 빈 결과로 폴백.",
                        agentId.Value, agentRouting.KnowledgeBaseRef ?? "(global)");
                    return new List<RagSearchResultDto>();
                }
            }
        }

        // ── 자체 KB 폴백 흐름 (KnowledgeBaseSource != "DocUtil") ─────────
        // ADR-2 (Phase 6.4) 에 따라 자체 KB(KnowledgeBaseDocument/DocumentChunk)
        // 는 deprecate 진행 중이며 Phase 8+ 에서 drop 예정이다. 본 흐름은
        //   - Phase 5+ 호환 (KnowledgeBaseSource 미설정 또는 "AgentHub" Agent)
        //   - Phase 6.5 e2e 검증 전 안전망
        // 으로 유지된다. 신규 Agent 는 KnowledgeBaseSource="DocUtil" + KnowledgeBaseRef
        // 를 설정하여 위 분기로 라우팅되도록 권장. 본 영역의 KnowledgeBaseDocuments /
        // DocumentChunks 호출은 [Obsolete] 클래스를 사용하므로 빌드 시 CS0618 경고가
        // 발생하나, 의도적 deprecation 표시이므로 #pragma 로 차단하지 않는다.
        // ----------------------------------------------------------------
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

    // ── Phase 6.2: DocUtil 응답 → RagSearchResultDto 매핑 ───────────────────
    // DocUtil 의 청크 식별자(string UUID/문자열) 와 RagSearchResultDto 의 정수
    // DocumentId/ChunkId 사이 mismatch 를 한국어 주석과 함께 흡수한다.
    //   - DocumentId: 청크 메타에 document_id 가 정수로 들어있을 수 있으므로 best-effort 추출, 실패 시 0
    //   - ChunkId: hit.Id 의 안정적 hash(int) 로 매핑 — 운영자 화면에서는 Source 가 우선 표시되므로 비결정성 영향 없음
    //   - Title/Source: 메타에서 source 또는 title 추출, 미존재 시 "DocUtil" 폴백
    //   - Metadata: DocUtil 원본 메타를 JSON 문자열로 직렬화하여 RagSearchResultDto.Metadata 에 보존
    // 이 매핑은 임시 — Phase 6.4 에서 RagSearchResultDto 자체를 string ID 로 확장하는 것이 정도(正道).
    // ----------------------------------------------------------------------
    private static RagSearchResultDto MapDocUtilHitToDto(DocUtilSearchHit hit)
    {
        var metadataJson = hit.Metadata is null
            ? null
            : System.Text.Json.JsonSerializer.Serialize(hit.Metadata);

        // 메타에서 정수 document_id / 제목 / 소스를 best-effort 로 추출.
        int documentId = 0;
        string? title = null;
        string? source = null;
        if (hit.Metadata is System.Text.Json.JsonElement el && el.ValueKind == System.Text.Json.JsonValueKind.Object)
        {
            if (el.TryGetProperty("document_id", out var docIdProp))
            {
                if (docIdProp.ValueKind == System.Text.Json.JsonValueKind.Number && docIdProp.TryGetInt32(out var dId))
                    documentId = dId;
                else if (docIdProp.ValueKind == System.Text.Json.JsonValueKind.String
                         && int.TryParse(docIdProp.GetString(), out var dIdStr))
                    documentId = dIdStr;
            }
            if (el.TryGetProperty("title", out var titleProp) && titleProp.ValueKind == System.Text.Json.JsonValueKind.String)
                title = titleProp.GetString();
            if (el.TryGetProperty("source", out var srcProp) && srcProp.ValueKind == System.Text.Json.JsonValueKind.String)
                source = srcProp.GetString();
        }

        return new RagSearchResultDto
        {
            DocumentId = documentId,
            ChunkId = hit.Id?.GetHashCode() ?? 0, // string UUID → 안정적 int hash. RagSearchResultDto.ChunkId 는 long.
            Title = title ?? "DocUtil Document",
            Content = hit.Content,
            Similarity = (float)hit.Score,
            Source = source ?? "DocUtil",
            Metadata = metadataJson,
        };
    }
}
