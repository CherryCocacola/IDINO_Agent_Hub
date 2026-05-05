using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("Tools")]
public class Tool
{
    [Key]
    public int ToolId { get; set; }

    [Required]
    [MaxLength(50)]
    public string ToolCode { get; set; } = string.Empty;

    [Required]
    [MaxLength(100)]
    public string ToolName { get; set; } = string.Empty;

    [MaxLength(500)]
    public string? Description { get; set; }

    [Required]
    [MaxLength(20)]
    public string ToolType { get; set; } = string.Empty; // CSharp, Python, JavaScript, Api

    [MaxLength(50)]
    public string? Category { get; set; }

    [MaxLength(100)]
    public string? IconClass { get; set; }

    [MaxLength(20)]
    public string? ColorCode { get; set; }

    [Required]
    public int CreatedBy { get; set; }

    [Required]
    public bool IsPublic { get; set; } = false;

    [Required]
    public bool IsActive { get; set; } = true;

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("CreatedBy")]
    public virtual User Creator { get; set; } = null!;

    public virtual ICollection<ToolVersion> ToolVersions { get; set; } = new List<ToolVersion>();
    public virtual ICollection<ToolExecution> ToolExecutions { get; set; } = new List<ToolExecution>();
}
