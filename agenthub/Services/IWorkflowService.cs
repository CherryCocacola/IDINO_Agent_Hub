using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IWorkflowService
{
    Task<List<WorkflowDto>> GetWorkflowsAsync(int? userId = null, bool? isPublic = null, string? search = null);
    Task<WorkflowDto?> GetWorkflowByIdAsync(int workflowId);
    Task<WorkflowDto> CreateWorkflowAsync(CreateWorkflowRequestDto request, int createdBy);
    Task<WorkflowDto?> UpdateWorkflowAsync(int workflowId, UpdateWorkflowRequestDto request, int userId);
    Task<bool> DeleteWorkflowAsync(int workflowId, int userId);
}
