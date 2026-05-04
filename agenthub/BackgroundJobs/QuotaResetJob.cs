using Hangfire;
using AIAgentManagement.Data;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.BackgroundJobs;

public class QuotaResetJob
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<QuotaResetJob> _logger;

    public QuotaResetJob(
        AIAgentManagementDbContext context,
        ILogger<QuotaResetJob> logger)
    {
        _context = context;
        _logger = logger;
    }

    [AutomaticRetry(Attempts = 3)]
    public async Task ResetDailyQuotas()
    {
        try
        {
            var quotas = await _context.ApiQuotas.ToListAsync();
            
            foreach (var quota in quotas)
            {
                // Reset daily usage (monthly is kept for reporting)
                quota.LastResetAt = DateTime.UtcNow;
                quota.UpdatedAt = DateTime.UtcNow;
            }

            await _context.SaveChangesAsync();
            _logger.LogInformation("Daily quotas reset completed for {Count} quotas", quotas.Count);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error resetting daily quotas");
            throw;
        }
    }

    [AutomaticRetry(Attempts = 3)]
    public async Task ResetMonthlyQuotas()
    {
        try
        {
            var quotas = await _context.ApiQuotas.ToListAsync();
            
            foreach (var quota in quotas)
            {
                quota.CurrentUsage = 0;
                quota.CurrentCost = 0;
                quota.LastResetAt = DateTime.UtcNow;
                quota.UpdatedAt = DateTime.UtcNow;
            }

            await _context.SaveChangesAsync();
            _logger.LogInformation("Monthly quotas reset completed for {Count} quotas", quotas.Count);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error resetting monthly quotas");
            throw;
        }
    }
}
