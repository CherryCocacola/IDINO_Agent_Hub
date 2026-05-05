using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("Workflows")]
public class Workflow
{
    [Key]
    public int WorkflowId { get; set; }

    [Required]
    [MaxLength(50)]
    public string WorkflowCode { get; set; } = string.Empty;

    [Required]
    [MaxLength(100)]
    public string WorkflowName { get; set; } = string.Empty;

    [MaxLength(500)]
    public string? Description { get; set; }

    public string? WorkflowDefinition { get; set; } // JSON 형식의 전체 Workflow 정의

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

    public virtual ICollection<WorkflowNode> WorkflowNodes { get; set; } = new List<WorkflowNode>();
    public virtual ICollection<WorkflowExecution> WorkflowExecutions { get; set; } = new List<WorkflowExecution>();
}
