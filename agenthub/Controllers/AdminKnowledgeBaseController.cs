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
    private readonly ILogger<AdminKnowledgeBaseController> _logger;

    public AdminKnowledgeBaseController(
        IDocUtilClient docUtilClient,
        ILogger<AdminKnowledgeBaseController> logger)
    {
        _docUtilClient = docUtilClient;
        _logger = logger;
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
