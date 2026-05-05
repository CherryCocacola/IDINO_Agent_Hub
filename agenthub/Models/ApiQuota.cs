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

    [Required]
    public int MonthlyLimit { get; set; } = 1000;

    [Required]
    public int DailyLimit { get; set; } = 100;

    [Required]
    [Column(TypeName = "decimal(10, 2)")]
    public decimal CostLimit { get; set; } = 100.00m;

    [Required]
    public int CurrentUsage { get; set; } = 0;

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
