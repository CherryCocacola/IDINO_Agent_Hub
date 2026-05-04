namespace AIAgentManagement.DTOs;

public class KnowledgeBaseDocumentListDto
{
    public int DocumentId { get; set; }
    public int UserId { get; set; }
    public string UserName { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string SourceType { get; set; } = string.Empty;
    public string? SourceId { get; set; }
    public bool IsIndexed { get; set; }
    public DateTime? IndexedAt { get; set; }
    public int ChunkCount { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}
