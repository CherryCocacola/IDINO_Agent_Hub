using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

[Table("ApiServices")]
public class ApiService
{
    [Key]
    public int ServiceId { get; set; }

    [Required]
    [MaxLength(50)]
    public string ServiceCode { get; set; } = string.Empty;

    [Required]
    [MaxLength(100)]
    public string ServiceName { get; set; } = string.Empty;

    [MaxLength(500)]
    public string? Description { get; set; }

    [MaxLength(100)]
    public string? IconClass { get; set; }

    [MaxLength(20)]
    public string? ColorCode { get; set; }

    [MaxLength(500)]
    public string? ApiEndpoint { get; set; }

    [MaxLength(100)]
    public string? DefaultModel { get; set; }

    [Required]
    [Column(TypeName = "decimal(10, 4)")]
    public decimal CostPerRequest { get; set; } = 0;

    [Required]
    public bool IsActive { get; set; } = true;

    [Required]
    public int SortOrder { get; set; } = 0;

    [Required]
    [MaxLength(50)]
    public string ServiceType { get; set; } = "Chat"; // Chat, ImageGeneration, VideoGeneration, Both

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Required]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    public virtual ICollection<Agent> Agents { get; set; } = new List<Agent>();
    public virtual ICollection<ApiQuota> ApiQuotas { get; set; } = new List<ApiQuota>();
    public virtual ICollection<ApiUsage> ApiUsages { get; set; } = new List<ApiUsage>();
    public virtual ICollection<ChatConversation> ChatConversations { get; set; } = new List<ChatConversation>();
    public virtual ICollection<ApiServiceModel> ApiServiceModels { get; set; } = new List<ApiServiceModel>();
}
