namespace AIAgentManagement.DTOs;

public class ToolExecutionDto
{
    public long ExecutionId { get; set; }
    public int ToolId { get; set; }
    public string ToolName { get; set; } = string.Empty;
    public int? VersionId { get; set; }
    public string? Version { get; set; }
    public int? UserId { get; set; }
    public string? InputData { get; set; }
    public string? OutputData { get; set; }
    public string Status { get; set; } = string.Empty;
    public string? ErrorMessage { get; set; }
    public int? ExecutionTime { get; set; }
    public long? MemoryUsage { get; set; }
    public DateTime CreatedAt { get; set; }
}
