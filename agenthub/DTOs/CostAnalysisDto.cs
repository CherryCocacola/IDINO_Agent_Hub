namespace AIAgentManagement.DTOs;

public class CostAnalysisDto
{
    public decimal TotalCost { get; set; }
    public DateTime StartDate { get; set; }
    public DateTime EndDate { get; set; }
    public List<ServiceCostDto> ServiceCosts { get; set; } = new();
}

public class ServiceCostDto
{
    public int ServiceId { get; set; }
    public string ServiceName { get; set; } = string.Empty;
    public decimal TotalCost { get; set; }
    public int RequestCount { get; set; }
    public decimal Percentage { get; set; }
}
