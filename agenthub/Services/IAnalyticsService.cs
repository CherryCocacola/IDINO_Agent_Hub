using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IAnalyticsService
{
    Task<DashboardStatsDto> GetDashboardStatsAsync();
    Task<List<UsageStatsDto>> GetUsageStatsAsync(DateTime? startDate, DateTime? endDate, int? userId = null);
    Task<CostAnalysisDto> GetCostAnalysisAsync(DateTime? startDate, DateTime? endDate);
    Task<List<UserUsageDto>> GetTopUsersAsync(int top = 10);
    Task<TeamStatsDto> GetTeamStatsAsync();
    Task<UserUsageDto> GetUserUsageAsync(int userId, DateTime? startDate = null, DateTime? endDate = null);
    Task<(List<ApiUsageDto> Items, int TotalCount)> GetUsageHistoryAsync(DateTime? startDate, DateTime? endDate, int? userId = null, int? serviceId = null, int? statusCode = null, string? search = null, int skip = 0, int take = 100);
    /// <summary>
    /// 사용 내역 전체 집계 통계 (SQL aggregate 함수 사용, 빠름)
    /// </summary>
    Task<UsageHistorySummaryDto> GetUsageHistorySummaryAsync(DateTime? startDate, DateTime? endDate, int? userId = null, int? serviceId = null, int? statusCode = null);
}
