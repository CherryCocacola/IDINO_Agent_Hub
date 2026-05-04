namespace AIAgentManagement.DTOs;

public class UserUsageDto
{
    public int UserId { get; set; }
    public string Email { get; set; } = string.Empty;
    public string FullName { get; set; } = string.Empty;
    public int RequestCount { get; set; }
    public decimal TotalCost { get; set; }
    public int TotalTokens { get; set; }
}
