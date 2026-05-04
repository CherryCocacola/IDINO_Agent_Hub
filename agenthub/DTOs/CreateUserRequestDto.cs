using System.ComponentModel.DataAnnotations;

namespace AIAgentManagement.DTOs;

public class CreateUserRequestDto
{
    [Required]
    [EmailAddress]
    public string Email { get; set; } = string.Empty;

    [Required]
    [MinLength(8)]
    public string Password { get; set; } = string.Empty;

    [Required]
    public string FullName { get; set; } = string.Empty;

    public string? PhoneNumber { get; set; }
    public string? Department { get; set; }
    public string? Status { get; set; }
    public List<int>? RoleIds { get; set; }
}
