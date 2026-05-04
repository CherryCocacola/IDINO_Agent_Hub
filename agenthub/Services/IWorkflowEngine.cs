namespace AIAgentManagement.Services;

public interface IWorkflowEngine
{
    Task<WorkflowExecutionResult> ExecuteAsync(int workflowId, string? inputData, CancellationToken cancellationToken = default);
}

public class WorkflowExecutionResult
{
    public bool Success { get; set; }
    public string? OutputData { get; set; }
    public string? ErrorMessage { get; set; }
    public Dictionary<int, NodeExecutionResult> NodeResults { get; set; } = new();
    public int TotalExecutionTime { get; set; }
}

public class NodeExecutionResult
{
    public int NodeId { get; set; }
    public string Status { get; set; } = string.Empty;
    public string? InputData { get; set; }
    public string? OutputData { get; set; }
    public string? ErrorMessage { get; set; }
    public int ExecutionTime { get; set; }
}
