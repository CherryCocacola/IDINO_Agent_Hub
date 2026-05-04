namespace AIAgentManagement.DTOs;

public class QuotaCheckResult
{
    public bool CanUse { get; set; }
    public string Message { get; set; } = string.Empty;
}
