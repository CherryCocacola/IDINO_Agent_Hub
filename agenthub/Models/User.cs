using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("Users")]
public class User
{
    [Key]
    public int UserId { get; set; }

    [Required]
    [MaxLength(100)]
    public string Email { get; set; } = string.Empty;

    [Required]
    [MaxLength(255)]
    public string PasswordHash { get; set; } = string.Empty;

    [Required]
    [MaxLength(100)]
    public string FullName { get; set; } = string.Empty;

    [MaxLength(20)]
    public string? PhoneNumber { get; set; }

    [MaxLength(100)]
    [Obsolete("트랙 #88 — DepartmentId FK 로 정규화. 2026-06-11 DROP 예정.")]
    public string? Department { get; set; }

    /// <summary>
    /// 트랙 #88 — 소속 부서 FK (Departments.DepartmentId). NULL 허용 (미배정 사용자).
    /// 기존 Department string 컬럼은 deprecate 후 30일 read-only 유예.
    /// </summary>
    public int? DepartmentId { get; set; }

    /// <summary>
    /// 트랙 #88 — DocUtil tb_users.id (uuid) 와의 매핑. NULL 허용 (DocUtil 미사용 사용자).
    /// UNIQUE 제약 — 한 AgentHub User 는 한 DocUtil 사용자에만 매핑.
    /// </summary>
    public Guid? OriginalDocutilUuid { get; set; }

    /// <summary>
    /// 트랙 #98 (2026-05-18) — DocUtil tb_organizations.id 와 매핑되는 단일 조직 UUID.
    /// DocUtil tb_users VIEW 의 organization_id 컬럼을 채우는 데 사용.
    /// 현재 단일 조직 "아이디노" (00000000-0000-4000-a000-000000000001) 만 운영.
    /// </summary>
    public Guid? OrganizationId { get; set; }

    /// <summary>
    /// 트랙 #98 — 사용자 i18n 언어 코드 (ko/en/vi). DocUtil tb_users.language 와 매핑.
    /// </summary>
    [MaxLength(10)]
    public string? Language { get; set; }

    /// <summary>
    /// 트랙 #98 — 로그인 실패 누적 카운트 (계정 잠금 정책). DocUtil tb_users.failed_login_count.
    /// </summary>
    public int FailedLoginCount { get; set; }

    /// <summary>
    /// 트랙 #98 — 계정 잠금 만료 시각. DocUtil tb_users.locked_until.
    /// </summary>
    public DateTime? LockedUntil { get; set; }

    [MaxLength(500)]
    public string? Bio { get; set; }

    public string? ProfileImageUrl { get; set; }

    [Required]
    [MaxLength(20)]
    public string Status { get; set; } = "Active";

    [Required]
    public bool IsEmailVerified { get; set; } = false;

    public DateTime? LastLoginAt { get; set; }

    [Required]
    public bool IsDeleted { get; set; } = false;

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    [MaxLength(255)]
    public string? TwoFactorSecret { get; set; }

    [Required]
    public bool IsTwoFactorEnabled { get; set; } = false;

    public string? TwoFactorBackupCodes { get; set; }

    // 비밀번호 재설정
    [MaxLength(255)]
    public string? PasswordResetToken { get; set; }

    public DateTime? PasswordResetTokenExpiry { get; set; }

    // Navigation properties
    [ForeignKey("DepartmentId")]
    public virtual Department? DepartmentRef { get; set; }

    public virtual ICollection<UserRole> UserRoles { get; set; } = new List<UserRole>();
    public virtual ICollection<ChatConversation> ChatConversations { get; set; } = new List<ChatConversation>();
    public virtual ICollection<ApiQuota> ApiQuotas { get; set; } = new List<ApiQuota>();
    public virtual ICollection<ApiUsage> ApiUsages { get; set; } = new List<ApiUsage>();
    public virtual ICollection<ActivityLog> ActivityLogs { get; set; } = new List<ActivityLog>();
    public virtual ICollection<UserSession> UserSessions { get; set; } = new List<UserSession>();
    public virtual ICollection<UserPreference> UserPreferences { get; set; } = new List<UserPreference>();
    public virtual ICollection<Agent> CreatedAgents { get; set; } = new List<Agent>();
    public virtual ICollection<Tool> CreatedTools { get; set; } = new List<Tool>();
    public virtual ICollection<ToolExecution> ToolExecutions { get; set; } = new List<ToolExecution>();
    public virtual ICollection<Workflow> CreatedWorkflows { get; set; } = new List<Workflow>();
    public virtual ICollection<WorkflowExecution> WorkflowExecutions { get; set; } = new List<WorkflowExecution>();
}
