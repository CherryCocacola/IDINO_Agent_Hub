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

    /// <summary>
    /// API 키 분류 (트랙 #91 — ApiKeyPoolService DB 통합).
    /// <list type="bullet">
    /// <item><c>"External"</c> — 외부 노출용 키. 사용자가 외부 시스템(OpenAI SDK 등)에서 AgentHub <c>/v1/*</c>
    /// 또는 <c>/api/agents/{id}/chat</c> 을 호출할 때 사용하는 <c>ak-...</c> 형식 키 (`ApiKeyAuthService` 인증 대상).</item>
    /// <item><c>"Provider"</c> — 외부 LLM 키 풀(`IApiKeyPoolService`) 용 키. 운영자가 콘솔에서 등록한
    /// OpenAI/Claude/Gemini 등 외부 LLM 호출용 평문 키. AgentHub 내부 `AiProxyService` 가 풀에서 라운드로빈으로 꺼내 사용.</item>
    /// </list>
    /// 두 종류를 같은 `ApiKeys` 테이블에 두되 `KeyType` 으로 격리하여 인증 핫패스(External) 와 풀 갱신(Provider) 을 분리.
    /// </summary>
    [Required]
    [MaxLength(20)]
    public string KeyType { get; set; } = "External";

    public int? AgentId { get; set; } // Agent 전용 API Key인 경우

    [Required]
    [MaxLength(500)]
    public string EncryptedKey { get; set; } = string.Empty; // 암호화된 API 키 (AES-GCM ciphertext, base64)

    /// <summary>
    /// AES-GCM nonce (12바이트). per-record 무작위 생성으로 결정적 암호화를 차단한다.
    /// TECHSPEC §16 C1 — 고정 IV(`new byte[16]`) 결함 해소를 위한 신규 컬럼.
    /// 기존 행(legacy CBC)에서는 NULL — Phase 3.6 백필 마이그레이션 전까지 폴백 분기로 처리.
    /// </summary>
    public byte[]? KeyIv { get; set; }

    /// <summary>
    /// AES-GCM 인증 태그 (16바이트). 무결성 검증 + ciphertext 변조 차단.
    /// TECHSPEC §16 C1 — AEAD 부재 결함 해소를 위한 신규 컬럼.
    /// 기존 행(legacy CBC)에서는 NULL — Phase 3.6 백필 전까지 폴백 분기로 처리.
    /// </summary>
    public byte[]? KeyTag { get; set; }

    /// <summary>
    /// 평문 API 키의 SHA-256 해시 (대문자 16진수, 64자).
    /// 인증 핫패스에서 UNIQUE 인덱스 조회로 O(N) 풀스캔을 O(log N)으로 단축한다.
    /// TECHSPEC §16 C3 — 풀스캔 + 전수 복호화 결함 해소를 위한 신규 컬럼.
    /// 기존 행(legacy)에서는 NULL — 폴백 풀스캔 분기에서 즉시 백필.
    /// </summary>
    [MaxLength(64)]
    public string? KeyHash { get; set; }

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
