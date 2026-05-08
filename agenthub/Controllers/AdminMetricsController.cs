using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminMetricsController — 운영자 메트릭 BFF (Phase 4)
//
// 통합 비전: 운영자가 RAG 파이프라인의 in-memory 카운터를 즉시 조회하여
// 시연/장애 대응 시 사용. 외부 prometheus 도입 전 단계의 경량 게이트웨이.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//   2. IRagMetrics 스냅샷 → RagMetricsSnapshotDto 매핑(파생 통계 계산 포함)
//   3. JSON camelCase 직렬화(Program.cs JsonNamingPolicy 적용)
//
// 책임 범위 밖:
//   - 카운터 초기화/리셋(서버 재시작으로만 가능 — 본 단계의 의도된 단순성)
//   - 외부 prometheus push(추후 별도 트랙)
//   - 시계열 영속화(DB 적재 — 별도 트랙)
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 메트릭 BFF — Phase 4.
/// AgentHub 운영자가 RAG 파이프라인 카운터를 조회하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/metrics")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminMetricsController : ControllerBase
{
    private readonly IRagMetrics _ragMetrics;
    private readonly ILogger<AdminMetricsController> _logger;

    public AdminMetricsController(
        IRagMetrics ragMetrics,
        ILogger<AdminMetricsController> logger)
    {
        _ragMetrics = ragMetrics;
        _logger = logger;
    }

    /// <summary>
    /// RAG 파이프라인 in-memory 카운터 + 파생 통계 스냅샷.
    /// 서버 부팅 이후의 누적값으로, 재시작 시 0 으로 초기화된다.
    /// </summary>
    /// <returns>200 OK + <see cref="RagMetricsSnapshotDto"/></returns>
    [HttpGet("rag")]
    [ProducesResponseType(typeof(RagMetricsSnapshotDto), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ErrorResponseDto), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ErrorResponseDto), StatusCodes.Status403Forbidden)]
    public IActionResult GetRagMetrics()
    {
        var snapshot = _ragMetrics.GetSnapshot();

        // ── 파생 통계 계산 ───────────────────────────────────────────────
        // calls=0 분모 보호 — 0 으로 나누기 회피.
        var queryRewriteTotal = snapshot.QueryRewriteCacheHit + snapshot.QueryRewriteCacheMiss;
        var docUtilSearchTotal = snapshot.DocUtilSearchCacheHit + snapshot.DocUtilSearchCacheMiss;
        var ragResultCacheTotal = snapshot.RagResultCacheHit + snapshot.RagResultCacheMiss;

        var dto = new RagMetricsSnapshotDto
        {
            QueryRewriteCacheHit = snapshot.QueryRewriteCacheHit,
            QueryRewriteCacheMiss = snapshot.QueryRewriteCacheMiss,
            QueryRewriteCalls = snapshot.QueryRewriteCalls,
            QueryRewriteFailures = snapshot.QueryRewriteFailures,

            DocUtilSearchCacheHit = snapshot.DocUtilSearchCacheHit,
            DocUtilSearchCacheMiss = snapshot.DocUtilSearchCacheMiss,
            DocUtilSearchCalls = snapshot.DocUtilSearchCalls,
            DocUtilSearchFailures = snapshot.DocUtilSearchFailures,
            DocUtilSearchLatencyMsTotal = snapshot.DocUtilSearchLatencyMsTotal,

            RagInvocations = snapshot.RagInvocations,
            RagZeroResults = snapshot.RagZeroResults,
            RagDistinctChunksTotal = snapshot.RagDistinctChunksTotal,

            RagResultCacheHit = snapshot.RagResultCacheHit,
            RagResultCacheMiss = snapshot.RagResultCacheMiss,

            // 평균 latency = latency_total / max(1, calls) — 0 분모 방지
            AvgDocUtilSearchLatencyMs = snapshot.DocUtilSearchCalls > 0
                ? (double)snapshot.DocUtilSearchLatencyMsTotal / snapshot.DocUtilSearchCalls
                : 0d,

            // hit ratio = hit / (hit+miss) — 분모 0 이면 0
            QueryRewriteCacheHitRatio = queryRewriteTotal > 0
                ? (double)snapshot.QueryRewriteCacheHit / queryRewriteTotal
                : 0d,

            DocUtilSearchCacheHitRatio = docUtilSearchTotal > 0
                ? (double)snapshot.DocUtilSearchCacheHit / docUtilSearchTotal
                : 0d,

            RagResultCacheHitRatio = ragResultCacheTotal > 0
                ? (double)snapshot.RagResultCacheHit / ragResultCacheTotal
                : 0d,

            // 평균 distinct chunks = total / invocations
            AvgRagDistinctChunks = snapshot.RagInvocations > 0
                ? (double)snapshot.RagDistinctChunksTotal / snapshot.RagInvocations
                : 0d,
        };

        _logger.LogDebug(
            "RAG 메트릭 조회 - RagInvocations={Inv}, DocUtilCalls={Calls}, AvgLatency={Avg}ms",
            dto.RagInvocations, dto.DocUtilSearchCalls, dto.AvgDocUtilSearchLatencyMs);

        return Ok(dto);
    }
}
