namespace AIAgentManagement.DTOs;

/// <summary>
/// 사용자 정보 외부 노출 DTO.
/// 트랙 #98 (2026-05-18) — 부서 트리 노출 + DocUtil 통합 호환 필드 추가:
///   - DepartmentId / DepartmentName / DepartmentPath: AgentHub Departments 트리 (회사 > 본부 > 팀)
///   - OrganizationId / Language: DocUtil tb_users VIEW 호환 (단일 조직 + i18n)
///   - Department(string) 는 호환을 위해 유지 — 2026-06-11 DROP 예정 (트랙 #88).
/// </summary>
public class UserDto
{
    public int UserId { get; set; }
    public string Email { get; set; } = string.Empty;
    public string FullName { get; set; } = string.Empty;
    public string? PhoneNumber { get; set; }

    /// <summary>레거시 부서명 문자열 (deprecated, 2026-06-11 DROP).</summary>
    public string? Department { get; set; }

    /// <summary>정규화된 부서 FK (Departments.DepartmentId).</summary>
    public int? DepartmentId { get; set; }

    /// <summary>부서 이름 (예: "Si 4팀").</summary>
    public string? DepartmentName { get; set; }

    /// <summary>부서 트리 전체 경로 (예: "아이디노(주) > M.SI본부 > Si 4팀").</summary>
    public string? DepartmentPath { get; set; }

    /// <summary>DocUtil tb_organizations.id 와 매핑되는 단일 조직 UUID.</summary>
    public Guid? OrganizationId { get; set; }

    /// <summary>사용자 언어 코드 (ko/en/vi). DocUtil tb_users.language 와 매핑.</summary>
    public string? Language { get; set; }

    public string? Bio { get; set; }
    public string? ProfileImageUrl { get; set; }
    public string Status { get; set; } = string.Empty;
    public List<string> Roles { get; set; } = new();
    public DateTime? LastLoginAt { get; set; }
    public DateTime CreatedAt { get; set; }
}
