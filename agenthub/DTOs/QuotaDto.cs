namespace AIAgentManagement.DTOs;

public class QuotaDto
{
    public int QuotaId { get; set; }
    public int UserId { get; set; }
    public string UserEmail { get; set; } = string.Empty;
    public int ServiceId { get; set; }
    public string ServiceName { get; set; } = string.Empty;
    public int MonthlyLimit { get; set; }
    public int DailyLimit { get; set; }
    public decimal CostLimit { get; set; }
    public int CurrentUsage { get; set; }
    public decimal CurrentCost { get; set; }
    public int AlertThreshold { get; set; }
    public bool IsAlertEnabled { get; set; }
    public DateTime? LastResetAt { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}
