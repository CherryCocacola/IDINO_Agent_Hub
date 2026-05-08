namespace AIAgentManagement.Services;

// ════════════════════════════════════════════════════════════════════════════
// RagMetrics — IRagMetrics 의 in-memory atomic 카운터 구현 (Phase 4)
//
// 모든 카운터는 `long` 필드 + `Interlocked.Increment` / `Interlocked.Add`.
// 락 없이 다중 스레드 동시 갱신 안전. GetSnapshot() 은 best-effort read —
// 카운터별 시점이 다를 수 있지만 운영 지표 수준에서 충분.
//
// DI 등록: Program.cs 에서 `AddSingleton<IRagMetrics, RagMetrics>()` —
//   QueryRewriter(Singleton), DocUtilClient(Scoped), RagService(Scoped) 모두
//   동일 인스턴스 공유. captive 위험 없음(IRagMetrics 는 외부 의존성 0).
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// IRagMetrics 의 in-memory 구현. 서버 재시작 시 초기화되는 휘발성 카운터로,
/// 운영자 시연/디버깅용 즉시 가시성 확보가 목적.
/// </summary>
public sealed class RagMetrics : IRagMetrics
{
    private long _queryRewriteCacheHit;
    private long _queryRewriteCacheMiss;
    private long _queryRewriteCalls;
    private long _queryRewriteFailures;

    private long _docUtilSearchCacheHit;
    private long _docUtilSearchCacheMiss;
    private long _docUtilSearchCalls;
    private long _docUtilSearchFailures;
    private long _docUtilSearchLatencyMsTotal;

    // 후속 트랙 2026-05-08 — DocUtilClient.ListCollectionsAsync 카운터.
    private long _docUtilCollectionCacheHit;
    private long _docUtilCollectionCacheMiss;
    private long _docUtilCollectionCalls;
    private long _docUtilCollectionFailures;

    private long _ragInvocations;
    private long _ragZeroResults;
    private long _ragDistinctChunksTotal;
    private long _ragResultCacheHit;
    private long _ragResultCacheMiss;

    public void IncrementQueryRewriteCacheHit()
        => Interlocked.Increment(ref _queryRewriteCacheHit);

    public void IncrementQueryRewriteCacheMiss()
        => Interlocked.Increment(ref _queryRewriteCacheMiss);

    public void IncrementQueryRewriteCall()
        => Interlocked.Increment(ref _queryRewriteCalls);

    public void IncrementQueryRewriteFailure()
        => Interlocked.Increment(ref _queryRewriteFailures);

    public void IncrementDocUtilSearchCacheHit()
        => Interlocked.Increment(ref _docUtilSearchCacheHit);

    public void IncrementDocUtilSearchCacheMiss()
        => Interlocked.Increment(ref _docUtilSearchCacheMiss);

    public void IncrementDocUtilSearchCall()
        => Interlocked.Increment(ref _docUtilSearchCalls);

    public void IncrementDocUtilSearchFailure()
        => Interlocked.Increment(ref _docUtilSearchFailures);

    public void RecordDocUtilSearchLatency(long milliseconds)
    {
        // 음수 방어 — Stopwatch.ElapsedMilliseconds 는 항상 양수지만 호출자
        // 실수 또는 단위 혼동(초 vs 밀리초) 케이스에서 0 미만은 무시.
        if (milliseconds < 0) return;
        Interlocked.Add(ref _docUtilSearchLatencyMsTotal, milliseconds);
    }

    public void IncrementDocUtilCollectionCacheHit()
        => Interlocked.Increment(ref _docUtilCollectionCacheHit);

    public void IncrementDocUtilCollectionCacheMiss()
        => Interlocked.Increment(ref _docUtilCollectionCacheMiss);

    public void IncrementDocUtilCollectionCall()
        => Interlocked.Increment(ref _docUtilCollectionCalls);

    public void IncrementDocUtilCollectionFailure()
        => Interlocked.Increment(ref _docUtilCollectionFailures);

    public void IncrementRagInvocation()
        => Interlocked.Increment(ref _ragInvocations);

    public void IncrementRagZeroResult()
        => Interlocked.Increment(ref _ragZeroResults);

    public void RecordRagDistinctChunks(int count)
    {
        if (count <= 0) return;
        Interlocked.Add(ref _ragDistinctChunksTotal, count);
    }

    public void IncrementRagResultCacheHit()
        => Interlocked.Increment(ref _ragResultCacheHit);

    public void IncrementRagResultCacheMiss()
        => Interlocked.Increment(ref _ragResultCacheMiss);

    public RagMetricsSnapshot GetSnapshot()
        => new(
            QueryRewriteCacheHit: Interlocked.Read(ref _queryRewriteCacheHit),
            QueryRewriteCacheMiss: Interlocked.Read(ref _queryRewriteCacheMiss),
            QueryRewriteCalls: Interlocked.Read(ref _queryRewriteCalls),
            QueryRewriteFailures: Interlocked.Read(ref _queryRewriteFailures),
            DocUtilSearchCacheHit: Interlocked.Read(ref _docUtilSearchCacheHit),
            DocUtilSearchCacheMiss: Interlocked.Read(ref _docUtilSearchCacheMiss),
            DocUtilSearchCalls: Interlocked.Read(ref _docUtilSearchCalls),
            DocUtilSearchFailures: Interlocked.Read(ref _docUtilSearchFailures),
            DocUtilSearchLatencyMsTotal: Interlocked.Read(ref _docUtilSearchLatencyMsTotal),
            DocUtilCollectionCacheHit: Interlocked.Read(ref _docUtilCollectionCacheHit),
            DocUtilCollectionCacheMiss: Interlocked.Read(ref _docUtilCollectionCacheMiss),
            DocUtilCollectionCalls: Interlocked.Read(ref _docUtilCollectionCalls),
            DocUtilCollectionFailures: Interlocked.Read(ref _docUtilCollectionFailures),
            RagInvocations: Interlocked.Read(ref _ragInvocations),
            RagZeroResults: Interlocked.Read(ref _ragZeroResults),
            RagDistinctChunksTotal: Interlocked.Read(ref _ragDistinctChunksTotal),
            RagResultCacheHit: Interlocked.Read(ref _ragResultCacheHit),
            RagResultCacheMiss: Interlocked.Read(ref _ragResultCacheMiss));
}
