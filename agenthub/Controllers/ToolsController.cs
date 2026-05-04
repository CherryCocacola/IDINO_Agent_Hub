using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class ToolsController : ControllerBase
{
    private readonly IToolService _toolService;
    private readonly IToolExecutionService _toolExecutionService;
    private readonly ILogger<ToolsController> _logger;

    public ToolsController(
        IToolService toolService,
        IToolExecutionService toolExecutionService,
        ILogger<ToolsController> logger)
    {
        _toolService = toolService;
        _toolExecutionService = toolExecutionService;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<List<ToolDto>>> GetTools(
        [FromQuery] int? userId,
        [FromQuery] bool? isPublic,
        [FromQuery] string? toolType,
        [FromQuery] string? search)
    {
        try
        {
            var tools = await _toolService.GetToolsAsync(userId, isPublic, toolType, search);
            return Ok(tools);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting tools");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<ToolDto>> GetTool(int id)
    {
        try
        {
            var tool = await _toolService.GetToolByIdAsync(id);
            if (tool == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(tool);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting tool {ToolId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost]
    public async Task<ActionResult<ToolDto>> CreateTool([FromBody] CreateToolRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var tool = await _toolService.CreateToolAsync(request, userId);
            return CreatedAtAction(nameof(GetTool), new { id = tool.ToolId }, tool);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating tool: {Message}", ex.Message);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPut("{id}")]
    public async Task<ActionResult<ToolDto>> UpdateTool(int id, [FromBody] UpdateToolRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var tool = await _toolService.UpdateToolAsync(id, request, userId);
            if (tool == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(tool);
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating tool {ToolId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpDelete("{id}")]
    public async Task<ActionResult> DeleteTool(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var result = await _toolService.DeleteToolAsync(id, userId);
            if (!result)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return NoContent();
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting tool {ToolId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("{id}/versions")]
    public async Task<ActionResult<List<ToolVersionDto>>> GetToolVersions(int id)
    {
        try
        {
            var versions = await _toolService.GetToolVersionsAsync(id);
            return Ok(versions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting tool versions for tool {ToolId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost("{id}/versions")]
    public async Task<ActionResult<ToolVersionDto>> CreateToolVersion(
        int id,
        [FromBody] CreateToolVersionRequestDto request)
    {
        try
        {
            var version = await _toolService.CreateToolVersionAsync(
                id,
                request.Version,
                request.Code,
                request.Config);

            return CreatedAtAction(nameof(GetToolVersions), new { id }, version);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating tool version: {Message}", ex.Message);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPut("{id}/versions/{versionId}/activate")]
    public async Task<ActionResult> ActivateToolVersion(int id, int versionId)
    {
        try
        {
            var result = await _toolService.SetActiveVersionAsync(id, versionId);
            if (!result)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error activating tool version");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost("{id}/execute")]
    public async Task<ActionResult<ToolExecutionDto>> ExecuteTool(
        int id,
        [FromBody] ExecuteToolRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            int? userId = null;
            if (!string.IsNullOrEmpty(userIdClaim) && int.TryParse(userIdClaim, out var parsedUserId))
            {
                userId = parsedUserId;
            }

            var execution = await _toolExecutionService.ExecuteToolAsync(id, request, userId);
            return Ok(execution);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error executing tool {ToolId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("executions")]
    public async Task<ActionResult<List<ToolExecutionDto>>> GetExecutions(
        [FromQuery] int? toolId,
        [FromQuery] int? userId,
        [FromQuery] string? status,
        [FromQuery] int skip = 0,
        [FromQuery] int take = 50)
    {
        try
        {
            var executions = await _toolExecutionService.GetExecutionsAsync(toolId, userId, status, skip, take);
            return Ok(executions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting tool executions");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("executions/{id}")]
    public async Task<ActionResult<ToolExecutionDto>> GetExecution(long id)
    {
        try
        {
            var execution = await _toolExecutionService.GetExecutionByIdAsync(id);
            if (execution == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(execution);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting execution {ExecutionId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }
}

public class CreateToolVersionRequestDto
{
    public string Version { get; set; } = string.Empty;
    public string? Code { get; set; }
    public string? Config { get; set; }
}
