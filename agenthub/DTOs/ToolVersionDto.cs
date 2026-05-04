namespace AIAgentManagement.DTOs;

public class ToolVersionDto
{
    public int VersionId { get; set; }
    public int ToolId { get; set; }
    public string Version { get; set; } = string.Empty;
    public string? Code { get; set; }
    public string? Config { get; set; } // JSON 형식
    public bool IsActive { get; set; }
    public DateTime CreatedAt { get; set; }
}
