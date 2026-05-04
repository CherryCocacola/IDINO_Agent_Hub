namespace AIAgentManagement.DTOs;

public class WorkflowNodeExecutionDto
{
    public long NodeExecutionId { get; set; }
    public long ExecutionId { get; set; }
    public int NodeId { get; set; }
    public string NodeCode { get; set; } = string.Empty;
    public string NodeType { get; set; } = string.Empty;
    public string? InputData { get; set; }
    public string? OutputData { get; set; }
    public string Status { get; set; } = string.Empty;
    public string? ErrorMessage { get; set; }
    public DateTime StartedAt { get; set; }
    public DateTime? CompletedAt { get; set; }
    public int? ExecutionTime { get; set; }
}
