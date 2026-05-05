namespace AIAgentManagement.DTOs;

public class SetQuotaRequestDto
{
    public int? MonthlyLimit { get; set; }
    /// <summary>월간 토큰 한도 (선택). NULL 이면 변경하지 않음. Phase 3.3d 신설.</summary>
    public long? MonthlyTokenLimit { get; set; }
    public int? DailyLimit { get; set; }
    public decimal? CostLimit { get; set; }
    public int? AlertThreshold { get; set; }
    public bool? IsAlertEnabled { get; set; }
}
