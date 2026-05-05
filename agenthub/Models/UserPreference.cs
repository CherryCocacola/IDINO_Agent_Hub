using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("UserPreferences")]
public class UserPreference
{
    [Key]
    public int PreferenceId { get; set; }

    [Required]
    public int UserId { get; set; }

    [Required]
    [MaxLength(100)]
    public string PreferenceKey { get; set; } = string.Empty;

    public string? PreferenceValue { get; set; }

    [Required]
    [MaxLength(20)]
    public string DataType { get; set; } = "String";

    [MaxLength(50)]
    public string? Category { get; set; }

    [MaxLength(500)]
    public string? Description { get; set; }

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    [ForeignKey("UserId")]
    public virtual User User { get; set; } = null!;
}
