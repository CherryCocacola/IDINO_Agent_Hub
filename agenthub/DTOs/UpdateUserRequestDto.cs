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

    /// <summary>
    /// 트랙 #147 (2026-06-01) M2 — 프로필 사진. base64 data URL 형식
    /// ("data:image/png;base64,..."). 약 200KB (base64 인코딩 후) 미만 권장.
    /// 빈 문자열 전달 시 제거 (NULL 로 저장), null 전달 시 기존 값 유지.
    /// </summary>
    [MaxLength(300_000)]
    public string? ProfileImageUrl { get; set; }

    // 트랙 #120 (2026-05-27): DB CHECK constraint (Active/Pending/Inactive) 와 일치.
    // 이전: Suspended 가 잘못 정의됐고 Pending 누락 → 사용자 상태 '대기' 변경 시 400 결함.
    // Pending = 신규 가입 후 관리자 승인 대기 (CreateUser default 상태).
    [RegularExpression("^(Active|Pending|Inactive)$", ErrorMessage = "Status는 Active, Pending, Inactive 중 하나여야 합니다.")]
    public string? Status { get; set; }

    public string? CurrentPassword { get; set; }

    [MinLength(8, ErrorMessage = "비밀번호는 최소 8자 이상이어야 합니다.")]
    public string? Password { get; set; }

    public List<int>? RoleIds { get; set; }
}
