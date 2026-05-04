namespace AIAgentManagement.DTOs;

public class ApiServiceDto
{
    public int ServiceId { get; set; }
    public string ServiceCode { get; set; } = string.Empty;
    public string ServiceName { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? IconClass { get; set; }
    public string? ColorCode { get; set; }
    public string? DefaultModel { get; set; }
    public decimal CostPerRequest { get; set; }
    public bool IsActive { get; set; }
    public string ServiceType { get; set; } = "Chat";
}
