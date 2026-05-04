namespace AIAgentManagement.DTOs;

public class ApiUsageDto
{
    public long UsageId { get; set; }
    public int UserId { get; set; }
    public string? UserName { get; set; }
    public int ServiceId { get; set; }
    public string ServiceName { get; set; } = string.Empty;
    public string? Model { get; set; }
    public int? TokensUsed { get; set; }
    public decimal RequestCost { get; set; }
    public DateTime RequestTime { get; set; }
    public int? ResponseTime { get; set; }
    public int? StatusCode { get; set; }
    public string? ErrorMessage { get; set; }
    public string? Prompt { get; set; }
}
