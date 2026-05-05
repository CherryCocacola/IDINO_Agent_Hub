using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("ApiServiceModels")]
public class ApiServiceModel
{
    [Key]
    public int ModelId { get; set; }

    [Required]
    public int ServiceId { get; set; }

    [Required]
    [MaxLength(100)]
    public string ModelName { get; set; } = string.Empty;

    [MaxLength(500)]
    public string? Description { get; set; }

    [Required]
    public bool IsActive { get; set; } = true;

    [Required]
    public int SortOrder { get; set; } = 0;

    [MaxLength(50)]
    public string? ModelType { get; set; } // "stable", "preview", "experimental"

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("ServiceId")]
    public virtual ApiService ApiService { get; set; } = null!;
}
