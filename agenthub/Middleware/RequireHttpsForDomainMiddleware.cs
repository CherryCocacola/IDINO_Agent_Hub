namespace AIAgentManagement.Middleware;

/// <summary>
/// agenthub.idino.co.kr 도메인으로 접속 시 HTTP 요청을 HTTPS로 리다이렉트합니다.
/// 다른 호스트(localhost 등)에는 영향을 주지 않습니다.
/// </summary>
public class RequireHttpsForDomainMiddleware
{
    private const string HttpsOnlyHost = "agenthub.idino.co.kr";
    private readonly RequestDelegate _next;

    public RequireHttpsForDomainMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var host = context.Request.Host.Value ?? "";
        // 호스트가 agenthub.idino.co.kr 이고 (포트 포함 비교)
        var isTargetHost = host.StartsWith(HttpsOnlyHost, StringComparison.OrdinalIgnoreCase) ||
                          host.Equals(HttpsOnlyHost, StringComparison.OrdinalIgnoreCase);
        var isHttps = context.Request.IsHttps;

        if (isTargetHost && !isHttps)
        {
            var redirectUrl = $"https://{host}{context.Request.Path}{context.Request.QueryString}";
            context.Response.Redirect(redirectUrl, permanent: true);
            return;
        }

        await _next(context);
    }
}
