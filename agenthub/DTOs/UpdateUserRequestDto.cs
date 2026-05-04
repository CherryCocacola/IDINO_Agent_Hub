using System.ComponentModel.DataAnnotations;

namespace AIAgentManagement.DTOs;

public class UpdateUserRequestDto
{
    [MaxLength(100)]
    public string? FullName { get; set; }

    [MaxLength(20)]
    [Phone]
    public string? PhoneNumber { get; set; }

    [MaxLength(100)]
    public string? Department { get; set; }

    [MaxLength(500)]
    public string? Bio { get; set; }

    [RegularExpression("^(Active|Inactive|Suspended)$", ErrorMessage = "Status는 Active, Inactive, Suspended 중 하나여야 합니다.")]
    public string? Status { get; set; }

    public string? CurrentPassword { get; set; }

    [MinLength(8, ErrorMessage = "비밀번호는 최소 8자 이상이어야 합니다.")]
    public string? Password { get; set; }

    public List<int>? RoleIds { get; set; }
}
