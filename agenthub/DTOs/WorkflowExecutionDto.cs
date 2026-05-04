namespace AIAgentManagement.DTOs;

public class WorkflowExecutionDto
{
    public long ExecutionId { get; set; }
    public int WorkflowId { get; set; }
    public string WorkflowName { get; set; } = string.Empty;
    public int? UserId { get; set; }
    public string? InputData { get; set; }
    public string? OutputData { get; set; }
    public string Status { get; set; } = string.Empty;
    public string? ErrorMessage { get; set; }
    public DateTime StartedAt { get; set; }
    public DateTime? CompletedAt { get; set; }
    public int? ExecutionTime { get; set; }
    public List<WorkflowNodeExecutionDto>? NodeExecutions { get; set; }
}
