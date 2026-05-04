namespace AIAgentManagement.DTOs;

public class UsageStatsDto
{
    public int ServiceId { get; set; }
    public string ServiceName { get; set; } = string.Empty;
    public DateTime Date { get; set; }
    public int RequestCount { get; set; }
    public int TotalTokens { get; set; }
    public decimal TotalCost { get; set; }
    public int AverageResponseTime { get; set; }
}
