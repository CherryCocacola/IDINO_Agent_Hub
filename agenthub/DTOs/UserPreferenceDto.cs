namespace AIAgentManagement.DTOs;

public class UserPreferenceDto
{
    public int PreferenceId { get; set; }
    public int UserId { get; set; }
    public string PreferenceKey { get; set; } = string.Empty;
    public string? PreferenceValue { get; set; }
    public string DataType { get; set; } = "String";
    public string? Category { get; set; }
    public string? Description { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}

public class CreateUserPreferenceRequestDto
{
    public string PreferenceKey { get; set; } = string.Empty;
    public string? PreferenceValue { get; set; }
    public string? DataType { get; set; }
    public string? Category { get; set; }
    public string? Description { get; set; }
}

public class UpdateUserPreferenceRequestDto
{
    public string? PreferenceValue { get; set; }
    public string? DataType { get; set; }
    public string? Category { get; set; }
    public string? Description { get; set; }
}
