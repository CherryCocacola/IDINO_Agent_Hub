using Hangfire;
using AIAgentManagement.Data;
using AIAgentManagement.Services;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.BackgroundJobs;

public class ReportGenerationJob
{
    private readonly AIAgentManagementDbContext _context;
    private readonly IAnalyticsService _analyticsService;
    private readonly ILogger<ReportGenerationJob> _logger;

    public ReportGenerationJob(
        AIAgentManagementDbContext context,
        IAnalyticsService analyticsService,
        ILogger<ReportGenerationJob> logger)
    {
        _context = context;
        _analyticsService = analyticsService;
        _logger = logger;
    }

    [AutomaticRetry(Attempts = 3)]
    public async Task GenerateDailyReport()
    {
        try
        {
            var yesterday = DateTime.UtcNow.AddDays(-1);
            var startDate = yesterday.Date;
            var endDate = yesterday.Date.AddDays(1);

            var stats = await _analyticsService.GetUsageStatsAsync(startDate, endDate);
            var costAnalysis = await _analyticsService.GetCostAnalysisAsync(startDate, endDate);

            _logger.LogInformation("Daily report generated for {Date}", yesterday.Date);
            // In a full implementation, you would save the report to a Reports table
            // and send it via email or store it in storage
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating daily report");
            throw;
        }
    }

    [AutomaticRetry(Attempts = 3)]
    public async Task GenerateMonthlyReport()
    {
        try
        {
            var lastMonth = DateTime.UtcNow.AddMonths(-1);
            var startDate = new DateTime(lastMonth.Year, lastMonth.Month, 1);
            var endDate = startDate.AddMonths(1);

            var stats = await _analyticsService.GetUsageStatsAsync(startDate, endDate);
            var costAnalysis = await _analyticsService.GetCostAnalysisAsync(startDate, endDate);
            var topUsers = await _analyticsService.GetTopUsersAsync(10);

            _logger.LogInformation("Monthly report generated for {Month}", lastMonth.ToString("yyyy-MM"));
            // In a full implementation, you would save the report to a Reports table
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating monthly report");
            throw;
        }
    }
}
