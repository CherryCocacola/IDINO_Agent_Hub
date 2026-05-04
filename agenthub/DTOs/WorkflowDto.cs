namespace AIAgentManagement.DTOs;

public class WorkflowDto
{
    public int WorkflowId { get; set; }
    public string WorkflowCode { get; set; } = string.Empty;
    public string WorkflowName { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? WorkflowDefinition { get; set; } // JSON 형식
    public string? IconClass { get; set; }
    public string? ColorCode { get; set; }
    public int CreatedBy { get; set; }
    public string CreatedByName { get; set; } = string.Empty;
    public bool IsPublic { get; set; }
    public bool IsActive { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public List<WorkflowNodeDto>? Nodes { get; set; }
}
