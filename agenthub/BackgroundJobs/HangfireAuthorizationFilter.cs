using Hangfire.Dashboard;
using System.Security.Claims;

namespace AIAgentManagement.BackgroundJobs;

public class HangfireAuthorizationFilter : IDashboardAuthorizationFilter
{
    public bool Authorize(DashboardContext context)
    {
        var httpContext = context.GetHttpContext();

        // 인증되지 않은 사용자 차단
        if (httpContext.User.Identity?.IsAuthenticated != true)
            return false;

        // Admin 역할 또는 SuperAdmin 역할이 있어야 접근 가능
        var role = httpContext.User.FindFirst(ClaimTypes.Role)?.Value
                   ?? httpContext.User.FindFirst("role")?.Value;

        return role == "Admin" || role == "SuperAdmin";
    }
}
