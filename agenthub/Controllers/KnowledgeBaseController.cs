using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ── Phase 6.4 (ADR-2): 운영자 KB 화면은 AgentHub Vue UI(Phase 6.3) 로 이전 ──
// 본 컨트롤러(`/api/knowledgebase`) 는 자체 KB CRUD 를 그대로 노출하나
// 신규 운영자 작업은 Phase 6.3 의 KB 콘솔 (IDocUtilClient 경유) 사용 권장.
// 라우트는 Phase 5+ 호환을 위해 보존 — Swagger 에서 deprecated 표시.
// Phase 8+ 에서 자체 KB 테이블 drop 과 함께 제거.
// ----------------------------------------------------------------------
[Obsolete("ADR-2: 운영자 KB 관리는 AgentHub Vue UI(Phase 6.3, IDocUtilClient 경유) 로 이전. /api/knowledgebase 는 Phase 5+ 호환 유지. Phase 8+ 에서 제거 예정.", error: false)]
[ApiController]
[Route("api/[controller]")]
[Authorize]
public class KnowledgeBaseController : ControllerBase
{
    private readonly IKnowledgeBaseService _knowledgeBaseService;
    private readonly ILogger<KnowledgeBaseController> _logger;

    public KnowledgeBaseController(
        IKnowledgeBaseService knowledgeBaseService,
        ILogger<KnowledgeBaseController> logger)
    {
        _knowledgeBaseService = knowledgeBaseService;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<List<KnowledgeBaseDocumentListDto>>> GetDocuments([FromQuery] string? search, [FromQuery] bool? isIndexed)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var documents = await _knowledgeBaseService.GetDocumentsAsync(userId, search, isIndexed);
            return Ok(documents);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting documents");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<KnowledgeBaseDocumentDto>> GetDocument(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var document = await _knowledgeBaseService.GetDocumentByIdAsync(id, userId);
            if (document == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(document);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting document {DocumentId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost]
    public async Task<ActionResult<KnowledgeBaseDocumentDto>> CreateDocument([FromBody] CreateKnowledgeBaseDocumentRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            var document = await _knowledgeBaseService.CreateDocumentAsync(request, userId);
            return CreatedAtAction(nameof(GetDocument), new { id = document.DocumentId }, document);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating document");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred while creating document"));
        }
    }

    [HttpPut("{id}")]
    public async Task<ActionResult<KnowledgeBaseDocumentDto>> UpdateDocument(int id, [FromBody] UpdateKnowledgeBaseDocumentRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var document = await _knowledgeBaseService.UpdateDocumentAsync(id, request, userId);
            if (document == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(document);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating document {DocumentId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred while updating document"));
        }
    }

    [HttpDelete("{id}")]
    public async Task<ActionResult> DeleteDocument(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var deleted = await _knowledgeBaseService.DeleteDocumentAsync(id, userId);
            if (!deleted)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting document {DocumentId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred while deleting document"));
        }
    }

    [HttpPost("{id}/index")]
    public async Task<ActionResult> IndexDocument(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var success = await _knowledgeBaseService.IndexDocumentAsync(id, userId);
            if (!success)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(new { message = "Document indexed successfully" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error indexing document {DocumentId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred while indexing document"));
        }
    }

    [HttpPost("{id}/reindex")]
    public async Task<ActionResult> ReindexDocument(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var success = await _knowledgeBaseService.ReindexDocumentAsync(id, userId);
            if (!success)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(new { message = "Document reindexed successfully" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error reindexing document {DocumentId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred while reindexing document"));
        }
    }
}
