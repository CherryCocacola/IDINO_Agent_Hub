using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilSearchTestController — DocUtil 검색 테스트 운영자 BFF (트랙 A1 Phase B)
//
// 통합 비전 (P1 Control Plane / P5 인증 / R2 단일 진입점):
//   AgentHub 운영자 콘솔이 DocUtil 의 검색 품질 평가 화면(`/search-test`) 을 단일 진입점에서 운영.
//   하이브리드/챗봇/QA/키워드/관리자 테스트 5가지 모드 + 이력 + 검색 범위 옵션 dropdown 까지 흡수.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//      DocUtil `/search/test` 는 RequireAdmin 강제 — visibility bypass (as_user_view=False) 모드.
//      그 외 검색 endpoint 는 사용자 진입점이지만 운영자 화면이므로 동일 권한.
//   2. 검색 결과는 BFF 캐시 X — 사용자 입력별 1회성, 캐시하면 변경된 KB 가 즉시 반영되지 않음.
//      search/history 만 짧은 TTL(30초) 캐시.
//   3. 4xx/5xx → 502 ErrorResponseDto 한국어 매핑.
//
// 캐시 namespace 격리:
//   `docutil-search-test-history` — 다른 도메인(FAQ/Reports/Templates/Search-scopes/Settings)과 분리.
//   검색 이력은 사용자별 데이터지만 BFF 캐시는 version-prefix 만 사용(키 폭발 회피 — page/size 조합당 1개).
//
// search-scopes dropdown 옵션:
//   기존 ListSearchScopeOptionsAsync() 재사용 — `/api/admin/docutil/search-test/scopes` endpoint 로 노출.
//   별도 캐시 무효화는 search-scopes 자체 namespace(`docutil-search-scopes`) 에서 관리(여기서 X).
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 DocUtil 검색 테스트 BFF — 트랙 A1 Phase B.
/// AgentHub Vue 콘솔의 `/admin/docutil-search-test` 페이지가 호출하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/docutil/search-test")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminDocUtilSearchTestController : ControllerBase
{
    private const string HistoryCacheKeyPrefix = "du:search-test-history:";
    public const string HistoryCacheVersionNamespace = "docutil-search-test-history";
    private static readonly TimeSpan HistoryCacheTtl = TimeSpan.FromSeconds(30);

    private readonly IDocUtilClient _docUtilClient;
    private readonly CachingService _cachingService;
    private readonly ILogger<AdminDocUtilSearchTestController> _logger;

    public AdminDocUtilSearchTestController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        ILogger<AdminDocUtilSearchTestController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _logger = logger;
    }

    // ──────────────────────────────────────────────────────────────────────
    // 검색 5종 (POST) — 캐시 없음, 1회성
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 하이브리드 검색 실행 — DocUtil `/api/v1/search` 위임(as_user_view=True).
    /// </summary>
    [HttpPost("hybrid")]
    public async Task<ActionResult<DocUtilSearchHybridResult>> Hybrid(
        [FromBody] DocUtilSearchRequest request,
        CancellationToken ct = default)
    {
        var bad = ValidateSearchRequest(request);
        if (bad != null) return bad;

        try
        {
            var result = await _docUtilClient.SearchHybridAsync(request, ct);
            return Ok(result);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 하이브리드 검색 실패");
            return StatusCode(502, new ErrorResponseDto(
                "하이브리드 검색에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 챗봇 검색 실행 — DocUtil `/api/v1/search/chatbot` 위임(검색 + LLM 응답 + FAQ 옵션).
    /// </summary>
    [HttpPost("chatbot")]
    public async Task<ActionResult<DocUtilSearchChatbotResult>> Chatbot(
        [FromBody] DocUtilSearchChatbotRequest request,
        CancellationToken ct = default)
    {
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(request.Query))
        {
            return BadRequest(ErrorResponseDto.BadRequest("질의가 비어 있습니다."));
        }
        if (request.Query.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("질의는 2000자 이하여야 합니다."));
        }
        if (string.IsNullOrWhiteSpace(request.SearchScopeId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("검색 범위 ID가 비어 있습니다."));
        }

        try
        {
            var result = await _docUtilClient.SearchChatbotAsync(request, ct);
            return Ok(result);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 챗봇 검색 실패");
            return StatusCode(502, new ErrorResponseDto(
                "챗봇 검색에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// QA 검색 실행 — DocUtil `/api/v1/search/qa` 위임(인용 enforce + hallucination score).
    /// </summary>
    [HttpPost("qa")]
    public async Task<ActionResult<DocUtilSearchQaResult>> Qa(
        [FromBody] DocUtilSearchQaRequest request,
        CancellationToken ct = default)
    {
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(request.Query))
        {
            return BadRequest(ErrorResponseDto.BadRequest("질의가 비어 있습니다."));
        }
        if (request.Query.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("질의는 2000자 이하여야 합니다."));
        }

        try
        {
            var result = await _docUtilClient.SearchQaAsync(request, ct);
            return Ok(result);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil QA 검색 실패");
            return StatusCode(502, new ErrorResponseDto(
                "QA 검색에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 키워드(BM25) 검색 실행 — DocUtil `/api/v1/search/keyword` 위임.
    /// </summary>
    [HttpPost("keyword")]
    public async Task<ActionResult<DocUtilSearchHybridResult>> Keyword(
        [FromBody] DocUtilSearchKeywordRequest request,
        CancellationToken ct = default)
    {
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(request.Query))
        {
            return BadRequest(ErrorResponseDto.BadRequest("질의가 비어 있습니다."));
        }
        if (request.Query.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("질의는 2000자 이하여야 합니다."));
        }

        try
        {
            var result = await _docUtilClient.SearchKeywordAsync(request, ct);
            return Ok(result);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 키워드 검색 실패");
            return StatusCode(502, new ErrorResponseDto(
                "키워드 검색에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 운영자 검색 테스트 실행 — DocUtil `/api/v1/search/test` 위임(admin bypass, as_user_view=False).
    /// 실제 사용자가 보는 결과와 별개로 visibility 검사 없이 평가 — 검색 품질 디버깅용.
    /// </summary>
    [HttpPost("admin-test")]
    public async Task<ActionResult<DocUtilSearchHybridResult>> AdminTest(
        [FromBody] DocUtilSearchTestRequest request,
        CancellationToken ct = default)
    {
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(request.Query))
        {
            return BadRequest(ErrorResponseDto.BadRequest("질의가 비어 있습니다."));
        }
        if (request.Query.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("질의는 2000자 이하여야 합니다."));
        }
        if (string.IsNullOrWhiteSpace(request.SearchScopeId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("검색 범위 ID가 비어 있습니다."));
        }

        try
        {
            var result = await _docUtilClient.SearchAdminTestAsync(request, ct);
            return Ok(result);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 운영자 검색 테스트 실패");
            return StatusCode(502, new ErrorResponseDto(
                "운영자 검색 테스트에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 보조 endpoint — history + scopes dropdown
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 검색 이력 조회 — DocUtil `/api/v1/search/history` 위임 + 30초 캐시(version-prefix).
    /// </summary>
    /// <param name="page">페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 20, 1~100).</param>
    [HttpGet("history")]
    public async Task<ActionResult<List<DocUtilSearchHistoryItem>>> History(
        [FromQuery] int page = 1,
        [FromQuery] int size = 20,
        CancellationToken ct = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 100) size = 20;

        var version = await _cachingService.GetVersionAsync(HistoryCacheVersionNamespace);
        var cacheKey = $"{HistoryCacheKeyPrefix}v{version}:list:{page}|{size}";

        var cached = await _cachingService.GetAsync<CachedHistoryListDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 검색 이력 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToList());
        }
        _logger.LogDebug("DocUtil 검색 이력 캐시 miss - key={Key}", cacheKey);

        try
        {
            var items = await _docUtilClient.SearchHistoryAsync(page, size, ct);
            await _cachingService.SetAsync(cacheKey, CachedHistoryListDto.From(items), HistoryCacheTtl);
            return Ok(items);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 검색 이력 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "검색 이력을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 검색 범위 dropdown 옵션 — DocUtil `/api/v1/search-scopes/options` 위임.
    /// <para>
    /// 검색 테스트 페이지가 로드 시 호출하는 보조 endpoint. 캐시는 SearchScopes Controller 의
    /// 자체 namespace(docutil-search-scopes) 에서 관리되므로 여기서는 무캐시 패스루.
    /// </para>
    /// </summary>
    [HttpGet("scopes")]
    public async Task<ActionResult<List<DocUtilSearchScopeOption>>> Scopes(CancellationToken ct = default)
    {
        try
        {
            var opts = await _docUtilClient.ListSearchScopeOptionsAsync(ct);
            return Ok(opts);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 검색 범위 옵션 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "검색 범위 옵션을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 검증 헬퍼
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 하이브리드/시맨틱 검색 요청 공통 검증 — query 필수 + max_results 범위.
    /// 검증 실패 시 BadRequest 반환, 성공 시 null.
    /// </summary>
    private static ActionResult? ValidateSearchRequest(DocUtilSearchRequest? request)
    {
        if (request == null)
        {
            return new BadRequestObjectResult(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(request.Query))
        {
            return new BadRequestObjectResult(ErrorResponseDto.BadRequest("질의가 비어 있습니다."));
        }
        if (request.Query.Length > 2000)
        {
            return new BadRequestObjectResult(ErrorResponseDto.BadRequest("질의는 2000자 이하여야 합니다."));
        }
        if (request.MaxResults < 1 || request.MaxResults > 100)
        {
            return new BadRequestObjectResult(ErrorResponseDto.BadRequest("max_results 는 1~100 사이여야 합니다."));
        }
        return null;
    }

    // ──────────────────────────────────────────────────────────────────────
    // 캐시 wrapper DTO (record 가 아닌 클래스 — System.Text.Json 캐시 역직렬화 안정성)
    // ──────────────────────────────────────────────────────────────────────

    private sealed class CachedHistoryItemDto
    {
        public string Id { get; set; } = string.Empty;
        public string Query { get; set; } = string.Empty;
        public string SearchType { get; set; } = string.Empty;
        public int ResultCount { get; set; }
        public DateTime CreatedAt { get; set; }

        public static CachedHistoryItemDto From(DocUtilSearchHistoryItem i) => new()
        {
            Id = i.Id,
            Query = i.Query,
            SearchType = i.SearchType,
            ResultCount = i.ResultCount,
            CreatedAt = i.CreatedAt,
        };

        public DocUtilSearchHistoryItem ToRecord() => new(Id, Query, SearchType, ResultCount, CreatedAt);
    }

    private sealed class CachedHistoryListDto
    {
        public CachedHistoryItemDto[] Items { get; set; } = Array.Empty<CachedHistoryItemDto>();

        public static CachedHistoryListDto From(List<DocUtilSearchHistoryItem> list) => new()
        {
            Items = list.Select(CachedHistoryItemDto.From).ToArray(),
        };

        public List<DocUtilSearchHistoryItem> ToList()
            => Items.Select(c => c.ToRecord()).ToList();
    }
}
