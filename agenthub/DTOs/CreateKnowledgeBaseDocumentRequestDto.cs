using System.ComponentModel.DataAnnotations;

namespace AIAgentManagement.DTOs;

public class CreateKnowledgeBaseDocumentRequestDto
{
    [Required]
    [MaxLength(500)]
    public string Title { get; set; } = string.Empty;

    [Required]
    public string Content { get; set; } = string.Empty;

    [MaxLength(50)]
    public string SourceType { get; set; } = "KnowledgeBase";

    [MaxLength(255)]
    public string? SourceId { get; set; }

    public bool IndexImmediately { get; set; } = true; // 즉시 인덱싱 여부
}
