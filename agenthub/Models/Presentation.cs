using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("Presentations")]
public class Presentation
{
    [Key]
    public int PresentationId { get; set; }

    [Required]
    public int UserId { get; set; }

    [Required]
    [MaxLength(200)]
    public string Title { get; set; } = string.Empty;

    [Column(TypeName = "nvarchar(max)")]
    public string? Slides { get; set; } // JSON 형식으로 슬라이드 데이터 저장

    [MaxLength(50)]
    public string? ThemeId { get; set; }

    /// <summary>슬라이드 비율: 4:3, 16:9, 16:10 (기본 16:9)</summary>
    [MaxLength(20)]
    public string? SlideSize { get; set; }

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("UserId")]
    public virtual User? User { get; set; }
}
