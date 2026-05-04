namespace AIAgentManagement.DTOs;

public class ImageGenerationResponseDto
{
    public List<string> ImageUrls { get; set; } = new();
    public string Prompt { get; set; } = string.Empty;
    public string Model { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; }
    public decimal Cost { get; set; }
    public int ResponseTime { get; set; } // milliseconds
    public int? ConversationId { get; set; } // 저장된 대화 ID
}
