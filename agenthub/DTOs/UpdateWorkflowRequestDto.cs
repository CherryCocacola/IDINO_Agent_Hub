namespace AIAgentManagement.DTOs;

public class UpdateWorkflowRequestDto
{
    public string? WorkflowName { get; set; }
    public string? Description { get; set; }
    public string? WorkflowDefinition { get; set; } // JSON 형식
    public string? IconClass { get; set; }
    public string? ColorCode { get; set; }
    public bool? IsPublic { get; set; }
    public bool? IsActive { get; set; }
    public List<WorkflowNodeDto>? Nodes { get; set; }
}
