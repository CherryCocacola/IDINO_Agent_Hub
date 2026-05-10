using System.Globalization;
using System.Net.Http.Headers;
using System.Text;
using System.Web;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilOperationsController — DocUtil Dashboard + Audit 운영자 BFF (Phase 10.2a)
//
// 통합 비전(P1 Control Plane / P5 인증 / R2 단일 진입점):
//   AgentHub 운영자 콘솔이 DocUtil 의 운영 모니터링(대시보드 5종) + 감사 로그(2종)
//   를 모두 단일 진입점에서 관리. Phase 10.1a~c 의 사용자/조직/부서/할당량/프로젝트
//   트랙과 동일한 BFF 패턴(IDocUtilTokenProvider 4단계 폴백 + 한국어 502 매핑) 적용.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//   2. TTL 캐시 분리:
//      - `du:dashboard:` (5분) — 부하 절감 + 어느 정도 신선도 균형
//      - `du:audit:`     (1분) — 감사 로그는 실시간성 우선
//      - export 는 캐시 미적용(stream + 매번 신선)
//   3. DocUtil DTO → JSON camelCase 직렬화(Program.cs JsonNamingPolicy 적용)
//   4. 4xx/5xx → 502 ErrorResponseDto 한국어 매핑(InvalidOperationException 변환)
//   5. CSV export 의 stream 보존(FileStreamResult + 한글 RFC 5987 filename)
//
// 캐시 namespace 분리 사유:
//   `docutil-collections` (Phase 10.1c) 와는 의도적으로 분리 — dashboard / audit 는
//   collections 와 의미적으로 무관(데이터 도메인 다름). 본 트랙은 자체 namespace 만
//   증가(version-key 미사용, 단순 TTL) — mutation 부재이므로 invalidate 트리거 없음.
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 DocUtil 대시보드/감사 로그 BFF — Phase 10.2a.
/// AgentHub Vue 콘솔의 `/admin/docutil-dashboard` + `/admin/docutil-audit` 페이지가 호출.
/// </summary>
[ApiController]
[Route("api/admin/docutil")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminDocUtilOperationsController : ControllerBase
{
    // 캐시 prefix — Phase 10.1 의 `du:projects:` / `du:c:` 와 분리.
    private const string DashboardCacheKeyPrefix = "du:dashboard:";
    private const string AuditCacheKeyPrefix = "du:audit:";
    // 대시보드는 5분 TTL — 부하 절감 + 신선도 균형.
    private static readonly TimeSpan DashboardCacheTtl = TimeSpan.FromMinutes(5);
    // 감사 로그는 1분 TTL — 실시간성 우선.
    private static readonly TimeSpan AuditCacheTtl = TimeSpan.FromMinutes(1);

    private readonly IDocUtilClient _docUtilClient;
    private readonly CachingService _cachingService;
    private readonly ILogger<AdminDocUtilOperationsController> _logger;

    public AdminDocUtilOperationsController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        ILogger<AdminDocUtilOperationsController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _logger = logger;
    }

    // ──────────────────────────────────────────────────────────────────────
    // 대시보드 5 endpoint
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 대시보드 KPI 메트릭 — DocUtil `/api/v1/dashboard/metrics` 위임 + 5분 캐시.
    /// </summary>
    [HttpGet("dashboard/metrics")]
    public async Task<ActionResult<DocUtilDashboardMetrics>> GetDashboardMetrics(
        CancellationToken ct = default)
    {
        var cacheKey = $"{DashboardCacheKeyPrefix}metrics";
        var cached = await _cachingService.GetAsync<DocUtilDashboardMetrics>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 대시보드 메트릭 캐시 hit - key={Key}", cacheKey);
            return Ok(cached);
        }
        _logger.LogDebug("DocUtil 대시보드 메트릭 캐시 miss - key={Key}", cacheKey);

        try
        {
            var metrics = await _docUtilClient.GetDashboardMetricsAsync(ct);
            await _cachingService.SetAsync(cacheKey, metrics, DashboardCacheTtl);
            return Ok(metrics);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 대시보드 메트릭 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 대시보드 메트릭을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 시간별 평균 응답시간 시계열 — DocUtil `/api/v1/dashboard/response-times` 위임.
    /// </summary>
    /// <param name="period">집계 기간 라벨(예: "7d", "24h"). null/공백이면 DocUtil 기본 동작.</param>
    [HttpGet("dashboard/response-times")]
    public async Task<ActionResult<DocUtilResponseTimes>> GetDashboardResponseTimes(
        [FromQuery] string? period = null,
        CancellationToken ct = default)
    {
        var periodKey = string.IsNullOrWhiteSpace(period) ? "_" : period.Trim().ToLowerInvariant();
        var cacheKey = $"{DashboardCacheKeyPrefix}response-times:{periodKey}";
        var cached = await _cachingService.GetAsync<DocUtilResponseTimes>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 응답시간 캐시 hit - key={Key}", cacheKey);
            return Ok(cached);
        }

        try
        {
            var data = await _docUtilClient.GetDashboardResponseTimesAsync(period, ct);
            await _cachingService.SetAsync(cacheKey, data, DashboardCacheTtl);
            return Ok(data);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 응답시간 데이터 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 응답시간 데이터를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 일별 검색 오류 카운트 — DocUtil `/api/v1/dashboard/search-errors` 위임.
    /// </summary>
    [HttpGet("dashboard/search-errors")]
    public async Task<ActionResult<DocUtilSearchErrors>> GetDashboardSearchErrors(
        [FromQuery] string? period = null,
        CancellationToken ct = default)
    {
        var periodKey = string.IsNullOrWhiteSpace(period) ? "_" : period.Trim().ToLowerInvariant();
        var cacheKey = $"{DashboardCacheKeyPrefix}search-errors:{periodKey}";
        var cached = await _cachingService.GetAsync<DocUtilSearchErrors>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 검색 오류 캐시 hit - key={Key}", cacheKey);
            return Ok(cached);
        }

        try
        {
            var data = await _docUtilClient.GetDashboardSearchErrorsAsync(period, ct);
            await _cachingService.SetAsync(cacheKey, data, DashboardCacheTtl);
            return Ok(data);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 검색 오류 데이터 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 검색 오류 데이터를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 검색 사용량 통계 — DocUtil `/api/v1/dashboard/search-usage` 위임.
    /// </summary>
    [HttpGet("dashboard/search-usage")]
    public async Task<ActionResult<DocUtilSearchUsage>> GetDashboardSearchUsage(
        [FromQuery] string? period = null,
        CancellationToken ct = default)
    {
        var periodKey = string.IsNullOrWhiteSpace(period) ? "_" : period.Trim().ToLowerInvariant();
        var cacheKey = $"{DashboardCacheKeyPrefix}search-usage:{periodKey}";
        var cached = await _cachingService.GetAsync<DocUtilSearchUsage>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 검색 사용량 캐시 hit - key={Key}", cacheKey);
            return Ok(cached);
        }

        try
        {
            var data = await _docUtilClient.GetDashboardSearchUsageAsync(period, ct);
            await _cachingService.SetAsync(cacheKey, data, DashboardCacheTtl);
            return Ok(data);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 검색 사용량 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 검색 사용량을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 문서 업로드 상태 분포 — DocUtil `/api/v1/dashboard/upload-status` 위임.
    /// </summary>
    [HttpGet("dashboard/upload-status")]
    public async Task<ActionResult<DocUtilUploadStatus>> GetDashboardUploadStatus(
        CancellationToken ct = default)
    {
        var cacheKey = $"{DashboardCacheKeyPrefix}upload-status";
        var cached = await _cachingService.GetAsync<DocUtilUploadStatus>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 업로드 상태 캐시 hit - key={Key}", cacheKey);
            return Ok(cached);
        }

        try
        {
            var data = await _docUtilClient.GetDashboardUploadStatusAsync(ct);
            await _cachingService.SetAsync(cacheKey, data, DashboardCacheTtl);
            return Ok(data);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 업로드 상태 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 업로드 상태를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 감사 로그 — GET 목록 / GET CSV export
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 감사 로그 목록(페이징 + 필터) — DocUtil `/api/v1/audit-logs` 위임 + 1분 캐시.
    /// </summary>
    /// <param name="page">페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 50, 한도 1~200).</param>
    /// <param name="action">action 정확 일치 필터(예: "auth.login").</param>
    /// <param name="resourceType">resource_type 정확 일치 필터(예: "auth").</param>
    /// <param name="userId">user_id(UUID) 정확 일치 필터.</param>
    /// <param name="startDate">시작 시각(ISO-8601).</param>
    /// <param name="endDate">종료 시각(ISO-8601).</param>
    [HttpGet("audit-logs")]
    public async Task<ActionResult<DocUtilAuditLogList>> ListAuditLogs(
        [FromQuery] int page = 1,
        [FromQuery] int size = 50,
        [FromQuery] string? action = null,
        [FromQuery] string? resourceType = null,
        [FromQuery] string? userId = null,
        [FromQuery] DateTime? startDate = null,
        [FromQuery] DateTime? endDate = null,
        CancellationToken ct = default)
    {
        // 캐시 키: 모든 필터 조합 — 빈/공백/null 은 "_".
        string K(string? s) => string.IsNullOrWhiteSpace(s) ? "_" : s.Trim().ToLowerInvariant();
        string D(DateTime? d) => d?.ToUniversalTime().ToString("o", CultureInfo.InvariantCulture) ?? "_";
        var cacheKey = $"{AuditCacheKeyPrefix}list:{page}|{size}|{K(action)}|{K(resourceType)}|{K(userId)}|{D(startDate)}|{D(endDate)}";

        var cached = await _cachingService.GetAsync<DocUtilAuditLogList>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 감사 로그 목록 캐시 hit - key={Key}", cacheKey);
            return Ok(cached);
        }
        _logger.LogDebug("DocUtil 감사 로그 목록 캐시 miss - key={Key}", cacheKey);

        try
        {
            var list = await _docUtilClient.ListAuditLogsAsync(
                page, size, action, resourceType, userId, startDate, endDate, ct);
            await _cachingService.SetAsync(cacheKey, list, AuditCacheTtl);
            return Ok(list);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 감사 로그 목록 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 감사 로그 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 감사 로그 CSV 내보내기 — DocUtil `/api/v1/audit-logs/export` 위임.
    /// <para>
    /// 응답은 text/csv binary stream. 캐시 미적용(매번 신선한 export 보장).
    /// 한글 파일명은 RFC 5987 (filename*=UTF-8''...) 로 인코딩.
    /// </para>
    /// </summary>
    [HttpGet("audit-logs/export")]
    public async Task<IActionResult> ExportAuditLogs(
        [FromQuery] string? action = null,
        [FromQuery] string? resourceType = null,
        [FromQuery] string? userId = null,
        [FromQuery] DateTime? startDate = null,
        [FromQuery] DateTime? endDate = null,
        CancellationToken ct = default)
    {
        DocUtilAuditExport export;
        try
        {
            export = await _docUtilClient.ExportAuditLogsAsync(
                action, resourceType, userId, startDate, endDate, ct);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 감사 로그 export 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 감사 로그를 내보내지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }

        // FileStreamResult 가 stream Dispose 책임 — DocUtilClient 의 HttpResponseOwnedStream
        // 이 stream Dispose 시 응답/요청까지 함께 정리하므로 누수 없음.

        // 한국어 파일명도 안전하게 처리 — RFC 5987 (filename*=UTF-8''...).
        // ASCII fallback 의 비-ASCII 문자는 underscore 로 치환(Header 안전).
        var rawName = string.IsNullOrWhiteSpace(export.FileName) ? "audit_logs.csv" : export.FileName;
        var asciiFallback = ToAsciiSafe(rawName);
        var encoded = HttpUtility.UrlPathEncode(rawName);
        var disposition = $"attachment; filename=\"{asciiFallback}\"; filename*=UTF-8''{encoded}";

        Response.Headers["Content-Disposition"] = disposition;

        return new FileStreamResult(export.Stream, export.ContentType)
        {
            // FileDownloadName 을 별도 설정하면 ASP.NET Core 가 별도 Content-Disposition 헤더를
            // 자동 합성해 RFC 5987 우리 헤더와 충돌. 직접 위에서 설정한 값 우선.
            EnableRangeProcessing = false,
        };
    }

    /// <summary>
    /// HTTP 헤더 ASCII fallback — 비-ASCII 는 underscore 치환.
    /// 실제 한글 파일명은 RFC 5987 의 filename*=UTF-8''... 로 전달되므로 fallback 은 호환성 보호 용도.
    /// </summary>
    private static string ToAsciiSafe(string name)
    {
        var sb = new StringBuilder(name.Length);
        foreach (var c in name)
        {
            sb.Append(c < 0x20 || c >= 0x7f || c == '"' || c == '\\' ? '_' : c);
        }
        return sb.ToString();
    }
}
