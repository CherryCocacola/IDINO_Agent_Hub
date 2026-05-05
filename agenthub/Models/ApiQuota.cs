using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("ApiQuotas")]
public class ApiQuota
{
    [Key]
    public int QuotaId { get; set; }

    [Required]
    public int UserId { get; set; }

    [Required]
    public int ServiceId { get; set; }

    /// <summary>
    /// 월간 호출 횟수 한도 (요청 건수 단위). 0 이하는 미적용으로 해석한다.
    /// </summary>
    [Required]
    public int MonthlyLimit { get; set; } = 1000;

    /// <summary>
    /// 월간 토큰 한도 (선택). NULL 이면 토큰 기준 한도 미적용 — 기존 호출 횟수/비용 기준만 사용.
    /// LLM 비용 구조상 호출 횟수보다 토큰 누적이 더 정확한 cost driver 이므로 병행 운영한다.
    /// </summary>
    public long? MonthlyTokenLimit { get; set; }

    [Required]
    public int DailyLimit { get; set; } = 100;

    [Required]
    [Column(TypeName = "decimal(10, 2)")]
    public decimal CostLimit { get; set; } = 100.00m;

    /// <summary>
    /// 월간 누적 호출 횟수 (RecordUsageAsync 호출 시마다 +1).
    /// </summary>
    [Required]
    public int CurrentUsage { get; set; } = 0;

    /// <summary>
    /// 월간 누적 토큰 수 (Phase 3.3d / TECHSPEC §16 H10 — 호출 시 tokens 인자 누적).
    /// int 범위(약 21억) 초과 가능성이 있어 long 으로 정의 — Npgsql 기본 매핑은 bigint.
    /// </summary>
    [Required]
    public long CurrentTokens { get; set; } = 0L;

    [Required]
    [Column(TypeName = "decimal(10, 2)")]
    public decimal CurrentCost { get; set; } = 0.00m;

    [Required]
    public int AlertThreshold { get; set; } = 80;

    [Required]
    public bool IsAlertEnabled { get; set; } = true;

    public DateTime? LastResetAt { get; set; }

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("UserId")]
    public virtual User User { get; set; } = null!;

    [ForeignKey("ServiceId")]
    public virtual ApiService ApiService { get; set; } = null!;
}
