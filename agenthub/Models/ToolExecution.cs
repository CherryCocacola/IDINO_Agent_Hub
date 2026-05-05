using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("ToolExecutions")]
public class ToolExecution
{
    [Key]
    public long ExecutionId { get; set; }

    [Required]
    public int ToolId { get; set; }

    public int? VersionId { get; set; }

    public int? UserId { get; set; }

    public string? InputData { get; set; } // JSON 형식

    public string? OutputData { get; set; } // JSON 형식

    [Required]
    [MaxLength(20)]
    public string Status { get; set; } = "Running"; // Running, Completed, Failed, Cancelled

    public string? ErrorMessage { get; set; }

    public int? ExecutionTime { get; set; } // 밀리초

    public long? MemoryUsage { get; set; } // 바이트

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("ToolId")]
    public virtual Tool Tool { get; set; } = null!;

    [ForeignKey("VersionId")]
    public virtual ToolVersion? ToolVersion { get; set; }

    [ForeignKey("UserId")]
    public virtual User? User { get; set; }
}
