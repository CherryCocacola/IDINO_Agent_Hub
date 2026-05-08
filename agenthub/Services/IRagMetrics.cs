namespace AIAgentManagement.Services;

// ════════════════════════════════════════════════════════════════════════════
// IRagMetrics — Phase 4 RAG 운영 관측성 (Singleton)
//
// 목적:
//   QueryRewriter 캐시 hit율 / DocUtil 검색 latency / RAG 호출 카운터 등
//   운영자가 시연/장애 대응 시 즉시 파악해야 하는 in-memory 지표를 노출.
//   외부 prometheus / OpenTelemetry 도입 전 단계의 경량 카운터 구현 — 서버
//   재시작 시 초기화되는 본질적 한계를 받아들이고 디스크 영속화는 하지 않는다.
//
// DI 수명: Singleton — 메모리 내 atomic 카운터 공유. 모든 호출자(QueryRewriter,
//   DocUtilClient, RagService) 가 동일 인스턴스를 참조하여 합산 정확도 보장.
//
// 스레드 안전성: 구현체(RagMetrics)는 `Interlocked.Increment` / `Interlocked.Add`
//   기반 long 카운터만 사용 — 락 없이 다중 스레드 동시 갱신 안전.
//
// 외부 표면: AdminMetricsController (`GET /api/admin/metrics/rag`) 가 GetSnapshot()
//   호출 후 RagMetricsSnapshotDto 로 직렬화하여 운영자에게 반환.
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// RAG 파이프라인의 in-memory 카운터 인터페이스.
/// 모든 호출은 thread-safe atomic 연산이며 로깅과 무관(부수 효과 없음).
/// </summary>
public interface IRagMetrics
{
    // ── QueryRewriter (LlmQueryRewriter) ─────────────────────────────────
    /// <summary>QueryRewriter 캐시 hit (IMemoryCache 60분 TTL).</summary>
    void IncrementQueryRewriteCacheHit();
    /// <summary>QueryRewriter 캐시 miss(LLM 호출 또는 graceful fallback 직전).</summary>
    void IncrementQueryRewriteCacheMiss();
    /// <summary>QueryRewriter LLM 호출 시도(실패/성공 무관, 호출 발생 시점).</summary>
    void IncrementQueryRewriteCall();
    /// <summary>QueryRewriter LLM 호출 실패(예외 catch).</summary>
    void IncrementQueryRewriteFailure();

    // ── DocUtilClient.SearchAsync ─────────────────────────────────────────
    /// <summary>DocUtil 검색 응답 캐시 hit (CachingService 5분 TTL).</summary>
    void IncrementDocUtilSearchCacheHit();
    /// <summary>DocUtil 검색 응답 캐시 miss(HTTP 호출 직전).</summary>
    void IncrementDocUtilSearchCacheMiss();
    /// <summary>DocUtil 검색 HTTP 호출 시도.</summary>
    void IncrementDocUtilSearchCall();
    /// <summary>DocUtil 검색 HTTP 호출 실패(InvalidOperationException 등).</summary>
    void IncrementDocUtilSearchFailure();
    /// <summary>DocUtil 검색 HTTP 호출 latency 누적(밀리초). 평균은 latency_total / max(1, calls).</summary>
    void RecordDocUtilSearchLatency(long milliseconds);

    // ── RagService.RetrieveAsync ──────────────────────────────────────────
    /// <summary>RAG 위임 진입(빈 query / 비활성 분기 포함하지 않는 실제 위임 흐름).</summary>
    void IncrementRagInvocation();
    /// <summary>RAG 결과 0건(DocUtil 검색은 성공했지만 매칭 청크 없음).</summary>
    void IncrementRagZeroResult();
    /// <summary>RAG 결과 distinct chunks 누적. 평균은 RagInvocation 으로 나눠서 계산.</summary>
    void RecordRagDistinctChunks(int count);
    /// <summary>RagService 결과 캐시 hit (version-key prefix 적용된 10분 TTL `rag:` 키).</summary>
    void IncrementRagResultCacheHit();
    /// <summary>RagService 결과 캐시 miss (DocUtil 위임 흐름 진입 직전).</summary>
    void IncrementRagResultCacheMiss();

    /// <summary>한 시점 카운터 스냅샷 — AdminMetricsController 직렬화용.</summary>
    RagMetricsSnapshot GetSnapshot();
}

/// <summary>
/// RagMetrics 의 한 시점 스냅샷(record). atomic Read 가 아닌 best-effort —
/// 다중 스레드 환경에서 카운터별 read 가 다른 시점일 수 있으나 운영 지표
/// 수준에서 무시 가능.
/// </summary>
public sealed record RagMetricsSnapshot(
    long QueryRewriteCacheHit,
    long QueryRewriteCacheMiss,
    long QueryRewriteCalls,
    long QueryRewriteFailures,
    long DocUtilSearchCacheHit,
    long DocUtilSearchCacheMiss,
    long DocUtilSearchCalls,
    long DocUtilSearchFailures,
    long DocUtilSearchLatencyMsTotal,
    long RagInvocations,
    long RagZeroResults,
    long RagDistinctChunksTotal,
    long RagResultCacheHit,
    long RagResultCacheMiss);
