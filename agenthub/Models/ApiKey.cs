using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("ApiKeys")]
public class ApiKey
{
    [Key]
    public int ApiKeyId { get; set; }

    [Required]
    public int UserId { get; set; }

    [Required]
    [MaxLength(100)]
    public string KeyName { get; set; } = string.Empty;

    [MaxLength(50)]
    public string ServiceCode { get; set; } = string.Empty; // chatgpt, claude, gemini, agent-api, etc.

    public int? AgentId { get; set; } // Agent 전용 API Key인 경우

    [Required]
    [MaxLength(500)]
    public string EncryptedKey { get; set; } = string.Empty; // 암호화된 API 키

    [MaxLength(500)]
    public string? Description { get; set; }

    public DateTime? ExpiresAt { get; set; }

    [Required]
    public bool IsActive { get; set; } = true;

    public DateTime? LastUsedAt { get; set; }

    public int UsageCount { get; set; } = 0;

    // ── 보안 확장 필드 ─────────────────────────────────────────
    /// <summary>
    /// 허용된 IP 목록 (쉼표 구분, 예: "192.168.1.1,10.0.0.0").
    /// null 또는 빈 문자열이면 모든 IP 허용.
    /// </summary>
    [MaxLength(2000)]
    public string? AllowedIps { get; set; }

    /// <summary>
    /// 허용된 스코프 목록 (쉼표 구분, 예: "chat,stream,info").
    /// null 또는 빈 문자열이면 모든 스코프 허용.
    /// 지원 값: chat | stream | info | usage
    /// </summary>
    [MaxLength(200)]
    public string? Scopes { get; set; }

    /// <summary>분당 최대 요청 수. null이면 무제한.</summary>
    public int? RateLimitPerMinute { get; set; }

    /// <summary>일당 최대 요청 수. null이면 무제한.</summary>
    public int? RateLimitPerDay { get; set; }

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("UserId")]
    public virtual User User { get; set; } = null!;

    [ForeignKey("AgentId")]
    public virtual Agent? Agent { get; set; }
}
