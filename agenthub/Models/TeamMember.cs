using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("TeamMembers")]
public class TeamMember
{
    [Key]
    public int TeamMemberId { get; set; }

    [Required]
    public int TeamId { get; set; }

    [Required]
    public int UserId { get; set; }

    [MaxLength(50)]
    public string? Role { get; set; } // 팀 내 역할 (예: "Leader", "Member", "Contributor")

    [Required]
    public DateTime JoinedAt { get; set; } = DateTime.UtcNow;

    public DateTime? LeftAt { get; set; }

    [Required]
    public bool IsActive { get; set; } = true;

    public int? AddedBy { get; set; } // 팀에 추가한 사람의 UserId

    // Navigation properties
    [ForeignKey("TeamId")]
    public virtual Team Team { get; set; } = null!;

    [ForeignKey("UserId")]
    public virtual User User { get; set; } = null!;
}
