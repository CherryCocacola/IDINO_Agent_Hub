using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("WorkflowNodes")]
public class WorkflowNode
{
    [Key]
    public int NodeId { get; set; }

    [Required]
    public int WorkflowId { get; set; }

    [Required]
    [MaxLength(50)]
    public string NodeCode { get; set; } = string.Empty;

    [Required]
    [MaxLength(20)]
    public string NodeType { get; set; } = string.Empty; // Agent, LLM, Tool, Condition, Loop, Merge, DataTransform

    public string? NodeConfig { get; set; } // JSON 형식의 노드 설정

    public double? PositionX { get; set; }

    public double? PositionY { get; set; }

    public string? Connections { get; set; } // JSON 형식의 연결 정보

    [Required]
    public int SortOrder { get; set; } = 0;

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("WorkflowId")]
    public virtual Workflow Workflow { get; set; } = null!;

    public virtual ICollection<WorkflowNodeExecution> WorkflowNodeExecutions { get; set; } = new List<WorkflowNodeExecution>();
}
