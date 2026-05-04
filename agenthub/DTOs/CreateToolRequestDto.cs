using System.ComponentModel.DataAnnotations;

namespace AIAgentManagement.DTOs;

public class CreateToolRequestDto
{
    public string? ToolCode { get; set; }

    [Required]
    public string ToolName { get; set; } = string.Empty;

    public string? Description { get; set; }

    [Required]
    public string ToolType { get; set; } = string.Empty; // CSharp, Python, JavaScript, Api

    public string? Category { get; set; }
    public string? IconClass { get; set; }
    public string? ColorCode { get; set; }
    public bool? IsPublic { get; set; }

    // 첫 버전 정보
    public string? Version { get; set; }
    public string? Code { get; set; }
    public string? Config { get; set; } // JSON 형식의 설정 (파라미터 정의 등)
}
