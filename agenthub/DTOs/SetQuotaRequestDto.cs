namespace AIAgentManagement.DTOs;

public class SetQuotaRequestDto
{
    public int? MonthlyLimit { get; set; }
    public int? DailyLimit { get; set; }
    public decimal? CostLimit { get; set; }
    public int? AlertThreshold { get; set; }
    public bool? IsAlertEnabled { get; set; }
}
