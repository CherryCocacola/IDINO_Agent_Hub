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
