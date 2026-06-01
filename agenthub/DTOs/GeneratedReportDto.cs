using System.ComponentModel.DataAnnotations;

namespace AIAgentManagement.DTOs;

public class GeneratedReportDto
{
    public int ReportId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string ReportType { get; set; } = string.Empty;
    public string Format { get; set; } = string.Empty;
    public DateTime StartDate { get; set; }
    public DateTime EndDate { get; set; }
    public string Status { get; set; } = string.Empty;
    public string? DownloadUrl { get; set; }
    public long? FileSizeBytes { get; set; }
    public string? ErrorMessage { get; set; }
    public int CreatedBy { get; set; }
    public string? CreatorName { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime? CompletedAt { get; set; }
}

/// <summary>
/// 트랙 #147 M1 — 보고서 생성 요청.
/// </summary>
public class CreateReportRequestDto
{
    [Required]
    [MaxLength(200)]
    public string Name { get; set; } = string.Empty;

    /// <summary>"daily" | "weekly" | "monthly" | "custom".</summary>
    [Required]
    [RegularExpression("^(daily|weekly|monthly|custom)$",
        ErrorMessage = "ReportType 은 daily/weekly/monthly/custom 중 하나여야 합니다.")]
    public string ReportType { get; set; } = "monthly";

    /// <summary>"xlsx" 우선. PDF 는 후속 트랙.</summary>
    [RegularExpression("^(xlsx)$", ErrorMessage = "현재 xlsx 형식만 지원합니다.")]
    public string Format { get; set; } = "xlsx";

    /// <summary>ReportType="custom" 시 필수. 그 외 자동 계산.</summary>
    public DateTime? StartDate { get; set; }
    public DateTime? EndDate { get; set; }
}
