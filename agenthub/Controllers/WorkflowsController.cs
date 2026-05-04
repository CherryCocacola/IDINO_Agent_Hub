using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class WorkflowsController : ControllerBase
{
    private readonly IWorkflowService _workflowService;
    private readonly IWorkflowExecutionService _workflowExecutionService;
    private readonly ILogger<WorkflowsController> _logger;

    public WorkflowsController(
        IWorkflowService workflowService,
        IWorkflowExecutionService workflowExecutionService,
        ILogger<WorkflowsController> logger)
    {
        _workflowService = workflowService;
        _workflowExecutionService = workflowExecutionService;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<List<WorkflowDto>>> GetWorkflows(
        [FromQuery] int? userId,
        [FromQuery] bool? isPublic,
        [FromQuery] string? search)
    {
        try
        {
            var workflows = await _workflowService.GetWorkflowsAsync(userId, isPublic, search);
            return Ok(workflows);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting workflows");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<WorkflowDto>> GetWorkflow(int id)
    {
        try
        {
            var workflow = await _workflowService.GetWorkflowByIdAsync(id);
            if (workflow == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(workflow);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting workflow {WorkflowId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost]
    public async Task<ActionResult<WorkflowDto>> CreateWorkflow([FromBody] CreateWorkflowRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var workflow = await _workflowService.CreateWorkflowAsync(request, userId);
            return CreatedAtAction(nameof(GetWorkflow), new { id = workflow.WorkflowId }, workflow);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating workflow: {Message}", ex.Message);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPut("{id}")]
    public async Task<ActionResult<WorkflowDto>> UpdateWorkflow(int id, [FromBody] UpdateWorkflowRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var workflow = await _workflowService.UpdateWorkflowAsync(id, request, userId);
            if (workflow == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(workflow);
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating workflow {WorkflowId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpDelete("{id}")]
    public async Task<ActionResult> DeleteWorkflow(int id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var result = await _workflowService.DeleteWorkflowAsync(id, userId);
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
            _logger.LogError(ex, "Error deleting workflow {WorkflowId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost("{id}/execute")]
    public async Task<ActionResult<WorkflowExecutionDto>> ExecuteWorkflow(
        int id,
        [FromBody] ExecuteWorkflowRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            int? userId = null;
            if (!string.IsNullOrEmpty(userIdClaim) && int.TryParse(userIdClaim, out var parsedUserId))
            {
                userId = parsedUserId;
            }

            var execution = await _workflowExecutionService.ExecuteWorkflowAsync(id, request, userId);
            return Ok(execution);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error executing workflow {WorkflowId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("executions")]
    public async Task<ActionResult<List<WorkflowExecutionDto>>> GetExecutions(
        [FromQuery] int? workflowId,
        [FromQuery] int? userId,
        [FromQuery] string? status,
        [FromQuery] int skip = 0,
        [FromQuery] int take = 50)
    {
        try
        {
            var executions = await _workflowExecutionService.GetExecutionsAsync(workflowId, userId, status, skip, take);
            return Ok(executions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting workflow executions");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("executions/{id}")]
    public async Task<ActionResult<WorkflowExecutionDto>> GetExecution(long id)
    {
        try
        {
            var execution = await _workflowExecutionService.GetExecutionByIdAsync(id);
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

    [HttpPost("executions/{id}/cancel")]
    public async Task<ActionResult> CancelExecution(long id)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var result = await _workflowExecutionService.CancelExecutionAsync(id, userId);
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
            _logger.LogError(ex, "Error cancelling execution {ExecutionId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }
}
