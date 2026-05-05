using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

public class QuotaService : IQuotaService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly CachingService _cachingService;

    public QuotaService(AIAgentManagementDbContext context, CachingService cachingService)
    {
        _context = context;
        _cachingService = cachingService;
    }

    public async Task<List<QuotaDto>> GetQuotasAsync(int? userId = null, int? serviceId = null)
    {
        var query = _context.ApiQuotas
            .Include(q => q.User)
            .Include(q => q.ApiService)
            .AsQueryable();

        if (userId.HasValue)
        {
            query = query.Where(q => q.UserId == userId.Value);
        }

        if (serviceId.HasValue)
        {
            query = query.Where(q => q.ServiceId == serviceId.Value);
        }

        var quotas = await query.ToListAsync();

        // null-safe: 사용자 또는 서비스가 삭제된 경우에도 500 오류 없이 빈 문자열 반환
        return quotas.Select(q => new QuotaDto
        {
            QuotaId = q.QuotaId,
            UserId = q.UserId,
            UserEmail = q.User?.Email ?? string.Empty,
            ServiceId = q.ServiceId,
            ServiceName = q.ApiService?.ServiceName ?? string.Empty,
            MonthlyLimit = q.MonthlyLimit,
            MonthlyTokenLimit = q.MonthlyTokenLimit, // Phase 3.3d
            DailyLimit = q.DailyLimit,
            CostLimit = q.CostLimit,
            CurrentUsage = q.CurrentUsage,
            CurrentTokens = q.CurrentTokens, // Phase 3.3d
            CurrentCost = q.CurrentCost,
            AlertThreshold = q.AlertThreshold,
            IsAlertEnabled = q.IsAlertEnabled,
            LastResetAt = q.LastResetAt,
            CreatedAt = q.CreatedAt,
            UpdatedAt = q.UpdatedAt
        }).ToList();
    }

    public async Task<QuotaDto?> GetQuotaAsync(int userId, int serviceId)
    {
        var cacheKey = _cachingService.GetQuotaKey(userId, serviceId);
        var cached = await _cachingService.GetAsync<QuotaDto>(cacheKey);
        if (cached != null)
        {
            return cached;
        }

        var quota = await _context.ApiQuotas
            .Include(q => q.User)
            .Include(q => q.ApiService)
            .FirstOrDefaultAsync(q => q.UserId == userId && q.ServiceId == serviceId);

        if (quota == null) return null;

        var dto = new QuotaDto
        {
            QuotaId = quota.QuotaId,
            UserId = quota.UserId,
            UserEmail = quota.User?.Email ?? string.Empty,
            ServiceId = quota.ServiceId,
            ServiceName = quota.ApiService?.ServiceName ?? string.Empty,
            MonthlyLimit = quota.MonthlyLimit,
            MonthlyTokenLimit = quota.MonthlyTokenLimit, // Phase 3.3d
            DailyLimit = quota.DailyLimit,
            CostLimit = quota.CostLimit,
            CurrentUsage = quota.CurrentUsage,
            CurrentTokens = quota.CurrentTokens, // Phase 3.3d
            CurrentCost = quota.CurrentCost,
            AlertThreshold = quota.AlertThreshold,
            IsAlertEnabled = quota.IsAlertEnabled,
            LastResetAt = quota.LastResetAt,
            CreatedAt = quota.CreatedAt,
            UpdatedAt = quota.UpdatedAt
        };

        await _cachingService.SetAsync(cacheKey, dto, TimeSpan.FromMinutes(5));
        return dto;
    }

    public async Task<QuotaDto> SetQuotaAsync(int userId, int serviceId, SetQuotaRequestDto request)
    {
        var quota = await _context.ApiQuotas
            .FirstOrDefaultAsync(q => q.UserId == userId && q.ServiceId == serviceId);

        if (quota == null)
        {
            quota = new Models.ApiQuota
            {
                UserId = userId,
                ServiceId = serviceId,
                MonthlyLimit = request.MonthlyLimit ?? 1000,
                MonthlyTokenLimit = request.MonthlyTokenLimit, // Phase 3.3d: 선택 한도 (null = 미적용)
                DailyLimit = request.DailyLimit ?? 100,
                CostLimit = request.CostLimit ?? 100.00m,
                CurrentUsage = 0,
                CurrentTokens = 0L, // Phase 3.3d
                CurrentCost = 0,
                AlertThreshold = request.AlertThreshold ?? 80,
                IsAlertEnabled = request.IsAlertEnabled ?? true,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            };
            _context.ApiQuotas.Add(quota);
        }
        else
        {
            quota.MonthlyLimit = request.MonthlyLimit ?? quota.MonthlyLimit;
            // Phase 3.3d: MonthlyTokenLimit 는 nullable. 요청 본문에 키 자체가 없으면 기존값 유지.
            // 명시적으로 null 로 보내 한도를 해제하려면 별도 엔드포인트가 필요하므로 본 메서드는 "제공된 값으로 갱신"만 처리.
            if (request.MonthlyTokenLimit.HasValue)
            {
                quota.MonthlyTokenLimit = request.MonthlyTokenLimit;
            }
            quota.DailyLimit = request.DailyLimit ?? quota.DailyLimit;
            quota.CostLimit = request.CostLimit ?? quota.CostLimit;
            quota.AlertThreshold = request.AlertThreshold ?? quota.AlertThreshold;
            quota.IsAlertEnabled = request.IsAlertEnabled ?? quota.IsAlertEnabled;
            quota.UpdatedAt = DateTime.UtcNow;
        }

        await _context.SaveChangesAsync();
        
        // Invalidate cache
        var cacheKey = _cachingService.GetQuotaKey(userId, serviceId);
        await _cachingService.RemoveAsync(cacheKey);
        
        return await GetQuotaAsync(userId, serviceId) ?? throw new InvalidOperationException("Failed to set quota");
    }

    public async Task<QuotaCheckResult> CheckQuotaAsync(int userId, int serviceId)
    {
        var quota = await _context.ApiQuotas
            .FirstOrDefaultAsync(q => q.UserId == userId && q.ServiceId == serviceId);

        if (quota == null)
        {
            // No quota set, allow usage
            return new QuotaCheckResult { CanUse = true };
        }

        // Check monthly limit (호출 횟수 기준)
        if (quota.CurrentUsage >= quota.MonthlyLimit)
        {
            return new QuotaCheckResult
            {
                CanUse = false,
                Message = "Monthly quota limit exceeded"
            };
        }

        // Phase 3.3d: 월간 토큰 한도 검사 (선택 — MonthlyTokenLimit 가 NULL 이면 미적용).
        // 호출 횟수 기준보다 LLM 비용 구조에 더 가까운 기준이라 병행 운영한다.
        if (quota.MonthlyTokenLimit.HasValue && quota.CurrentTokens >= quota.MonthlyTokenLimit.Value)
        {
            return new QuotaCheckResult
            {
                CanUse = false,
                Message = "Monthly token limit exceeded"
            };
        }

        // Check daily limit
        var today = DateTime.UtcNow.Date;
        var todayUsage = await _context.ApiUsages
            .Where(u => u.UserId == userId && 
                       u.ServiceId == serviceId && 
                       u.RequestTime.Date == today)
            .CountAsync();

        if (todayUsage >= quota.DailyLimit)
        {
            return new QuotaCheckResult
            {
                CanUse = false,
                Message = "Daily quota limit exceeded"
            };
        }

        // Check cost limit
        if (quota.CurrentCost >= quota.CostLimit)
        {
            return new QuotaCheckResult
            {
                CanUse = false,
                Message = "Cost limit exceeded"
            };
        }

        return new QuotaCheckResult { CanUse = true };
    }

    /// <summary>
    /// LLM 호출 1건의 사용량을 ApiQuota 에 누적한다.
    /// Phase 3.3d (TECHSPEC §16 H10) — tokens 파라미터를 폐기하던 버그 수정.
    /// 호출 횟수(CurrentUsage), 토큰(CurrentTokens), 비용(CurrentCost) 3개 카운터를 동시에 갱신한다.
    /// </summary>
    public async Task RecordUsageAsync(int userId, int serviceId, int tokens, decimal cost)
    {
        var quota = await _context.ApiQuotas
            .FirstOrDefaultAsync(q => q.UserId == userId && q.ServiceId == serviceId);

        if (quota != null)
        {
            quota.CurrentUsage++;
            // Phase 3.3d: 호출처가 정성껏 전달하던 토큰 수가 그동안 누락되던 버그 해소.
            // tokens 가 0 인 호출(예: ImageGenerationController)은 그대로 0 누적되어 영향 없음.
            quota.CurrentTokens += tokens;
            quota.CurrentCost += cost;
            quota.UpdatedAt = DateTime.UtcNow;
            await _context.SaveChangesAsync();

            // Invalidate cache
            var cacheKey = _cachingService.GetQuotaKey(userId, serviceId);
            await _cachingService.RemoveAsync(cacheKey);
        }
    }

    public async Task<int> GetTodayUsageAsync(int userId, int serviceId)
    {
        var today = DateTime.UtcNow.Date;
        var todayUsage = await _context.ApiUsages
            .Where(u => u.UserId == userId && 
                       u.ServiceId == serviceId && 
                       u.RequestTime.Date == today)
            .CountAsync();
        
        return todayUsage;
    }
}
