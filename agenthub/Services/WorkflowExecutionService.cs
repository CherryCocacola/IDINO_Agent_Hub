using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

public class WorkflowExecutionService : IWorkflowExecutionService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly IWorkflowEngine _workflowEngine;
    private readonly ILogger<WorkflowExecutionService> _logger;

    public WorkflowExecutionService(
        AIAgentManagementDbContext context,
        IWorkflowEngine workflowEngine,
        ILogger<WorkflowExecutionService> logger)
    {
        _context = context;
        _workflowEngine = workflowEngine;
        _logger = logger;
    }

    public async Task<WorkflowExecutionDto> ExecuteWorkflowAsync(int workflowId, ExecuteWorkflowRequestDto request, int? userId = null)
    {
        var workflow = await _context.Workflows
            .FirstOrDefaultAsync(w => w.WorkflowId == workflowId && w.IsActive);

        if (workflow == null)
        {
            throw new InvalidOperationException($"Workflow {workflowId} not found or inactive");
        }

        // 실행 기록 생성
        var execution = new WorkflowExecution
        {
            WorkflowId = workflowId,
            UserId = userId,
            InputData = request.InputData,
            Status = "Running",
            StartedAt = DateTime.UtcNow
        };

        _context.WorkflowExecutions.Add(execution);
        await _context.SaveChangesAsync();

        // 비동기 실행 (WaitForCompletion이 false인 경우)
        if (request.WaitForCompletion == false)
        {
            _ = Task.Run(async () =>
            {
                try
                {
                    await ExecuteWorkflowInternalAsync(execution.ExecutionId, workflowId, request.InputData);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error in background workflow execution");
                }
            });

            return MapToDto(execution, workflow);
        }

        // 동기 실행
        try
        {
            var result = await _workflowEngine.ExecuteAsync(workflowId, request.InputData);

            execution.Status = result.Success ? "Completed" : "Failed";
            execution.OutputData = result.OutputData;
            execution.ErrorMessage = result.ErrorMessage;
            execution.CompletedAt = DateTime.UtcNow;
            execution.ExecutionTime = result.TotalExecutionTime;

            // 노드 실행 기록 저장
            foreach (var nodeResult in result.NodeResults)
            {
                var nodeExecution = new WorkflowNodeExecution
                {
                    ExecutionId = execution.ExecutionId,
                    NodeId = nodeResult.Key,
                    InputData = nodeResult.Value.InputData,
                    OutputData = nodeResult.Value.OutputData,
                    Status = nodeResult.Value.Status,
                    ErrorMessage = nodeResult.Value.ErrorMessage,
                    StartedAt = DateTime.UtcNow,
                    CompletedAt = DateTime.UtcNow,
                    ExecutionTime = nodeResult.Value.ExecutionTime
                };

                _context.WorkflowNodeExecutions.Add(nodeExecution);
            }

            await _context.SaveChangesAsync();
        }
        catch (Exception ex)
        {
            execution.Status = "Failed";
            execution.ErrorMessage = ex.Message;
            execution.CompletedAt = DateTime.UtcNow;
            await _context.SaveChangesAsync();

            _logger.LogError(ex, "Error executing workflow {WorkflowId}", workflowId);
        }

        return MapToDto(execution, workflow);
    }

    private async Task ExecuteWorkflowInternalAsync(long executionId, int workflowId, string? inputData)
    {
        var execution = await _context.WorkflowExecutions.FindAsync(executionId);
        if (execution == null) return;

        try
        {
            var result = await _workflowEngine.ExecuteAsync(workflowId, inputData);

            execution.Status = result.Success ? "Completed" : "Failed";
            execution.OutputData = result.OutputData;
            execution.ErrorMessage = result.ErrorMessage;
            execution.CompletedAt = DateTime.UtcNow;
            execution.ExecutionTime = result.TotalExecutionTime;

            // 노드 실행 기록 저장
            foreach (var nodeResult in result.NodeResults)
            {
                var nodeExecution = new WorkflowNodeExecution
                {
                    ExecutionId = execution.ExecutionId,
                    NodeId = nodeResult.Key,
                    InputData = nodeResult.Value.InputData,
                    OutputData = nodeResult.Value.OutputData,
                    Status = nodeResult.Value.Status,
                    ErrorMessage = nodeResult.Value.ErrorMessage,
                    StartedAt = DateTime.UtcNow,
                    CompletedAt = DateTime.UtcNow,
                    ExecutionTime = nodeResult.Value.ExecutionTime
                };

                _context.WorkflowNodeExecutions.Add(nodeExecution);
            }

            await _context.SaveChangesAsync();
        }
        catch (Exception ex)
        {
            execution.Status = "Failed";
            execution.ErrorMessage = ex.Message;
            execution.CompletedAt = DateTime.UtcNow;
            await _context.SaveChangesAsync();

            _logger.LogError(ex, "Error in background workflow execution");
        }
    }

    public async Task<WorkflowExecutionDto?> GetExecutionByIdAsync(long executionId)
    {
        var execution = await _context.WorkflowExecutions
            .AsNoTracking()
            .Include(e => e.Workflow)
            .Include(e => e.WorkflowNodeExecutions)
            .ThenInclude(ne => ne.WorkflowNode)
            .FirstOrDefaultAsync(e => e.ExecutionId == executionId);

        if (execution == null)
        {
            return null;
        }

        return MapToDto(execution, execution.Workflow);
    }

    public async Task<List<WorkflowExecutionDto>> GetExecutionsAsync(int? workflowId = null, int? userId = null, string? status = null, int skip = 0, int take = 50)
    {
        var query = _context.WorkflowExecutions
            .AsNoTracking()
            .Include(e => e.Workflow)
            .AsQueryable();

        if (workflowId.HasValue)
        {
            query = query.Where(e => e.WorkflowId == workflowId.Value);
        }

        if (userId.HasValue)
        {
            query = query.Where(e => e.UserId == userId.Value);
        }

        if (!string.IsNullOrEmpty(status))
        {
            query = query.Where(e => e.Status == status);
        }

        var executions = await query
            .OrderByDescending(e => e.StartedAt)
            .Skip(skip)
            .Take(take)
            .ToListAsync();

        return executions.Select(e => MapToDto(e, e.Workflow)).ToList();
    }

    public async Task<bool> CancelExecutionAsync(long executionId, int userId)
    {
        var execution = await _context.WorkflowExecutions
            .FirstOrDefaultAsync(e => e.ExecutionId == executionId && e.Status == "Running");

        if (execution == null)
        {
            return false;
        }

        if (execution.UserId != userId)
        {
            throw new UnauthorizedAccessException("You don't have permission to cancel this execution");
        }

        execution.Status = "Cancelled";
        execution.CompletedAt = DateTime.UtcNow;
        await _context.SaveChangesAsync();

        return true;
    }

    private WorkflowExecutionDto MapToDto(WorkflowExecution execution, Workflow workflow)
    {
        return new WorkflowExecutionDto
        {
            ExecutionId = execution.ExecutionId,
            WorkflowId = execution.WorkflowId,
            WorkflowName = workflow.WorkflowName,
            UserId = execution.UserId,
            InputData = execution.InputData,
            OutputData = execution.OutputData,
            Status = execution.Status,
            ErrorMessage = execution.ErrorMessage,
            StartedAt = execution.StartedAt,
            CompletedAt = execution.CompletedAt,
            ExecutionTime = execution.ExecutionTime,
            NodeExecutions = execution.WorkflowNodeExecutions?.Select(ne => new WorkflowNodeExecutionDto
            {
                NodeExecutionId = ne.NodeExecutionId,
                ExecutionId = ne.ExecutionId,
                NodeId = ne.NodeId,
                NodeCode = ne.WorkflowNode?.NodeCode ?? "",
                NodeType = ne.WorkflowNode?.NodeType ?? "",
                InputData = ne.InputData,
                OutputData = ne.OutputData,
                Status = ne.Status,
                ErrorMessage = ne.ErrorMessage,
                StartedAt = ne.StartedAt,
                CompletedAt = ne.CompletedAt,
                ExecutionTime = ne.ExecutionTime
            }).ToList()
        };
    }
}
