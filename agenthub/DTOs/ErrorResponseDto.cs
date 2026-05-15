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

    /// <summary>
    /// DocUtil 호출 실패 → 한국어 ErrorResponseDto 매핑.
    /// <para>
    /// Phase 10.x Task #9 (2026-05-15) 신설 — 13개 AdminDocUtil*Controller 의 catch 분기가
    /// 단일 errorCode <c>DOCUTIL_UPSTREAM_ERROR</c> 로 묶이지 않도록, exception 의
    /// <see cref="Exceptions.DocUtilUpstreamException.ErrorCode"/> 를 ResponseDto.ErrorCode 로 그대로 전파.
    /// </para>
    /// <para>
    /// 호출자(Controller) 는 <see cref="MapDocUtilUpstreamToStatusCode"/> 와 함께 사용하여
    /// 적절한 HTTP status code 도 일관 매핑한다.
    /// </para>
    /// </summary>
    public static ErrorResponseDto FromDocUtilUpstream(
        Exceptions.DocUtilUpstreamException ex,
        string? userMessage = null)
    {
        // 호출자가 한국어 사용자 메시지를 따로 주지 않으면 예외 메시지를 그대로 사용.
        // DocUtilClient.EnsureSuccessOrThrowKoreanAsync 가 이미 한국어 안내를 만들어 둠.
        return new ErrorResponseDto(
            message: userMessage ?? ex.Message,
            errorCode: ex.ErrorCode,
            details: new
            {
                upstreamStatus = (int)ex.StatusCode,
                upstreamPath = ex.Path,
            });
    }

    /// <summary>
    /// DocUtil 예외의 errorCode 에 대응되는 AgentHub 외부 표면 HTTP status code.
    /// <list type="bullet">
    /// <item><term>DOCUTIL_TOKEN_MISSING / DOCUTIL_TOKEN_FORBIDDEN</term>
    ///   <description>503 Service Unavailable — 운영자 자격 정상화 필요 신호</description></item>
    /// <item><term>DOCUTIL_DEPRECATED</term>
    ///   <description>410 Gone — 신규 워크플로로 안내</description></item>
    /// <item><term>DOCUTIL_VALIDATION_ERROR</term>
    ///   <description>422 — 입력 검증 실패</description></item>
    /// <item><term>그 외(UPSTREAM_ERROR / UPSTREAM_UNREACHABLE)</term>
    ///   <description>502 Bad Gateway — 일반 upstream 장애</description></item>
    /// </list>
    /// </summary>
    public static int MapDocUtilUpstreamToStatusCode(Exceptions.DocUtilUpstreamException ex)
    {
        return ex.ErrorCode switch
        {
            Exceptions.DocUtilUpstreamException.ErrorCodes.TokenMissing => 503,
            Exceptions.DocUtilUpstreamException.ErrorCodes.TokenForbidden => 503,
            Exceptions.DocUtilUpstreamException.ErrorCodes.Deprecated => 410,
            Exceptions.DocUtilUpstreamException.ErrorCodes.ValidationError => 422,
            _ => 502, // UpstreamError / UpstreamUnreachable / 기타
        };
    }
}
