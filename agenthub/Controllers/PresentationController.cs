using System.Text.Json;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;
using AIAgentManagement.Data;
using AIAgentManagement.Infrastructure;
using AIAgentManagement.Settings;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/presentations")]
[Authorize]
public class PresentationController : ControllerBase
{
    private readonly IPresentationService _presentationService;
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<PresentationController> _logger;

    public PresentationController(
        IPresentationService presentationService,
        AIAgentManagementDbContext context,
        ILogger<PresentationController> logger)
    {
        _presentationService = presentationService;
        _context = context;
        _logger = logger;
    }

    [HttpPost("generate")]
    public async Task<ActionResult<PresentationDto>> GeneratePresentation([FromBody] PresentationGenerationRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId) || userId <= 0)
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            // 항상 로그인한 사용자 ID 사용 (클라이언트 값 무시)
            request.UserId = userId;
            var presentation = await _presentationService.GeneratePresentationAsync(request);

            return Ok(presentation);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating presentation");
            var inner = ex.InnerException?.Message;
            var message = ex.Message + (string.IsNullOrEmpty(inner) ? "" : " " + inner);
            if (message.Length > 500) message = message.Substring(0, 500);
            return StatusCode(500, ErrorResponseDto.InternalError(message));
        }
    }

    /// <summary>PRESENTATIONS 테이블에서 현재 사용자의 프레젠테이션 목록 조회. Slides(nvarchar max) 컬럼 제외 — DB 레벨 OPENJSON으로 슬라이드 수만 계산.</summary>
    [HttpGet("list")]
    public async Task<ActionResult<List<PresentationListItemDto>>> GetPresentations()
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            // Slides(nvarchar max) 컬럼은 SELECT 제외. SlideCount는 PresentationSlides 테이블에서 COUNT.
            // 레거시 호환: PresentationSlides에 없으면 OPENJSON(Slides) 폴백.
            var list = await _context.Database.SqlQueryRaw<PresentationListItemDto>(
                """
                SELECT TOP 100
                    p.PresentationId,
                    p.UserId,
                    p.Title,
                    p.ThemeId,
                    ISNULL(
                        (SELECT COUNT(*) FROM PresentationSlides ps WHERE ps.PresentationId = p.PresentationId),
                        ISNULL((SELECT COUNT(*) FROM OPENJSON(p.Slides)), 0)
                    ) AS SlideCount,
                    p.CreatedAt,
                    p.UpdatedAt
                FROM Presentations p
                WHERE p.UserId = {0}
                ORDER BY p.UpdatedAt DESC
                """,
                userId
            ).ToListAsync();

            return Ok(list);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting presentations from PRESENTATIONS table");
            return StatusCode(500, ErrorResponseDto.InternalError("프레젠테이션 목록을 불러오는데 실패했습니다."));
        }
    }

    [HttpGet("themes")]
    public ActionResult<IReadOnlyList<PresentationThemeConfig>> GetThemes()
    {
        return Ok(PresentationThemes.All);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<PresentationDto>> GetPresentation(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var presentation = await _presentationService.GetPresentationAsync(id, userId);
            return Ok(presentation);
        }
        catch (InvalidOperationException ex)
        {
            return NotFound(ErrorResponseDto.NotFound(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting presentation {PresentationId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError($"An error occurred: {ex.Message}"));
        }
    }

    [HttpPut("{id}/theme")]
    public async Task<ActionResult<PresentationDto>> UpdateTheme(int id, [FromBody] SetThemeRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                return Unauthorized(ErrorResponseDto.Unauthorized());
            if (request == null)
                return BadRequest(ErrorResponseDto.BadRequest("Request body is required."));
            // 빈 문자열은 기본 테마로 초기화
            var themeId = request.ThemeId?.Trim() ?? "";
            var presentation = await _presentationService.UpdateThemeAsync(id, userId, themeId);
            return Ok(presentation);
        }
        catch (InvalidOperationException ex)
        {
            return NotFound(ErrorResponseDto.NotFound(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating theme for presentation {PresentationId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError(ex.Message));
        }
    }

    [HttpPut("{id}")]
    public async Task<ActionResult<PresentationDto>> UpdatePresentation(int id, [FromBody] PresentationDto? presentation)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            if (presentation == null)
            {
                return BadRequest(ErrorResponseDto.BadRequest("Request body is required."));
            }

            if (presentation.PresentationId != id)
            {
                return BadRequest(ErrorResponseDto.BadRequest("Presentation ID mismatch"));
            }

            var updatedPresentation = await _presentationService.UpdatePresentationAsync(id, userId, presentation);
            return Ok(updatedPresentation);
        }
        catch (InvalidOperationException ex)
        {
            return NotFound(ErrorResponseDto.NotFound(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating presentation {PresentationId}", id);
            var msg = ex.Message + (ex.InnerException != null ? " " + ex.InnerException.Message : "");
            if (msg.Length > 500) msg = msg.Substring(0, 500);
            return StatusCode(500, ErrorResponseDto.InternalError(msg));
        }
    }

    [HttpPost("{id}/slides")]
    public async Task<ActionResult<PresentationDto>> AddSlide(int id, [FromBody] SlideDto slide)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var presentation = await _presentationService.AddSlideAsync(id, userId, slide);
            return Ok(presentation);
        }
        catch (InvalidOperationException ex)
        {
            return NotFound(ErrorResponseDto.NotFound(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error adding slide to presentation {PresentationId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError($"An error occurred: {ex.Message}"));
        }
    }

    [HttpPut("{id}/slides/{slideId}")]
    public async Task<ActionResult<PresentationDto>> UpdateSlide(int id, string slideId, [FromBody] SlideDto? slide)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            if (slide == null)
            {
                return BadRequest(ErrorResponseDto.BadRequest("Slide body is required."));
            }

            var presentation = await _presentationService.UpdateSlideAsync(id, userId, slideId, slide);
            return Ok(presentation);
        }
        catch (InvalidOperationException ex)
        {
            return NotFound(ErrorResponseDto.NotFound(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating slide {SlideId} in presentation {PresentationId}", slideId, id);
            var msg = ex.Message + (ex.InnerException != null ? " " + ex.InnerException.Message : "");
            if (msg.Length > 500) msg = msg.Substring(0, 500);
            return StatusCode(500, ErrorResponseDto.InternalError(msg));
        }
    }

    [HttpDelete("{id}/slides/{slideId}")]
    public async Task<ActionResult<PresentationDto>> DeleteSlide(int id, string slideId)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var presentation = await _presentationService.DeleteSlideAsync(id, userId, slideId);
            return Ok(presentation);
        }
        catch (InvalidOperationException ex)
        {
            return NotFound(ErrorResponseDto.NotFound(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting slide {SlideId} from presentation {PresentationId}", slideId, id);
            return StatusCode(500, ErrorResponseDto.InternalError($"An error occurred: {ex.Message}"));
        }
    }

    [HttpPost("{id}/reorder")]
    public async Task<ActionResult<PresentationDto>> ReorderSlides(int id, [FromBody] ReorderSlidesRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var presentation = await _presentationService.ReorderSlidesAsync(id, userId, request.SlideIds);
            return Ok(presentation);
        }
        catch (InvalidOperationException ex)
        {
            return NotFound(ErrorResponseDto.NotFound(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error reordering slides in presentation {PresentationId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError($"An error occurred: {ex.Message}"));
        }
    }

    [HttpGet("{id}/export/pptx")]
    public async Task<IActionResult> ExportToPptx(int id, [FromQuery] string? themeId = null)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var stream = await _presentationService.ExportToPptxAsync(id, userId, themeId);
            var presentation = await _presentationService.GetPresentationAsync(id, userId);
            
            // 스트림을 바이트 배열로 변환
            byte[] fileBytes;
            using (var memoryStream = new MemoryStream())
            {
                await stream.CopyToAsync(memoryStream);
                fileBytes = memoryStream.ToArray();
            }
            stream.Dispose();
            
            // 파일명에서 제어 문자 및 특수 문자 제거
            var safeTitle = System.Text.RegularExpressions.Regex.Replace(
                presentation.Title, 
                @"[\x00-\x1F\x7F-\x9F]", 
                ""
            ).Replace(" ", "_").Replace("\"", "").Replace("\\", "").Replace("/", "").Replace(":", "").Replace("*", "").Replace("?", "").Replace("<", "").Replace(">", "").Replace("|", "");
            
            var filename = $"{safeTitle}_{DateTime.UtcNow:yyyyMMddHHmmss}.pptx";
            return File(fileBytes, "application/vnd.openxmlformats-officedocument.presentationml.presentation", filename);
        }
        catch (InvalidOperationException ex)
        {
            return NotFound(ErrorResponseDto.NotFound(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error exporting presentation {PresentationId} to PPTX", id);
            var inner = ex.InnerException?.Message;
            var message = ex.Message + (string.IsNullOrEmpty(inner) ? "" : " " + inner);
            if (message.Length > 500) message = message.Substring(0, 500);
            return StatusCode(500, ErrorResponseDto.InternalError(message));
        }
    }

    /// <summary>DB 저장 없이 클라이언트 데이터로 PPTX 내보내기. 문자열 잘림 오류 우회.</summary>
    [HttpPost("export/pptx")]
    public async Task<IActionResult> ExportToPptxFromBody([FromBody] PresentationDto presentation)
    {
        try
        {
            if (presentation?.Slides == null || presentation.Slides.Count == 0)
                return BadRequest(ErrorResponseDto.BadRequest("슬라이드가 없습니다."));
            var stream = await _presentationService.ExportToPptxFromDtoAsync(presentation);
            byte[] fileBytes;
            using (var ms = new MemoryStream())
            {
                await stream.CopyToAsync(ms);
                fileBytes = ms.ToArray();
            }
            stream.Dispose();
            var title = presentation.Title ?? "presentation";
            var safeTitle = System.Text.RegularExpressions.Regex.Replace(title, @"[\x00-\x1F\x7F-\x9F]", "").Replace(" ", "_").Replace("\"", "").Replace("\\", "").Replace("/", "").Replace(":", "").Replace("*", "").Replace("?", "").Replace("<", "").Replace(">", "").Replace("|", "");
            var filename = $"{safeTitle}_{DateTime.UtcNow:yyyyMMddHHmmss}.pptx";
            return File(fileBytes, "application/vnd.openxmlformats-officedocument.presentationml.presentation", filename);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error exporting PPTX from body");
            return StatusCode(500, ErrorResponseDto.InternalError(ex.Message));
        }
    }

    /// <summary>DB 저장 없이 클라이언트 데이터로 PDF 내보내기. 문자열 잘림 오류 우회.</summary>
    [HttpPost("export/pdf")]
    public async Task<IActionResult> ExportToPdfFromBody([FromBody] PresentationDto presentation)
    {
        try
        {
            if (presentation?.Slides == null || presentation.Slides.Count == 0)
                return BadRequest(ErrorResponseDto.BadRequest("슬라이드가 없습니다."));
            var stream = await _presentationService.ExportToPdfFromDtoAsync(presentation);
            byte[] fileBytes;
            using (var ms = new MemoryStream())
            {
                await stream.CopyToAsync(ms);
                fileBytes = ms.ToArray();
            }
            stream.Dispose();
            var title = presentation.Title ?? "presentation";
            var safeTitle = System.Text.RegularExpressions.Regex.Replace(title, @"[\x00-\x1F\x7F-\x9F]", "").Replace(" ", "_").Replace("\"", "").Replace("\\", "").Replace("/", "").Replace(":", "").Replace("*", "").Replace("?", "").Replace("<", "").Replace(">", "").Replace("|", "");
            var filename = $"{safeTitle}_{DateTime.UtcNow:yyyyMMddHHmmss}.pdf";
            return File(fileBytes, "application/pdf", filename);
        }
        catch (InvalidOperationException ex) when (ex.Message.Contains("LibreOffice") || ex.Message.Contains("PDF 변환"))
        {
            // 사용자가 PDF 를 요청했는데 PPTX 를 응답으로 돌려주면 확장자/내용이 일치하지
            // 않아 운영자가 혼란을 겪고 보안 검수에서도 실패한다. 따라서 자동 fallback 을
            // 사용하지 않고 503 으로 명확히 실패 신호를 보낸다. 사용자는 별도 메뉴에서
            // PPTX 다운로드를 직접 선택할 수 있다.
            _logger.LogWarning(ex, "PDF conversion unavailable (LibreOffice missing or conversion error)");
            return StatusCode(503, new ErrorResponseDto(
                "PDF 변환 서비스를 일시적으로 사용할 수 없습니다. PPTX 다운로드를 이용해 주세요.",
                "PDF_CONVERSION_UNAVAILABLE",
                null
            ));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error exporting PDF from body");
            return StatusCode(500, ErrorResponseDto.InternalError(ex.Message));
        }
    }

    [HttpGet("{id}/export/pdf")]
    public async Task<IActionResult> ExportToPdf(int id, [FromQuery] string? themeId = null)
    {
        var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
        {
            return Unauthorized(ErrorResponseDto.Unauthorized());
        }

        try
        {
            var stream = await _presentationService.ExportToPdfAsync(id, userId, themeId);
            var presentation = await _presentationService.GetPresentationAsync(id, userId);
            
            // 스트림을 바이트 배열로 변환
            byte[] fileBytes;
            using (var memoryStream = new MemoryStream())
            {
                await stream.CopyToAsync(memoryStream);
                fileBytes = memoryStream.ToArray();
            }
            stream.Dispose();
            
            // 파일명에서 제어 문자 및 특수 문자 제거
            var safeTitle = System.Text.RegularExpressions.Regex.Replace(
                presentation.Title, 
                @"[\x00-\x1F\x7F-\x9F]", 
                ""
            ).Replace(" ", "_").Replace("\"", "").Replace("\\", "").Replace("/", "").Replace(":", "").Replace("*", "").Replace("?", "").Replace("<", "").Replace(">", "").Replace("|", "");
            
            var filename = $"{safeTitle}_{DateTime.UtcNow:yyyyMMddHHmmss}.pdf";
            return File(fileBytes, "application/pdf", filename);
        }
        catch (InvalidOperationException ex) when (ex.Message.Contains("LibreOffice") || ex.Message.Contains("PDF 변환"))
        {
            // 사용자가 PDF 를 요청했는데 PPTX 를 응답으로 돌려주면 확장자/내용이 일치하지
            // 않아 운영자가 혼란을 겪고 보안 검수에서도 실패한다. 따라서 자동 fallback 을
            // 사용하지 않고 503 으로 명확히 실패 신호를 보낸다. 사용자는 별도 메뉴에서
            // PPTX 다운로드를 직접 선택할 수 있다.
            _logger.LogWarning(ex, "PDF conversion unavailable for presentation {PresentationId} (LibreOffice missing or conversion error)", id);
            return StatusCode(503, new ErrorResponseDto(
                "PDF 변환 서비스를 일시적으로 사용할 수 없습니다. PPTX 다운로드를 이용해 주세요.",
                "PDF_CONVERSION_UNAVAILABLE",
                null
            ));
        }
        catch (InvalidOperationException ex)
        {
            return NotFound(ErrorResponseDto.NotFound(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error exporting presentation {PresentationId} to PDF", id);
            return StatusCode(500, ErrorResponseDto.InternalError($"An error occurred: {ex.Message}"));
        }
    }

}

public class ReorderSlidesRequestDto
{
    public List<string> SlideIds { get; set; } = new();
}
