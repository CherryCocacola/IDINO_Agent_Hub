using System.ComponentModel.DataAnnotations;

namespace AIAgentManagement.DTOs;

public class CreateWorkflowRequestDto
{
    public string? WorkflowCode { get; set; }

    [Required]
    public string WorkflowName { get; set; } = string.Empty;

    public string? Description { get; set; }
    public string? WorkflowDefinition { get; set; } // JSON 형식
    public string? IconClass { get; set; }
    public string? ColorCode { get; set; }
    public bool? IsPublic { get; set; }
    public List<WorkflowNodeDto>? Nodes { get; set; }
}
