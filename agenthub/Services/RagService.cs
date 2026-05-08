using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using Microsoft.EntityFrameworkCore;
using System.Security.Cryptography;
using System.Text;

namespace AIAgentManagement.Services;

public class RagService : IRagService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly CachingService _cachingService;
    private readonly IDocUtilClient _docUtilClient;
    private readonly IQueryRewriter _queryRewriter;
    private readonly IRagMetrics _ragMetrics;
    private readonly ILogger<RagService> _logger;

    // RRF (Reciprocal Rank Fusion) 상수 — Cormack et al. 2009 표준값
    private const int RrfK = 60;

    public RagService(
        AIAgentManagementDbContext context,
        CachingService cachingService,
        IDocUtilClient docUtilClient,
        IQueryRewriter queryRewriter,
        IRagMetrics ragMetrics,
        ILogger<RagService> logger)
    {
        _context = context;
        _cachingService = cachingService;
        _docUtilClient = docUtilClient;
        _queryRewriter = queryRewriter;
        _ragMetrics = ragMetrics;
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

        // ── Phase 8 (ADR-2): KnowledgeBaseSource 단일 분기 ──────────────────
        // 자체 KB(KnowledgeBaseDocuments / DocumentChunks / AgentDocuments) 코드/스키마는
        // 본 Phase 에서 완전 제거되었다. 이제 Agent.KnowledgeBaseSource="DocUtil" 만
        // 실제 RAG 를 수행하며, 그 외(NULL / "AgentHub" 등) 는 RAG 비활성으로 처리한다.
        // 운영자가 KnowledgeBaseSource 를 바꾸지 않은 채로 EnableRag=true 인 Agent 는
        // 정보 로그를 남기고 빈 결과를 반환 — ChatService 는 그대로 LLM 호출을 진행한다.
        // ----------------------------------------------------------------
        if (!agentId.HasValue)
        {
            _logger.LogInformation(
                "RAG 비활성 - AgentId 미지정. ADR-2 단일 권위 정책에 따라 RAG 결과 없이 진행합니다.");
            return new List<RagSearchResultDto>();
        }

        var agentRouting = await _context.Agents
            .AsNoTracking()
            .Where(a => a.AgentId == agentId.Value)
            .Select(a => new { a.KnowledgeBaseSource, a.KnowledgeBaseRef })
            .FirstOrDefaultAsync(cancellationToken);

        if (agentRouting == null
            || !string.Equals(agentRouting.KnowledgeBaseSource, "DocUtil", StringComparison.OrdinalIgnoreCase))
        {
            _logger.LogInformation(
                "RAG 비활성 - AgentId={AgentId}, KnowledgeBaseSource={Source}. ADR-2 에 따라 자체 KB 폴백은 제거되었습니다 (DocUtil 만 권위).",
                agentId.Value, agentRouting?.KnowledgeBaseSource ?? "(null)");
            return new List<RagSearchResultDto>();
        }

        // documentIds 파라미터는 자체 KB 시점의 호출 규약이었으므로, DocUtil 위임에서는
        // 사용하지 않음을 디버그 로그로 남긴다 (외부 시그니처 호환 보존).
        if (documentIds != null && documentIds.Count > 0)
        {
            _logger.LogDebug(
                "RAG documentIds 파라미터는 DocUtil 위임 흐름에서 무시됩니다 (Count={Count}).",
                documentIds.Count);
        }

        // userId 는 DocUtil 위임 흐름에서 컬렉션 권한 검사가 별도로 수행되므로 선택값.
        if (userId.HasValue)
        {
            _logger.LogDebug(
                "RAG userId 필터는 DocUtil 위임 흐름에서 적용되지 않습니다 (UserId={UserId}).",
                userId.Value);
        }

        // ── Phase 4: RAG 위임 진입 카운터 ─────────────────────────────────
        // 빈 query / KB 비활성 분기에서는 IncrementRagInvocation() 호출하지 않음 —
        // 실제 DocUtil 위임 흐름만 invocation 으로 집계(평균 distinct chunks 분모 정합).
        _ragMetrics.IncrementRagInvocation();

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

            // ── Phase 4: RAG 결과 메트릭 ─────────────────────────────────
            _ragMetrics.RecordRagDistinctChunks(rrfScores.Count);
            if (docutilResults.Count == 0)
            {
                _ragMetrics.IncrementRagZeroResult();
            }

            // RAG 결과 캐싱(10분) — 문서 갱신 가능성을 고려하여 짧은 TTL 유지.
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
