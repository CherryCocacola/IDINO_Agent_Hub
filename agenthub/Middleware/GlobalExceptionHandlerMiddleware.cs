using System.Text.Json;
using AIAgentManagement.DTOs;

namespace AIAgentManagement.Middleware;

public class GlobalExceptionHandlerMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<GlobalExceptionHandlerMiddleware> _logger;

    public GlobalExceptionHandlerMiddleware(RequestDelegate next, ILogger<GlobalExceptionHandlerMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "처리되지 않은 예외 발생: {Path}", context.Request.Path);
            await HandleExceptionAsync(context, ex);
        }
    }

    private static async Task HandleExceptionAsync(HttpContext context, Exception ex)
    {
        if (context.Response.HasStarted)
            return;

        context.Response.ContentType = "application/json";

        // 트랙 #143 (2026-06-01): HttpRequestException 공통 매핑 — 외부 LLM/upstream HTTP 결함을
        // 모든 controller 에서 일관 처리 (트랙 #141/#142 의 AgentsController 한정 패치를 전역화).
        // 429 (TooManyRequests) → 503, 그 외 → 502. AiProxyService 등이 부착한 한국어 메시지 그대로 사용.
        var (statusCode, errorCode, message) = ex switch
        {
            UnauthorizedAccessException => (401, "UNAUTHORIZED", "인증이 필요합니다."),
            KeyNotFoundException        => (404, "NOT_FOUND", "요청한 리소스를 찾을 수 없습니다."),
            ArgumentException           => (400, "INVALID_ARGUMENT", ex.Message),
            InvalidOperationException   => (400, "INVALID_OPERATION", ex.Message),
            HttpRequestException hre    => (
                hre.StatusCode == System.Net.HttpStatusCode.TooManyRequests ? 503 : 502,
                "EXTERNAL_LLM_UPSTREAM_ERROR",
                string.IsNullOrWhiteSpace(hre.Message)
                    ? "외부 LLM 호출에 실패했습니다. 잠시 후 다시 시도해 주세요."
                    : hre.Message),
            _                           => (500, "INTERNAL_SERVER_ERROR", "서버 내부 오류가 발생했습니다.")
        };

        context.Response.StatusCode = statusCode;

        var response = new ErrorResponseDto(message, errorCode);
        var json = JsonSerializer.Serialize(response, new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        });

        await context.Response.WriteAsync(json);
    }
}
