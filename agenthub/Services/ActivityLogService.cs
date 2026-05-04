using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

public class ActivityLogService : IActivityLogService
{
    private readonly AIAgentManagementDbContext _context;

    public ActivityLogService(AIAgentManagementDbContext context)
    {
        _context = context;
    }

    public async Task<(List<ActivityLogDto> Items, int TotalCount)> GetActivityLogsAsync(
        DateTime? startDate = null,
        DateTime? endDate = null,
        int? userId = null,
        string? actionFilter = null,
        string? search = null,
        int skip = 0,
        int take = 100)
    {
        var start = startDate ?? DateTime.UtcNow.AddDays(-30);
        var end = endDate ?? DateTime.UtcNow.AddDays(1);

        var query = _context.ActivityLogs
            .Include(a => a.User)
            .Where(a => a.CreatedAt >= start && a.CreatedAt <= end);

        if (userId.HasValue)
        {
            query = query.Where(a => a.UserId == userId.Value);
        }

        if (!string.IsNullOrWhiteSpace(actionFilter))
        {
            if (actionFilter == "POST /api/auth/login")
            {
                query = query.Where(a => a.ActivityType.Contains("login", StringComparison.OrdinalIgnoreCase));
            }
            else if (actionFilter == "POST")
            {
                query = query.Where(a => a.ActivityType.StartsWith("POST"));
            }
            else if (actionFilter == "PUT")
            {
                query = query.Where(a => a.ActivityType.StartsWith("PUT") || a.ActivityType.StartsWith("PATCH"));
            }
            else if (actionFilter == "DELETE")
            {
                query = query.Where(a => a.ActivityType.StartsWith("DELETE"));
            }
        }

        if (!string.IsNullOrWhiteSpace(search))
        {
            var s = search.ToLower();
            query = query.Where(a =>
                (a.IpAddress != null && a.IpAddress.ToLower().Contains(s)) ||
                (a.Description != null && a.Description.ToLower().Contains(s)) ||
                (a.Details != null && a.Details.ToLower().Contains(s)) ||
                (a.ActivityType != null && a.ActivityType.ToLower().Contains(s)));
        }

        var totalCount = await query.CountAsync();

        var logs = await query
            .OrderByDescending(a => a.CreatedAt)
            .Skip(skip)
            .Take(take)
            .Select(a => new ActivityLogDto
            {
                LogId = a.LogId,
                UserId = a.UserId,
                UserName = a.User != null ? (a.User.FullName ?? a.User.Email) : null,
                ActivityType = a.ActivityType,
                EntityType = a.EntityType,
                EntityId = a.EntityId,
                Description = a.Description,
                IpAddress = a.IpAddress,
                UserAgent = a.UserAgent,
                Details = a.Details,
                CreatedAt = a.CreatedAt
            })
            .ToListAsync();

        return (logs, totalCount);
    }
}
