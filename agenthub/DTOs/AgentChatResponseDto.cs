using System.Text.Json.Serialization;

namespace AIAgentManagement.DTOs;

public class AgentChatResponseDto
{
    [JsonPropertyName("messageId")]
    public int MessageId { get; set; }

    [JsonPropertyName("conversationId")]
    public int? ConversationId { get; set; }

    [JsonPropertyName("content")]
    public string Content { get; set; } = string.Empty;

    [JsonPropertyName("model")]
    public string Model { get; set; } = string.Empty;

    [JsonPropertyName("tokensUsed")]
    public int? TokensUsed { get; set; }

    [JsonPropertyName("cost")]
    public decimal? Cost { get; set; }

    [JsonPropertyName("responseTime")]
    public int ResponseTime { get; set; }

    [JsonPropertyName("citations")]
    public List<string>? Citations { get; set; }
}
