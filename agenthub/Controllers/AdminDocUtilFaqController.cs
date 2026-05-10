using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilFaqController — DocUtil FAQ 운영자 BFF (Phase 10.2c)
//
// 통합 비전(P1 Control Plane / P5 인증 / R2 단일 진입점):
//   AgentHub 운영자 콘솔이 DocUtil 의 FAQ(질문/답변 카탈로그) — 페이징/검색/카테고리/스코프 필터 +
//   생성/수정/삭제 — 까지 단일 진입점에서 운영. Phase 10.1/10.2a/10.2b 와 동일 BFF 패턴.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//   2. TTL 캐시 + version-key invalidate (5분 TTL):
//      - prefix `du:faq:`, version namespace `docutil-faq`
//      - mutation 성공/실패 모두 invalidate (10.1b ghost 처리 패턴)
//   3. 4xx/5xx → 502 ErrorResponseDto 한국어 매핑
//
// 캐시 namespace 격리:
//   `docutil-search-scopes` / `docutil-collections` 등 다른 도메인과 의도적 분리.
//   FAQ 가 search-scope 에 바인딩되어도 invalidate 가 cascade 되지 않음 — 콘솔 새로고침
//   시 5분 TTL 자연 expire 로 일관성 회복(아니면 명시적으로 재호출).
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 DocUtil FAQ 관리 BFF — Phase 10.2c.
/// AgentHub Vue 콘솔의 `/admin/docutil-faq` 페이지가 호출하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/docutil/faq")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminDocUtilFaqController : ControllerBase
{
    private const string CacheKeyPrefix = "du:faq:";
    public const string CacheVersionNamespace = "docutil-faq";
    private static readonly TimeSpan CacheTtl = TimeSpan.FromMinutes(5);

    private readonly IDocUtilClient _docUtilClient;
    private readonly CachingService _cachingService;
    private readonly ILogger<AdminDocUtilFaqController> _logger;

    public AdminDocUtilFaqController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        ILogger<AdminDocUtilFaqController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _logger = logger;
    }

    /// <summary>
    /// FAQ 캐시 일괄 무효화 — version-key 패턴.
    /// mutation 성공/실패 모두 호출(10.1b ghost 정합성 보장).
    /// 실패는 swallow + 경고 로그(캐시 무효화는 best-effort).
    /// </summary>
    private async Task InvalidateFaqCacheAsync()
    {
        try
        {
            var v = await _cachingService.IncrementVersionAsync(CacheVersionNamespace);
            _logger.LogInformation("DocUtil FAQ 캐시 invalidate - newVersion={V}", v);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "DocUtil FAQ 캐시 invalidate 실패(무시)");
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // FAQ — GET 목록 / POST / GET 상세 / PUT / DELETE
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// FAQ 목록(페이징 + 필터) — DocUtil `/api/v1/faq` 위임 + 5분 캐시.
    /// </summary>
    /// <param name="page">페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 20, 1~100).</param>
    /// <param name="scopeId">검색 범위 필터(UUID, 선택).</param>
    /// <param name="category">카테고리 필터(선택).</param>
    /// <param name="q">질문/답변 텍스트 검색(선택).</param>
    [HttpGet("")]
    public async Task<ActionResult<DocUtilFaqList>> ListFaqs(
        [FromQuery] int page = 1,
        [FromQuery] int size = 20,
        [FromQuery] string? scopeId = null,
        [FromQuery] string? category = null,
        [FromQuery] string? q = null,
        CancellationToken ct = default)
    {
        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        // q/scopeId/category 가 너무 길면 cache key 폭발 — 정규화(공백 제거 + 소문자) 후 해시 대체.
        string Normalize(string? s) => string.IsNullOrWhiteSpace(s) ? "_" : s.Trim().ToLowerInvariant();
        var cacheKey = $"{CacheKeyPrefix}v{version}:list:{page}|{size}|{Normalize(scopeId)}|{Normalize(category)}|{Normalize(q)}";

        var cached = await _cachingService.GetAsync<CachedFaqListDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil FAQ 목록 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil FAQ 목록 캐시 miss - key={Key}", cacheKey);

        try
        {
            var list = await _docUtilClient.ListFaqsAsync(page, size, scopeId, category, q, ct);
            await _cachingService.SetAsync(cacheKey, CachedFaqListDto.From(list), CacheTtl);
            return Ok(list);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil FAQ 목록 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil FAQ 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// FAQ 신규 생성 — DocUtil `/api/v1/faq` (POST). 성공/실패 모두 캐시 일괄 무효화.
    /// </summary>
    [HttpPost("")]
    public async Task<ActionResult<DocUtilFaqDetail>> CreateFaq(
        [FromBody] DocUtilCreateFaqRequest request,
        CancellationToken ct = default)
    {
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(request.Question))
        {
            return BadRequest(ErrorResponseDto.BadRequest("질문이 비어 있습니다."));
        }
        if (request.Question.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("질문은 2000자 이하여야 합니다."));
        }
        if (string.IsNullOrWhiteSpace(request.Answer))
        {
            return BadRequest(ErrorResponseDto.BadRequest("답변이 비어 있습니다."));
        }
        if (request.Category != null && request.Category.Length > 128)
        {
            return BadRequest(ErrorResponseDto.BadRequest("카테고리는 128자 이하여야 합니다."));
        }

        try
        {
            var created = await _docUtilClient.CreateFaqAsync(request, ct);
            _logger.LogInformation("운영자 DocUtil FAQ 생성 성공 - FaqId={Id}", created.Id);
            await InvalidateFaqCacheAsync();
            return CreatedAtAction(nameof(GetFaq), new { faqId = created.Id }, created);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil FAQ 생성 실패");
            await InvalidateFaqCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "FAQ 생성에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// FAQ 상세 조회 — DocUtil `/api/v1/faq/{faq_id}` 위임 + 5분 캐시.
    /// 404 응답은 한국어 ErrorResponseDto 로 정규화.
    /// </summary>
    [HttpGet("{faqId}")]
    public async Task<ActionResult<DocUtilFaqDetail>> GetFaq(
        string faqId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(faqId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("FAQ 식별자가 비어 있습니다."));
        }

        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{CacheKeyPrefix}v{version}:detail:{faqId}";

        var cached = await _cachingService.GetAsync<CachedFaqDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil FAQ 상세 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil FAQ 상세 캐시 miss - key={Key}", cacheKey);

        try
        {
            var detail = await _docUtilClient.GetFaqAsync(faqId, ct);
            if (detail == null)
            {
                return NotFound(ErrorResponseDto.NotFound("FAQ 를 찾을 수 없습니다."));
            }
            await _cachingService.SetAsync(cacheKey, CachedFaqDto.From(detail), CacheTtl);
            return Ok(detail);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil FAQ 상세 조회 실패 (id={Id})", faqId);
            return StatusCode(502, new ErrorResponseDto(
                "FAQ 상세를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// FAQ 수정 — DocUtil `/api/v1/faq/{faq_id}` (PUT). 성공/실패 모두 캐시 일괄 무효화.
    /// </summary>
    [HttpPut("{faqId}")]
    public async Task<ActionResult<DocUtilFaqDetail>> UpdateFaq(
        string faqId,
        [FromBody] DocUtilUpdateFaqRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(faqId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("FAQ 식별자가 비어 있습니다."));
        }
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (request.Question != null && request.Question.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("질문은 2000자 이하여야 합니다."));
        }
        if (request.Category != null && request.Category.Length > 128)
        {
            return BadRequest(ErrorResponseDto.BadRequest("카테고리는 128자 이하여야 합니다."));
        }

        try
        {
            var updated = await _docUtilClient.UpdateFaqAsync(faqId, request, ct);
            _logger.LogInformation("운영자 DocUtil FAQ 수정 성공 - FaqId={Id}", updated.Id);
            await InvalidateFaqCacheAsync();
            return Ok(updated);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil FAQ 수정 실패 (id={Id})", faqId);
            await InvalidateFaqCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "FAQ 수정에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// FAQ 삭제 — DocUtil `/api/v1/faq/{faq_id}` (DELETE). 성공/실패 모두 invalidate.
    /// </summary>
    [HttpDelete("{faqId}")]
    public async Task<IActionResult> DeleteFaq(string faqId, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(faqId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("FAQ 식별자가 비어 있습니다."));
        }

        try
        {
            await _docUtilClient.DeleteFaqAsync(faqId, ct);
            _logger.LogInformation("운영자 DocUtil FAQ 삭제 성공 - FaqId={Id}", faqId);
            await InvalidateFaqCacheAsync();
            return NoContent();
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil FAQ 삭제 실패 (id={Id})", faqId);
            await InvalidateFaqCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "FAQ 삭제에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 캐시 wrapper DTO (record 가 아닌 클래스 — System.Text.Json 캐시 시 deserialize 안정성).
    // ──────────────────────────────────────────────────────────────────────

    private sealed class CachedFaqDto
    {
        public string Id { get; set; } = string.Empty;
        public string? SearchScopeId { get; set; }
        public string OrganizationId { get; set; } = string.Empty;
        public string Question { get; set; } = string.Empty;
        public string Answer { get; set; } = string.Empty;
        public string? Category { get; set; }
        public int DisplayOrder { get; set; }
        public bool IsActive { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }

        public static CachedFaqDto From(DocUtilFaq f) => new()
        {
            Id = f.Id,
            SearchScopeId = f.SearchScopeId,
            OrganizationId = f.OrganizationId,
            Question = f.Question,
            Answer = f.Answer,
            Category = f.Category,
            DisplayOrder = f.DisplayOrder,
            IsActive = f.IsActive,
            CreatedAt = f.CreatedAt,
            UpdatedAt = f.UpdatedAt,
        };

        public static CachedFaqDto From(DocUtilFaqDetail d) => new()
        {
            Id = d.Id,
            SearchScopeId = d.SearchScopeId,
            OrganizationId = d.OrganizationId,
            Question = d.Question,
            Answer = d.Answer,
            Category = d.Category,
            DisplayOrder = d.DisplayOrder,
            IsActive = d.IsActive,
            CreatedAt = d.CreatedAt,
            UpdatedAt = d.UpdatedAt,
        };

        public DocUtilFaq ToFaq() => new(
            Id, SearchScopeId, OrganizationId, Question, Answer,
            Category, DisplayOrder, IsActive, CreatedAt, UpdatedAt);

        public DocUtilFaqDetail ToRecord() => new(
            Id, SearchScopeId, OrganizationId, Question, Answer,
            Category, DisplayOrder, IsActive, CreatedAt, UpdatedAt);
    }

    private sealed class CachedFaqListDto
    {
        public CachedFaqDto[] Items { get; set; } = Array.Empty<CachedFaqDto>();
        public long Total { get; set; }
        public int Page { get; set; }
        public int Size { get; set; }

        public static CachedFaqListDto From(DocUtilFaqList list) => new()
        {
            Items = list.Items.Select(CachedFaqDto.From).ToArray(),
            Total = list.Total,
            Page = list.Page,
            Size = list.Size,
        };

        public DocUtilFaqList ToRecord() => new(
            Items.Select(c => c.ToFaq()).ToArray(),
            Total, Page, Size);
    }
}
