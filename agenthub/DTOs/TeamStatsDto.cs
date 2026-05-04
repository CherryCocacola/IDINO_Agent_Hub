namespace AIAgentManagement.DTOs;

public class TeamStatsDto
{
    public int TotalMembers { get; set; }
    public int TotalApiCalls { get; set; }
    public decimal TotalCost { get; set; }
    public int SharedAgents { get; set; }
    public List<UserUsageDto> UserUsages { get; set; } = new();
}
