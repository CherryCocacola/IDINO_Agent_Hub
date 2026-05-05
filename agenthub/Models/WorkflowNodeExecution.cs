using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("WorkflowNodeExecutions")]
public class WorkflowNodeExecution
{
    [Key]
    public long NodeExecutionId { get; set; }

    [Required]
    public long ExecutionId { get; set; }

    [Required]
    public int NodeId { get; set; }

    public string? InputData { get; set; } // JSON 형식

    public string? OutputData { get; set; } // JSON 형식

    [Required]
    [MaxLength(20)]
    public string Status { get; set; } = "Running"; // Running, Completed, Failed, Skipped

    public string? ErrorMessage { get; set; }

    [Required]
    public DateTime StartedAt { get; set; } = DateTime.UtcNow;

    public DateTime? CompletedAt { get; set; }

    public int? ExecutionTime { get; set; } // 밀리초

    // Navigation properties
    [ForeignKey("ExecutionId")]
    public virtual WorkflowExecution WorkflowExecution { get; set; } = null!;

    [ForeignKey("NodeId")]
    public virtual WorkflowNode WorkflowNode { get; set; } = null!;
}
