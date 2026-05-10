using System.Net.Http.Headers;
using System.Text;
using System.Web;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilReportsController — DocUtil 보고서/템플릿 운영자 BFF (Phase 10.2c)
//
// 통합 비전(P1 Control Plane / P5 인증 / R2 단일 진입점):
//   AgentHub 운영자 콘솔이 DocUtil 의 보고서 라이프사이클(생성/이력/다운로드/삭제) +
//   템플릿 카탈로그(생성/수정/삭제) 까지 단일 진입점에서 운영. Phase 10.1/10.2a/10.2b 와
//   동일 BFF 패턴.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//   2. TTL 캐시 분리 + version-key invalidate:
//      - prefix `du:reports:list:` (1분 TTL — 실시간성 우선) + namespace `docutil-reports`
//      - prefix `du:reports:detail:` (5분 TTL) + namespace `docutil-reports`
//      - prefix `du:reports:templates:` (10분 TTL — 카탈로그성) + namespace `docutil-report-templates`
//      - download 는 stream — 캐시 미적용
//   3. 4xx/5xx → 502 ErrorResponseDto 한국어 매핑
//   4. mutation(POST/PUT/DELETE/generate) 의 성공/실패 모두 invalidate (10.1b ghost 처리 패턴)
//   5. binary stream 다운로드 — Phase 10.2a HttpResponseOwnedStream 재사용 + RFC 5987 한글 파일명
//   6. multipart upload — 템플릿 생성 시 file 첨부 가능
//
// 캐시 namespace 분리 사유:
//   `docutil-reports`(보고서 인스턴스) 와 `docutil-report-templates`(템플릿 카탈로그) 분리.
//   템플릿 mutation 으로 보고서 캐시는 invalidate 되지 않음 — 템플릿 변경이 즉시 보고서 목록에
//   영향 주는 게 아니므로 의도적 격리.
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 DocUtil 보고서/템플릿 관리 BFF — Phase 10.2c.
/// AgentHub Vue 콘솔의 `/admin/docutil-reports` 페이지가 호출하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/docutil/reports")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminDocUtilReportsController : ControllerBase
{
    private const string ReportListCachePrefix = "du:reports:list:";
    private const string ReportDetailCachePrefix = "du:reports:detail:";
    private const string TemplatesCachePrefix = "du:reports:templates:";
    public const string ReportsCacheVersionNamespace = "docutil-reports";
    public const string TemplatesCacheVersionNamespace = "docutil-report-templates";

    private static readonly TimeSpan ReportListCacheTtl = TimeSpan.FromMinutes(1);
    private static readonly TimeSpan ReportDetailCacheTtl = TimeSpan.FromMinutes(5);
    private static readonly TimeSpan TemplatesCacheTtl = TimeSpan.FromMinutes(10);

    // 운영자가 generate POST 호출 시 한 번에 너무 큰 generation_params 를 보내지 못하도록
    // 사이즈 캡(JSON 직렬화 후 64KB).
    private const int GenerationParamsMaxBytes = 64 * 1024;

    private readonly IDocUtilClient _docUtilClient;
    private readonly CachingService _cachingService;
    private readonly ILogger<AdminDocUtilReportsController> _logger;

    public AdminDocUtilReportsController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        ILogger<AdminDocUtilReportsController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _logger = logger;
    }

    /// <summary>
    /// 보고서 캐시 일괄 무효화 — 보고서 mutation(생성/삭제) 시.
    /// </summary>
    private async Task InvalidateReportsCacheAsync()
    {
        try
        {
            var v = await _cachingService.IncrementVersionAsync(ReportsCacheVersionNamespace);
            _logger.LogInformation("DocUtil 보고서 캐시 invalidate - newVersion={V}", v);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "DocUtil 보고서 캐시 invalidate 실패(무시)");
        }
    }

    /// <summary>
    /// 템플릿 캐시 일괄 무효화 — 템플릿 mutation(생성/수정/삭제) 시.
    /// </summary>
    private async Task InvalidateTemplatesCacheAsync()
    {
        try
        {
            var v = await _cachingService.IncrementVersionAsync(TemplatesCacheVersionNamespace);
            _logger.LogInformation("DocUtil 보고서 템플릿 캐시 invalidate - newVersion={V}", v);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "DocUtil 보고서 템플릿 캐시 invalidate 실패(무시)");
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // 보고서 (목록/상세/생성/삭제/다운로드) — 5 endpoint
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// 보고서 목록(페이징) — DocUtil `/api/v1/reports` 위임 + 1분 캐시.
    /// <para>
    /// status 필터는 OpenAPI 에 없으므로 백엔드는 page/size 만 위임. status 필드는 응답에 포함되어
    /// 클라이언트(프론트) 측에서 필터링. status 쿼리는 호환성 위해 받지만 무시(로깅만).
    /// </para>
    /// </summary>
    [HttpGet("")]
    public async Task<ActionResult<DocUtilReportList>> ListReports(
        [FromQuery] int page = 1,
        [FromQuery] int size = 20,
        [FromQuery] string? status = null,
        CancellationToken ct = default)
    {
        var version = await _cachingService.GetVersionAsync(ReportsCacheVersionNamespace);
        var cacheKey = $"{ReportListCachePrefix}v{version}:{page}|{size}";

        var cached = await _cachingService.GetAsync<CachedReportListDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 보고서 목록 캐시 hit - key={Key}", cacheKey);
            return Ok(MaybeFilterByStatus(cached.ToRecord(), status));
        }
        _logger.LogDebug("DocUtil 보고서 목록 캐시 miss - key={Key}", cacheKey);

        try
        {
            var list = await _docUtilClient.ListReportsAsync(page, size, ct);
            await _cachingService.SetAsync(cacheKey, CachedReportListDto.From(list), ReportListCacheTtl);
            return Ok(MaybeFilterByStatus(list, status));
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보고서 목록 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 보고서 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// status 클라이언트 측 필터(DocUtil 에 status 필터가 없어 BFF 차원에서 후처리).
    /// <para>대소문자 무관 비교. null 또는 빈 값이면 원본 그대로 반환.</para>
    /// </summary>
    private static DocUtilReportList MaybeFilterByStatus(DocUtilReportList list, string? status)
    {
        if (string.IsNullOrWhiteSpace(status))
        {
            return list;
        }
        var key = status.Trim().ToLowerInvariant();
        var filtered = list.Items
            .Where(r => string.Equals(r.Status, key, StringComparison.OrdinalIgnoreCase))
            .ToArray();
        // page/size/total 은 원본 페이지 메타 보존 — 운영자가 페이지네이션 의미를 잃지 않도록.
        // 단, 후처리 필터 결과 개수가 의미상 다르면 별도 표시 필요(현 트랙은 단순 필터링).
        return new DocUtilReportList(filtered, list.Total, list.Page, list.Size);
    }

    /// <summary>
    /// 보고서 상세 — DocUtil `/api/v1/reports/{report_id}` 위임 + 5분 캐시.
    /// 404 응답은 한국어 ErrorResponseDto 로 정규화.
    /// </summary>
    [HttpGet("{reportId}")]
    public async Task<ActionResult<DocUtilReportDetail>> GetReport(
        string reportId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(reportId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("보고서 식별자가 비어 있습니다."));
        }

        var version = await _cachingService.GetVersionAsync(ReportsCacheVersionNamespace);
        var cacheKey = $"{ReportDetailCachePrefix}v{version}:{reportId}";

        var cached = await _cachingService.GetAsync<CachedReportDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 보고서 상세 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 보고서 상세 캐시 miss - key={Key}", cacheKey);

        try
        {
            var detail = await _docUtilClient.GetReportAsync(reportId, ct);
            if (detail == null)
            {
                return NotFound(ErrorResponseDto.NotFound("보고서를 찾을 수 없습니다."));
            }
            await _cachingService.SetAsync(cacheKey, CachedReportDto.From(detail), ReportDetailCacheTtl);
            return Ok(detail);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보고서 상세 조회 실패 (id={Id})", reportId);
            return StatusCode(502, new ErrorResponseDto(
                "보고서 상세를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 보고서 생성 — DocUtil `/api/v1/reports/generate` (POST). 캐시 일괄 무효화.
    /// <para>
    /// 응답은 free-form (DocUtil 의 비동기 job 응답일 가능성). raw dict 그대로 운영자에게 노출.
    /// </para>
    /// </summary>
    [HttpPost("generate")]
    public async Task<ActionResult<IDictionary<string, object?>>> GenerateReport(
        [FromBody] DocUtilGenerateReportRequest request,
        CancellationToken ct = default)
    {
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(request.Title))
        {
            return BadRequest(ErrorResponseDto.BadRequest("보고서 제목이 비어 있습니다."));
        }
        if (request.Title.Length > 500)
        {
            return BadRequest(ErrorResponseDto.BadRequest("보고서 제목은 500자 이하여야 합니다."));
        }
        if (request.OutputFormat != null && request.OutputFormat.Length > 16)
        {
            return BadRequest(ErrorResponseDto.BadRequest("출력 포맷이 잘못되었습니다."));
        }

        // generation_params 가 너무 크면 사전 차단(DocUtil 422 회피).
        if (request.GenerationParams != null)
        {
            try
            {
                var serialized = System.Text.Json.JsonSerializer.Serialize(request.GenerationParams);
                if (Encoding.UTF8.GetByteCount(serialized) > GenerationParamsMaxBytes)
                {
                    return BadRequest(ErrorResponseDto.BadRequest(
                        $"generation_params 가 너무 큽니다(최대 {GenerationParamsMaxBytes / 1024} KB)."));
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "generation_params 직렬화 실패 — 그대로 위임");
            }
        }

        try
        {
            var resp = await _docUtilClient.GenerateReportAsync(request, ct);
            _logger.LogInformation(
                "운영자 DocUtil 보고서 생성 요청 성공 - Title={Title}, TemplateId={TemplateId}, OutputFormat={Format}",
                request.Title, request.TemplateId ?? "(none)", request.OutputFormat ?? "docx");
            await InvalidateReportsCacheAsync();
            // DocUtil 측 비동기 처리일 수 있어 202 가 자연스럽지만, 동기 200 인 경우도 동일한 본문이 옴.
            // 본 BFF 는 응답 본문을 그대로 노출(상태 코드는 200 통일 — Vue 측 분기 단순화).
            return Ok(resp.Data);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보고서 생성 실패 (title={Title})", request.Title);
            await InvalidateReportsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "보고서 생성에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 보고서 삭제 — DocUtil `/api/v1/reports/{report_id}` (DELETE). 성공/실패 모두 invalidate.
    /// </summary>
    [HttpDelete("{reportId}")]
    public async Task<IActionResult> DeleteReport(string reportId, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(reportId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("보고서 식별자가 비어 있습니다."));
        }

        try
        {
            await _docUtilClient.DeleteReportAsync(reportId, ct);
            _logger.LogInformation("운영자 DocUtil 보고서 삭제 성공 - ReportId={Id}", reportId);
            await InvalidateReportsCacheAsync();
            return NoContent();
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보고서 삭제 실패 (id={Id})", reportId);
            await InvalidateReportsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "보고서 삭제에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 보고서 다운로드 — DocUtil `/api/v1/reports/{report_id}/download` 위임.
    /// <para>
    /// 응답은 binary stream. 캐시 미적용(매번 신선한 다운로드 보장).
    /// 한글 파일명은 RFC 5987 (filename*=UTF-8''...) 로 인코딩.
    /// </para>
    /// </summary>
    [HttpGet("{reportId}/download")]
    public async Task<IActionResult> DownloadReport(string reportId, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(reportId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("보고서 식별자가 비어 있습니다."));
        }

        DocUtilReportDownload download;
        try
        {
            download = await _docUtilClient.DownloadReportAsync(reportId, ct);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보고서 다운로드 실패 (id={Id})", reportId);
            return StatusCode(502, new ErrorResponseDto(
                "보고서를 다운로드하지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }

        // FileStreamResult 가 stream Dispose 책임 — DocUtilClient 의 HttpResponseOwnedStream
        // 이 stream Dispose 시 응답/요청까지 함께 정리(Phase 10.2a 와 동일 패턴).

        var rawName = string.IsNullOrWhiteSpace(download.FileName)
            ? $"report-{reportId}"
            : download.FileName;
        var asciiFallback = ToAsciiSafe(rawName);
        var encoded = HttpUtility.UrlPathEncode(rawName);
        var disposition = $"attachment; filename=\"{asciiFallback}\"; filename*=UTF-8''{encoded}";

        Response.Headers["Content-Disposition"] = disposition;

        return new FileStreamResult(download.Stream, download.ContentType)
        {
            EnableRangeProcessing = false,
        };
    }

    // ══════════════════════════════════════════════════════════════════════
    // 보고서 템플릿 (목록/상세/생성/수정/삭제) — 5 endpoint
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// 보고서 템플릿 목록(페이징) — DocUtil `/api/v1/reports/templates` 위임 + 10분 캐시.
    /// </summary>
    [HttpGet("templates")]
    public async Task<ActionResult<DocUtilReportTemplateList>> ListTemplates(
        [FromQuery] int page = 1,
        [FromQuery] int size = 20,
        CancellationToken ct = default)
    {
        var version = await _cachingService.GetVersionAsync(TemplatesCacheVersionNamespace);
        var cacheKey = $"{TemplatesCachePrefix}v{version}:list:{page}|{size}";

        var cached = await _cachingService.GetAsync<CachedTemplateListDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 보고서 템플릿 목록 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }

        try
        {
            var list = await _docUtilClient.ListReportTemplatesAsync(page, size, ct);
            await _cachingService.SetAsync(cacheKey, CachedTemplateListDto.From(list), TemplatesCacheTtl);
            return Ok(list);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보고서 템플릿 목록 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 보고서 템플릿 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 보고서 템플릿 상세 — DocUtil `/api/v1/reports/templates/{template_id}` 위임 + 10분 캐시.
    /// </summary>
    [HttpGet("templates/{templateId}")]
    public async Task<ActionResult<DocUtilReportTemplateDetail>> GetTemplate(
        string templateId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 식별자가 비어 있습니다."));
        }

        var version = await _cachingService.GetVersionAsync(TemplatesCacheVersionNamespace);
        var cacheKey = $"{TemplatesCachePrefix}v{version}:detail:{templateId}";

        var cached = await _cachingService.GetAsync<CachedTemplateDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 보고서 템플릿 상세 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }

        try
        {
            var detail = await _docUtilClient.GetReportTemplateAsync(templateId, ct);
            if (detail == null)
            {
                return NotFound(ErrorResponseDto.NotFound("템플릿을 찾을 수 없습니다."));
            }
            await _cachingService.SetAsync(cacheKey, CachedTemplateDto.From(detail), TemplatesCacheTtl);
            return Ok(detail);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보고서 템플릿 상세 조회 실패 (id={Id})", templateId);
            return StatusCode(502, new ErrorResponseDto(
                "템플릿 상세를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 보고서 템플릿 생성 — DocUtil `/api/v1/reports/templates` (POST, multipart/form-data).
    /// <para>
    /// multipart 본문 — name + format + description? + file?. file 은 IFormFile 로 받아 stream 으로 위임.
    /// </para>
    /// </summary>
    [HttpPost("templates")]
    [RequestSizeLimit(50 * 1024 * 1024)] // 50 MB 한도
    public async Task<ActionResult<DocUtilReportTemplateDetail>> CreateTemplate(
        [FromForm] string name,
        [FromForm] string? format = null,
        [FromForm] string? description = null,
        [FromForm] IFormFile? file = null,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(name))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 이름이 비어 있습니다."));
        }
        if (name.Length > 255)
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 이름은 255자 이하여야 합니다."));
        }
        if (description != null && description.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 설명은 2000자 이하여야 합니다."));
        }

        var request = new DocUtilCreateReportTemplateRequest(
            Name: name,
            Format: string.IsNullOrWhiteSpace(format) ? "docx" : format,
            Description: description);

        Stream? fileStream = null;
        string? fileName = null;
        if (file != null && file.Length > 0)
        {
            fileStream = file.OpenReadStream();
            fileName = file.FileName;
        }

        try
        {
            DocUtilReportTemplateDetail created;
            try
            {
                created = await _docUtilClient.CreateReportTemplateAsync(request, fileStream, fileName, ct);
            }
            finally
            {
                fileStream?.Dispose();
            }

            _logger.LogInformation(
                "운영자 DocUtil 보고서 템플릿 생성 성공 - TemplateId={Id}, Name={Name}, HasFile={HasFile}",
                created.Id, created.Name, file != null);
            await InvalidateTemplatesCacheAsync();
            return CreatedAtAction(nameof(GetTemplate), new { templateId = created.Id }, created);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보고서 템플릿 생성 실패 (name={Name})", request.Name);
            await InvalidateTemplatesCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "템플릿 생성에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 보고서 템플릿 수정 — DocUtil `/api/v1/reports/templates/{template_id}` (PUT, JSON name?/description?).
    /// 성공/실패 모두 invalidate.
    /// </summary>
    [HttpPut("templates/{templateId}")]
    public async Task<ActionResult<DocUtilReportTemplateDetail>> UpdateTemplate(
        string templateId,
        [FromBody] DocUtilUpdateReportTemplateRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 식별자가 비어 있습니다."));
        }
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (request.Name != null && (request.Name.Length == 0 || request.Name.Length > 255))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 이름은 1~255자여야 합니다."));
        }
        if (request.Description != null && request.Description.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 설명은 2000자 이하여야 합니다."));
        }

        try
        {
            var updated = await _docUtilClient.UpdateReportTemplateAsync(templateId, request, ct);
            _logger.LogInformation("운영자 DocUtil 보고서 템플릿 수정 성공 - TemplateId={Id}", updated.Id);
            await InvalidateTemplatesCacheAsync();
            return Ok(updated);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보고서 템플릿 수정 실패 (id={Id})", templateId);
            await InvalidateTemplatesCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "템플릿 수정에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 보고서 템플릿 삭제 — DocUtil `/api/v1/reports/templates/{template_id}` (DELETE). 성공/실패 모두 invalidate.
    /// </summary>
    [HttpDelete("templates/{templateId}")]
    public async Task<IActionResult> DeleteTemplate(string templateId, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 식별자가 비어 있습니다."));
        }

        try
        {
            await _docUtilClient.DeleteReportTemplateAsync(templateId, ct);
            _logger.LogInformation("운영자 DocUtil 보고서 템플릿 삭제 성공 - TemplateId={Id}", templateId);
            await InvalidateTemplatesCacheAsync();
            return NoContent();
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보고서 템플릿 삭제 실패 (id={Id})", templateId);
            await InvalidateTemplatesCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "템플릿 삭제에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 한글 파일명 RFC 5987 ASCII fallback 헬퍼.
    // ──────────────────────────────────────────────────────────────────────

    private static string ToAsciiSafe(string name)
    {
        var sb = new StringBuilder(name.Length);
        foreach (var c in name)
        {
            sb.Append(c < 0x20 || c >= 0x7f || c == '"' || c == '\\' ? '_' : c);
        }
        return sb.ToString();
    }

    // ──────────────────────────────────────────────────────────────────────
    // 캐시 wrapper DTO
    // ──────────────────────────────────────────────────────────────────────

    private sealed class CachedReportDto
    {
        public string Id { get; set; } = string.Empty;
        public string? TemplateId { get; set; }
        public string OrganizationId { get; set; } = string.Empty;
        public string Title { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public string OutputFormat { get; set; } = string.Empty;
        public string? OutputStoragePath { get; set; }
        public string[]? SourceDocumentIds { get; set; }
        public string? SourceChatSessionId { get; set; }
        public IDictionary<string, object?>? GenerationParams { get; set; }
        public string? RenderingMode { get; set; }
        public IDictionary<string, object?>? Jinja2Context { get; set; }
        public string? ErrorMessage { get; set; }
        public string GeneratedBy { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        public DateTime? CompletedAt { get; set; }

        public static CachedReportDto From(DocUtilReport r) => new()
        {
            Id = r.Id,
            TemplateId = r.TemplateId,
            OrganizationId = r.OrganizationId,
            Title = r.Title,
            Status = r.Status,
            OutputFormat = r.OutputFormat,
            OutputStoragePath = r.OutputStoragePath,
            SourceDocumentIds = r.SourceDocumentIds,
            SourceChatSessionId = r.SourceChatSessionId,
            GenerationParams = r.GenerationParams,
            RenderingMode = r.RenderingMode,
            Jinja2Context = r.Jinja2Context,
            ErrorMessage = r.ErrorMessage,
            GeneratedBy = r.GeneratedBy,
            CreatedAt = r.CreatedAt,
            CompletedAt = r.CompletedAt,
        };

        public static CachedReportDto From(DocUtilReportDetail d) => new()
        {
            Id = d.Id,
            TemplateId = d.TemplateId,
            OrganizationId = d.OrganizationId,
            Title = d.Title,
            Status = d.Status,
            OutputFormat = d.OutputFormat,
            OutputStoragePath = d.OutputStoragePath,
            SourceDocumentIds = d.SourceDocumentIds,
            SourceChatSessionId = d.SourceChatSessionId,
            GenerationParams = d.GenerationParams,
            RenderingMode = d.RenderingMode,
            Jinja2Context = d.Jinja2Context,
            ErrorMessage = d.ErrorMessage,
            GeneratedBy = d.GeneratedBy,
            CreatedAt = d.CreatedAt,
            CompletedAt = d.CompletedAt,
        };

        public DocUtilReport ToReport() => new(
            Id, TemplateId, OrganizationId, Title, Status, OutputFormat,
            OutputStoragePath, SourceDocumentIds, SourceChatSessionId,
            GenerationParams, RenderingMode, Jinja2Context, ErrorMessage,
            GeneratedBy, CreatedAt, CompletedAt);

        public DocUtilReportDetail ToRecord() => new(
            Id, TemplateId, OrganizationId, Title, Status, OutputFormat,
            OutputStoragePath, SourceDocumentIds, SourceChatSessionId,
            GenerationParams, RenderingMode, Jinja2Context, ErrorMessage,
            GeneratedBy, CreatedAt, CompletedAt);
    }

    private sealed class CachedReportListDto
    {
        public CachedReportDto[] Items { get; set; } = Array.Empty<CachedReportDto>();
        public long Total { get; set; }
        public int Page { get; set; }
        public int Size { get; set; }

        public static CachedReportListDto From(DocUtilReportList list) => new()
        {
            Items = list.Items.Select(CachedReportDto.From).ToArray(),
            Total = list.Total,
            Page = list.Page,
            Size = list.Size,
        };

        public DocUtilReportList ToRecord() => new(
            Items.Select(c => c.ToReport()).ToArray(),
            Total, Page, Size);
    }

    private sealed class CachedTemplateDto
    {
        public string Id { get; set; } = string.Empty;
        public string OrganizationId { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string? Description { get; set; }
        public string Format { get; set; } = string.Empty;
        public string? TemplateStoragePath { get; set; }
        public IDictionary<string, object?>? Schema { get; set; }
        public string CreatedBy { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }

        public static CachedTemplateDto From(DocUtilReportTemplate t) => new()
        {
            Id = t.Id,
            OrganizationId = t.OrganizationId,
            Name = t.Name,
            Description = t.Description,
            Format = t.Format,
            TemplateStoragePath = t.TemplateStoragePath,
            Schema = t.Schema,
            CreatedBy = t.CreatedBy,
            CreatedAt = t.CreatedAt,
            UpdatedAt = t.UpdatedAt,
        };

        public static CachedTemplateDto From(DocUtilReportTemplateDetail d) => new()
        {
            Id = d.Id,
            OrganizationId = d.OrganizationId,
            Name = d.Name,
            Description = d.Description,
            Format = d.Format,
            TemplateStoragePath = d.TemplateStoragePath,
            Schema = d.Schema,
            CreatedBy = d.CreatedBy,
            CreatedAt = d.CreatedAt,
            UpdatedAt = d.UpdatedAt,
        };

        public DocUtilReportTemplate ToTemplate() => new(
            Id, OrganizationId, Name, Description, Format, TemplateStoragePath,
            Schema, CreatedBy, CreatedAt, UpdatedAt);

        public DocUtilReportTemplateDetail ToRecord() => new(
            Id, OrganizationId, Name, Description, Format, TemplateStoragePath,
            Schema, CreatedBy, CreatedAt, UpdatedAt);
    }

    private sealed class CachedTemplateListDto
    {
        public CachedTemplateDto[] Items { get; set; } = Array.Empty<CachedTemplateDto>();
        public long Total { get; set; }
        public int Page { get; set; }
        public int Size { get; set; }

        public static CachedTemplateListDto From(DocUtilReportTemplateList list) => new()
        {
            Items = list.Items.Select(CachedTemplateDto.From).ToArray(),
            Total = list.Total,
            Page = list.Page,
            Size = list.Size,
        };

        public DocUtilReportTemplateList ToRecord() => new(
            Items.Select(c => c.ToTemplate()).ToArray(),
            Total, Page, Size);
    }
}
