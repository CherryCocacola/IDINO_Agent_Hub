using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("PiiDetectionLogs")]
public class PiiDetectionLog
{
    [Key]
    public int LogId { get; set; }

    public int? UserId { get; set; }

    public int? AgentId { get; set; }

    public int? ConversationId { get; set; }

    [Required]
    [MaxLength(50)]
    public string DetectionType { get; set; } = string.Empty; // PhoneNumber, ResidentNumber 등

    [Required]
    public string OriginalMessage { get; set; } = string.Empty; // 원본 메시지 (일부만 저장, 전체는 저장하지 않음)

    [Required]
    public string ActionTaken { get; set; } = string.Empty; // "Block" or "Mask"

    [Required]
    public DateTime DetectedAt { get; set; } = DateTime.UtcNow;

    [MaxLength(50)]
    public string? IpAddress { get; set; }

    // Navigation properties
    [ForeignKey("UserId")]
    public virtual User? User { get; set; }

    [ForeignKey("AgentId")]
    public virtual Agent? Agent { get; set; }
}
