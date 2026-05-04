using System.ComponentModel.DataAnnotations;

namespace AIAgentManagement.DTOs;

public class CreateConversationRequestDto
{
    public int? AgentId { get; set; }

    [Required]
    public int ServiceId { get; set; }

    public string? Title { get; set; }
    public string? Model { get; set; }
    public decimal? Temperature { get; set; }
    public int? MaxTokens { get; set; }
    public string? SystemPrompt { get; set; }
    public string? Language { get; set; } // 'ko', 'en', 'auto'
}
