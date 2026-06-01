using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AIAgentManagement.Models;

/// <summary>
/// 운영자 보고서 — 사용량/비용/감사 집계를 PDF/Excel 로 생성한 산출물.
/// </summary>
/// <remarks>
/// 트랙 #147 M1 (2026-06-01): /reports 화면 정식 구현. ApiUsages 를 기간/사용자/서비스
/// 단위로 집계하여 Excel(.xlsx) 또는 PDF 파일을 생성. 파일은 wwwroot/uploads/reports/
/// 에 저장하고 URL 을 DownloadUrl 컬럼에 저장.
///
/// ReportType:
///   - "daily"   : 일일 요약 (당일 사용량 + 비용)
///   - "weekly"  : 주간 분석 (7일 트렌드)
///   - "monthly" : 월간 종합 (30일 비용/사용량)
///   - "custom"  : 사용자 정의 (start/end 지정)
///
/// Status:
///   - "pending"   : 생성 요청만 들어옴
///   - "generating": Hangfire 작업 진행 중(향후 비동기 모드)
///   - "completed" : 파일 생성 완료, DownloadUrl 활성
///   - "failed"    : 생성 실패 (ErrorMessage 참조)
/// </remarks>
[Table("GeneratedReports")]
public class GeneratedReport
{
    [Key]
    public int ReportId { get; set; }

    [Required]
    [MaxLength(200)]
    public string Name { get; set; } = string.Empty;

    [Required]
    [MaxLength(20)]
    public string ReportType { get; set; } = "monthly";

    /// <summary>"xlsx" | "pdf" — 본 트랙은 xlsx 만 우선 구현.</summary>
    [Required]
    [MaxLength(10)]
    public string Format { get; set; } = "xlsx";

    [Required]
    public DateTime StartDate { get; set; }

    [Required]
    public DateTime EndDate { get; set; }

    [Required]
    [MaxLength(20)]
    public string Status { get; set; } = "pending";

    /// <summary>SPA 경로 (`/uploads/reports/{filename}`). Status="completed" 시에만 유효.</summary>
    [MaxLength(500)]
    public string? DownloadUrl { get; set; }

    /// <summary>생성 산출 파일 크기 (byte) — 운영 모니터링용.</summary>
    public long? FileSizeBytes { get; set; }

    /// <summary>실패 시 오류 메시지. Status="failed" 시 노출.</summary>
    [MaxLength(2000)]
    public string? ErrorMessage { get; set; }

    /// <summary>생성 요청자 — UserId FK.</summary>
    [Required]
    public int CreatedBy { get; set; }

    [Required]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public DateTime? CompletedAt { get; set; }

    [ForeignKey("CreatedBy")]
    public virtual User? Creator { get; set; }
}
