using System.ComponentModel.DataAnnotations;

namespace AIAgentManagement.DTOs;

public class CreateAgentRequestDto
{
    public string? AgentCode { get; set; }

    [Required]
    public string AgentName { get; set; } = string.Empty;

    public string? Description { get; set; }

    [Required]
    public int ServiceId { get; set; }

    public string? SystemPrompt { get; set; }
    public string? IconClass { get; set; }
    public string? ColorCode { get; set; }
    [Range(0.0, 2.0, ErrorMessage = "Temperature는 0.0~2.0 사이여야 합니다.")]
    public decimal? Temperature { get; set; }

    [Range(1, 128000, ErrorMessage = "MaxTokens는 1~128000 사이여야 합니다.")]
    public int? MaxTokens { get; set; }
    public string? DefaultModel { get; set; }
    public bool? IsPublic { get; set; }
    public int? SortOrder { get; set; }
    public bool EnableRag { get; set; } = false;
    public bool? PiiProtectionEnabled { get; set; }
    public string? PiiProtectionMode { get; set; }
    public List<int>? SelectedDocumentIds { get; set; }
    // 공유 / 임베드 설정
    public string? WelcomeMessage { get; set; }
    public string? PlaceholderText { get; set; }
    public string? ChatTheme { get; set; }
    public bool AllowGuestChat { get; set; } = false;
    public string? AllowedEmbedDomains { get; set; }
}
