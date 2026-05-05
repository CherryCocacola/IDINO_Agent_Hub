using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("ToolVersions")]
public class ToolVersion
{
    [Key]
    public int VersionId { get; set; }

    [Required]
    public int ToolId { get; set; }

    [Required]
    [MaxLength(20)]
    public string Version { get; set; } = string.Empty;

    public string? Code { get; set; } // Tool 코드 (C#, Python, JavaScript 등)

    public string? Config { get; set; } // JSON 형식의 설정 (파라미터 정의 등)

    [Required]
    public bool IsActive { get; set; } = true;

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("ToolId")]
    public virtual Tool Tool { get; set; } = null!;

    public virtual ICollection<ToolExecution> ToolExecutions { get; set; } = new List<ToolExecution>();
}
