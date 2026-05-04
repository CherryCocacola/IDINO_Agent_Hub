using AIAgentManagement.Infrastructure;
using AIAgentManagement.Models;
using System.Security.Claims;

namespace AIAgentManagement.Middleware;

public class ActivityLoggingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ActivityLoggingMiddleware> _logger;
    private readonly ActivityLogChannel _channel;

    // ActivityLogChannel은 Singleton이므로 생성자 주입 가능
    public ActivityLoggingMiddleware(
        RequestDelegate next,
        ILogger<ActivityLoggingMiddleware> logger,
        ActivityLogChannel channel)
    {
        _next = next;
        _logger = logger;
        _channel = channel;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        // API 요청만 로깅 (정적 파일, Swagger 등 제외)
        var path = context.Request.Path.Value ?? "";
        var isApiRequest = path.StartsWith("/api/", StringComparison.OrdinalIgnoreCase) ||
                          path.StartsWith("/hubs/", StringComparison.OrdinalIgnoreCase);

        if (isApiRequest && context.User.Identity?.IsAuthenticated == true)
        {
            var userIdClaim = context.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (int.TryParse(userIdClaim, out var userId))
            {
                var fullPath = $"{context.Request.Method} {context.Request.Path}";
                // ActivityType: MaxLength(50) 제한
                var activityType = fullPath.Length > 50 ? fullPath[..50] : fullPath;
                // UserAgent: MaxLength(500) 제한
                var rawUserAgent = context.Request.Headers["User-Agent"].ToString();

                var activityLog = new ActivityLog
                {
                    UserId = userId,
                    ActivityType = activityType,
                    EntityType = "API",
                    Description = fullPath.Length > 500 ? fullPath[..500] : fullPath,
                    IpAddress = context.Connection.RemoteIpAddress?.ToString(),
                    UserAgent = rawUserAgent.Length > 500 ? rawUserAgent[..500] : rawUserAgent,
                    CreatedAt = DateTime.UtcNow
                };

                // DB 직접 저장 없이 채널에 넣고 즉시 반환
                // ActivityLogWorker가 백그라운드에서 배치 INSERT 처리
                if (!_channel.TryWrite(activityLog))
                {
                    _logger.LogWarning("ActivityLog 채널 용량 초과. 로그 유실: {Path}", path);
                }
            }
        }

        await _next(context);
    }
}
