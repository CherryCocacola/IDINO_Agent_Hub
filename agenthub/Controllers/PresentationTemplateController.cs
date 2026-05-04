using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/presentation-templates")]
[Authorize]
public class PresentationTemplateController : ControllerBase
{
    private readonly IPresentationTemplateService _templateService;
    private readonly ILogger<PresentationTemplateController> _logger;

    public PresentationTemplateController(
        IPresentationTemplateService templateService,
        ILogger<PresentationTemplateController> logger)
    {
        _templateService = templateService;
        _logger = logger;
    }

    [HttpPost("upload")]
    public async Task<ActionResult<PresentationTemplateDto>> UploadTemplate(
        [FromForm] TemplateUploadRequestDto request,
        [FromForm] IFormFile templateFile)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            if (templateFile == null || templateFile.Length == 0)
            {
                return BadRequest(ErrorResponseDto.BadRequest("Template file is required"));
            }

            var extension = Path.GetExtension(templateFile.FileName).ToLowerInvariant();
            if (extension != ".pptx")
            {
                return BadRequest(ErrorResponseDto.BadRequest("Only PPTX files are supported"));
            }

            var template = await _templateService.UploadTemplateAsync(userId, templateFile, request);
            return Ok(template);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error uploading template");
            return StatusCode(500, ErrorResponseDto.InternalError($"An error occurred: {ex.Message}"));
        }
    }

    [HttpGet]
    public async Task<ActionResult<List<PresentationTemplateDto>>> GetTemplates(
        [FromQuery] string? category,
        [FromQuery] bool? isPublic)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            int? userId = null;
            if (!string.IsNullOrEmpty(userIdClaim) && int.TryParse(userIdClaim, out var parsedUserId))
            {
                userId = parsedUserId;
            }

            var templates = await _templateService.GetTemplatesAsync(userId, category, isPublic);
            return Ok(templates);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting templates");
            return StatusCode(500, ErrorResponseDto.InternalError($"An error occurred: {ex.Message}"));
        }
    }

    /// <summary>Download or preview template file. Use ?inline=1 or ?inline=true for preview (Content-Disposition: inline).</summary>
    [HttpGet("{id}/file")]
    public async Task<IActionResult> GetTemplateFile(int id, [FromQuery] string? inline = null)
    {
        try
        {
            var result = await _templateService.GetTemplateFileAsync(id);
            if (result == null)
                return NotFound(ErrorResponseDto.NotFound("Template or file not found"));

            var isInline = inline == "1" || string.Equals(inline, "true", StringComparison.OrdinalIgnoreCase);
            var (stream, fileName) = result.Value;
            const string contentType = "application/vnd.openxmlformats-officedocument.presentationml.presentation";
            var cd = new Microsoft.Net.Http.Headers.ContentDispositionHeaderValue(isInline ? "inline" : "attachment")
            {
                FileName = fileName
            };
            Response.Headers.ContentDisposition = cd.ToString();
            return File(stream, contentType, enableRangeProcessing: false);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting template file {TemplateId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError($"An error occurred: {ex.Message}"));
        }
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<PresentationTemplateDto>> GetTemplate(int id)
    {
        try
        {
            var template = await _templateService.GetTemplateAsync(id);
            return Ok(template);
        }
        catch (InvalidOperationException ex)
        {
            return NotFound(ErrorResponseDto.NotFound(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting template {TemplateId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError($"An error occurred: {ex.Message}"));
        }
    }

    [HttpDelete("{id}")]
    public async Task<ActionResult> DeleteTemplate(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var result = await _templateService.DeleteTemplateAsync(id, userId);
            if (!result)
            {
                return NotFound(ErrorResponseDto.NotFound("Template not found"));
            }

            return Ok(new { message = "Template deleted successfully" });
        }
        catch (UnauthorizedAccessException ex)
        {
            return Forbid(ex.Message);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting template {TemplateId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError($"An error occurred: {ex.Message}"));
        }
    }

    [HttpPost("{id}/generate")]
    public async Task<ActionResult<PresentationDto>> GenerateFromTemplate(
        int id,
        [FromBody] PresentationGenerationRequestDto request)
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

            if (request.UserId.HasValue)
            {
                userId = request.UserId.Value;
            }

            request.UserId = userId;
            var presentation = await _templateService.GenerateFromTemplateAsync(id, request);

            return Ok(presentation);
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ErrorResponseDto.BadRequest(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating presentation from template {TemplateId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError($"An error occurred: {ex.Message}"));
        }
    }
}
