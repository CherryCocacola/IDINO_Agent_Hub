using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("PresentationTemplates")]
public class PresentationTemplate
{
    [Key]
    public int TemplateId { get; set; }

    [Required]
    [MaxLength(200)]
    public string TemplateName { get; set; } = string.Empty;

    [MaxLength(500)]
    public string? Description { get; set; }

    [Required]
    [MaxLength(500)]
    public string TemplateFilePath { get; set; } = string.Empty;

    [Column(TypeName = "nvarchar(max)")]
    public string? TemplateStructure { get; set; } // JSON 형식으로 슬라이드 구조 저장

    [MaxLength(50)]
    public string Category { get; set; } = "business"; // business, education, marketing, creative

    public bool IsPublic { get; set; } = false;

    public int? CreatedBy { get; set; }

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("CreatedBy")]
    public virtual User? Creator { get; set; }
}
