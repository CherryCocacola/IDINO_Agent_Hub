using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("ApiUsages")]
public class ApiUsage
{
    [Key]
    public long UsageId { get; set; }

    [Required]
    public int UserId { get; set; }

    [Required]
    public int ServiceId { get; set; }

    public int? ConversationId { get; set; }

    [MaxLength(100)]
    public string? Model { get; set; }

    public int? TokensUsed { get; set; }

    [Required]
    [Column(TypeName = "decimal(10, 4)")]
    public decimal RequestCost { get; set; } = 0;

    [Required]
    public DateTime RequestTime { get; set; } = DateTime.UtcNow;

    public int? ResponseTime { get; set; }

    public int? StatusCode { get; set; }

    public string? ErrorMessage { get; set; }

    /// <summary>사용자 프롬프트 앞 500자 — ChatMessages 별도 쿼리 없이 내역 표시용</summary>
    [MaxLength(500)]
    public string? Prompt { get; set; }

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("UserId")]
    public virtual User User { get; set; } = null!;

    [ForeignKey("ServiceId")]
    public virtual ApiService ApiService { get; set; } = null!;

    [ForeignKey("ConversationId")]
    public virtual ChatConversation? ChatConversation { get; set; }
}
