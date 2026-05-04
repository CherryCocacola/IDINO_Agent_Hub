namespace AIAgentManagement.DTOs;

public class PiiDetectionLogDto
{
    public int LogId { get; set; }
    public int? UserId { get; set; }
    public string? UserName { get; set; }
    public int? AgentId { get; set; }
    public string? AgentName { get; set; }
    public int? ConversationId { get; set; }
    public string DetectionType { get; set; } = string.Empty;
    public string DetectionTypeName { get; set; } = string.Empty;
    public string OriginalMessage { get; set; } = string.Empty;
    public string ActionTaken { get; set; } = string.Empty;
    public DateTime DetectedAt { get; set; }
    public string? IpAddress { get; set; }
}

public class PiiDetectionStatisticsDto
{
    public int TotalDetections { get; set; }
    public int BlockedCount { get; set; }
    public int MaskedCount { get; set; }
    public Dictionary<string, int> DetectionTypeCounts { get; set; } = new();
    public Dictionary<string, int> DailyCounts { get; set; } = new();
    public Dictionary<string, int> AgentCounts { get; set; } = new();
    public Dictionary<string, int> UserCounts { get; set; } = new();
}
