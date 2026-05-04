using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace AIAgentManagement.DTOs;

public class AgentChatRequestDto
{
    [Required]
    [JsonPropertyName("message")]
    public string Message { get; set; } = string.Empty;

    [JsonPropertyName("conversationId")]
    public int? ConversationId { get; set; }

    [JsonPropertyName("temperature")]
    public decimal? Temperature { get; set; }

    [JsonPropertyName("maxTokens")]
    public int? MaxTokens { get; set; }

    [JsonPropertyName("model")]
    public string? Model { get; set; }

    [JsonPropertyName("enableRag")]
    public bool? EnableRag { get; set; }

    [JsonPropertyName("enableWebSearch")]
    public bool? EnableWebSearch { get; set; }

    [JsonPropertyName("language")]
    public string? Language { get; set; } // 'ko', 'en', 'auto'

    [JsonPropertyName("ragTopK")]
    public int? RagTopK { get; set; }

    [JsonPropertyName("documentIds")]
    public List<int>? DocumentIds { get; set; }
}
