using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("DocumentChunks")]
public class DocumentChunk
{
    [Key]
    public long ChunkId { get; set; }

    [Required]
    public int DocumentId { get; set; }

    [Required]
    public int ChunkIndex { get; set; } // 청크 순서

    [Required]
    public string Content { get; set; } = string.Empty;

    public string? Embedding { get; set; } // JSON 배열로 벡터 저장

    public string? Metadata { get; set; } // JSON 형식의 메타데이터

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // Navigation property
    [ForeignKey("DocumentId")]
    public virtual KnowledgeBaseDocument? Document { get; set; }
}
