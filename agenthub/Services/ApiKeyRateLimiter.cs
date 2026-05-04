using Microsoft.Extensions.Caching.Memory;

namespace AIAgentManagement.Services;

/// <summary>
/// IMemoryCache 기반 슬라이딩 윈도우 Rate Limiter.
/// Singleton으로 등록하여 요청 간 상태를 유지합니다.
/// 다중 서버(수평 확장) 환경에서는 Redis 기반 구현으로 교체 필요.
/// </summary>
public class ApiKeyRateLimiter : IApiKeyRateLimiter
{
    private readonly IMemoryCache _cache;
    private readonly ILogger<ApiKeyRateLimiter> _logger;

    // 슬라이딩 윈도우 만료 여유값 (Race Condition 방지)
    private static readonly TimeSpan MinuteWindow = TimeSpan.FromMinutes(1).Add(TimeSpan.FromSeconds(1));
    private static readonly TimeSpan DayWindow = TimeSpan.FromDays(1).Add(TimeSpan.FromSeconds(10));

    public ApiKeyRateLimiter(IMemoryCache cache, ILogger<ApiKeyRateLimiter> logger)
    {
        _cache = cache;
        _logger = logger;
    }

    public RateLimitResult CheckAndIncrement(int apiKeyId, int? limitPerMinute, int? limitPerDay)
    {
        // 1) 분당 제한 검사
        if (limitPerMinute.HasValue && limitPerMinute.Value > 0)
        {
            var minuteKey = $"rl:min:{apiKeyId}";
            var minuteCount = _cache.GetOrCreate(minuteKey, entry =>
            {
                entry.AbsoluteExpirationRelativeToNow = MinuteWindow;
                return 0;
            });

            if (minuteCount >= limitPerMinute.Value)
            {
                _logger.LogWarning("Rate Limit 초과(분) — ApiKeyId={ApiKeyId}, Limit={Limit}", apiKeyId, limitPerMinute.Value);
                return RateLimitResult.ExceededMinute();
            }

            _cache.Set(minuteKey, minuteCount + 1, MinuteWindow);
        }

        // 2) 일당 제한 검사
        if (limitPerDay.HasValue && limitPerDay.Value > 0)
        {
            var dayKey = $"rl:day:{apiKeyId}:{DateTime.UtcNow:yyyyMMdd}";
            var dayCount = _cache.GetOrCreate(dayKey, entry =>
            {
                entry.AbsoluteExpirationRelativeToNow = DayWindow;
                return 0;
            });

            if (dayCount >= limitPerDay.Value)
            {
                _logger.LogWarning("Rate Limit 초과(일) — ApiKeyId={ApiKeyId}, Limit={Limit}", apiKeyId, limitPerDay.Value);
                return RateLimitResult.ExceededDay();
            }

            _cache.Set(dayKey, dayCount + 1, DayWindow);
        }

        return RateLimitResult.Ok();
    }
}
