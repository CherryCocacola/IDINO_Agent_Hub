using System.ComponentModel.DataAnnotations;

namespace AIAgentManagement.DTOs;

public class SendMessageRequestDto
{
    [Required]
    public string Message { get; set; } = string.Empty;

    public bool? Stream { get; set; }
    public bool? EnableWebSearch { get; set; }
    public bool? EnableRag { get; set; }
    public int? RagTopK { get; set; }
    public string? Language { get; set; } // 'ko', 'en', 'auto'
}
