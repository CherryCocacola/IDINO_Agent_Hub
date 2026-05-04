namespace AIAgentManagement.DTOs;

public class UpdateToolRequestDto
{
    public string? ToolName { get; set; }
    public string? Description { get; set; }
    public string? Category { get; set; }
    public string? IconClass { get; set; }
    public string? ColorCode { get; set; }
    public bool? IsPublic { get; set; }
    public bool? IsActive { get; set; }
}
