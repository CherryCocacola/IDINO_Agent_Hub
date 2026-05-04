namespace AIAgentManagement.DTOs;

public class DashboardStatsDto
{
    public int TotalUsers { get; set; }
    public int ActiveUsers { get; set; }
    public int TodayApiCalls { get; set; }
    public decimal ThisMonthCost { get; set; }
}
