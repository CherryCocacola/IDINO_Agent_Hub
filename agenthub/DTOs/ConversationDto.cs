namespace AIAgentManagement.DTOs;

public class ConversationDto
{
    public int ConversationId { get; set; }
    public int UserId { get; set; }
    public int? AgentId { get; set; }
    public string? AgentName { get; set; }
    public int ServiceId { get; set; }
    public string ServiceName { get; set; } = string.Empty;
    public string? Title { get; set; }
    public string? Model { get; set; }
    public decimal? Temperature { get; set; }
    public int? MaxTokens { get; set; }
    public int MessageCount { get; set; }
    public int TotalTokens { get; set; }
    public decimal TotalCost { get; set; }
    public DateTime? LastMessageAt { get; set; }
    public bool IsArchived { get; set; }
    public bool IsPinned { get; set; }
    public string? Language { get; set; } // 'ko', 'en', 'auto'
    public bool EnableRag { get; set; }
    public bool EnableWebSearch { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}
