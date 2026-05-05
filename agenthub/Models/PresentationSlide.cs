using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

/// <summary>
/// 프레젠테이션 슬라이드 — Presentations.Slides(nvarchar max JSON)를 별도 테이블로 분리.
/// 슬라이드별 1행으로 저장하여 '문자열 잘림' 오류 근본 해결.
/// Content, ChartsJson, TablesJson, ImagesJson 은 nvarchar(max) 컬럼으로 길이 제한 없음.
/// </summary>
[Table("PresentationSlides")]
public class PresentationSlide
{
    [Key]
    [MaxLength(50)]
    public string SlideId { get; set; } = Guid.NewGuid().ToString();

    [Required]
    public int PresentationId { get; set; }

    [Required]
    public int SlideNumber { get; set; }

    [Required]
    [MaxLength(500)]
    public string Title { get; set; } = string.Empty;

    [Column(TypeName = "nvarchar(max)")]
    public string Content { get; set; } = string.Empty;

    [Required]
    [MaxLength(50)]
    public string Layout { get; set; } = "title-content";

    [MaxLength(2000)]
    public string? ImageUrl { get; set; }

    [MaxLength(2000)]
    public string? ImageDescription { get; set; }

    [MaxLength(2000)]
    public string? ImagePrompt { get; set; }

    /// <summary>ChartDto[] JSON 배열 (nvarchar max, 잘림 없음)</summary>
    [Column(TypeName = "nvarchar(max)")]
    public string? ChartsJson { get; set; }

    /// <summary>TableDto[] JSON 배열 (nvarchar max, 잘림 없음)</summary>
    [Column(TypeName = "nvarchar(max)")]
    public string? TablesJson { get; set; }

    /// <summary>string[] JSON 배열 (이미지 URL 목록, nvarchar max)</summary>
    [Column(TypeName = "nvarchar(max)")]
    public string? ImagesJson { get; set; }

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    [ForeignKey("PresentationId")]
    public virtual Presentation? Presentation { get; set; }
}
