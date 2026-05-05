using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("BannedWords")]
public class BannedWord
{
    [Key]
    public int BannedWordId { get; set; }

    [Required]
    [MaxLength(200)]
    public string Word { get; set; } = string.Empty;

    public int? AgentId { get; set; } // NULL이면 전역 금칙어, 값이 있으면 해당 Agent 전용

    [MaxLength(500)]
    public string? Description { get; set; }

    [Required]
    public bool IsActive { get; set; } = true;

    [Required]
    public int CreatedBy { get; set; } // 등록한 관리자 ID

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("AgentId")]
    public virtual Agent? Agent { get; set; }

    [ForeignKey("CreatedBy")]
    public virtual User Creator { get; set; } = null!;
}
