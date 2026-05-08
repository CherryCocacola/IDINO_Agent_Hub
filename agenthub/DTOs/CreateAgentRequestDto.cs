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
    // ── LLM 라우팅 / RAG 권위 (Phase 5.1, ADR-1/ADR-2). null 시 서비스 레이어가 기본값 적용 ──
    public string? LlmRouting { get; set; }              // null → "External" 폴백
    public string? RoutingPolicyJson { get; set; }       // Hybrid 전용
    public string? KnowledgeBaseSource { get; set; }     // null → "AgentHub" 폴백
    public string? KnowledgeBaseRef { get; set; }        // DocUtil collection ID
    public string? ConsumerSystems { get; set; }         // 호출 화이트리스트 JSON
    // ───────────────────────────────────────────────────────────────────────
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
