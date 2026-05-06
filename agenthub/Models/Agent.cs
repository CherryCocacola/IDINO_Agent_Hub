using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("Agents")]
public class Agent
{
    [Key]
    public int AgentId { get; set; }

    [Required]
    [MaxLength(50)]
    public string AgentCode { get; set; } = string.Empty;

    [Required]
    [MaxLength(100)]
    public string AgentName { get; set; } = string.Empty;

    [MaxLength(500)]
    public string? Description { get; set; }

    [Required]
    public int ServiceId { get; set; }

    public string? SystemPrompt { get; set; }

    [MaxLength(100)]
    public string? IconClass { get; set; }

    [MaxLength(20)]
    public string? ColorCode { get; set; }

    [Column(TypeName = "decimal(3, 2)")]
    public decimal? Temperature { get; set; } = 0.7m;

    public int? MaxTokens { get; set; } = 4096;

    [MaxLength(100)]
    public string? DefaultModel { get; set; }

    [Required]
    public bool IsPublic { get; set; } = true;

    [Required]
    public int CreatedBy { get; set; }

    [Required]
    public bool IsActive { get; set; } = true;

    [Required]
    public int SortOrder { get; set; } = 0;

    [Required]
    public bool EnableRag { get; set; } = false;

    // ── LLM 라우팅 정책 (Phase 5.1, TECHSPEC §15.4 / ADR-1) ─────────────────
    /// <summary>
    /// LLM 라우팅 모드. AgentHub 통합 아키텍처(P3) 의 라우팅 단위 — Agent 별로 결정한다.
    /// - "External": 외부 LLM (OpenAI/Claude/Gemini/...) — 기존 ApiKeyPool 경유
    /// - "Internal": 사내 LAN-only Nexus (옵션 B, AiProxyService.CallNexusAsync 경유)
    /// - "Hybrid": 런타임 라우팅 정책(아래 RoutingPolicyJson) 평가 후 분기
    /// 값은 항상 PascalCase 문자열로 저장한다. 빈 값/NULL 은 "External" 폴백.
    /// </summary>
    [Required]
    [MaxLength(16)]
    public string LlmRouting { get; set; } = "External";

    /// <summary>
    /// LlmRouting="Hybrid" 일 때만 의미 있는 라우팅 결정 규칙(JSON 직렬화).
    /// HybridRouter (Phase 5.2 도입 예정) 가 평가한다. 외부망/내부망 분기 기준 카탈로그는
    /// .claude/rules/domain-model.md 의 RoutingPolicyJson 스키마 참조.
    /// 예: { "piiThreshold":"block","piiAction":"internal","dataLabels":{...},
    ///       "modelCapability":{"vision":"external"},"costThreshold":{...},"default":"external" }
    /// External/Internal 모드에서는 NULL.
    /// </summary>
    [Column(TypeName = "text")]
    public string? RoutingPolicyJson { get; set; }

    /// <summary>
    /// 지식베이스(RAG) 권위 시스템. ADR-2 에 따라 통합 후 단일 권위는 "DocUtil".
    /// 기존 자체 KB(KnowledgeBaseDocument) 를 사용하는 Agent 는 "AgentHub" 폴백
    /// (Phase 6 에서 DocUtil 로 마이그레이션 예정 — deprecate 대상).
    /// </summary>
    [Required]
    [MaxLength(32)]
    public string KnowledgeBaseSource { get; set; } = "AgentHub";

    /// <summary>
    /// 외부 KB 시스템에서 사용하는 collection 식별자.
    /// - KnowledgeBaseSource="DocUtil" 일 때: DocUtil collection ID
    /// - KnowledgeBaseSource="AgentHub" 일 때: NULL (AgentDocuments 조인으로 결정)
    /// </summary>
    [MaxLength(100)]
    public string? KnowledgeBaseRef { get; set; }

    /// <summary>
    /// 이 Agent 를 호출할 수 있는 End-User App 화이트리스트(JSON 배열).
    /// 예: ["docutil-user","career-coaching"]
    /// NULL 이면 모든 등록된 ConsumerSystem 에 노출 (운영자 콘솔 호출 한정).
    /// .claude/rules/domain-model.md 의 End-User App 카탈로그 참조.
    /// </summary>
    [Column(TypeName = "text")]
    public string? ConsumerSystems { get; set; }
    // ───────────────────────────────────────────────────────────────────────

    [Required]
    public bool PiiProtectionEnabled { get; set; } = true;

    [MaxLength(20)]
    public string? PiiProtectionMode { get; set; } // NULL이면 전역 설정 사용, "Block" 또는 "Mask"

    // ── 공유 / 임베드 설정 ──────────────────────────────────────────
    /// <summary>챗봇 페이지 시작 시 봇이 먼저 보내는 환영 메시지</summary>
    [MaxLength(500)]
    public string? WelcomeMessage { get; set; }

    /// <summary>입력창 placeholder 문구</summary>
    [MaxLength(200)]
    public string? PlaceholderText { get; set; }

    /// <summary>챗봇 테마: "light" | "dark" | "auto"</summary>
    [MaxLength(10)]
    public string? ChatTheme { get; set; } = "light";

    /// <summary>비로그인(게스트) 사용자의 퍼블릭 채팅 허용 여부</summary>
    [Required]
    public bool AllowGuestChat { get; set; } = false;

    /// <summary>
    /// iframe 임베드를 허용할 도메인 목록 (쉼표 구분, null=전체허용).
    /// 예: "https://example.com,https://partner.com"
    /// </summary>
    [MaxLength(2000)]
    public string? AllowedEmbedDomains { get; set; }

    // ───────────────────────────────────────────────────────────────

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("ServiceId")]
    public virtual ApiService ApiService { get; set; } = null!;

    [ForeignKey("CreatedBy")]
    public virtual User Creator { get; set; } = null!;

    public virtual ICollection<ChatConversation> ChatConversations { get; set; } = new List<ChatConversation>();

    public virtual ICollection<AgentDocument> AgentDocuments { get; set; } = new List<AgentDocument>();
}
