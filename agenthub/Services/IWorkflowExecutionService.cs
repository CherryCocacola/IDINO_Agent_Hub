using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IWorkflowExecutionService
{
    Task<WorkflowExecutionDto> ExecuteWorkflowAsync(int workflowId, ExecuteWorkflowRequestDto request, int? userId = null);
    Task<WorkflowExecutionDto?> GetExecutionByIdAsync(long executionId);
    Task<List<WorkflowExecutionDto>> GetExecutionsAsync(int? workflowId = null, int? userId = null, string? status = null, int skip = 0, int take = 50);
    Task<bool> CancelExecutionAsync(long executionId, int userId);
}
