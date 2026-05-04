namespace AIAgentManagement.Middleware;

/// <summary>
/// GS인증 보안성 요구사항 대응 — OWASP 권장 보안 헤더 추가
/// </summary>
public class SecurityHeadersMiddleware
{
    private readonly RequestDelegate _next;

    public SecurityHeadersMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var headers = context.Response.Headers;

        // 클릭재킹 방지 — 동일 출처에서만 iframe 허용
        headers["X-Frame-Options"] = "SAMEORIGIN";

        // MIME 스니핑 방지
        headers["X-Content-Type-Options"] = "nosniff";

        // XSS 필터 활성화 (구형 브라우저용)
        headers["X-XSS-Protection"] = "1; mode=block";

        // Referrer 정책 — 외부 도메인으로 URL 정보 유출 방지
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin";

        // 권한 정책 — 불필요한 브라우저 기능 차단
        headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()";

        // HTTPS 접속 시 HSTS 활성화 (1년)
        if (context.Request.IsHttps)
        {
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains";
        }

        // Content Security Policy
        // Vue SPA: inline script/style 허용 필요, SignalR WebSocket 허용
        headers["Content-Security-Policy"] =
            "default-src 'self'; " +
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; " +
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; " +
            "img-src 'self' data: https: blob:; " +
            "font-src 'self' data: https://cdn.jsdelivr.net https://fonts.gstatic.com; " +
            "connect-src 'self' ws: wss:; " +
            "frame-ancestors 'self'; " +
            "object-src 'none'; " +
            "base-uri 'self';";

        await _next(context);
    }
}
