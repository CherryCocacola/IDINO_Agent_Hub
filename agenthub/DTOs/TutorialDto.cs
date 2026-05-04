namespace AIAgentManagement.DTOs;

public class TutorialDto
{
    public int TutorialId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? VideoUrl { get; set; }
    public string? ThumbnailUrl { get; set; }
    public string? Duration { get; set; }
    public string? Category { get; set; }
    public int SortOrder { get; set; }
    public bool IsActive { get; set; }
    public int ViewCount { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}

public class CreateTutorialRequestDto
{
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? VideoUrl { get; set; }
    public string? ThumbnailUrl { get; set; }
    public string? Duration { get; set; }
    public string? Category { get; set; }
    public int SortOrder { get; set; } = 0;
    public bool IsActive { get; set; } = true;
}

public class UpdateTutorialRequestDto
{
    public string? Title { get; set; }
    public string? Description { get; set; }
    public string? VideoUrl { get; set; }
    public string? ThumbnailUrl { get; set; }
    public string? Duration { get; set; }
    public string? Category { get; set; }
    public int? SortOrder { get; set; }
    public bool? IsActive { get; set; }
}
