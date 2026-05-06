using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

// ── Phase 6.4 (ADR-2): AgentHub 자체 KB 청크는 deprecate ──────────────
// DocUtil 의 청크/임베딩(Qdrant) 으로 대체. 본 엔티티는 Phase 5+ 호환을 위해 보존.
// Phase 8+ 에서 DB drop + 데이터 마이그레이션과 함께 제거 예정.
// 참고: .claude/rules/anti-patterns.md §7, .claude/rules/architecture.md P8
// ----------------------------------------------------------------------
[Obsolete("ADR-2: AgentHub 자체 KB 청크는 deprecate 됨. 신규 코드는 DocUtil 의 청크/임베딩을 IDocUtilClient.GetChunksAsync 로 조회할 것. Phase 8+ 에서 drop 예정.", error: false)]
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
