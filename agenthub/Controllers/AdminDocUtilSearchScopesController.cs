using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilSearchScopesController — DocUtil 검색범위 운영자 BFF (Phase 10.2b)
//
// 통합 비전(P1 Control Plane / P5 인증 / R2 단일 진입점 / P8 RAG 단일 권위):
//   AgentHub 운영자 콘솔이 DocUtil 의 검색범위(Search Scopes) — 프로젝트/보드/폴더
//   단위 RAG 튜닝 + 4 기능 토글(Chatbot/QA/Keyword/Agent) + 환경 설정 — 을
//   단일 진입점에서 관리. Phase 10.1/10.2a 와 동일 BFF 패턴 적용.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//   2. TTL 캐시 분리:
//      - `du:scopes:` (10분 TTL) + version-key invalidate (`docutil-search-scopes`)
//      - `du:scopes:locations:` / `du:scopes:options:` (30분 TTL) — 카탈로그성 데이터
//   3. DocUtil DTO → JSON camelCase 직렬화(Program.cs JsonNamingPolicy 적용)
//   4. 4xx/5xx → 502 ErrorResponseDto 한국어 매핑(InvalidOperationException 변환)
//   5. mutation(POST/PUT/DELETE) 의 성공/실패 모두 invalidate (10.1b ghost 처리 패턴)
//
// 캐시 namespace 분리 사유:
//   `docutil-collections` (Phase 10.1c) 와는 분리 — search-scopes 와 collections 는
//   의미적으로 무관한 데이터 도메인. 본 컨트롤러는 자체 namespace `docutil-search-scopes`.
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 DocUtil 검색범위 관리 BFF — Phase 10.2b.
/// AgentHub Vue 콘솔의 `/admin/docutil-search-scopes` 페이지가 호출하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/docutil/search-scopes")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminDocUtilSearchScopesController : ControllerBase
{
    private const string CacheKeyPrefix = "du:scopes:";
    public const string CacheVersionNamespace = "docutil-search-scopes";
    private static readonly TimeSpan CacheTtl = TimeSpan.FromMinutes(10);
    // Locations / Options 는 카탈로그성 — 변동 거의 없음. 30분 TTL + version-key 미적용(별도 namespace 도 미사용).
    private static readonly TimeSpan CatalogCacheTtl = TimeSpan.FromMinutes(30);

    private readonly IDocUtilClient _docUtilClient;
    private readonly CachingService _cachingService;
    private readonly ILogger<AdminDocUtilSearchScopesController> _logger;

    public AdminDocUtilSearchScopesController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        ILogger<AdminDocUtilSearchScopesController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _logger = logger;
    }

    /// <summary>
    /// 검색범위 캐시 일괄 무효화 — version-key 패턴.
    /// mutation(검색범위 생성/수정/삭제/환경 변경) 의 성공/실패 모두 호출(10.1b ghost 정합성 보장).
    /// 실패는 swallow + 경고 로그(캐시 무효화는 best-effort).
    /// </summary>
    private async Task InvalidateSearchScopesCacheAsync()
    {
        try
        {
            var v = await _cachingService.IncrementVersionAsync(CacheVersionNamespace);
            _logger.LogInformation("DocUtil 검색범위 캐시 invalidate - newVersion={V}", v);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "DocUtil 검색범위 캐시 invalidate 실패(무시)");
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 검색범위 — GET 목록 / GET 옵션 / GET 위치 카탈로그 / POST / GET 상세 / PUT / DELETE / PUT environment / GET valid-id
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 검색범위 목록(페이징) — DocUtil `/api/v1/search-scopes` 위임 + TTL 캐시.
    /// </summary>
    [HttpGet("")]
    public async Task<ActionResult<DocUtilSearchScopeList>> ListSearchScopes(
        [FromQuery] int page = 1,
        [FromQuery] int size = 20,
        CancellationToken ct = default)
    {
        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{CacheKeyPrefix}v{version}:list:{page}|{size}";

        var cached = await _cachingService.GetAsync<CachedSearchScopeListDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 검색범위 목록 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 검색범위 목록 캐시 miss - key={Key}", cacheKey);

        try
        {
            var list = await _docUtilClient.ListSearchScopesAsync(page, size, ct);
            await _cachingService.SetAsync(cacheKey, CachedSearchScopeListDto.From(list), CacheTtl);
            return Ok(list);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 검색범위 목록 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 검색범위 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 검색범위 옵션 목록(드롭다운용) — DocUtil `/api/v1/search-scopes/options` 위임 + 30분 캐시.
    /// </summary>
    [HttpGet("options")]
    public async Task<ActionResult<List<DocUtilSearchScopeOption>>> ListSearchScopeOptions(
        CancellationToken ct = default)
    {
        var cacheKey = $"{CacheKeyPrefix}options";
        var cached = await _cachingService.GetAsync<CachedSearchScopeOptionListDto>(cacheKey);
        if (cached?.Items != null)
        {
            _logger.LogDebug("DocUtil 검색범위 옵션 캐시 hit - key={Key}, count={Count}", cacheKey, cached.Items.Length);
            return Ok(cached.Items.ToList());
        }

        try
        {
            var options = await _docUtilClient.ListSearchScopeOptionsAsync(ct);
            await _cachingService.SetAsync(
                cacheKey,
                new CachedSearchScopeOptionListDto { Items = options.ToArray() },
                CatalogCacheTtl);
            return Ok(options);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 검색범위 옵션 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 검색범위 옵션을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 위치 카탈로그(검색범위 할당 가능한 프로젝트/보드/폴더) — DocUtil `/api/v1/search-scopes/locations` 위임 + 30분 캐시.
    /// <para>locationType 은 필수 query parameter — "project" | "board" | "folder".</para>
    /// </summary>
    [HttpGet("locations")]
    public async Task<ActionResult<List<DocUtilLocationOption>>> ListSearchScopeLocations(
        [FromQuery(Name = "locationType")] string locationType,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(locationType))
        {
            return BadRequest(ErrorResponseDto.BadRequest("locationType 파라미터가 비어 있습니다 (project/board/folder 중 하나)."));
        }
        var typeKey = locationType.Trim().ToLowerInvariant();
        if (typeKey != "project" && typeKey != "board" && typeKey != "folder")
        {
            return BadRequest(ErrorResponseDto.BadRequest("locationType 은 project / board / folder 중 하나여야 합니다."));
        }

        var cacheKey = $"{CacheKeyPrefix}locations:{typeKey}";
        var cached = await _cachingService.GetAsync<CachedLocationOptionListDto>(cacheKey);
        if (cached?.Items != null)
        {
            _logger.LogDebug("DocUtil 위치 카탈로그 캐시 hit - key={Key}, count={Count}", cacheKey, cached.Items.Length);
            return Ok(cached.Items.ToList());
        }

        try
        {
            var locations = await _docUtilClient.ListSearchScopeLocationsAsync(typeKey, ct);
            await _cachingService.SetAsync(
                cacheKey,
                new CachedLocationOptionListDto { Items = locations.ToArray() },
                CatalogCacheTtl);
            return Ok(locations);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 위치 카탈로그 조회 실패 (type={Type})", typeKey);
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 위치 카탈로그를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 검색범위 신규 생성 — DocUtil `/api/v1/search-scopes` (POST). 성공 시 캐시 일괄 무효화.
    /// </summary>
    [HttpPost("")]
    public async Task<ActionResult<DocUtilSearchScopeDetail>> CreateSearchScope(
        [FromBody] DocUtilCreateScopeRequest request,
        CancellationToken ct = default)
    {
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            return BadRequest(ErrorResponseDto.BadRequest("검색범위 이름이 비어 있습니다."));
        }
        if (request.Name.Length > 255)
        {
            return BadRequest(ErrorResponseDto.BadRequest("검색범위 이름은 255자 이하여야 합니다."));
        }
        if (request.Description != null && request.Description.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("검색범위 설명은 2000자 이하여야 합니다."));
        }

        try
        {
            var created = await _docUtilClient.CreateSearchScopeAsync(request, ct);
            _logger.LogInformation("운영자 DocUtil 검색범위 생성 성공 - ScopeId={Id}, Name={Name}", created.Id, created.Name);
            await InvalidateSearchScopesCacheAsync();
            return CreatedAtAction(nameof(GetSearchScope), new { scopeId = created.Id }, created);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 검색범위 생성 실패 (name={Name})", request.Name);
            await InvalidateSearchScopesCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "검색범위 생성에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 검색범위 상세 조회 — DocUtil `/api/v1/search-scopes/{scope_id}` 위임 + TTL 캐시.
    /// 404 응답은 한국어 ErrorResponseDto 로 정규화.
    /// </summary>
    [HttpGet("{scopeId}")]
    public async Task<ActionResult<DocUtilSearchScopeDetail>> GetSearchScope(
        string scopeId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(scopeId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("검색범위 식별자가 비어 있습니다."));
        }

        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{CacheKeyPrefix}v{version}:detail:{scopeId}";

        var cached = await _cachingService.GetAsync<CachedSearchScopeDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 검색범위 상세 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 검색범위 상세 캐시 miss - key={Key}", cacheKey);

        try
        {
            var detail = await _docUtilClient.GetSearchScopeAsync(scopeId, ct);
            if (detail == null)
            {
                return NotFound(ErrorResponseDto.NotFound("검색범위를 찾을 수 없습니다."));
            }
            await _cachingService.SetAsync(cacheKey, CachedSearchScopeDto.From(detail), CacheTtl);
            return Ok(detail);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 검색범위 상세 조회 실패 (id={Id})", scopeId);
            return StatusCode(502, new ErrorResponseDto(
                "검색범위 상세를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 검색범위 수정 — DocUtil `/api/v1/search-scopes/{scope_id}` (PUT). 성공/실패 모두 캐시 일괄 무효화.
    /// </summary>
    [HttpPut("{scopeId}")]
    public async Task<ActionResult<DocUtilSearchScopeDetail>> UpdateSearchScope(
        string scopeId,
        [FromBody] DocUtilUpdateScopeRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(scopeId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("검색범위 식별자가 비어 있습니다."));
        }
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (request.Name != null && (request.Name.Length == 0 || request.Name.Length > 255))
        {
            return BadRequest(ErrorResponseDto.BadRequest("검색범위 이름은 1~255자여야 합니다."));
        }
        if (request.Description != null && request.Description.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("검색범위 설명은 2000자 이하여야 합니다."));
        }

        try
        {
            var updated = await _docUtilClient.UpdateSearchScopeAsync(scopeId, request, ct);
            _logger.LogInformation("운영자 DocUtil 검색범위 수정 성공 - ScopeId={Id}", updated.Id);
            await InvalidateSearchScopesCacheAsync();
            return Ok(updated);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 검색범위 수정 실패 (id={Id})", scopeId);
            await InvalidateSearchScopesCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "검색범위 수정에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 검색범위 삭제 — DocUtil `/api/v1/search-scopes/{scope_id}` (DELETE). 성공/실패 모두 invalidate.
    /// </summary>
    [HttpDelete("{scopeId}")]
    public async Task<IActionResult> DeleteSearchScope(string scopeId, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(scopeId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("검색범위 식별자가 비어 있습니다."));
        }

        try
        {
            await _docUtilClient.DeleteSearchScopeAsync(scopeId, ct);
            _logger.LogInformation("운영자 DocUtil 검색범위 삭제 성공 - ScopeId={Id}", scopeId);
            await InvalidateSearchScopesCacheAsync();
            return NoContent();
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 검색범위 삭제 실패 (id={Id})", scopeId);
            await InvalidateSearchScopesCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "검색범위 삭제에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 검색범위 환경 설정 — DocUtil `/api/v1/search-scopes/{scope_id}/environment` (PUT). 성공/실패 모두 invalidate.
    /// </summary>
    [HttpPut("{scopeId}/environment")]
    public async Task<ActionResult<DocUtilSearchScopeDetail>> UpdateSearchScopeEnvironment(
        string scopeId,
        [FromBody] DocUtilUpdateScopeEnvironmentRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(scopeId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("검색범위 식별자가 비어 있습니다."));
        }
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }

        // 가중치 sum 검증 (DocUtil 내부 validation 외에 사전 차단 — title+keyword+content 합)
        if (request.TitleWeight.HasValue && (request.TitleWeight.Value < 0 || request.TitleWeight.Value > 1))
        {
            return BadRequest(ErrorResponseDto.BadRequest("title_weight 는 0~1 범위여야 합니다."));
        }
        if (request.KeywordWeight.HasValue && (request.KeywordWeight.Value < 0 || request.KeywordWeight.Value > 1))
        {
            return BadRequest(ErrorResponseDto.BadRequest("keyword_weight 는 0~1 범위여야 합니다."));
        }
        if (request.ContentWeight.HasValue && (request.ContentWeight.Value < 0 || request.ContentWeight.Value > 1))
        {
            return BadRequest(ErrorResponseDto.BadRequest("content_weight 는 0~1 범위여야 합니다."));
        }
        if (request.SimilarityThreshold.HasValue && (request.SimilarityThreshold.Value < 0 || request.SimilarityThreshold.Value > 1))
        {
            return BadRequest(ErrorResponseDto.BadRequest("similarity_threshold 는 0~1 범위여야 합니다."));
        }

        try
        {
            var updated = await _docUtilClient.UpdateSearchScopeEnvironmentAsync(scopeId, request, ct);
            _logger.LogInformation("운영자 DocUtil 검색범위 환경 수정 성공 - ScopeId={Id}", updated.Id);
            await InvalidateSearchScopesCacheAsync();
            return Ok(updated);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 검색범위 환경 수정 실패 (id={Id})", scopeId);
            await InvalidateSearchScopesCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "검색범위 환경 설정 변경에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 검색범위 valid-id 조회 — DocUtil `/api/v1/search-scopes/{scope_id}/valid-id`.
    /// <para>임베드 위젯의 scope_id 검증용. 응답은 free-form dict.</para>
    /// </summary>
    [HttpGet("{scopeId}/valid-id")]
    public async Task<ActionResult<IDictionary<string, object?>>> GetSearchScopeValidId(
        string scopeId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(scopeId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("검색범위 식별자가 비어 있습니다."));
        }

        try
        {
            var resp = await _docUtilClient.GetSearchScopeValidIdAsync(scopeId, ct);
            return Ok(resp.Data);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 검색범위 valid-id 조회 실패 (id={Id})", scopeId);
            return StatusCode(502, new ErrorResponseDto(
                "검색범위 valid-id 조회에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 캐시 wrapper DTO (record 직렬화 안정성 — Search/Project 와 동일 패턴)
    // ──────────────────────────────────────────────────────────────────────

    private sealed class CachedSearchScopeDto
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string? Description { get; set; }
        public string OrganizationId { get; set; } = string.Empty;
        public string CreatedBy { get; set; } = string.Empty;
        public string? ProjectId { get; set; }
        public string? BoardId { get; set; }
        public string? FolderId { get; set; }
        public string? LocationPath { get; set; }
        public bool ChatbotEnabled { get; set; }
        public string? ChatbotFaqTemplate { get; set; }
        public bool QaEnabled { get; set; }
        public string? QaPromptTemplate { get; set; }
        public string? QaLlmModel { get; set; }
        public bool KeywordSearchEnabled { get; set; }
        public bool AgentEnabled { get; set; }
        public int ChunkSize { get; set; }
        public int ChunkOverlap { get; set; }
        public double TitleWeight { get; set; }
        public double KeywordWeight { get; set; }
        public double ContentWeight { get; set; }
        public int MaxResults { get; set; }
        public double SimilarityThreshold { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }

        public static CachedSearchScopeDto From(DocUtilSearchScopeDetail d) => new()
        {
            Id = d.Id,
            Name = d.Name,
            Description = d.Description,
            OrganizationId = d.OrganizationId,
            CreatedBy = d.CreatedBy,
            ProjectId = d.ProjectId,
            BoardId = d.BoardId,
            FolderId = d.FolderId,
            LocationPath = d.LocationPath,
            ChatbotEnabled = d.ChatbotEnabled,
            ChatbotFaqTemplate = d.ChatbotFaqTemplate,
            QaEnabled = d.QaEnabled,
            QaPromptTemplate = d.QaPromptTemplate,
            QaLlmModel = d.QaLlmModel,
            KeywordSearchEnabled = d.KeywordSearchEnabled,
            AgentEnabled = d.AgentEnabled,
            ChunkSize = d.ChunkSize,
            ChunkOverlap = d.ChunkOverlap,
            TitleWeight = d.TitleWeight,
            KeywordWeight = d.KeywordWeight,
            ContentWeight = d.ContentWeight,
            MaxResults = d.MaxResults,
            SimilarityThreshold = d.SimilarityThreshold,
            CreatedAt = d.CreatedAt,
            UpdatedAt = d.UpdatedAt,
        };

        public DocUtilSearchScopeDetail ToRecord() => new(
            Id, Name, Description, OrganizationId, CreatedBy,
            ProjectId, BoardId, FolderId, LocationPath,
            ChatbotEnabled, ChatbotFaqTemplate, QaEnabled, QaPromptTemplate, QaLlmModel,
            KeywordSearchEnabled, AgentEnabled,
            ChunkSize, ChunkOverlap, TitleWeight, KeywordWeight, ContentWeight,
            MaxResults, SimilarityThreshold, CreatedAt, UpdatedAt);

        public DocUtilSearchScopeSummary ToSummary() => new(
            Id, Name, Description, OrganizationId, CreatedBy,
            ProjectId, BoardId, FolderId, LocationPath,
            ChatbotEnabled, ChatbotFaqTemplate, QaEnabled, QaPromptTemplate, QaLlmModel,
            KeywordSearchEnabled, AgentEnabled,
            ChunkSize, ChunkOverlap, TitleWeight, KeywordWeight, ContentWeight,
            MaxResults, SimilarityThreshold, CreatedAt, UpdatedAt);

        public static CachedSearchScopeDto From(DocUtilSearchScopeSummary s) => new()
        {
            Id = s.Id,
            Name = s.Name,
            Description = s.Description,
            OrganizationId = s.OrganizationId,
            CreatedBy = s.CreatedBy,
            ProjectId = s.ProjectId,
            BoardId = s.BoardId,
            FolderId = s.FolderId,
            LocationPath = s.LocationPath,
            ChatbotEnabled = s.ChatbotEnabled,
            ChatbotFaqTemplate = s.ChatbotFaqTemplate,
            QaEnabled = s.QaEnabled,
            QaPromptTemplate = s.QaPromptTemplate,
            QaLlmModel = s.QaLlmModel,
            KeywordSearchEnabled = s.KeywordSearchEnabled,
            AgentEnabled = s.AgentEnabled,
            ChunkSize = s.ChunkSize,
            ChunkOverlap = s.ChunkOverlap,
            TitleWeight = s.TitleWeight,
            KeywordWeight = s.KeywordWeight,
            ContentWeight = s.ContentWeight,
            MaxResults = s.MaxResults,
            SimilarityThreshold = s.SimilarityThreshold,
            CreatedAt = s.CreatedAt,
            UpdatedAt = s.UpdatedAt,
        };
    }

    private sealed class CachedSearchScopeListDto
    {
        public CachedSearchScopeDto[] Items { get; set; } = Array.Empty<CachedSearchScopeDto>();
        public long Total { get; set; }
        public int Page { get; set; }
        public int Size { get; set; }

        public static CachedSearchScopeListDto From(DocUtilSearchScopeList l) => new()
        {
            Items = l.Items.Select(CachedSearchScopeDto.From).ToArray(),
            Total = l.Total,
            Page = l.Page,
            Size = l.Size,
        };

        public DocUtilSearchScopeList ToRecord() => new(
            Items.Select(c => c.ToSummary()).ToArray(),
            Total,
            Page,
            Size);
    }

    private sealed class CachedSearchScopeOptionListDto
    {
        public DocUtilSearchScopeOption[]? Items { get; set; }
    }

    private sealed class CachedLocationOptionListDto
    {
        public DocUtilLocationOption[]? Items { get; set; }
    }
}
