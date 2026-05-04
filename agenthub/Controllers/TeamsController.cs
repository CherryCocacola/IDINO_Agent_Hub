using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class TeamsController : ControllerBase
{
    private readonly ITeamService _teamService;
    private readonly ILogger<TeamsController> _logger;

    public TeamsController(ITeamService teamService, ILogger<TeamsController> logger)
    {
        _teamService = teamService;
        _logger = logger;
    }

    [HttpGet]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<List<TeamDto>>> GetTeams([FromQuery] string? search, [FromQuery] bool? isActive)
    {
        try
        {
            var teams = await _teamService.GetTeamsAsync(search, isActive);
            return Ok(teams);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting teams");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("{id}")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<TeamDto>> GetTeam(int id)
    {
        try
        {
            var team = await _teamService.GetTeamByIdAsync(id);
            if (team == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }
            return Ok(team);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting team {TeamId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<TeamDto>> CreateTeam([FromBody] CreateTeamRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var team = await _teamService.CreateTeamAsync(request, userId);
            return CreatedAtAction(nameof(GetTeam), new { id = team.TeamId }, team);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating team");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPut("{id}")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<TeamDto>> UpdateTeam(int id, [FromBody] UpdateTeamRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var team = await _teamService.UpdateTeamAsync(id, request, userId);
            if (team == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }
            return Ok(team);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating team {TeamId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpDelete("{id}")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult> DeleteTeam(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var result = await _teamService.DeleteTeamAsync(id, userId);
            if (!result)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }
            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting team {TeamId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost("{id}/members")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<TeamMemberDto>> AddTeamMember(int id, [FromBody] AddTeamMemberRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var addedBy))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var member = await _teamService.AddTeamMemberAsync(id, request, addedBy);
            return Ok(member);
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ErrorResponseDto.BadRequest(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error adding team member to team {TeamId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpDelete("{id}/members/{userId}")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult> RemoveTeamMember(int id, int userId)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var removedBy))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var result = await _teamService.RemoveTeamMemberAsync(id, userId, removedBy);
            if (!result)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }
            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error removing team member from team {TeamId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPut("{id}/members/{userId}/role")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult> UpdateTeamMemberRole(int id, int userId, [FromBody] UpdateTeamMemberRoleRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var updatedBy))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var result = await _teamService.UpdateTeamMemberRoleAsync(id, userId, request.Role, updatedBy);
            if (!result)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }
            return Ok(new { message = "Team member role updated" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating team member role in team {TeamId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }
}

public class UpdateTeamMemberRoleRequestDto
{
    public string? Role { get; set; }
}
