using System.Net.Http.Headers;
using System.Text;
using System.Web;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilTemplatesController — DocUtil 문서 템플릿 운영자 BFF (Phase 10.2d)
//
// 통합 비전(P1 Control Plane / P5 인증 / R2 단일 진입점):
//   AgentHub 운영자 콘솔이 DocUtil 의 문서 템플릿(Jinja2 기반 문서 생성용) 카탈로그 +
//   파일 업로드(일반/빈양식/스마트 3종) + AI 자동채움 + 변환 + 변수 메타 편집 + 미리보기 다운로드 +
//   구조 조회 + 변수 매핑 적용까지 단일 진입점에서 운영. Phase 10.1/10.2a~10.2c 와 동일 BFF 패턴.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//   2. TTL 캐시(목록/상세) + version-key invalidate (10분 TTL — 카탈로그성, 보고서 템플릿과 동일 정책):
//      - prefix `du:doctpl:list:` + namespace `docutil-document-templates`
//      - prefix `du:doctpl:detail:` + namespace `docutil-document-templates`
//      - 변수 목록(GET /variables) 도 10분 캐시 — 폼 렌더링 안정성 우선
//      - 구조 / 미리보기 / auto-fill / convert / apply-mapping 은 캐시 미적용
//        (구조 조회는 운영자가 매번 fresh 확인을 원하고, 미리보기는 stream)
//   3. 4xx/5xx → 502 ErrorResponseDto 한국어 매핑(서비스 레이어가 InvalidOperationException 으로 통일)
//   4. mutation(POST/PUT/DELETE/convert/auto-fill/apply-mapping) 성공/실패 모두 invalidate (10.1b ghost 처리 패턴)
//   5. binary stream(preview) — Phase 10.2a HttpResponseOwnedStream + Phase 10.2c 다운로드 패턴 재사용
//      + RFC 5987 한글 파일명 + ASCII fallback
//   6. multipart upload — 3종(일반/빈양식/스마트) 각각 별도 endpoint 로 노출
//
// 캐시 namespace 격리(보고서 템플릿과 분리):
//   `docutil-document-templates` (본 컨트롤러) — Jinja2 문서 생성용 템플릿
//   `docutil-report-templates`   (AdminDocUtilReportsController) — 보고서 출력 템플릿
//   두 도메인은 독립 — invalidate 가 cascade 되지 않음.
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 DocUtil 문서 템플릿(Document Templates) 관리 BFF — Phase 10.2d.
/// AgentHub Vue 콘솔의 `/admin/docutil-templates` 페이지가 호출하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/docutil/templates")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminDocUtilTemplatesController : ControllerBase
{
    private const string ListCachePrefix = "du:doctpl:list:";
    private const string DetailCachePrefix = "du:doctpl:detail:";
    private const string VariablesCachePrefix = "du:doctpl:vars:";
    public const string CacheVersionNamespace = "docutil-document-templates";

    private static readonly TimeSpan ListCacheTtl = TimeSpan.FromMinutes(10);
    private static readonly TimeSpan DetailCacheTtl = TimeSpan.FromMinutes(10);
    private static readonly TimeSpan VariablesCacheTtl = TimeSpan.FromMinutes(10);

    // 업로드 본문 최대 크기(50MB) — 보고서 템플릿 컨트롤러와 동일.
    // DocUtil 측이 더 큰 파일을 받을 수 있으나 BFF 차원에서 사전 차단.
    private const int UploadMaxBytes = 50 * 1024 * 1024;

    // ai_analysis / mappings 등 free-form JSON body 의 직렬화 후 최대 크기(64KB).
    private const int FreeFormPayloadMaxBytes = 64 * 1024;

    private readonly IDocUtilClient _docUtilClient;
    private readonly CachingService _cachingService;
    private readonly ILogger<AdminDocUtilTemplatesController> _logger;

    public AdminDocUtilTemplatesController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        ILogger<AdminDocUtilTemplatesController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _logger = logger;
    }

    /// <summary>
    /// 문서 템플릿 캐시 일괄 무효화 — mutation 성공/실패 모두 호출(10.1b ghost 정합성 보장).
    /// 캐시 무효화는 best-effort — 실패는 swallow + 경고 로그.
    /// </summary>
    private async Task InvalidateTemplatesCacheAsync()
    {
        try
        {
            var v = await _cachingService.IncrementVersionAsync(CacheVersionNamespace);
            _logger.LogInformation("DocUtil 문서 템플릿 캐시 invalidate - newVersion={V}", v);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "DocUtil 문서 템플릿 캐시 invalidate 실패(무시)");
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // CRUD — 목록 / 상세 / 생성 / 수정 / 삭제 (5 endpoint)
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// 문서 템플릿 목록(페이징 + 유형 필터) — DocUtil `/api/v1/templates` 위임 + 10분 캐시.
    /// </summary>
    /// <param name="page">페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 20, 1~100).</param>
    /// <param name="templateType">템플릿 유형 필터(선택).</param>
    [HttpGet("")]
    public async Task<ActionResult<DocUtilDocumentTemplateList>> ListTemplates(
        [FromQuery] int page = 1,
        [FromQuery] int size = 20,
        [FromQuery] string? templateType = null,
        CancellationToken ct = default)
    {
        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        string Normalize(string? s) => string.IsNullOrWhiteSpace(s) ? "_" : s.Trim().ToLowerInvariant();
        var cacheKey = $"{ListCachePrefix}v{version}:{page}|{size}|{Normalize(templateType)}";

        var cached = await _cachingService.GetAsync<CachedDocumentTemplateListDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 문서 템플릿 목록 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 문서 템플릿 목록 캐시 miss - key={Key}", cacheKey);

        try
        {
            var list = await _docUtilClient.ListDocumentTemplatesAsync(templateType, page, size, ct);
            await _cachingService.SetAsync(cacheKey, CachedDocumentTemplateListDto.From(list), ListCacheTtl);
            return Ok(list);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 템플릿 목록 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 문서 템플릿 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 문서 템플릿 상세 — DocUtil `/api/v1/templates/{template_id}` 위임 + 10분 캐시.
    /// 404 응답은 한국어 ErrorResponseDto 로 정규화.
    /// </summary>
    [HttpGet("{templateId}")]
    public async Task<ActionResult<DocUtilDocumentTemplateDetail>> GetTemplate(
        string templateId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 식별자가 비어 있습니다."));
        }

        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{DetailCachePrefix}v{version}:{templateId}";

        var cached = await _cachingService.GetAsync<CachedDocumentTemplateDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 문서 템플릿 상세 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 문서 템플릿 상세 캐시 miss - key={Key}", cacheKey);

        try
        {
            var detail = await _docUtilClient.GetDocumentTemplateAsync(templateId, ct);
            if (detail == null)
            {
                return NotFound(ErrorResponseDto.NotFound("템플릿을 찾을 수 없습니다."));
            }
            await _cachingService.SetAsync(cacheKey, CachedDocumentTemplateDto.From(detail), DetailCacheTtl);
            return Ok(detail);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 템플릿 상세 조회 실패 (id={Id})", templateId);
            return StatusCode(502, new ErrorResponseDto(
                "템플릿 상세를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 문서 템플릿 생성(JSON, 메타데이터만) — DocUtil `/api/v1/templates` (POST).
    /// 성공/실패 모두 캐시 일괄 무효화.
    /// </summary>
    [HttpPost("")]
    public async Task<ActionResult<DocUtilDocumentTemplateDetail>> CreateTemplate(
        [FromBody] DocUtilCreateDocumentTemplateRequest request,
        CancellationToken ct = default)
    {
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 이름이 비어 있습니다."));
        }
        if (request.Name.Length > 255)
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 이름은 255자 이하여야 합니다."));
        }
        if (string.IsNullOrWhiteSpace(request.TemplateType))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 유형이 비어 있습니다."));
        }
        if (request.TemplateType.Length > 100)
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 유형은 100자 이하여야 합니다."));
        }
        if (string.IsNullOrWhiteSpace(request.OutputFormat))
        {
            return BadRequest(ErrorResponseDto.BadRequest("출력 형식이 비어 있습니다."));
        }
        if (request.OutputFormat.Length > 20)
        {
            return BadRequest(ErrorResponseDto.BadRequest("출력 형식은 20자 이하여야 합니다."));
        }
        if (request.Description != null && request.Description.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 설명은 2000자 이하여야 합니다."));
        }
        if (request.SamplePrompt != null && request.SamplePrompt.Length > 5000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("예시 프롬프트는 5000자 이하여야 합니다."));
        }

        try
        {
            var created = await _docUtilClient.CreateDocumentTemplateAsync(request, ct);
            _logger.LogInformation(
                "운영자 DocUtil 문서 템플릿 생성 성공 - TemplateId={Id}, Name={Name}, Type={Type}",
                created.Id, created.Name, created.TemplateType);
            await InvalidateTemplatesCacheAsync();
            return CreatedAtAction(nameof(GetTemplate), new { templateId = created.Id }, created);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 템플릿 생성 실패 (name={Name})", request.Name);
            await InvalidateTemplatesCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "템플릿 생성에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 문서 템플릿 수정(partial) — DocUtil `/api/v1/templates/{template_id}` (PUT).
    /// </summary>
    [HttpPut("{templateId}")]
    public async Task<ActionResult<DocUtilDocumentTemplateDetail>> UpdateTemplate(
        string templateId,
        [FromBody] DocUtilUpdateDocumentTemplateRequest request,
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
        if (request.TemplateType != null && request.TemplateType.Length > 100)
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 유형은 100자 이하여야 합니다."));
        }
        if (request.OutputFormat != null && request.OutputFormat.Length > 20)
        {
            return BadRequest(ErrorResponseDto.BadRequest("출력 형식은 20자 이하여야 합니다."));
        }
        if (request.SamplePrompt != null && request.SamplePrompt.Length > 5000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("예시 프롬프트는 5000자 이하여야 합니다."));
        }

        try
        {
            var updated = await _docUtilClient.UpdateDocumentTemplateAsync(templateId, request, ct);
            _logger.LogInformation("운영자 DocUtil 문서 템플릿 수정 성공 - TemplateId={Id}", updated.Id);
            await InvalidateTemplatesCacheAsync();
            return Ok(updated);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 템플릿 수정 실패 (id={Id})", templateId);
            await InvalidateTemplatesCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "템플릿 수정에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 문서 템플릿 삭제 — DocUtil `/api/v1/templates/{template_id}` (DELETE).
    /// </summary>
    [HttpDelete("{templateId}")]
    public async Task<IActionResult> DeleteTemplate(string templateId, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 식별자가 비어 있습니다."));
        }

        try
        {
            await _docUtilClient.DeleteDocumentTemplateAsync(templateId, ct);
            _logger.LogInformation("운영자 DocUtil 문서 템플릿 삭제 성공 - TemplateId={Id}", templateId);
            await InvalidateTemplatesCacheAsync();
            return NoContent();
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 템플릿 삭제 실패 (id={Id})", templateId);
            await InvalidateTemplatesCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "템플릿 삭제에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // 파일 업로드 — 일반 / 빈양식 / 스마트 (3 endpoint)
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// 템플릿 파일 업로드(일반 Jinja2) — DocUtil `/api/v1/templates/upload`.
    /// 파일 내 {{ }} 변수가 자동 추출되어 응답에 포함된다.
    /// </summary>
    [HttpPost("upload")]
    [RequestSizeLimit(UploadMaxBytes)]
    public async Task<ActionResult<DocUtilDocumentTemplateUpload>> UploadTemplate(
        [FromForm] string templateType,
        [FromForm] string outputFormat,
        [FromForm] string? tone = null,
        [FromForm] string? name = null,
        [FromForm] string? description = null,
        IFormFile? file = null,
        CancellationToken ct = default)
        => await UploadInternalAsync(
            isBlank: false,
            isSmart: false,
            templateType,
            outputFormat,
            tone,
            name,
            description,
            file,
            ct);

    /// <summary>
    /// 빈 양식 업로드(AI 자동 Jinja2 변환) — DocUtil `/api/v1/templates/upload-blank`.
    /// </summary>
    [HttpPost("upload-blank")]
    [RequestSizeLimit(UploadMaxBytes)]
    public async Task<ActionResult<DocUtilDocumentTemplateUpload>> UploadBlankForm(
        [FromForm] string templateType,
        [FromForm] string outputFormat,
        [FromForm] string? tone = null,
        [FromForm] string? name = null,
        [FromForm] string? description = null,
        IFormFile? file = null,
        CancellationToken ct = default)
        => await UploadInternalAsync(
            isBlank: true,
            isSmart: false,
            templateType,
            outputFormat,
            tone,
            name,
            description,
            file,
            ct);

    /// <summary>
    /// 스마트 업로드(자동 라우팅) — DocUtil `/api/v1/templates/upload-smart`.
    /// name/template_type 생략 가능 — DocUtil 측이 파일명/내용에서 자동 추측.
    /// </summary>
    [HttpPost("upload-smart")]
    [RequestSizeLimit(UploadMaxBytes)]
    public async Task<ActionResult<DocUtilDocumentTemplateUpload>> UploadSmart(
        [FromForm] string? templateType = null,
        [FromForm] string? tone = null,
        [FromForm] string? name = null,
        [FromForm] string? description = null,
        IFormFile? file = null,
        CancellationToken ct = default)
        => await UploadInternalAsync(
            isBlank: false,
            isSmart: true,
            templateType,
            outputFormat: null,
            tone,
            name,
            description,
            file,
            ct);

    private async Task<ActionResult<DocUtilDocumentTemplateUpload>> UploadInternalAsync(
        bool isBlank,
        bool isSmart,
        string? templateType,
        string? outputFormat,
        string? tone,
        string? name,
        string? description,
        IFormFile? file,
        CancellationToken ct)
    {
        if (file == null || file.Length == 0)
        {
            return BadRequest(ErrorResponseDto.BadRequest("업로드할 파일이 비어 있습니다."));
        }

        if (!isSmart)
        {
            if (string.IsNullOrWhiteSpace(templateType))
            {
                return BadRequest(ErrorResponseDto.BadRequest("템플릿 유형이 비어 있습니다."));
            }
            if (templateType.Length > 100)
            {
                return BadRequest(ErrorResponseDto.BadRequest("템플릿 유형은 100자 이하여야 합니다."));
            }
            if (string.IsNullOrWhiteSpace(outputFormat))
            {
                return BadRequest(ErrorResponseDto.BadRequest("출력 형식이 비어 있습니다."));
            }
            if (outputFormat.Length > 20)
            {
                return BadRequest(ErrorResponseDto.BadRequest("출력 형식은 20자 이하여야 합니다."));
            }
        }
        else
        {
            // 스마트 업로드: template_type 은 nullable, 단 입력했으면 길이 검증.
            if (templateType != null && templateType.Length > 100)
            {
                return BadRequest(ErrorResponseDto.BadRequest("템플릿 유형은 100자 이하여야 합니다."));
            }
        }
        if (name != null && name.Length > 255)
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 이름은 255자 이하여야 합니다."));
        }
        if (description != null && description.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 설명은 2000자 이하여야 합니다."));
        }

        using var fileStream = file.OpenReadStream();
        var fileName = file.FileName;
        var resolvedTone = string.IsNullOrWhiteSpace(tone) ? "formal" : tone;

        try
        {
            DocUtilDocumentTemplateUpload uploaded;
            if (isSmart)
            {
                var smartReq = new DocUtilUploadSmartTemplateRequest(
                    Name: name,
                    Description: description,
                    TemplateType: templateType,
                    Tone: resolvedTone);
                uploaded = await _docUtilClient.UploadSmartTemplateAsync(smartReq, fileStream, fileName, ct);
            }
            else
            {
                var stdReq = new DocUtilUploadDocumentTemplateRequest(
                    TemplateType: templateType!,
                    OutputFormat: outputFormat!,
                    Tone: resolvedTone,
                    Name: name,
                    Description: description);
                if (isBlank)
                {
                    uploaded = await _docUtilClient.UploadBlankFormAsync(stdReq, fileStream, fileName, ct);
                }
                else
                {
                    uploaded = await _docUtilClient.UploadDocumentTemplateAsync(stdReq, fileStream, fileName, ct);
                }
            }

            _logger.LogInformation(
                "운영자 DocUtil 문서 템플릿 업로드 성공 - TemplateId={Id}, Name={Name}, Mode={Mode}, RenderingMode={RenderingMode}",
                uploaded.Id,
                uploaded.Name,
                isSmart ? "smart" : (isBlank ? "blank" : "standard"),
                uploaded.RenderingMode);

            await InvalidateTemplatesCacheAsync();
            return Ok(uploaded);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex,
                "DocUtil 문서 템플릿 업로드 실패 - FileName={FileName}, Mode={Mode}",
                fileName,
                isSmart ? "smart" : (isBlank ? "blank" : "standard"));
            await InvalidateTemplatesCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "템플릿 업로드에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // 변수 메타 / AI 자동채움 / 변환 / 구조 / 매핑 적용 / 미리보기 (7 endpoint)
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// 변수 메타 조회 — DocUtil `/api/v1/templates/{template_id}/variables` 위임 + 10분 캐시.
    /// </summary>
    [HttpGet("{templateId}/variables")]
    public async Task<ActionResult<List<DocUtilDocumentTemplateVariable>>> GetVariables(
        string templateId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 식별자가 비어 있습니다."));
        }

        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{VariablesCachePrefix}v{version}:{templateId}";

        var cached = await _cachingService.GetAsync<CachedVariablesDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 템플릿 변수 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToList());
        }

        try
        {
            var variables = await _docUtilClient.GetDocumentTemplateVariablesAsync(templateId, ct);
            await _cachingService.SetAsync(cacheKey, CachedVariablesDto.From(variables), VariablesCacheTtl);
            return Ok(variables);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 템플릿 변수 조회 실패 (id={Id})", templateId);
            return StatusCode(502, new ErrorResponseDto(
                "템플릿 변수를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 변수 메타 일괄 수정 — DocUtil `/api/v1/templates/{template_id}/variables` (PUT).
    /// 성공/실패 모두 invalidate.
    /// </summary>
    [HttpPut("{templateId}/variables")]
    public async Task<ActionResult<DocUtilDocumentTemplateDetail>> UpdateVariables(
        string templateId,
        [FromBody] DocUtilUpdateDocumentTemplateVariablesRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 식별자가 비어 있습니다."));
        }
        if (request == null || request.Variables == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        // 변수 배열 길이 캡 — 너무 큰 배열을 DocUtil 로 보내지 않도록.
        if (request.Variables.Length > 1000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("변수 배열이 너무 큽니다(최대 1000개)."));
        }
        foreach (var v in request.Variables)
        {
            if (v == null || string.IsNullOrWhiteSpace(v.Name))
            {
                return BadRequest(ErrorResponseDto.BadRequest("변수 이름이 비어 있습니다."));
            }
        }

        try
        {
            var updated = await _docUtilClient.UpdateDocumentTemplateVariablesAsync(templateId, request, ct);
            _logger.LogInformation(
                "운영자 DocUtil 템플릿 변수 메타 수정 성공 - TemplateId={Id}, Count={Count}",
                templateId, request.Variables.Length);
            await InvalidateTemplatesCacheAsync();
            return Ok(updated);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 템플릿 변수 수정 실패 (id={Id})", templateId);
            await InvalidateTemplatesCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "템플릿 변수 수정에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// AI 자동채움 — DocUtil `/api/v1/templates/{template_id}/auto-fill` (POST).
    /// 캐시 미적용 — 매 호출 fresh 결과 보장.
    /// </summary>
    [HttpPost("{templateId}/auto-fill")]
    public async Task<ActionResult<DocUtilDocumentTemplateAutoFill>> AutoFill(
        string templateId,
        [FromBody] DocUtilAutoFillDocumentTemplateRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 식별자가 비어 있습니다."));
        }
        if (request == null || request.SourceDocumentIds == null || request.SourceDocumentIds.Length == 0)
        {
            return BadRequest(ErrorResponseDto.BadRequest("소스 문서 ID 가 비어 있습니다."));
        }
        if (request.SourceDocumentIds.Length > 50)
        {
            return BadRequest(ErrorResponseDto.BadRequest("소스 문서 ID 는 최대 50개입니다."));
        }
        if (request.AiPrompt != null && request.AiPrompt.Length > 5000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("AI 프롬프트는 5000자 이하여야 합니다."));
        }

        try
        {
            var result = await _docUtilClient.AutoFillDocumentTemplateAsync(templateId, request, ct);
            _logger.LogInformation(
                "운영자 DocUtil 템플릿 자동채움 성공 - TemplateId={Id}, SourceCount={SourceCount}",
                templateId, request.SourceDocumentIds.Length);
            return Ok(result);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 템플릿 자동채움 실패 (id={Id})", templateId);
            return StatusCode(502, new ErrorResponseDto(
                "AI 자동채움에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 일반 문서 → Jinja2 변환 — DocUtil `/api/v1/templates/{template_id}/convert` (POST).
    /// <para>
    /// Phase 10.x Medium 보강 (2026-05-11) — convert 는 templateStoragePath(원본 파일) 가 있어야
    /// 의미가 있다. 사전에 GetDocumentTemplateAsync 로 확인 후 null 이면 400 BadRequest +
    /// 한국어 안내 즉시 반환(DocUtil 측 422/500 회피, 운영자 UX 개선).
    /// </para>
    /// </summary>
    [HttpPost("{templateId}/convert")]
    public async Task<ActionResult<DocUtilDocumentTemplateDetail>> ConvertToTemplate(
        string templateId,
        [FromBody] ConvertTemplateRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 식별자가 비어 있습니다."));
        }
        if (request == null || request.AiAnalysis == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("ai_analysis 가 비어 있습니다."));
        }

        // ai_analysis 사이즈 캡 — 너무 큰 free-form payload 사전 차단.
        try
        {
            var serialized = System.Text.Json.JsonSerializer.Serialize(request.AiAnalysis);
            if (Encoding.UTF8.GetByteCount(serialized) > FreeFormPayloadMaxBytes)
            {
                return BadRequest(ErrorResponseDto.BadRequest(
                    $"ai_analysis 가 너무 큽니다(최대 {FreeFormPayloadMaxBytes / 1024} KB)."));
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "ai_analysis 직렬화 실패 — 그대로 위임");
        }

        // Phase 10.x — 사전 검증: 원본 파일 미업로드 템플릿은 변환 불가.
        if (!await EnsureTemplateHasStorageAsync(templateId, ct))
        {
            return BadRequest(new ErrorResponseDto(
                "이 템플릿은 원본 파일이 업로드되지 않아 변환할 수 없습니다. 먼저 파일을 업로드하세요.",
                "DOCUTIL_TEMPLATE_NO_STORAGE",
                new { templateId, operation = "convert" }));
        }

        try
        {
            var detail = await _docUtilClient.ConvertDocumentTemplateAsync(templateId, request.AiAnalysis, ct);
            _logger.LogInformation("운영자 DocUtil 템플릿 변환 성공 - TemplateId={Id}", templateId);
            await InvalidateTemplatesCacheAsync();
            return Ok(detail);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 템플릿 변환 실패 (id={Id})", templateId);
            await InvalidateTemplatesCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "템플릿 변환에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 에디터용 문서 구조 — DocUtil `/api/v1/templates/{template_id}/structure` 위임.
    /// 캐시 미적용 — 운영자가 매번 fresh 구조 확인을 원함.
    /// </summary>
    [HttpGet("{templateId}/structure")]
    public async Task<ActionResult<IDictionary<string, object?>>> GetStructure(
        string templateId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 식별자가 비어 있습니다."));
        }

        try
        {
            var structure = await _docUtilClient.GetDocumentTemplateStructureAsync(templateId, ct);
            return Ok(structure);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 템플릿 구조 조회 실패 (id={Id})", templateId);
            return StatusCode(502, new ErrorResponseDto(
                "템플릿 구조를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 변수 매핑 적용 — DocUtil `/api/v1/templates/{template_id}/apply-mapping` (POST).
    /// </summary>
    [HttpPost("{templateId}/apply-mapping")]
    public async Task<ActionResult<DocUtilDocumentTemplateDetail>> ApplyMapping(
        string templateId,
        [FromBody] DocUtilApplyDocumentTemplateMappingRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 식별자가 비어 있습니다."));
        }
        if (request == null || request.Mappings == null || request.Mappings.Length == 0)
        {
            return BadRequest(ErrorResponseDto.BadRequest("변수 매핑이 비어 있습니다."));
        }
        if (request.Mappings.Length > 1000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("변수 매핑이 너무 많습니다(최대 1000개)."));
        }
        foreach (var m in request.Mappings)
        {
            if (m == null || string.IsNullOrWhiteSpace(m.VariableName))
            {
                return BadRequest(ErrorResponseDto.BadRequest("매핑의 variable_name 이 비어 있습니다."));
            }
            if (string.IsNullOrWhiteSpace(m.LocationType))
            {
                return BadRequest(ErrorResponseDto.BadRequest("매핑의 location_type 이 비어 있습니다."));
            }
            if (m.LocationType != "table_cell" && m.LocationType != "paragraph")
            {
                return BadRequest(ErrorResponseDto.BadRequest(
                    "매핑의 location_type 은 'table_cell' 또는 'paragraph' 만 허용됩니다."));
            }
        }

        // Phase 10.x Medium 보강 — 원본 파일 미업로드 템플릿은 매핑 적용 불가.
        // DocUtil 측이 storage_path 기준으로 파일을 열어 매핑을 적용하므로 null 이면 즉시 차단.
        if (!await EnsureTemplateHasStorageAsync(templateId, ct))
        {
            return BadRequest(new ErrorResponseDto(
                "이 템플릿은 원본 파일이 업로드되지 않아 변수 매핑을 적용할 수 없습니다. 먼저 파일을 업로드하세요.",
                "DOCUTIL_TEMPLATE_NO_STORAGE",
                new { templateId, operation = "apply-mapping" }));
        }

        try
        {
            var updated = await _docUtilClient.ApplyDocumentTemplateMappingAsync(templateId, request, ct);
            _logger.LogInformation(
                "운영자 DocUtil 템플릿 매핑 적용 성공 - TemplateId={Id}, MappingCount={Count}",
                templateId, request.Mappings.Length);
            await InvalidateTemplatesCacheAsync();
            return Ok(updated);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 템플릿 매핑 적용 실패 (id={Id})", templateId);
            await InvalidateTemplatesCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "변수 매핑 적용에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 템플릿 파일 미리보기/다운로드 — DocUtil `/api/v1/templates/{template_id}/preview`.
    /// binary stream. 캐시 미적용. RFC 5987 한글 파일명 + ASCII fallback.
    /// </summary>
    [HttpGet("{templateId}/preview")]
    public async Task<IActionResult> Preview(string templateId, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("템플릿 식별자가 비어 있습니다."));
        }

        DocUtilDocumentTemplatePreview preview;
        try
        {
            preview = await _docUtilClient.PreviewDocumentTemplateAsync(templateId, ct);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 템플릿 미리보기 실패 (id={Id})", templateId);
            return StatusCode(502, new ErrorResponseDto(
                "템플릿 미리보기에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }

        // FileStreamResult 가 stream Dispose 책임. HttpResponseOwnedStream 이 응답/요청 lifetime 결합.
        var rawName = string.IsNullOrWhiteSpace(preview.FileName)
            ? $"template-{templateId}"
            : preview.FileName;
        var asciiFallback = ToAsciiSafe(rawName);
        var encoded = HttpUtility.UrlPathEncode(rawName);
        var disposition = $"attachment; filename=\"{asciiFallback}\"; filename*=UTF-8''{encoded}";

        Response.Headers["Content-Disposition"] = disposition;

        return new FileStreamResult(preview.Stream, preview.ContentType)
        {
            EnableRangeProcessing = false,
        };
    }

    // ──────────────────────────────────────────────────────────────────────
    // 헬퍼 — 사전 검증 (Phase 10.x Medium 보강)
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 템플릿이 원본 파일(TemplateStoragePath) 을 보유하고 있는지 확인.
    /// <para>
    /// convert / apply-mapping 은 원본 파일이 있어야 의미가 있는 작업이므로 사전에 차단한다.
    /// DocUtil 호출(GetDocumentTemplateAsync) 자체가 실패하면(404/5xx 등) false 가 아닌 예외로 전파
    /// → 호출자의 catch (InvalidOperationException) 분기가 502 로 응답.
    /// </para>
    /// <para>
    /// 캐시 namespace 와 일치하는 prefix(DetailCachePrefix) 로 short-circuit 확인 시도(캐시 hit 시
    /// DocUtil 추가 호출 없이 즉시 판정), miss 시 _docUtilClient.GetDocumentTemplateAsync 위임.
    /// </para>
    /// </summary>
    /// <returns>true = 원본 파일 보유, false = TemplateStoragePath 가 null/빈 문자열.</returns>
    private async Task<bool> EnsureTemplateHasStorageAsync(string templateId, CancellationToken ct)
    {
        // 캐시 short-circuit — Detail 캐시가 살아있으면 DocUtil 호출 없이 판정.
        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{DetailCachePrefix}v{version}:{templateId}";
        var cached = await _cachingService.GetAsync<CachedDocumentTemplateDto>(cacheKey);
        if (cached != null)
        {
            return !string.IsNullOrWhiteSpace(cached.TemplateStoragePath);
        }

        // 캐시 miss — DocUtil 호출. 404 등은 호출자의 InvalidOperationException catch 로 전파.
        var detail = await _docUtilClient.GetDocumentTemplateAsync(templateId, ct);
        if (detail == null)
        {
            // 404 — convert/apply-mapping 진입 자체가 무효. 호출자에서 InvalidOperationException 으로
            // 전파되도록 throw(EnsureSuccessOrThrowKoreanAsync 와 동일 패턴).
            throw new InvalidOperationException("템플릿을 찾을 수 없습니다.");
        }

        // detail 을 캐시에 저장 — 다음 호출 short-circuit.
        await _cachingService.SetAsync(cacheKey, CachedDocumentTemplateDto.From(detail), DetailCacheTtl);
        return !string.IsNullOrWhiteSpace(detail.TemplateStoragePath);
    }

    // ──────────────────────────────────────────────────────────────────────
    // 헬퍼 — RFC 5987 ASCII fallback
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
    // ConvertTemplate 요청 본문 — ai_analysis dict 한 필드
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// convert endpoint 요청 본문 wrapper — DocUtil 라우터의 body 형식 { "ai_analysis": {...} } 그대로.
    /// </summary>
    public sealed record ConvertTemplateRequest(
        IDictionary<string, object?> AiAnalysis);

    // ──────────────────────────────────────────────────────────────────────
    // 캐시 wrapper DTO (record 가 아닌 클래스 — System.Text.Json 캐시 시 deserialize 안정성)
    // ──────────────────────────────────────────────────────────────────────

    private sealed class CachedDocumentTemplateDto
    {
        public string Id { get; set; } = string.Empty;
        public string OrganizationId { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string? Description { get; set; }
        public string TemplateType { get; set; } = string.Empty;
        public string Tone { get; set; } = "formal";
        public string OutputFormat { get; set; } = string.Empty;
        public IDictionary<string, object?>? Schema { get; set; }
        public string? SamplePrompt { get; set; }
        public bool IsActive { get; set; }
        public string CreatedBy { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }
        public string? TemplateStoragePath { get; set; }
        public IDictionary<string, object?>? Jinja2Variables { get; set; }
        public string RenderingMode { get; set; } = "jinja2";
        public IDictionary<string, object?>? ImageGenerationConfig { get; set; }

        public static CachedDocumentTemplateDto From(DocUtilDocumentTemplate t) => new()
        {
            Id = t.Id,
            OrganizationId = t.OrganizationId,
            Name = t.Name,
            Description = t.Description,
            TemplateType = t.TemplateType,
            Tone = t.Tone,
            OutputFormat = t.OutputFormat,
            Schema = t.Schema,
            SamplePrompt = t.SamplePrompt,
            IsActive = t.IsActive,
            CreatedBy = t.CreatedBy,
            CreatedAt = t.CreatedAt,
            UpdatedAt = t.UpdatedAt,
            TemplateStoragePath = t.TemplateStoragePath,
            Jinja2Variables = t.Jinja2Variables,
            RenderingMode = t.RenderingMode,
            ImageGenerationConfig = t.ImageGenerationConfig,
        };

        public static CachedDocumentTemplateDto From(DocUtilDocumentTemplateDetail d) => new()
        {
            Id = d.Id,
            OrganizationId = d.OrganizationId,
            Name = d.Name,
            Description = d.Description,
            TemplateType = d.TemplateType,
            Tone = d.Tone,
            OutputFormat = d.OutputFormat,
            Schema = d.Schema,
            SamplePrompt = d.SamplePrompt,
            IsActive = d.IsActive,
            CreatedBy = d.CreatedBy,
            CreatedAt = d.CreatedAt,
            UpdatedAt = d.UpdatedAt,
            TemplateStoragePath = d.TemplateStoragePath,
            Jinja2Variables = d.Jinja2Variables,
            RenderingMode = d.RenderingMode,
            ImageGenerationConfig = d.ImageGenerationConfig,
        };

        public DocUtilDocumentTemplate ToTemplate() => new(
            Id, OrganizationId, Name, Description, TemplateType, Tone, OutputFormat,
            Schema, SamplePrompt, IsActive, CreatedBy, CreatedAt, UpdatedAt,
            TemplateStoragePath, Jinja2Variables, RenderingMode, ImageGenerationConfig);

        public DocUtilDocumentTemplateDetail ToRecord() => new(
            Id, OrganizationId, Name, Description, TemplateType, Tone, OutputFormat,
            Schema, SamplePrompt, IsActive, CreatedBy, CreatedAt, UpdatedAt,
            TemplateStoragePath, Jinja2Variables, RenderingMode, ImageGenerationConfig);
    }

    private sealed class CachedDocumentTemplateListDto
    {
        public CachedDocumentTemplateDto[] Items { get; set; } = Array.Empty<CachedDocumentTemplateDto>();
        public long Total { get; set; }
        public int Page { get; set; }
        public int Size { get; set; }

        public static CachedDocumentTemplateListDto From(DocUtilDocumentTemplateList list) => new()
        {
            Items = list.Items.Select(CachedDocumentTemplateDto.From).ToArray(),
            Total = list.Total,
            Page = list.Page,
            Size = list.Size,
        };

        public DocUtilDocumentTemplateList ToRecord() => new(
            Items.Select(c => c.ToTemplate()).ToArray(),
            Total, Page, Size);
    }

    private sealed class CachedVariableDto
    {
        public string Name { get; set; } = string.Empty;
        public string VarType { get; set; } = "string";
        public string? Label { get; set; }
        public string? Description { get; set; }
        public bool Required { get; set; } = true;
        public string Category { get; set; } = "ai_generated";

        public static CachedVariableDto From(DocUtilDocumentTemplateVariable v) => new()
        {
            Name = v.Name,
            VarType = v.VarType,
            Label = v.Label,
            Description = v.Description,
            Required = v.Required,
            Category = v.Category,
        };

        public DocUtilDocumentTemplateVariable ToRecord() => new(
            Name, VarType, Label, Description, Required, Category);
    }

    private sealed class CachedVariablesDto
    {
        public CachedVariableDto[] Items { get; set; } = Array.Empty<CachedVariableDto>();

        public static CachedVariablesDto From(IEnumerable<DocUtilDocumentTemplateVariable> vars) => new()
        {
            Items = vars.Select(CachedVariableDto.From).ToArray(),
        };

        public List<DocUtilDocumentTemplateVariable> ToList() =>
            Items.Select(v => v.ToRecord()).ToList();
    }
}
