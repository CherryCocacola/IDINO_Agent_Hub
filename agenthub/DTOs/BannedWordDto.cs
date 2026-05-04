namespace AIAgentManagement.DTOs;

public class BannedWordDto
{
    public int BannedWordId { get; set; }
    public string Word { get; set; } = string.Empty;
    public int? AgentId { get; set; }
    public string? AgentName { get; set; }
    public string? Description { get; set; }
    public bool IsActive { get; set; }
    public int CreatedBy { get; set; }
    public string? CreatedByName { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}

public class CreateBannedWordRequestDto
{
    public string Word { get; set; } = string.Empty;
    public int? AgentId { get; set; }
    public string? Description { get; set; }
}

public class UpdateBannedWordRequestDto
{
    public string? Word { get; set; }
    public int? AgentId { get; set; }
    public string? Description { get; set; }
    public bool? IsActive { get; set; }
}

public class BannedWordCheckResult
{
    public bool IsBlocked { get; set; }
    public List<string> BlockedWords { get; set; } = new();
}
