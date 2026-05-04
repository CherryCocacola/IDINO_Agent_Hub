namespace AIAgentManagement.Services;

public interface IApiKeyRateLimiter
{
    /// <summary>
    /// API 키의 요청 카운터를 증가시키고 제한 초과 여부를 반환합니다.
    /// </summary>
    /// <param name="apiKeyId">API 키 ID</param>
    /// <param name="limitPerMinute">분당 최대 요청 수 (null이면 무제한)</param>
    /// <param name="limitPerDay">일당 최대 요청 수 (null이면 무제한)</param>
    /// <returns>제한 초과 시 RateLimitResult (IsExceeded=true), 정상 시 IsExceeded=false</returns>
    RateLimitResult CheckAndIncrement(int apiKeyId, int? limitPerMinute, int? limitPerDay);
}

public class RateLimitResult
{
    public bool IsExceeded { get; init; }
    /// <summary>초과된 제한 종류: "minute" 또는 "day"</summary>
    public string? LimitType { get; init; }
    /// <summary>Retry-After 초(seconds)</summary>
    public int RetryAfterSeconds { get; init; }

    public static RateLimitResult Ok() => new() { IsExceeded = false };
    public static RateLimitResult ExceededMinute() => new() { IsExceeded = true, LimitType = "minute", RetryAfterSeconds = 60 };
    public static RateLimitResult ExceededDay() => new() { IsExceeded = true, LimitType = "day", RetryAfterSeconds = 86400 };
}
