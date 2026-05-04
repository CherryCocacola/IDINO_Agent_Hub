namespace AIAgentManagement.DTOs;

public class WorkflowNodeDto
{
    public int NodeId { get; set; }
    public int WorkflowId { get; set; }
    public string NodeCode { get; set; } = string.Empty;
    public string NodeType { get; set; } = string.Empty; // Agent, LLM, Tool, Condition, Loop, Merge, DataTransform
    public string? NodeConfig { get; set; } // JSON 형식
    public double? PositionX { get; set; }
    public double? PositionY { get; set; }
    public string? Connections { get; set; } // JSON 형식
    public int SortOrder { get; set; }
}
