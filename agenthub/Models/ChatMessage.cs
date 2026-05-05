using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("ChatMessages")]
public class ChatMessage
{
    [Key]
    public long MessageId { get; set; }

    [Required]
    public int ConversationId { get; set; }

    [Required]
    [MaxLength(20)]
    public string Role { get; set; } = string.Empty; // user, assistant, system

    [Required]
    public string Content { get; set; } = string.Empty;

    public int? TokensUsed { get; set; }

    [MaxLength(100)]
    public string? Model { get; set; }

    [MaxLength(50)]
    public string? FinishReason { get; set; }

    public string? Attachments { get; set; }

    public string? Metadata { get; set; }

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("ConversationId")]
    public virtual ChatConversation ChatConversation { get; set; } = null!;
}
