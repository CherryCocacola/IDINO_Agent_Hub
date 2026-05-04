namespace AIAgentManagement.DTOs;

public class RagSearchResultDto
{
    public int DocumentId { get; set; }
    public long ChunkId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public float Similarity { get; set; }
    public string Source { get; set; } = string.Empty;
    public string? Metadata { get; set; } // JSON
}
