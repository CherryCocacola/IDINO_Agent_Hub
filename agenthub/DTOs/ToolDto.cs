namespace AIAgentManagement.DTOs;

public class ToolDto
{
    public int ToolId { get; set; }
    public string ToolCode { get; set; } = string.Empty;
    public string ToolName { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string ToolType { get; set; } = string.Empty; // CSharp, Python, JavaScript, Api
    public string? Category { get; set; }
    public string? IconClass { get; set; }
    public string? ColorCode { get; set; }
    public int CreatedBy { get; set; }
    public string CreatedByName { get; set; } = string.Empty;
    public bool IsPublic { get; set; }
    public bool IsActive { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public ToolVersionDto? ActiveVersion { get; set; }
}
