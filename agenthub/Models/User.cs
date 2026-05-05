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
    public string? Department { get; set; }

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
