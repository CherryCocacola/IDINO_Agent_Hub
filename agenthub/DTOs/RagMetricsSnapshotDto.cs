namespace AIAgentManagement.DTOs;

// ════════════════════════════════════════════════════════════════════════════
// RagMetricsSnapshotDto — `GET /api/admin/metrics/rag` 응답 DTO (Phase 4)
//
// JSON 직렬화는 Program.cs 의 JsonNamingPolicy.CamelCase 적용 —
// `queryRewriteCacheHit` 등 camelCase 로 노출.
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// RAG 파이프라인 in-memory 카운터 + 파생 통계의 한 시점 스냅샷.
/// 모든 누적값은 서버 부팅 이후의 합. 서버 재시작 시 0 으로 초기화된다.
/// </summary>
public sealed class RagMetricsSnapshotDto
{
    // ── QueryRewriter (LlmQueryRewriter) ─────────────────────────────────
    public long QueryRewriteCacheHit { get; set; }
    public long QueryRewriteCacheMiss { get; set; }
    public long QueryRewriteCalls { get; set; }
    public long QueryRewriteFailures { get; set; }

    // ── DocUtilClient.SearchAsync ─────────────────────────────────────────
    public long DocUtilSearchCacheHit { get; set; }
    public long DocUtilSearchCacheMiss { get; set; }
    public long DocUtilSearchCalls { get; set; }
    public long DocUtilSearchFailures { get; set; }
    public long DocUtilSearchLatencyMsTotal { get; set; }

    // ── DocUtilClient.ListCollectionsAsync (후속 트랙 2026-05-08) ────────
    // 단순 TTL 10분 캐시(version-key 미적용 — DocUtil mutation 비BFF 통과).
    public long DocUtilCollectionCacheHit { get; set; }
    public long DocUtilCollectionCacheMiss { get; set; }
    public long DocUtilCollectionCalls { get; set; }
    public long DocUtilCollectionFailures { get; set; }

    // ── RagService.RetrieveAsync ──────────────────────────────────────────
    public long RagInvocations { get; set; }
    public long RagZeroResults { get; set; }
    public long RagDistinctChunksTotal { get; set; }

    // ── RagService 결과 캐시(version-key prefix `v{N}:rag:...`) ──────────
    public long RagResultCacheHit { get; set; }
    public long RagResultCacheMiss { get; set; }

    // ── 파생 지표(서버에서 계산하여 클라이언트 단순화) ────────────────────
    /// <summary>DocUtil 검색 평균 latency (ms). calls=0 이면 0.</summary>
    public double AvgDocUtilSearchLatencyMs { get; set; }

    /// <summary>QueryRewriter 캐시 hit 비율 (0.0~1.0). hit+miss=0 이면 0.</summary>
    public double QueryRewriteCacheHitRatio { get; set; }

    /// <summary>DocUtil 검색 캐시 hit 비율 (0.0~1.0). hit+miss=0 이면 0.</summary>
    public double DocUtilSearchCacheHitRatio { get; set; }

    /// <summary>DocUtil 컬렉션 캐시 hit 비율 (0.0~1.0). hit+miss=0 이면 0.</summary>
    public double DocUtilCollectionCacheHitRatio { get; set; }

    /// <summary>RagService 결과 캐시 hit 비율 (0.0~1.0). hit+miss=0 이면 0.</summary>
    public double RagResultCacheHitRatio { get; set; }

    /// <summary>RAG 호출당 평균 distinct chunks. invocations=0 이면 0.</summary>
    public double AvgRagDistinctChunks { get; set; }
}
