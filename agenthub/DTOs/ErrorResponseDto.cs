namespace AIAgentManagement.DTOs;

/// <summary>
/// 통일된 에러 응답 형식
/// </summary>
public class ErrorResponseDto
{
    public string Message { get; set; } = string.Empty;
    public string? ErrorCode { get; set; }
    public object? Details { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;

    public ErrorResponseDto(string message, string? errorCode = null, object? details = null)
    {
        Message = message;
        ErrorCode = errorCode;
        Details = details;
    }

    public static ErrorResponseDto FromBannedWordException(Exceptions.BannedWordException ex)
    {
        return new ErrorResponseDto(
            message: ex.Message,
            errorCode: "BANNED_WORD_DETECTED",
            details: new { BlockedWords = ex.BlockedWords }
        );
    }

    public static ErrorResponseDto FromPiiDetectionException(Exceptions.PiiDetectionException ex)
    {
        return new ErrorResponseDto(
            message: ex.Message,
            errorCode: "PII_DETECTED",
            details: new
            {
                DetectedTypes = ex.DetectedTypes,
                DetectedCount = ex.DetectionResult.DetectedItems.Count
            }
        );
    }

    public static ErrorResponseDto InternalError(string message = "서버 내부 오류가 발생했습니다.")
        => new(message, "INTERNAL_SERVER_ERROR");

    public static ErrorResponseDto NotFound(string message = "요청한 리소스를 찾을 수 없습니다.")
        => new(message, "NOT_FOUND");

    public static ErrorResponseDto Forbidden(string message = "접근 권한이 없습니다.")
        => new(message, "FORBIDDEN");

    public static ErrorResponseDto BadRequest(string message, object? details = null)
        => new(message, "BAD_REQUEST", details);

    public static ErrorResponseDto Unauthorized(string message = "인증이 필요합니다.")
        => new(message, "UNAUTHORIZED");
}
