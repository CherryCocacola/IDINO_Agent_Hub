using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("WorkflowExecutions")]
public class WorkflowExecution
{
    [Key]
    public long ExecutionId { get; set; }

    [Required]
    public int WorkflowId { get; set; }

    public int? UserId { get; set; }

    public string? InputData { get; set; } // JSON 형식

    public string? OutputData { get; set; } // JSON 형식

    [Required]
    [MaxLength(20)]
    public string Status { get; set; } = "Running"; // Running, Completed, Failed, Cancelled

    public string? ErrorMessage { get; set; }

    [Required]
    public DateTime StartedAt { get; set; } = DateTime.UtcNow;

    public DateTime? CompletedAt { get; set; }

    public int? ExecutionTime { get; set; } // 밀리초

    // Navigation properties
    [ForeignKey("WorkflowId")]
    public virtual Workflow Workflow { get; set; } = null!;

    [ForeignKey("UserId")]
    public virtual User? User { get; set; }

    public virtual ICollection<WorkflowNodeExecution> WorkflowNodeExecutions { get; set; } = new List<WorkflowNodeExecution>();
}
