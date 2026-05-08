using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminKnowledgeBaseController — 운영자 KB 콘솔 BFF (Phase 6.3, ADR-2)
//
// 통합 비전: 운영자 KB 관리는 AgentHub Vue 콘솔에서만 수행한다(R2 단일 진입점).
// 본 컨트롤러는 IDocUtilClient 의 6 개 메서드를 운영자(`Admin` / `SuperAdmin`)
// 권한 게이트와 함께 외부 표면에 노출하는 단순 forwarding 레이어다.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//   2. multipart/form-data → Stream 변환(업로드)
//   3. DocUtil DTO → JSON camelCase 직렬화(Program.cs JsonNamingPolicy 적용)
//   4. 한국어 ErrorResponseDto 일관 응답
//
// 책임 범위 밖:
//   - DocUtil 인증 토큰 부착(DocUtilClient 가 처리)
//   - 한국어 에러 매핑(DocUtilClient 가 InvalidOperationException 으로 통일)
//   - Agent 권한 / Tenant 검증(추후 멀티테넌시 도입 시 별도 확장)
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 지식베이스(DocUtil) 관리 BFF — Phase 6.3.
/// AgentHub Vue 콘솔의 `/admin/knowledge-base` 페이지가 호출하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/knowledge-base")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminKnowledgeBaseController : ControllerBase
{
    private readonly IDocUtilClient _docUtilClient;
    private readonly CachingService _cachingService;
    private readonly ILogger<AdminKnowledgeBaseController> _logger;

    public AdminKnowledgeBaseController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        ILogger<AdminKnowledgeBaseController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _logger = logger;
    }

    /// <summary>
    /// DocUtil 검색 캐시 일괄 무효화 — version-key 패턴.
    /// upload/delete 등 mutation 성공 후 호출. 실패는 swallow + 경고 로그
    /// (캐시 무효화는 best-effort, 본 mutation 자체를 죽이지 않음).
    /// </summary>
    private async Task InvalidateSearchCacheAsync()
    {
        try
        {
            var v = await _cachingService.IncrementVersionAsync(DocUtilClient.SearchCacheVersionNamespace);
            _logger.LogInformation("DocUtil 검색 캐시 invalidate - newVersion={V}", v);
        }
        catch (Exception ex)
        {
            // best-effort — mutation 응답을 막지 않는다.
            _logger.LogWarning(ex, "DocUtil 검색 캐시 invalidate 실패(무시)");
        }
    }

    /// <summary>
    /// 문서 목록 조회 — DocUtil `/api/v1/documents` 위임.
    /// </summary>
    [HttpGet("documents")]
    public async Task<ActionResult<DocUtilDocumentList>> ListDocuments(
        [FromQuery(Name = "folderId")] string? folderId,
        [FromQuery] int page = 1,
        [FromQuery] int size = 20,
        CancellationToken ct = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 200) size = 20;

        try
        {
            var result = await _docUtilClient.ListDocumentsAsync(folderId, page, size, ct);
            return Ok(result);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 목록 조회 실패 (folderId={FolderId}, page={Page})", folderId, page);
            return StatusCode(502, new ErrorResponseDto(
                "지식베이스 문서 목록을 불러오지 못했습니다. DocUtil 서비스 상태를 확인하세요.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 문서 상세 조회 — DocUtil `/api/v1/documents/{id}` 위임.
    /// </summary>
    [HttpGet("documents/{id}")]
    public async Task<ActionResult<DocUtilDocumentDetail>> GetDocument(string id, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            return BadRequest(ErrorResponseDto.BadRequest("문서 식별자가 비어 있습니다."));
        }

        try
        {
            var detail = await _docUtilClient.GetDocumentAsync(id, ct);
            if (detail == null)
            {
                return NotFound(ErrorResponseDto.NotFound("해당 문서를 찾을 수 없습니다."));
            }
            return Ok(detail);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 상세 조회 실패 (id={Id})", id);
            return StatusCode(502, new ErrorResponseDto(
                "지식베이스 문서 상세를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 문서 업로드 — multipart/form-data → DocUtil `/api/v1/documents/upload` 위임.
    /// </summary>
    [HttpPost("documents/upload")]
    [RequestSizeLimit(100 * 1024 * 1024)] // 100MB — DocUtil 측 한도와 일치 권장
    public async Task<ActionResult<DocUtilUploadResult>> UploadDocument(
        [FromForm] IFormFile file,
        [FromForm(Name = "folderId")] string? folderId,
        [FromForm] string? visibility,
        CancellationToken ct = default)
    {
        if (file == null || file.Length == 0)
        {
            return BadRequest(ErrorResponseDto.BadRequest("업로드할 파일이 없습니다."));
        }

        try
        {
            await using var stream = file.OpenReadStream();
            var result = await _docUtilClient.UploadDocumentAsync(
                stream,
                file.FileName,
                folderId,
                visibility,
                ct);

            _logger.LogInformation(
                "운영자 KB 업로드 성공: {FileName} ({Size} bytes) → DocUtil id={Id}",
                file.FileName, file.Length, result.Id);

            // KB mutation 성공 → DocUtil 검색 캐시 일괄 무효화(version-key bump).
            // 다음 RAG 검색부터 새 문서가 즉시 반영(이전 5분 TTL 대기 제거).
            await InvalidateSearchCacheAsync();

            return Ok(result);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 업로드 실패 ({FileName})", file.FileName);
            return StatusCode(502, new ErrorResponseDto(
                "문서 업로드에 실패했습니다. 잠시 후 다시 시도하세요.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 문서 삭제 — DocUtil `/api/v1/documents/{id}` 위임 (DELETE).
    /// </summary>
    [HttpDelete("documents/{id}")]
    public async Task<IActionResult> DeleteDocument(string id, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            return BadRequest(ErrorResponseDto.BadRequest("문서 식별자가 비어 있습니다."));
        }

        try
        {
            await _docUtilClient.DeleteDocumentAsync(id, ct);
            _logger.LogInformation("운영자 KB 삭제: id={Id}", id);

            // KB mutation 성공 → DocUtil 검색 캐시 일괄 무효화(version-key bump).
            // 다음 RAG 검색부터 삭제된 문서 결과가 사라짐(이전 5분 TTL 대기 제거).
            await InvalidateSearchCacheAsync();

            return NoContent();
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 문서 삭제 실패 (id={Id})", id);
            return StatusCode(502, new ErrorResponseDto(
                "문서 삭제에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 문서 청크 목록 — DocUtil `/api/v1/documents/{id}/chunks` 위임.
    /// 운영자가 임베딩 결과 검수 시 사용.
    /// </summary>
    [HttpGet("documents/{id}/chunks")]
    public async Task<ActionResult<List<DocUtilChunk>>> GetChunks(string id, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            return BadRequest(ErrorResponseDto.BadRequest("문서 식별자가 비어 있습니다."));
        }

        try
        {
            var chunks = await _docUtilClient.GetChunksAsync(id, ct);
            return Ok(chunks);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 청크 조회 실패 (id={Id})", id);
            return StatusCode(502, new ErrorResponseDto(
                "청크 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// DocUtil 컬렉션(projects) 카탈로그 — DocUtil `/api/v1/projects` 위임.
    ///
    /// 호출 컨텍스트(2026-05-08 후속 트랙):
    ///   AgentBuilder.vue 의 KnowledgeBaseRef 입력을 텍스트 → dropdown 으로 전환.
    ///   운영자가 DocUtil 콘솔에서 만든 collection 을 GUI 에서 직접 선택할 수 있도록
    ///   카탈로그를 BFF 표면화한다. id/name/description 3 필드만 노출(BFF 단순화).
    ///
    /// 응답 형식: List&lt;DocUtilCollection&gt; (camelCase 직렬화 — Program.cs JsonNamingPolicy 적용).
    /// 예시:
    ///   [
    ///     { "id": "c6955ce6-...", "name": "부산대", "description": "...." },
    ///     { "id": "...",          "name": "...",   "description": null }
    ///   ]
    ///
    /// 권한: Admin / SuperAdmin (컨트롤러 레벨 [Authorize] 상속). Bearer JWT 미부착 시 401.
    /// 502: DocUtil 접근 실패(JWT 만료/네트워크/서비스 다운) — 한국어 ErrorResponseDto 응답.
    /// </summary>
    /// <param name="page">페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 50, 최대 200).</param>
    [HttpGet("collections")]
    public async Task<ActionResult<List<DocUtilCollection>>> ListCollections(
        [FromQuery] int page = 1,
        [FromQuery] int size = 50,
        CancellationToken ct = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 200) size = 50;

        try
        {
            var collections = await _docUtilClient.ListCollectionsAsync(page, size, ct);
            return Ok(collections);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 컬렉션 목록 조회 실패 (page={Page}, size={Size})", page, size);
            return StatusCode(502, new ErrorResponseDto(
                "지식베이스 컬렉션 목록을 불러오지 못했습니다. DocUtil 서비스 상태를 확인하세요.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 운영자 KB 검색 — DocUtil `/api/v1/search` 위임.
    /// </summary>
    [HttpPost("search")]
    public async Task<ActionResult<DocUtilSearchResult>> Search(
        [FromBody] AdminKnowledgeBaseSearchRequest request,
        CancellationToken ct = default)
    {
        if (request == null || string.IsNullOrWhiteSpace(request.Query))
        {
            return BadRequest(ErrorResponseDto.BadRequest("검색어를 입력하세요."));
        }

        var maxResults = request.MaxResults is > 0 and <= 50 ? request.MaxResults.Value : 10;

        try
        {
            var result = await _docUtilClient.SearchAsync(
                request.Query,
                request.CollectionRef,
                maxResults,
                ct);
            return Ok(result);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 검색 실패 (query 길이={Length})", request.Query.Length);
            return StatusCode(502, new ErrorResponseDto(
                "지식베이스 검색에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }
}

/// <summary>
/// 운영자 검색 요청 DTO. 외부 표면(camelCase): { "query": ..., "collectionRef": ..., "maxResults": ... }.
/// </summary>
public sealed class AdminKnowledgeBaseSearchRequest
{
    /// <summary>사용자 질의 원문.</summary>
    public string Query { get; set; } = string.Empty;

    /// <summary>DocUtil collection / folder 참조(선택). 미지정 시 글로벌 검색.</summary>
    public string? CollectionRef { get; set; }

    /// <summary>상위 결과 개수(기본 10, 최대 50).</summary>
    public int? MaxResults { get; set; }
}
