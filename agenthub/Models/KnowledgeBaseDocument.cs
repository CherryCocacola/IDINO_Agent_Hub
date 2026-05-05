using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("KnowledgeBaseDocuments")]
public class KnowledgeBaseDocument
{
    [Key]
    public int DocumentId { get; set; }

    [Required]
    public int UserId { get; set; }

    [Required]
    [MaxLength(500)]
    public string Title { get; set; } = string.Empty;

    [Required]
    public string Content { get; set; } = string.Empty;

    [Required]
    [MaxLength(50)]
    public string SourceType { get; set; } = string.Empty; // "KnowledgeBase" or "UploadedFile"

    [MaxLength(255)]
    public string? SourceId { get; set; } // 파일 경로 또는 문서 ID

    [Required]
    public bool IsIndexed { get; set; } = false;

    public DateTime? IndexedAt { get; set; }

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("UserId")]
    public virtual User? User { get; set; }

    public virtual ICollection<DocumentChunk> Chunks { get; set; } = new List<DocumentChunk>();
}
