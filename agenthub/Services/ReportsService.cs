using ClosedXML.Excel;
using Microsoft.EntityFrameworkCore;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;

namespace AIAgentManagement.Services;

/// <summary>
/// 트랙 #147 M1 (2026-06-01) — 운영자 보고서 서비스 구현체.
/// ApiUsages 를 기간/사용자/서비스 단위로 집계하여 ClosedXML 로 xlsx 생성.
/// 파일은 wwwroot/uploads/reports/{guid}.xlsx 에 저장.
/// </summary>
public class ReportsService : IReportsService
{
    private readonly AIAgentManagementDbContext _db;
    private readonly IWebHostEnvironment _env;
    private readonly ILogger<ReportsService> _logger;

    public ReportsService(AIAgentManagementDbContext db, IWebHostEnvironment env, ILogger<ReportsService> logger)
    {
        _db = db;
        _env = env;
        _logger = logger;
    }

    public async Task<List<GeneratedReportDto>> ListAsync(int currentUserId, bool isAdmin, CancellationToken ct = default)
    {
        var q = _db.GeneratedReports
            .AsNoTracking()
            .Include(r => r.Creator)
            .OrderByDescending(r => r.CreatedAt)
            .AsQueryable();
        if (!isAdmin)
        {
            q = q.Where(r => r.CreatedBy == currentUserId);
        }
        var items = await q.Take(100).ToListAsync(ct);
        return items.Select(Map).ToList();
    }

    public async Task<GeneratedReportDto?> GetAsync(int reportId, int currentUserId, bool isAdmin, CancellationToken ct = default)
    {
        var r = await _db.GeneratedReports
            .AsNoTracking()
            .Include(x => x.Creator)
            .FirstOrDefaultAsync(x => x.ReportId == reportId, ct);
        if (r is null) return null;
        if (!isAdmin && r.CreatedBy != currentUserId) return null;
        return Map(r);
    }

    public async Task<GeneratedReportDto> CreateAsync(CreateReportRequestDto request, int currentUserId, CancellationToken ct = default)
    {
        // 기간 자동 계산 (custom 외).
        var now = DateTime.UtcNow;
        DateTime start, end;
        switch (request.ReportType)
        {
            case "daily":
                end = now;
                start = now.AddDays(-1);
                break;
            case "weekly":
                end = now;
                start = now.AddDays(-7);
                break;
            case "monthly":
                end = now;
                start = now.AddMonths(-1);
                break;
            case "custom":
                if (request.StartDate is null || request.EndDate is null)
                    throw new InvalidOperationException("custom 보고서는 StartDate / EndDate 가 필수입니다.");
                start = DateTime.SpecifyKind(request.StartDate.Value, DateTimeKind.Utc);
                end = DateTime.SpecifyKind(request.EndDate.Value, DateTimeKind.Utc);
                if (start >= end) throw new InvalidOperationException("StartDate 는 EndDate 보다 이전이어야 합니다.");
                break;
            default:
                throw new InvalidOperationException("알 수 없는 ReportType.");
        }

        var entity = new GeneratedReport
        {
            Name = request.Name,
            ReportType = request.ReportType,
            Format = "xlsx",
            StartDate = start,
            EndDate = end,
            Status = "generating",
            CreatedBy = currentUserId,
            CreatedAt = now
        };
        _db.GeneratedReports.Add(entity);
        await _db.SaveChangesAsync(ct);

        try
        {
            var (bytes, fileName) = await BuildExcelAsync(entity, currentUserId, ct);

            var uploadDir = Path.Combine(_env.WebRootPath ?? "wwwroot", "uploads", "reports");
            Directory.CreateDirectory(uploadDir);
            var savedName = $"{entity.ReportId}_{Guid.NewGuid():N}.xlsx";
            var savedPath = Path.Combine(uploadDir, savedName);
            await File.WriteAllBytesAsync(savedPath, bytes, ct);

            entity.DownloadUrl = $"/uploads/reports/{savedName}";
            entity.FileSizeBytes = bytes.LongLength;
            entity.Status = "completed";
            entity.CompletedAt = DateTime.UtcNow;
            await _db.SaveChangesAsync(ct);

            _logger.LogInformation(
                "운영자 보고서 생성 완료 - ReportId={Id}, Type={Type}, FileSize={Size}",
                entity.ReportId, entity.ReportType, bytes.Length);
        }
        catch (Exception ex)
        {
            entity.Status = "failed";
            entity.ErrorMessage = ex.Message.Length > 1900 ? ex.Message.Substring(0, 1900) : ex.Message;
            await _db.SaveChangesAsync(ct);
            _logger.LogError(ex, "운영자 보고서 생성 실패 - ReportId={Id}", entity.ReportId);
            throw;
        }

        // 재로드 (Creator include).
        var reloaded = await _db.GeneratedReports
            .AsNoTracking()
            .Include(r => r.Creator)
            .FirstAsync(r => r.ReportId == entity.ReportId, ct);
        return Map(reloaded);
    }

    public async Task<(byte[] Bytes, string FileName, string ContentType)?> DownloadAsync(int reportId, int currentUserId, bool isAdmin, CancellationToken ct = default)
    {
        var r = await _db.GeneratedReports.AsNoTracking().FirstOrDefaultAsync(x => x.ReportId == reportId, ct);
        if (r is null) return null;
        if (!isAdmin && r.CreatedBy != currentUserId) return null;
        if (r.Status != "completed" || string.IsNullOrWhiteSpace(r.DownloadUrl)) return null;

        var webRoot = _env.WebRootPath ?? "wwwroot";
        var relative = r.DownloadUrl.TrimStart('/').Replace('/', Path.DirectorySeparatorChar);
        var fullPath = Path.Combine(webRoot, relative);
        if (!File.Exists(fullPath)) return null;
        var bytes = await File.ReadAllBytesAsync(fullPath, ct);
        var fileName = $"{r.Name}_{r.StartDate:yyyyMMdd}_{r.EndDate:yyyyMMdd}.xlsx";
        return (bytes, fileName, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
    }

    public async Task<bool> DeleteAsync(int reportId, int currentUserId, bool isAdmin, CancellationToken ct = default)
    {
        var r = await _db.GeneratedReports.FirstOrDefaultAsync(x => x.ReportId == reportId, ct);
        if (r is null) return false;
        if (!isAdmin && r.CreatedBy != currentUserId) return false;

        // 파일도 같이 정리.
        if (!string.IsNullOrWhiteSpace(r.DownloadUrl))
        {
            try
            {
                var webRoot = _env.WebRootPath ?? "wwwroot";
                var relative = r.DownloadUrl.TrimStart('/').Replace('/', Path.DirectorySeparatorChar);
                var fullPath = Path.Combine(webRoot, relative);
                if (File.Exists(fullPath)) File.Delete(fullPath);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "운영자 보고서 파일 삭제 실패 (무시) - ReportId={Id}", reportId);
            }
        }

        _db.GeneratedReports.Remove(r);
        await _db.SaveChangesAsync(ct);
        return true;
    }

    // ── ClosedXML 시트 생성 ────────────────────────────────────────────────────
    private async Task<(byte[] Bytes, string FileName)> BuildExcelAsync(GeneratedReport entity, int currentUserId, CancellationToken ct)
    {
        var start = entity.StartDate;
        var end = entity.EndDate;

        // 집계 — ApiUsages.
        var usages = await _db.ApiUsages
            .AsNoTracking()
            .Where(u => u.CreatedAt >= start && u.CreatedAt <= end)
            .ToListAsync(ct);

        var byService = usages
            .GroupBy(u => u.ServiceId)
            .Select(g => new
            {
                ServiceId = g.Key,
                Count = g.Count(),
                Tokens = g.Sum(u => (long?)u.TokensUsed) ?? 0,
                Cost = g.Sum(u => u.RequestCost),
                AvgResponseMs = g.Average(u => (double?)u.ResponseTime) ?? 0
            })
            .ToList();

        var byUser = usages
            .GroupBy(u => u.UserId)
            .Select(g => new
            {
                UserId = g.Key,
                Count = g.Count(),
                Tokens = g.Sum(u => (long?)u.TokensUsed) ?? 0,
                Cost = g.Sum(u => u.RequestCost)
            })
            .OrderByDescending(x => x.Cost)
            .ToList();

        // 서비스/사용자 이름 조회.
        var serviceNames = await _db.ApiServices
            .AsNoTracking()
            .Where(s => byService.Select(x => x.ServiceId).Contains(s.ServiceId))
            .ToDictionaryAsync(s => s.ServiceId, s => s.ServiceName, ct);

        var userIds = byUser.Select(x => x.UserId).ToList();
        var userNames = await _db.Users
            .AsNoTracking()
            .Where(u => userIds.Contains(u.UserId))
            .ToDictionaryAsync(u => u.UserId, u => u.FullName ?? u.Email, ct);

        using var workbook = new XLWorkbook();

        // 요약 시트.
        var summary = workbook.AddWorksheet("요약");
        summary.Cell(1, 1).Value = "운영자 보고서";
        summary.Cell(1, 1).Style.Font.Bold = true;
        summary.Cell(1, 1).Style.Font.FontSize = 16;
        summary.Cell(2, 1).Value = $"보고서 명: {entity.Name}";
        summary.Cell(3, 1).Value = $"유형: {entity.ReportType}";
        summary.Cell(4, 1).Value = $"기간: {start:yyyy-MM-dd HH:mm} ~ {end:yyyy-MM-dd HH:mm} (UTC)";
        summary.Cell(5, 1).Value = $"생성 시각: {DateTime.UtcNow:yyyy-MM-dd HH:mm:ss} (UTC)";
        summary.Cell(7, 1).Value = "총 호출 수";
        summary.Cell(7, 2).Value = usages.Count;
        summary.Cell(8, 1).Value = "총 토큰";
        summary.Cell(8, 2).Value = usages.Sum(u => (long?)u.TokensUsed) ?? 0;
        summary.Cell(9, 1).Value = "총 비용 (USD)";
        summary.Cell(9, 2).Value = usages.Sum(u => u.RequestCost);
        summary.Cell(9, 2).Style.NumberFormat.Format = "0.0000";
        summary.Columns().AdjustToContents();

        // 서비스별.
        var sService = workbook.AddWorksheet("서비스별");
        sService.Cell(1, 1).Value = "서비스";
        sService.Cell(1, 2).Value = "호출 수";
        sService.Cell(1, 3).Value = "총 토큰";
        sService.Cell(1, 4).Value = "총 비용 (USD)";
        sService.Cell(1, 5).Value = "평균 응답 (ms)";
        sService.Range(1, 1, 1, 5).Style.Font.Bold = true;
        int row = 2;
        foreach (var s in byService.OrderByDescending(x => x.Cost))
        {
            sService.Cell(row, 1).Value = serviceNames.TryGetValue(s.ServiceId, out var n) ? n : $"#{s.ServiceId}";
            sService.Cell(row, 2).Value = s.Count;
            sService.Cell(row, 3).Value = s.Tokens;
            sService.Cell(row, 4).Value = s.Cost;
            sService.Cell(row, 4).Style.NumberFormat.Format = "0.0000";
            sService.Cell(row, 5).Value = Math.Round(s.AvgResponseMs, 0);
            row++;
        }
        sService.Columns().AdjustToContents();

        // 사용자별 (top 50).
        var sUser = workbook.AddWorksheet("사용자별 (Top 50)");
        sUser.Cell(1, 1).Value = "사용자";
        sUser.Cell(1, 2).Value = "호출 수";
        sUser.Cell(1, 3).Value = "총 토큰";
        sUser.Cell(1, 4).Value = "총 비용 (USD)";
        sUser.Range(1, 1, 1, 4).Style.Font.Bold = true;
        row = 2;
        foreach (var u in byUser.Take(50))
        {
            sUser.Cell(row, 1).Value = userNames.TryGetValue(u.UserId, out var n) ? n : $"#{u.UserId}";
            sUser.Cell(row, 2).Value = u.Count;
            sUser.Cell(row, 3).Value = u.Tokens;
            sUser.Cell(row, 4).Value = u.Cost;
            sUser.Cell(row, 4).Style.NumberFormat.Format = "0.0000";
            row++;
        }
        sUser.Columns().AdjustToContents();

        using var ms = new MemoryStream();
        workbook.SaveAs(ms);
        var bytes = ms.ToArray();
        var fileName = $"{entity.Name}.xlsx";
        return (bytes, fileName);
    }

    private static GeneratedReportDto Map(GeneratedReport r) => new()
    {
        ReportId = r.ReportId,
        Name = r.Name,
        ReportType = r.ReportType,
        Format = r.Format,
        StartDate = r.StartDate,
        EndDate = r.EndDate,
        Status = r.Status,
        DownloadUrl = r.DownloadUrl,
        FileSizeBytes = r.FileSizeBytes,
        ErrorMessage = r.ErrorMessage,
        CreatedBy = r.CreatedBy,
        CreatorName = r.Creator?.FullName ?? r.Creator?.Email,
        CreatedAt = r.CreatedAt,
        CompletedAt = r.CompletedAt
    };
}
