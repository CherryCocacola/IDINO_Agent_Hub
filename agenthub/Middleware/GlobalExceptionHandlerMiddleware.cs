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

        var (statusCode, errorCode, message) = ex switch
        {
            UnauthorizedAccessException => (401, "UNAUTHORIZED", "인증이 필요합니다."),
            KeyNotFoundException        => (404, "NOT_FOUND", "요청한 리소스를 찾을 수 없습니다."),
            ArgumentException           => (400, "INVALID_ARGUMENT", ex.Message),
            InvalidOperationException   => (400, "INVALID_OPERATION", ex.Message),
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
