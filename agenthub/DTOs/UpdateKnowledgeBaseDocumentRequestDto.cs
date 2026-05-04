using System.ComponentModel.DataAnnotations;

namespace AIAgentManagement.DTOs;

public class UpdateKnowledgeBaseDocumentRequestDto
{
    [MaxLength(500)]
    public string? Title { get; set; }

    public string? Content { get; set; }

    [MaxLength(50)]
    public string? SourceType { get; set; }

    [MaxLength(255)]
    public string? SourceId { get; set; }

    public bool? Reindex { get; set; } // 내용 변경 시 재인덱싱 여부
}
