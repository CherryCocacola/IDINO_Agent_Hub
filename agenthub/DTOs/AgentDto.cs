namespace AIAgentManagement.DTOs;

public class AgentDto
{
    public int AgentId { get; set; }
    public string AgentCode { get; set; } = string.Empty;
    public string AgentName { get; set; } = string.Empty;
    public string? Description { get; set; }
    public int ServiceId { get; set; }
    public string ServiceName { get; set; } = string.Empty;
    public string? SystemPrompt { get; set; }
    public string? IconClass { get; set; }
    public string? ColorCode { get; set; }
    public decimal? Temperature { get; set; }
    public int? MaxTokens { get; set; }
    public string? DefaultModel { get; set; }
    public bool IsPublic { get; set; }
    public bool EnableRag { get; set; }
    public int SortOrder { get; set; }
    // ── LLM 라우팅 / RAG 권위 (Phase 5.1, ADR-1/ADR-2). Vue 운영자 콘솔 외부 표면 정합성 ──
    public string LlmRouting { get; set; } = "External";       // External / Internal / Hybrid
    public string? RoutingPolicyJson { get; set; }              // Hybrid 전용 결정 규칙(JSON)
    public string KnowledgeBaseSource { get; set; } = "AgentHub"; // Phase 6+ 는 "DocUtil"
    public string? KnowledgeBaseRef { get; set; }               // DocUtil collection ID
    public string? ConsumerSystems { get; set; }                // 호출 가능 End-User App 화이트리스트 JSON
    // ──────────────────────────────────────────────────────────────────────
    public bool PiiProtectionEnabled { get; set; }
    public string? PiiProtectionMode { get; set; }
    // 공유 / 임베드 설정
    public string? WelcomeMessage { get; set; }
    public string? PlaceholderText { get; set; }
    public string? ChatTheme { get; set; }
    public bool AllowGuestChat { get; set; }
    public string? AllowedEmbedDomains { get; set; }
    public int CreatedBy { get; set; }
    public string CreatedByName { get; set; } = string.Empty;
    public bool IsActive { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    // ── Phase 8 (ADR-2): Documents 필드는 자체 KB 제거와 함께 폐기. RAG Agent 는
    // Agent.KnowledgeBaseSource="DocUtil" + Agent.KnowledgeBaseRef 로 식별한다.
}
