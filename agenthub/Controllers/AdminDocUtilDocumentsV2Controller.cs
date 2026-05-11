using System.Text;
using System.Web;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilDocumentsV2Controller — DocUtil 디자이너 문서 V2 운영자 BFF (Phase 10.2e)
//
// 통합 비전(P1 Control Plane / P5 인증 / R2 단일 진입점):
//   AgentHub 운영자 콘솔이 DocUtil 의 디자이너 기반 신규 문서 워크플로(Phase 4 S1/S2 D7/D8 산출물)
//   까지 단일 진입점에서 운영. 보고서 템플릿(Jinja2 기반) 후속 워크플로로, DocumentSchema
//   v1.0 의 22 컴포넌트 Discriminated Union 기반 자유 생성 + 부분 패치 + 비동기 export.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//   2. TTL 캐시(목록/상세 10분, version-key invalidate)
//      prefix `du:docv2:list:` / `du:docv2:detail:` + namespace `docutil-documents-v2`
//      - status 캐시 미적용(폴링 빈도 높음 — fresh 보장)
//      - export job ack(POST) / download(stream) 캐시 미적용
//   3. 4xx/5xx → 502 ErrorResponseDto 한국어 매핑
//   4. mutation(POST/PATCH/export) 성공/실패 모두 invalidate (10.1b ghost 처리 패턴)
//   5. binary stream(download) — Phase 10.2a HttpResponseOwnedStream + RFC 5987 한글 파일명 + ASCII fallback
//
// 도메인 특성:
//   - DocUtil 측 status: pending / running / completed / failed (export job state machine).
//   - DocumentSchema 는 free-form JSON dict — DocUtil 22 컴포넌트 union 그대로 pass-through.
//     BFF 는 schema 내용을 해석하지 않고 패스 — 운영자 UI 는 status / title / 메타데이터 위주.
//   - PATCH patch_type: page / component / tokens — 식별자 사전 검증을 BFF 차원에서도 한국어로 차단.
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 DocUtil 문서 V2(디자이너 워크플로) 관리 BFF — Phase 10.2e.
/// AgentHub Vue 콘솔의 `/admin/docutil-documents-v2` 페이지가 호출하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/docutil/documents-v2")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminDocUtilDocumentsV2Controller : ControllerBase
{
    private const string ListCachePrefix = "du:docv2:list:";
    private const string DetailCachePrefix = "du:docv2:detail:";
    public const string CacheVersionNamespace = "docutil-documents-v2";

    private static readonly TimeSpan ListCacheTtl = TimeSpan.FromMinutes(10);
    private static readonly TimeSpan DetailCacheTtl = TimeSpan.FromMinutes(10);

    // 입력 사전 차단(과도한 payload 방지).
    private const int MaxPromptLength = 8_000;
    private const int MaxSourceDocs = 10;
    private const int MaxPatchDataBytes = 256 * 1024;
    private const int MaxDesignTokensBytes = 16 * 1024;

    private readonly IDocUtilClient _docUtilClient;
    private readonly CachingService _cachingService;
    private readonly ILogger<AdminDocUtilDocumentsV2Controller> _logger;

    public AdminDocUtilDocumentsV2Controller(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        ILogger<AdminDocUtilDocumentsV2Controller> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _logger = logger;
    }

    /// <summary>
    /// 문서 V2 캐시 일괄 무효화 — mutation 성공/실패 모두 호출(ghost 정합성 보장).
    /// </summary>
    private async Task InvalidateDocumentsV2CacheAsync()
    {
        try
        {
            var v = await _cachingService.IncrementVersionAsync(CacheVersionNamespace);
            _logger.LogInformation("DocUtil 문서 V2 캐시 invalidate - newVersion={V}", v);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "DocUtil 문서 V2 캐시 invalidate 실패(무시)");
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // GET /api/admin/docutil/documents-v2 — 목록(limit/offset + 필터)
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// 문서 V2 목록 — DocUtil `/api/v1/v2/documents` 위임 + 10분 캐시.
    /// limit/offset 페이지네이션(DocUtil 측 V2 표준 — page/size 와 별개).
    /// </summary>
    /// <param name="limit">페이지 크기(기본 20, 1~100).</param>
    /// <param name="offset">조회 시작 오프셋(기본 0, ≥0).</param>
    /// <param name="documentType">문서 타입 필터(선택). slide_report/docx_report/proposal/minutes/...</param>
    /// <param name="mode">생성 모드 필터(선택). free_generation / template_fill.</param>
    [HttpGet("")]
    public async Task<ActionResult<DocUtilDocumentV2List>> ListDocumentsV2(
        [FromQuery] int limit = 20,
        [FromQuery] int offset = 0,
        [FromQuery] string? documentType = null,
        [FromQuery] string? mode = null,
        CancellationToken ct = default)
    {
        if (limit < 1 || limit > 100) limit = 20;
        if (offset < 0) offset = 0;

        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        string Normalize(string? s) => string.IsNullOrWhiteSpace(s) ? "_" : s.Trim().ToLowerInvariant();
        var cacheKey = $"{ListCachePrefix}v{version}:{limit}|{offset}|{Normalize(documentType)}|{Normalize(mode)}";

        var cached = await _cachingService.GetAsync<CachedDocumentV2ListDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 문서 V2 목록 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 문서 V2 목록 캐시 miss - key={Key}", cacheKey);

        try
        {
            var list = await _docUtilClient.ListDocumentsV2Async(documentType, mode, limit, offset, ct);
            await _cachingService.SetAsync(cacheKey, CachedDocumentV2ListDto.From(list), ListCacheTtl);
            return Ok(list);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 V2 목록 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 문서 V2 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // GET /api/admin/docutil/documents-v2/{documentId} — 단건
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// 문서 V2 단건 — DocUtil `/api/v1/v2/documents/{document_id}` 위임 + 10분 캐시.
    /// 404 응답은 한국어 ErrorResponseDto 로 정규화.
    /// </summary>
    [HttpGet("{documentId}")]
    public async Task<ActionResult<DocUtilDocumentV2Detail>> GetDocumentV2(
        string documentId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(documentId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("문서 식별자가 비어 있습니다."));
        }

        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{DetailCachePrefix}v{version}:{documentId}";

        var cached = await _cachingService.GetAsync<CachedDocumentV2Dto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 문서 V2 상세 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 문서 V2 상세 캐시 miss - key={Key}", cacheKey);

        try
        {
            var detail = await _docUtilClient.GetDocumentV2Async(documentId, ct);
            if (detail == null)
            {
                return NotFound(ErrorResponseDto.NotFound("DocUtil 문서 V2 를 찾을 수 없습니다."));
            }
            await _cachingService.SetAsync(cacheKey, CachedDocumentV2Dto.From(detail), DetailCacheTtl);
            return Ok(detail);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 V2 상세 조회 실패 (id={Id})", documentId);
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 문서 V2 상세를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // POST /api/admin/docutil/documents-v2 — 자유 생성(Mode A)
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// 문서 V2 자유 생성 — DocUtil `/api/v1/v2/documents` (POST, 202 Accepted).
    /// 현재 mode=free_generation 만 허용. RAG 근거 문서 ID 최대 10개.
    /// 성공/실패 모두 캐시 일괄 무효화.
    /// </summary>
    [HttpPost("")]
    public async Task<ActionResult<DocUtilDocumentV2Detail>> GenerateDocumentV2(
        [FromBody] DocUtilGenerateDocumentV2Request request,
        CancellationToken ct = default)
    {
        var err = ValidateGenerate(request);
        if (err != null) return BadRequest(ErrorResponseDto.BadRequest(err));

        try
        {
            var created = await _docUtilClient.GenerateDocumentV2Async(request, ct);
            _logger.LogInformation(
                "운영자 DocUtil 문서 V2 생성 성공 - DocId={Id}, Type={Type}, Mode={Mode}, Status={Status}",
                created.Id, created.DocumentType, created.Mode, created.Status);
            await InvalidateDocumentsV2CacheAsync();
            // 202 Accepted 의미를 살리되 Location 헤더는 단건 endpoint 로 설정.
            return CreatedAtAction(nameof(GetDocumentV2), new { documentId = created.Id }, created);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 V2 생성 실패 (Type={Type})", request?.DocumentType);
            await InvalidateDocumentsV2CacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 문서 V2 생성에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // PATCH /api/admin/docutil/documents-v2/{documentId} — 부분 패치
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// 문서 V2 부분 패치 — DocUtil `/api/v1/v2/documents/{document_id}` (PATCH).
    /// patch_type: page / component / tokens. expected_version 으로 낙관적 락 가능.
    /// 성공/실패 모두 캐시 일괄 무효화.
    /// </summary>
    [HttpPatch("{documentId}")]
    public async Task<ActionResult<DocUtilDocumentV2Detail>> PatchDocumentV2(
        string documentId,
        [FromBody] DocUtilPatchDocumentV2Request request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(documentId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("문서 식별자가 비어 있습니다."));
        }
        var err = ValidatePatch(request);
        if (err != null) return BadRequest(ErrorResponseDto.BadRequest(err));

        try
        {
            var patched = await _docUtilClient.PatchDocumentV2Async(documentId, request, ct);
            _logger.LogInformation(
                "운영자 DocUtil 문서 V2 패치 성공 - DocId={Id}, PatchType={Type}",
                patched.Id, request!.PatchType);
            await InvalidateDocumentsV2CacheAsync();
            return Ok(patched);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 V2 패치 실패 (id={Id}, type={Type})",
                documentId, request?.PatchType);
            await InvalidateDocumentsV2CacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 문서 V2 패치에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // POST /api/admin/docutil/documents-v2/{documentId}/export — 비동기 Export 요청
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// 문서 V2 export 비동기 요청 — DocUtil `/api/v1/v2/documents/{document_id}/export` (POST, 202).
    /// Celery 작업 등록 후 job_id 반환. 실제 빌드는 백그라운드.
    /// 캐시 invalidate 미적용(문서 자체는 변경 X — 부산물만 생성).
    /// </summary>
    /// <param name="documentId">대상 문서 ID.</param>
    /// <param name="request">{ format: pptx | docx | hwpx | pdf | html }</param>
    [HttpPost("{documentId}/export")]
    public async Task<ActionResult<DocUtilExportJobAck>> RequestExport(
        string documentId,
        [FromBody] DocUtilRequestDocumentV2ExportRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(documentId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("문서 식별자가 비어 있습니다."));
        }
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(request.Format))
        {
            return BadRequest(ErrorResponseDto.BadRequest("export 포맷이 비어 있습니다."));
        }
        if (request.Format is not ("pptx" or "docx" or "hwpx" or "pdf" or "html"))
        {
            return BadRequest(ErrorResponseDto.BadRequest(
                "지원하지 않는 포맷입니다. (허용: pptx, docx, hwpx, pdf, html)"));
        }

        try
        {
            var ack = await _docUtilClient.RequestDocumentV2ExportAsync(documentId, request, ct);
            _logger.LogInformation(
                "운영자 DocUtil 문서 V2 export 요청 - DocId={Id}, Format={Fmt}, JobId={JobId}",
                documentId, request.Format, ack.JobId);
            return Accepted(ack);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 V2 export 요청 실패 (id={Id}, fmt={Fmt})",
                documentId, request.Format);
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 문서 V2 export 요청에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // GET /api/admin/docutil/documents-v2/exports/{jobId} — 작업 상태 폴링
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// 문서 V2 export 작업 상태 폴링 — DocUtil `/api/v1/v2/documents/exports/{job_id}`.
    /// 캐시 미적용(폴링 빈도 높음 — fresh 보장).
    /// </summary>
    [HttpGet("exports/{jobId}")]
    public async Task<ActionResult<DocUtilExportJobStatus>> GetExportStatus(
        string jobId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(jobId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("작업 식별자가 비어 있습니다."));
        }

        try
        {
            var state = await _docUtilClient.GetDocumentV2ExportStatusAsync(jobId, ct);
            return Ok(state);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 V2 export 상태 조회 실패 (jobId={JobId})", jobId);
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 문서 V2 export 상태를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // GET /api/admin/docutil/documents-v2/exports/{jobId}/download — 결과 다운로드(프록시)
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// 문서 V2 export 결과 다운로드 — DocUtil `/api/v1/v2/documents/exports/{job_id}/download` 프록시.
    /// <para>
    /// 응답은 binary stream. HttpResponseOwnedStream 으로 lifetime 결합.
    /// 한글 파일명은 RFC 5987 (filename*=UTF-8''...) 인코딩 + ASCII fallback.
    /// </para>
    /// </summary>
    [HttpGet("exports/{jobId}/download")]
    public async Task<IActionResult> DownloadExport(
        string jobId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(jobId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("작업 식별자가 비어 있습니다."));
        }

        DocUtilDocumentV2Download download;
        try
        {
            download = await _docUtilClient.DownloadDocumentV2ExportAsync(jobId, ct);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 V2 export 다운로드 실패 (jobId={JobId})", jobId);
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 문서 V2 export 결과를 다운로드하지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }

        var rawName = string.IsNullOrWhiteSpace(download.FileName)
            ? $"document-{jobId}"
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
    // 검증 헬퍼
    // ══════════════════════════════════════════════════════════════════════

    private static string? ValidateGenerate(DocUtilGenerateDocumentV2Request? r)
    {
        if (r == null) return "요청 본문이 비어 있습니다.";
        if (string.IsNullOrWhiteSpace(r.Prompt)) return "프롬프트가 비어 있습니다.";
        if (r.Prompt.Length > MaxPromptLength) return $"프롬프트는 {MaxPromptLength}자 이하여야 합니다.";
        if (string.IsNullOrWhiteSpace(r.DocumentType)) return "문서 타입이 비어 있습니다.";
        // DocUtil 의 7가지 DocumentType Literal 과 1:1 매칭 — 사전 차단(서비스 비용 절감).
        if (r.DocumentType is not (
            "slide_report" or "docx_report" or "proposal" or "minutes"
            or "one_pager" or "weekly_status" or "freeform_doc"))
        {
            return "지원하지 않는 문서 타입입니다. "
                + "(허용: slide_report, docx_report, proposal, minutes, one_pager, weekly_status, freeform_doc)";
        }
        if (!string.IsNullOrWhiteSpace(r.Mode) && r.Mode is not ("free_generation" or "template_fill"))
        {
            return "mode 는 free_generation 또는 template_fill 이어야 합니다.";
        }
        if (r.Mode == "template_fill")
        {
            // DocUtil 측 D7 기준 — 본 endpoint 는 free_generation 만 허용.
            return "현재 운영자 콘솔은 mode=free_generation 만 지원합니다. (template_fill 은 DocUtil 측 D8 활성화 대기)";
        }
        if (r.SourceDocumentIds != null && r.SourceDocumentIds.Length > MaxSourceDocs)
        {
            return $"source_document_ids 는 최대 {MaxSourceDocs}개까지 지정 가능합니다.";
        }
        if (r.DesignTokens != null)
        {
            // free-form 이지만 과도한 payload 차단.
            try
            {
                var json = System.Text.Json.JsonSerializer.Serialize(r.DesignTokens);
                if (Encoding.UTF8.GetByteCount(json) > MaxDesignTokensBytes)
                {
                    return $"design_tokens 페이로드가 너무 큽니다. (최대 {MaxDesignTokensBytes / 1024}KB)";
                }
            }
            catch
            {
                return "design_tokens 직렬화에 실패했습니다.";
            }
        }
        return null;
    }

    private static string? ValidatePatch(DocUtilPatchDocumentV2Request? r)
    {
        if (r == null) return "요청 본문이 비어 있습니다.";
        if (string.IsNullOrWhiteSpace(r.PatchType)) return "patch_type 이 비어 있습니다.";
        if (r.PatchType is not ("page" or "component" or "tokens"))
        {
            return "patch_type 은 page / component / tokens 중 하나여야 합니다.";
        }
        if (r.PatchType == "page" && string.IsNullOrWhiteSpace(r.PageId))
        {
            return "patch_type=page 에는 page_id 가 필요합니다.";
        }
        if (r.PatchType == "component"
            && (string.IsNullOrWhiteSpace(r.PageId) || string.IsNullOrWhiteSpace(r.ComponentId)))
        {
            return "patch_type=component 에는 page_id 와 component_id 가 모두 필요합니다.";
        }
        if (r.PatchType == "tokens"
            && (!string.IsNullOrWhiteSpace(r.PageId) || !string.IsNullOrWhiteSpace(r.ComponentId)))
        {
            return "patch_type=tokens 에는 page_id / component_id 를 지정하지 않습니다.";
        }
        // 식별자 패턴 사전 차단(DocUtil 측 regex 와 동일).
        if (!string.IsNullOrWhiteSpace(r.PageId)
            && !System.Text.RegularExpressions.Regex.IsMatch(r.PageId, @"^p\d+$"))
        {
            return "page_id 는 'p1', 'p2' ... 형식이어야 합니다.";
        }
        if (!string.IsNullOrWhiteSpace(r.ComponentId)
            && !System.Text.RegularExpressions.Regex.IsMatch(r.ComponentId, @"^c\d+$"))
        {
            return "component_id 는 'c1', 'c2' ... 형식이어야 합니다.";
        }
        if (r.ExpectedVersion.HasValue && r.ExpectedVersion < 1)
        {
            return "expected_version 은 1 이상이어야 합니다.";
        }
        // patch_data 페이로드 크기 차단.
        if (r.Data != null)
        {
            try
            {
                var json = System.Text.Json.JsonSerializer.Serialize(r.Data);
                if (Encoding.UTF8.GetByteCount(json) > MaxPatchDataBytes)
                {
                    return $"data 페이로드가 너무 큽니다. (최대 {MaxPatchDataBytes / 1024}KB)";
                }
            }
            catch
            {
                return "data 직렬화에 실패했습니다.";
            }
        }
        return null;
    }

    /// <summary>
    /// 한글 파일명을 ASCII 안전 fallback 으로 변환 — RFC 5987 미지원 클라이언트 대비.
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

    // ══════════════════════════════════════════════════════════════════════
    // 캐시 직렬화용 DTO
    // ══════════════════════════════════════════════════════════════════════

    public sealed class CachedDocumentV2Dto
    {
        public string Id { get; set; } = string.Empty;
        public string OrganizationId { get; set; } = string.Empty;
        public string? GeneratedByUserId { get; set; }
        public string? AgentId { get; set; }
        public string? TemplateId { get; set; }
        public string DocumentType { get; set; } = string.Empty;
        public string Mode { get; set; } = "free_generation";
        public string Title { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public string? ErrorMessage { get; set; }
        public string? LlmProvider { get; set; }
        public string? LlmModel { get; set; }
        public int? PromptTokens { get; set; }
        public int? CompletionTokens { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime? CompletedAt { get; set; }
        public IDictionary<string, object?>? DocumentSchema { get; set; }

        public static CachedDocumentV2Dto From(DocUtilDocumentV2Detail r) => new()
        {
            Id = r.Id,
            OrganizationId = r.OrganizationId,
            GeneratedByUserId = r.GeneratedByUserId,
            AgentId = r.AgentId,
            TemplateId = r.TemplateId,
            DocumentType = r.DocumentType,
            Mode = r.Mode,
            Title = r.Title,
            Status = r.Status,
            ErrorMessage = r.ErrorMessage,
            LlmProvider = r.LlmProvider,
            LlmModel = r.LlmModel,
            PromptTokens = r.PromptTokens,
            CompletionTokens = r.CompletionTokens,
            CreatedAt = r.CreatedAt,
            CompletedAt = r.CompletedAt,
            DocumentSchema = r.DocumentSchema,
        };

        public DocUtilDocumentV2Detail ToRecord() => new(
            Id, OrganizationId, GeneratedByUserId, AgentId, TemplateId,
            DocumentType, Mode, Title, Status, ErrorMessage,
            LlmProvider, LlmModel, PromptTokens, CompletionTokens,
            CreatedAt, CompletedAt, DocumentSchema);
    }

    public sealed class CachedDocumentV2ListDto
    {
        public CachedDocumentV2Dto[] Items { get; set; } = Array.Empty<CachedDocumentV2Dto>();
        public long Total { get; set; }
        public int Limit { get; set; }
        public int Offset { get; set; }

        public static CachedDocumentV2ListDto From(DocUtilDocumentV2List l) => new()
        {
            Items = l.Items.Select(CachedDocumentV2Dto.From).ToArray(),
            Total = l.Total,
            Limit = l.Limit,
            Offset = l.Offset,
        };

        public DocUtilDocumentV2List ToRecord() => new(
            Items.Select(i => i.ToRecord()).ToArray(),
            Total, Limit, Offset);
    }
}
