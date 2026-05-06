using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

// ── Phase 6.4 (ADR-2): AgentHub 자체 KB 는 deprecate ───────────────────
// 신규 코드는 DocUtil 의 tb_documents 를 IDocUtilClient (Phase 6.1) 경유로 사용한다.
// 본 엔티티는 Phase 5+ 호환을 위해 보존되며, Phase 8+ 에서 DB drop + 데이터 마이그레이션과
// 함께 제거 예정. 신규 사용 시 CS0618 경고가 발생한다 (error: false).
// 참고: .claude/rules/anti-patterns.md §7, .claude/rules/architecture.md P8
// ----------------------------------------------------------------------
[Obsolete("ADR-2: AgentHub 자체 KB 는 deprecate 됨. 신규 코드는 DocUtil 의 tb_documents 를 IDocUtilClient 경유로 사용할 것. Phase 8+ 에서 drop 예정.", error: false)]
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
