using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("UserSessions")]
public class UserSession
{
    [Key]
    public int SessionId { get; set; }

    [Required]
    public int UserId { get; set; }

    [Required]
    [MaxLength(255)]
    public string SessionToken { get; set; } = string.Empty;

    [MaxLength(500)]
    public string? DeviceInfo { get; set; }

    [MaxLength(50)]
    public string? IpAddress { get; set; }

    [MaxLength(500)]
    public string? UserAgent { get; set; }

    [Required]
    public DateTime LoginAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime LastActivityAt { get; set; } = DateTime.UtcNow;

    public DateTime? LogoutAt { get; set; }

    /// <summary>
    /// 세션(refresh token) 만료 시각 (UTC).
    /// 트랙 #89 C2 — 만료 시 RefreshTokenAsync 가 새 토큰 발급을 거부하여 60분 무알림 강제 로그아웃을 방지.
    /// 기본값: LoginAt + JwtSettings:RefreshTokenExpirationInDays (default 7일).
    /// </summary>
    [Required]
    public DateTime ExpiresAt { get; set; }

    [Required]
    public bool IsActive { get; set; } = true;

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("UserId")]
    public virtual User User { get; set; } = null!;
}
