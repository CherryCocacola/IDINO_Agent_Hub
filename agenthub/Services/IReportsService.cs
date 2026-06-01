using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

/// <summary>
/// 운영자 보고서 (사용량/비용 집계 → Excel 산출) 서비스.
/// </summary>
/// <remarks>
/// 트랙 #147 M1 (2026-06-01) — /reports 화면 정식 구현.
/// 본 트랙은 동기 즉시 생성 + xlsx 단일 형식. Hangfire 비동기 + PDF 는 후속 트랙.
/// </remarks>
public interface IReportsService
{
    /// <summary>현재 사용자 시점에서 보이는 보고서 목록 (Admin 은 전체, 그 외는 본인 생성분만).</summary>
    Task<List<GeneratedReportDto>> ListAsync(int currentUserId, bool isAdmin, CancellationToken ct = default);

    /// <summary>단일 보고서 조회.</summary>
    Task<GeneratedReportDto?> GetAsync(int reportId, int currentUserId, bool isAdmin, CancellationToken ct = default);

    /// <summary>
    /// 보고서 생성 (동기). 사용량/비용 집계 후 Excel 파일 생성 + 저장. completed status 반환.
    /// </summary>
    Task<GeneratedReportDto> CreateAsync(CreateReportRequestDto request, int currentUserId, CancellationToken ct = default);

    /// <summary>다운로드용 — 파일 바이트 + 파일명 + content-type 반환.</summary>
    Task<(byte[] Bytes, string FileName, string ContentType)?> DownloadAsync(int reportId, int currentUserId, bool isAdmin, CancellationToken ct = default);

    /// <summary>본인 생성 보고서만 삭제 (Admin 은 전체).</summary>
    Task<bool> DeleteAsync(int reportId, int currentUserId, bool isAdmin, CancellationToken ct = default);
}
