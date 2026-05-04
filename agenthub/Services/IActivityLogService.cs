using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IActivityLogService
{
    Task<(List<ActivityLogDto> Items, int TotalCount)> GetActivityLogsAsync(
        DateTime? startDate = null,
        DateTime? endDate = null,
        int? userId = null,
        string? actionFilter = null,
        string? search = null,
        int skip = 0,
        int take = 100);
}
