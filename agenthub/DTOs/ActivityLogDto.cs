namespace AIAgentManagement.DTOs;

public class ActivityLogDto
{
    public long LogId { get; set; }
    public int? UserId { get; set; }
    public string? UserName { get; set; }
    public string ActivityType { get; set; } = string.Empty;
    public string? EntityType { get; set; }
    public int? EntityId { get; set; }
    public string? Description { get; set; }
    public string? IpAddress { get; set; }
    public string? UserAgent { get; set; }
    public string? Details { get; set; }
    public DateTime CreatedAt { get; set; }
}
