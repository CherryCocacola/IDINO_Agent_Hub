using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("Tutorials")]
public class Tutorial
{
    [Key]
    public int TutorialId { get; set; }

    [Required]
    [MaxLength(200)]
    public string Title { get; set; } = string.Empty;

    [MaxLength(1000)]
    public string? Description { get; set; }

    [MaxLength(500)]
    public string? VideoUrl { get; set; }

    [MaxLength(500)]
    public string? ThumbnailUrl { get; set; }

    [MaxLength(50)]
    public string? Duration { get; set; }

    [MaxLength(50)]
    public string? Category { get; set; }

    [Required]
    public int SortOrder { get; set; } = 0;

    [Required]
    public bool IsActive { get; set; } = true;

    [Required]
    public int ViewCount { get; set; } = 0;

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}
