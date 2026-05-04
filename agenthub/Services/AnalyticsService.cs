using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;

namespace AIAgentManagement.Services;

public class AnalyticsService : IAnalyticsService
{
    private readonly AIAgentManagementDbContext _context;

    public AnalyticsService(AIAgentManagementDbContext context)
    {
        _context = context;
    }

    public async Task<DashboardStatsDto> GetDashboardStatsAsync()
    {
        var totalUsers = await _context.Users.Where(u => !u.IsDeleted).CountAsync();
        var activeUsers = await _context.Users.Where(u => !u.IsDeleted && u.Status == "Active").CountAsync();
        var todayStart = DateTime.UtcNow.Date;
        var todayApiCalls = await _context.ApiUsages
            .Where(u => u.RequestTime.Date == todayStart)
            .CountAsync();
        var thisMonthStart = new DateTime(DateTime.UtcNow.Year, DateTime.UtcNow.Month, 1);
        var thisMonthCost = await _context.ApiUsages
            .Where(u => u.RequestTime >= thisMonthStart)
            .SumAsync(u => u.RequestCost);

        return new DashboardStatsDto
        {
            TotalUsers = totalUsers,
            ActiveUsers = activeUsers,
            TodayApiCalls = todayApiCalls,
            ThisMonthCost = thisMonthCost
        };
    }

    public async Task<List<UsageStatsDto>> GetUsageStatsAsync(DateTime? startDate, DateTime? endDate, int? userId = null)
    {
        var start = startDate ?? DateTime.UtcNow.AddDays(-30);
        var end = endDate ?? DateTime.UtcNow;

        var query = _context.ApiUsages
            .Include(u => u.ApiService)
            .Where(u => u.RequestTime >= start && u.RequestTime <= end);

        if (userId.HasValue)
        {
            query = query.Where(u => u.UserId == userId.Value);
        }

        var stats = await query
            .GroupBy(u => new { u.ServiceId, u.ApiService.ServiceName, Date = u.RequestTime.Date })
            .Select(g => new UsageStatsDto
            {
                ServiceId = g.Key.ServiceId,
                ServiceName = g.Key.ServiceName,
                Date = g.Key.Date,
                RequestCount = g.Count(),
                TotalTokens = g.Sum(u => u.TokensUsed ?? 0),
                TotalCost = g.Sum(u => u.RequestCost),
                AverageResponseTime = (int)g.Average(u => u.ResponseTime ?? 0)
            })
            .OrderBy(s => s.Date)
            .ThenBy(s => s.ServiceId)
            .ToListAsync();

        return stats;
    }

    public async Task<CostAnalysisDto> GetCostAnalysisAsync(DateTime? startDate, DateTime? endDate)
    {
        var start = startDate ?? DateTime.UtcNow.AddDays(-30);
        var end = endDate ?? DateTime.UtcNow;

        var totalCost = await _context.ApiUsages
            .Where(u => u.RequestTime >= start && u.RequestTime <= end)
            .SumAsync(u => u.RequestCost);

        var serviceCosts = await _context.ApiUsages
            .Include(u => u.ApiService)
            .Where(u => u.RequestTime >= start && u.RequestTime <= end)
            .GroupBy(u => new { u.ServiceId, u.ApiService.ServiceName })
            .Select(g => new ServiceCostDto
            {
                ServiceId = g.Key.ServiceId,
                ServiceName = g.Key.ServiceName,
                TotalCost = g.Sum(u => u.RequestCost),
                RequestCount = g.Count(),
                Percentage = 0 // Will be calculated
            })
            .ToListAsync();

        var total = serviceCosts.Sum(s => s.TotalCost);
        foreach (var serviceCost in serviceCosts)
        {
            serviceCost.Percentage = total > 0 ? (decimal)(serviceCost.TotalCost / total * 100) : 0;
        }

        return new CostAnalysisDto
        {
            TotalCost = totalCost,
            StartDate = start,
            EndDate = end,
            ServiceCosts = serviceCosts.OrderByDescending(s => s.TotalCost).ToList()
        };
    }

    public async Task<List<UserUsageDto>> GetTopUsersAsync(int top = 10)
    {
        var users = await _context.ApiUsages
            .Include(u => u.User)
            .GroupBy(u => new { u.UserId, u.User.Email, u.User.FullName })
            .Select(g => new UserUsageDto
            {
                UserId = g.Key.UserId,
                Email = g.Key.Email,
                FullName = g.Key.FullName ?? "",
                RequestCount = g.Count(),
                TotalCost = g.Sum(u => u.RequestCost),
                TotalTokens = g.Sum(u => u.TokensUsed ?? 0)
            })
            .OrderByDescending(u => u.RequestCount)
            .Take(top)
            .ToListAsync();

        return users;
    }

    public async Task<TeamStatsDto> GetTeamStatsAsync()
    {
        var totalMembers = await _context.Users.Where(u => !u.IsDeleted).CountAsync();
        
        var totalApiCalls = await _context.ApiUsages.CountAsync();
        
        var totalCost = await _context.ApiUsages.SumAsync(u => u.RequestCost);
        
        var sharedAgents = await _context.Agents.Where(a => a.IsPublic && a.IsActive).CountAsync();

        // 사용자별 사용량 계산
        var userUsages = await _context.ApiUsages
            .Include(u => u.User)
            .GroupBy(u => new { u.UserId, u.User.Email, u.User.FullName })
            .Select(g => new UserUsageDto
            {
                UserId = g.Key.UserId,
                Email = g.Key.Email,
                FullName = g.Key.FullName ?? "",
                RequestCount = g.Count(),
                TotalCost = g.Sum(u => u.RequestCost),
                TotalTokens = g.Sum(u => u.TokensUsed ?? 0)
            })
            .ToListAsync();

        return new TeamStatsDto
        {
            TotalMembers = totalMembers,
            TotalApiCalls = totalApiCalls,
            TotalCost = totalCost,
            SharedAgents = sharedAgents,
            UserUsages = userUsages
        };
    }

    public async Task<UserUsageDto> GetUserUsageAsync(int userId, DateTime? startDate = null, DateTime? endDate = null)
    {
        var start = startDate ?? DateTime.UtcNow.AddDays(-30);
        var end = endDate ?? DateTime.UtcNow;

        var user = await _context.Users.FindAsync(userId);
        if (user == null)
        {
            throw new KeyNotFoundException($"User with ID {userId} not found");
        }

        var usage = await _context.ApiUsages
            .Where(u => u.UserId == userId && u.RequestTime >= start && u.RequestTime <= end)
            .GroupBy(u => u.UserId)
            .Select(g => new UserUsageDto
            {
                UserId = g.Key,
                Email = user.Email,
                FullName = user.FullName,
                RequestCount = g.Count(),
                TotalCost = g.Sum(u => u.RequestCost),
                TotalTokens = g.Sum(u => u.TokensUsed ?? 0)
            })
            .FirstOrDefaultAsync();

        if (usage == null)
        {
            return new UserUsageDto
            {
                UserId = userId,
                Email = user.Email,
                FullName = user.FullName,
                RequestCount = 0,
                TotalCost = 0,
                TotalTokens = 0
            };
        }

        return usage;
    }

    public async Task<(List<ApiUsageDto> Items, int TotalCount)> GetUsageHistoryAsync(DateTime? startDate, DateTime? endDate, int? userId = null, int? serviceId = null, int? statusCode = null, string? search = null, int skip = 0, int take = 100)
    {
        var start = startDate ?? DateTime.UtcNow.AddDays(-30);
        var end = endDate ?? DateTime.UtcNow.AddDays(1);

        // Include 제거 — AsNoTracking + 프로젝션으로 필요한 컬럼만 SELECT
        // COUNT 쿼리에서 search 없을 때 JOIN 불필요 → 대폭 속도 개선
        var baseQuery = _context.ApiUsages
            .AsNoTracking()
            .Where(u => u.RequestTime >= start && u.RequestTime <= end);

        if (userId.HasValue)
            baseQuery = baseQuery.Where(u => u.UserId == userId.Value);

        if (serviceId.HasValue)
            baseQuery = baseQuery.Where(u => u.ServiceId == serviceId.Value);

        if (statusCode.HasValue)
            baseQuery = baseQuery.Where(u => u.StatusCode == statusCode.Value);

        if (!string.IsNullOrWhiteSpace(search))
        {
            var s = search.ToLower();
            baseQuery = baseQuery.Where(u =>
                (u.User != null && ((u.User.FullName ?? "").ToLower().Contains(s) || (u.User.Email ?? "").ToLower().Contains(s))) ||
                (u.ApiService != null && (u.ApiService.ServiceName ?? "").ToLower().Contains(s)) ||
                (u.Model != null && u.Model.ToLower().Contains(s)));
        }

        // COUNT와 페이지 데이터 병렬 조회
        // COUNT: search 없으면 JOIN 없이 ApiUsages 단일 테이블 COUNT → 빠름
        // LIST:  프로젝션으로 필요한 컬럼만 SELECT (User/ApiService 전체 로드 안 함)
        var countTask = baseQuery.CountAsync();
        var listTask = baseQuery
            .OrderByDescending(u => u.RequestTime)
            .Skip(skip)
            .Take(take)
            .Select(u => new ApiUsageDto
            {
                UsageId = u.UsageId,
                UserId = u.UserId,
                UserName = u.User.FullName ?? u.User.Email,
                ServiceId = u.ServiceId,
                ServiceName = u.ApiService.ServiceName,
                Model = u.Model,
                TokensUsed = u.TokensUsed,
                RequestCost = u.RequestCost,
                RequestTime = u.RequestTime,
                ResponseTime = u.ResponseTime,
                StatusCode = u.StatusCode,
                ErrorMessage = u.ErrorMessage,
                Prompt = u.Prompt
            })
            .ToListAsync();

        await Task.WhenAll(countTask, listTask);
        return (listTask.Result, countTask.Result);
    }

    /// <summary>
    /// 단일 SQL aggregate 쿼리로 KPI 집계 — 전체 데이터를 로드하지 않으므로 매우 빠름
    /// </summary>
    public async Task<UsageHistorySummaryDto> GetUsageHistorySummaryAsync(
        DateTime? startDate, DateTime? endDate,
        int? userId = null, int? serviceId = null, int? statusCode = null)
    {
        var start = startDate ?? DateTime.UtcNow.AddDays(-30);
        var end   = endDate   ?? DateTime.UtcNow.AddDays(1);

        // Include 불필요 — aggregate 쿼리이므로 JOIN 없이 ApiUsages 테이블만 사용
        var query = _context.ApiUsages
            .Where(u => u.RequestTime >= start && u.RequestTime <= end);

        if (userId.HasValue)
            query = query.Where(u => u.UserId == userId.Value);
        if (serviceId.HasValue)
            query = query.Where(u => u.ServiceId == serviceId.Value);
        if (statusCode.HasValue)
            query = query.Where(u => u.StatusCode == statusCode.Value);

        var stats = await query
            .GroupBy(_ => 1)
            .Select(g => new
            {
                Count   = g.Count(),
                Tokens  = g.Sum(u => u.TokensUsed ?? 0),
                Cost    = g.Sum(u => u.RequestCost),
                AvgTime = g.Average(u => (double?)(u.ResponseTime ?? 0))
            })
            .FirstOrDefaultAsync();

        if (stats == null)
            return new UsageHistorySummaryDto();

        return new UsageHistorySummaryDto
        {
            TotalCalls      = stats.Count,
            TotalTokens     = stats.Tokens,
            TotalCost       = (double)stats.Cost,
            AvgResponseTime = (stats.AvgTime ?? 0) / 1000.0   // ms → 초
        };
    }
}
