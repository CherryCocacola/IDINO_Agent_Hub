using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("SystemSettings")]
public class SystemSetting
{
    [Key]
    public int SettingId { get; set; }

    [Required]
    [MaxLength(100)]
    public string SettingKey { get; set; } = string.Empty;

    public string? SettingValue { get; set; }

    [Required]
    [MaxLength(20)]
    public string DataType { get; set; } = "String";

    [MaxLength(50)]
    public string? Category { get; set; }

    [MaxLength(500)]
    public string? Description { get; set; }

    [Required]
    public bool IsEncrypted { get; set; } = false;

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}
