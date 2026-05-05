using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("ChatConversations")]
public class ChatConversation
{
    [Key]
    public int ConversationId { get; set; }

    [Required]
    public int UserId { get; set; }

    public int? AgentId { get; set; }

    [Required]
    public int ServiceId { get; set; }

    [MaxLength(200)]
    public string? Title { get; set; }

    [MaxLength(100)]
    public string? Model { get; set; }

    [Column(TypeName = "decimal(3, 2)")]
    public decimal? Temperature { get; set; }

    public int? MaxTokens { get; set; }

    [Required]
    public int MessageCount { get; set; } = 0;

    [Required]
    public int TotalTokens { get; set; } = 0;

    [Required]
    [Column(TypeName = "decimal(10, 4)")]
    public decimal TotalCost { get; set; } = 0;

    public DateTime? LastMessageAt { get; set; }

    [Required]
    public bool IsArchived { get; set; } = false;

    [Required]
    public bool IsPinned { get; set; } = false;

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public string? SystemPrompt { get; set; }

    [MaxLength(10)]
    public string? Language { get; set; } // 'ko', 'en', 'auto'

    [Required]
    public bool EnableRag { get; set; } = false;

    [Required]
    public bool EnableWebSearch { get; set; } = false;

    // Navigation properties
    [ForeignKey("UserId")]
    public virtual User User { get; set; } = null!;

    [ForeignKey("AgentId")]
    public virtual Agent? Agent { get; set; }

    [ForeignKey("ServiceId")]
    public virtual ApiService ApiService { get; set; } = null!;

    public virtual ICollection<ChatMessage> ChatMessages { get; set; } = new List<ChatMessage>();
    public virtual ICollection<ApiUsage> ApiUsages { get; set; } = new List<ApiUsage>();
}
