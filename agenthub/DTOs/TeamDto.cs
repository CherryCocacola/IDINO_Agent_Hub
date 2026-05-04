namespace AIAgentManagement.DTOs;

public class TeamDto
{
    public int TeamId { get; set; }
    public string TeamName { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? Department { get; set; }
    public int? ManagerId { get; set; }
    public string? ManagerName { get; set; }
    public string? ManagerEmail { get; set; }
    public bool IsActive { get; set; }
    public int MemberCount { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public List<TeamMemberDto> Members { get; set; } = new();
}

public class TeamMemberDto
{
    public int TeamMemberId { get; set; }
    public int TeamId { get; set; }
    public int UserId { get; set; }
    public string UserName { get; set; } = string.Empty;
    public string UserEmail { get; set; } = string.Empty;
    public string? Role { get; set; } // 팀 내 역할
    public DateTime JoinedAt { get; set; }
    public bool IsActive { get; set; }
}

public class CreateTeamRequestDto
{
    public string TeamName { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? Department { get; set; }
    public int? ManagerId { get; set; }
}

public class UpdateTeamRequestDto
{
    public string? TeamName { get; set; }
    public string? Description { get; set; }
    public string? Department { get; set; }
    public int? ManagerId { get; set; }
    public bool? IsActive { get; set; }
}

public class AddTeamMemberRequestDto
{
    public int UserId { get; set; }
    public string? Role { get; set; } // 팀 내 역할
}
