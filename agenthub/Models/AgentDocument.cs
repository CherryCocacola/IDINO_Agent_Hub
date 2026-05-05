using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("AgentDocuments")]
public class AgentDocument
{
    [Key]
    public int AgentDocumentId { get; set; }

    [Required]
    public int AgentId { get; set; }

    [Required]
    public int DocumentId { get; set; }

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("AgentId")]
    public virtual Agent Agent { get; set; } = null!;

    [ForeignKey("DocumentId")]
    public virtual KnowledgeBaseDocument Document { get; set; } = null!;
}
