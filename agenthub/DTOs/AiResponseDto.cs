namespace AIAgentManagement.DTOs;

public class AiResponseDto
{
    public string Content { get; set; } = string.Empty;
    public string Model { get; set; } = string.Empty;
    public string FinishReason { get; set; } = string.Empty;
    public int PromptTokens { get; set; }
    public int CompletionTokens { get; set; }
    public int TotalTokens { get; set; }
    public int ResponseTime { get; set; } // milliseconds
    public decimal? Cost { get; set; }
    public List<string>? Citations { get; set; } // Perplexity AI citations
    public List<string>? ImageUrls { get; set; } // Gemini 3 Pro Image 편집된 이미지 URL들
}
