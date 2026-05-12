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
