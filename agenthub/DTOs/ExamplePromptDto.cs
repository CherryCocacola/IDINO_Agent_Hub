namespace AIAgentManagement.DTOs;

public class ExamplePromptDto
{
    public int ExamplePromptId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Prompt { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? ServiceCode { get; set; }
    public string? Model { get; set; }
    public string? Category { get; set; }
    public string? IconClass { get; set; }
    public int SortOrder { get; set; }
    public bool IsActive { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}

public class CreateExamplePromptRequestDto
{
    public string Title { get; set; } = string.Empty;
    public string Prompt { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? ServiceCode { get; set; }
    public string? Model { get; set; }
    public string? Category { get; set; }
    public string? IconClass { get; set; }
    public int SortOrder { get; set; } = 0;
    public bool IsActive { get; set; } = true;
}

public class UpdateExamplePromptRequestDto
{
    public string? Title { get; set; }
    public string? Prompt { get; set; }
    public string? Description { get; set; }
    public string? ServiceCode { get; set; }
    public string? Model { get; set; }
    public string? Category { get; set; }
    public string? IconClass { get; set; }
    public int? SortOrder { get; set; }
    public bool? IsActive { get; set; }
}
