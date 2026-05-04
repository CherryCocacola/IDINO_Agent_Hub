using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;
using System.Security.Claims;
using AIAgentManagement.Services;

namespace AIAgentManagement.Attributes;

/// <summary>
/// API 키 인증 + IP 화이트리스트 + Rate Limit + Scope 검증을 수행하는 필터.
/// JWT 인증이 이미 성공한 경우 Scope 검사만 수행합니다.
/// </summary>
[AttributeUsage(AttributeTargets.Class | AttributeTargets.Method, AllowMultiple = false)]
public class ApiKeyAuthorizeAttribute : Attribute, IAuthorizationFilter
{
    /// <summary>
    /// 이 엔드포인트에 필요한 스코프. 예: "stream", "info", "usage".
    /// null이면 스코프 검사 없이 인증된 키면 통과.
    /// </summary>
    public string? RequiredScope { get; set; }

    public ApiKeyAuthorizeAttribute(string? requiredScope = null)
    {
        RequiredScope = requiredScope;
    }

    public void OnAuthorization(AuthorizationFilterContext context)
    {
        var httpContext = context.HttpContext;

        // ── JWT 인증이 이미 성공한 경우 → Scope 검사 없이 통과 ──
        if (httpContext.User?.Identity?.IsAuthenticated == true
            && httpContext.User.Identity.AuthenticationType != "ApiKey")
        {
            return;
        }

        // ── API Key 추출 ────────────────────────────────────────
        string? apiKey = null;

        if (httpContext.Request.Headers.TryGetValue("X-API-Key", out var apiKeyHeader))
        {
            apiKey = apiKeyHeader.ToString();
        }
        else if (httpContext.Request.Headers.TryGetValue("Authorization", out var authHeader))
        {
            var authValue = authHeader.ToString();
            if (authValue.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
                apiKey = authValue["Bearer ".Length..].Trim();
        }

        if (string.IsNullOrWhiteSpace(apiKey))
        {
            context.Result = new UnauthorizedObjectResult(new
            {
                message = "API Key is required",
                hint = "X-API-Key 헤더 또는 Authorization: Bearer <key> 헤더를 포함해주세요."
            });
            return;
        }

        // ── API Key 검증 (DB 조회 + 복호화) ─────────────────────
        var apiKeyAuthService = httpContext.RequestServices.GetService<IApiKeyAuthService>();
        if (apiKeyAuthService == null)
        {
            context.Result = new StatusCodeResult(500);
            return;
        }

        var validationResult = apiKeyAuthService.ValidateApiKeyAsync(apiKey).GetAwaiter().GetResult();

        if (validationResult == null)
        {
            context.Result = new UnauthorizedObjectResult(new { message = "Invalid or expired API Key" });
            return;
        }

        // ── IP 화이트리스트 검사 ──────────────────────────────────
        var allowedIps = validationResult.AllowedIpList;
        if (allowedIps.Count > 0)
        {
            var clientIp = httpContext.Connection.RemoteIpAddress?.ToString() ?? string.Empty;

            // IPv6 루프백을 IPv4로 정규화
            if (clientIp == "::1") clientIp = "127.0.0.1";

            var isIpAllowed = allowedIps.Any(ip =>
                string.Equals(ip.Trim(), clientIp, StringComparison.OrdinalIgnoreCase));

            if (!isIpAllowed)
            {
                var logger = httpContext.RequestServices.GetService<ILogger<ApiKeyAuthorizeAttribute>>();
                logger?.LogWarning(
                    "IP 화이트리스트 차단: ApiKeyId={ApiKeyId}, ClientIP={ClientIP}, AllowedIPs={AllowedIPs}",
                    validationResult.ApiKeyId, clientIp, validationResult.AllowedIps);

                context.Result = new ObjectResult(new
                {
                    message = "Access denied: IP address not whitelisted",
                    clientIp
                })
                { StatusCode = 403 };
                return;
            }
        }

        // ── Rate Limiting 검사 ────────────────────────────────────
        var rateLimiter = httpContext.RequestServices.GetService<IApiKeyRateLimiter>();
        if (rateLimiter != null)
        {
            var rateLimitResult = rateLimiter.CheckAndIncrement(
                validationResult.ApiKeyId,
                validationResult.RateLimitPerMinute,
                validationResult.RateLimitPerDay);

            if (rateLimitResult.IsExceeded)
            {
                httpContext.Response.Headers["Retry-After"] = rateLimitResult.RetryAfterSeconds.ToString();
                context.Result = new ObjectResult(new
                {
                    message = $"Rate limit exceeded ({rateLimitResult.LimitType})",
                    retryAfterSeconds = rateLimitResult.RetryAfterSeconds
                })
                { StatusCode = 429 };
                return;
            }
        }

        // ── Scope 검사 ────────────────────────────────────────────
        if (!string.IsNullOrWhiteSpace(RequiredScope))
        {
            var scopes = validationResult.ScopeList;
            // 스코프가 비어있으면 모든 권한 허용
            if (scopes.Count > 0 && !scopes.Contains(RequiredScope, StringComparer.OrdinalIgnoreCase))
            {
                context.Result = new ObjectResult(new
                {
                    message = $"Insufficient scope. Required: '{RequiredScope}'",
                    yourScopes = validationResult.Scopes ?? "*"
                })
                { StatusCode = 403 };
                return;
            }
        }

        // ── Claims 구성 (API Key 인증 성공) ──────────────────────
        var claims = new List<Claim>
        {
            new Claim(ClaimTypes.NameIdentifier, validationResult.UserId.ToString()),
            new Claim("ApiKeyId", validationResult.ApiKeyId.ToString()),
        };

        if (validationResult.AgentId.HasValue)
            claims.Add(new Claim("AgentId", validationResult.AgentId.Value.ToString()));

        if (!string.IsNullOrWhiteSpace(validationResult.Scopes))
            claims.Add(new Claim("Scopes", validationResult.Scopes));

        var identity = new ClaimsIdentity(claims, "ApiKey");
        httpContext.User = new ClaimsPrincipal(identity);

        // HttpContext.Items에 검증 결과 보관 (컨트롤러에서 참조 가능)
        httpContext.Items["ApiKeyValidation"] = validationResult;
    }
}
