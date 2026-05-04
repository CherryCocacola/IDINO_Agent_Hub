using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class BannedWordsController : ControllerBase
{
    private readonly IBannedWordService _bannedWordService;
    private readonly ILogger<BannedWordsController> _logger;

    public BannedWordsController(
        IBannedWordService bannedWordService,
        ILogger<BannedWordsController> logger)
    {
        _bannedWordService = bannedWordService;
        _logger = logger;
    }

    [HttpGet]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<object>> GetBannedWords(
        [FromQuery] int? agentId,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20)
    {
        try
        {
            if (page < 1) page = 1;
            if (pageSize < 1 || pageSize > 100) pageSize = 20;

            var (items, totalCount) = await _bannedWordService.GetBannedWordsAsync(agentId, page, pageSize);
            
            return Ok(new
            {
                items,
                totalCount,
                page,
                pageSize,
                totalPages = (int)Math.Ceiling((double)totalCount / pageSize)
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting banned words. AgentId: {AgentId}, Page: {Page}, PageSize: {PageSize}", agentId, page, pageSize);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<BannedWordDto>> CreateBannedWord([FromBody] CreateBannedWordRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            if (string.IsNullOrWhiteSpace(request.Word))
            {
                return BadRequest(ErrorResponseDto.BadRequest("Word is required"));
            }

            var bannedWord = await _bannedWordService.CreateBannedWordAsync(request, userId);
            return CreatedAtAction(nameof(GetBannedWords), new { agentId = bannedWord.AgentId }, bannedWord);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating banned word");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPut("{id}")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<BannedWordDto>> UpdateBannedWord(int id, [FromBody] UpdateBannedWordRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var bannedWord = await _bannedWordService.UpdateBannedWordAsync(id, request, userId);
            if (bannedWord == null)
            {
                return NotFound(ErrorResponseDto.NotFound("Banned word not found"));
            }

            return Ok(bannedWord);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating banned word {BannedWordId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpDelete("{id}")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult> DeleteBannedWord(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var deleted = await _bannedWordService.DeleteBannedWordAsync(id, userId);
            if (!deleted)
            {
                return NotFound(ErrorResponseDto.NotFound("Banned word not found"));
            }

            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting banned word {BannedWordId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }
}
