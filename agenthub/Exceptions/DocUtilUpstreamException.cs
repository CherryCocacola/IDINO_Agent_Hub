using System.Net;

namespace AIAgentManagement.Exceptions;

/// <summary>
/// DocUtil upstream 호출 실패 시 발생하는 예외.
/// <para>
/// Phase 10.x (2026-05-11) 보강 — 기존 InvalidOperationException 일반화는 status code 식별이
/// 불가능하여 BFF 컨트롤러가 410 Gone 같은 특수 케이스를 별도 한국어 안내로 분기하지 못했다.
/// 본 예외는 upstream HTTP status code 와 한국어 메시지를 함께 전달하여 호출자가 분기할 수 있게 한다.
/// </para>
/// <para>
/// InvalidOperationException 을 상속한다 — 기존 컨트롤러의 `catch (InvalidOperationException ex)`
/// 분기가 그대로 동작하면서, status code 가 필요한 컨트롤러는 catch (DocUtilUpstreamException) 로
/// 더 구체적으로 catch 할 수 있다.
/// </para>
/// <para>
/// 원본 body 는 노출하지 않는다 — 클라이언트 응답에는 한국어 안내만, body 는 로그에만 잔류.
/// </para>
/// </summary>
public class DocUtilUpstreamException : InvalidOperationException
{
    /// <summary>upstream(DocUtil) HTTP status code.</summary>
    public HttpStatusCode StatusCode { get; }

    /// <summary>호출한 DocUtil 경로(로깅/디버깅용).</summary>
    public string Path { get; }

    /// <summary>
    /// 세분화된 errorCode. 호출자(BFF Controller) 가 ErrorResponseDto.ErrorCode 에 그대로 부착하여
    /// 운영자 트레이싱을 돕는다. 미지정 시 일반 카테고리(<c>DOCUTIL_UPSTREAM_ERROR</c>) 로 폴백.
    /// </summary>
    /// <remarks>
    /// Phase 10.x Task #9 (2026-05-15) 신설:
    ///   이전에는 모든 DocUtil 실패가 단일 코드 <c>DOCUTIL_UPSTREAM_ERROR</c> 로 묶여
    ///   운영자가 401/5xx/422/네트워크 장애를 구분하지 못했다. 본 속성으로 카테고리화한다.
    /// </remarks>
    public string ErrorCode { get; }

    public DocUtilUpstreamException(
        HttpStatusCode statusCode,
        string path,
        string message)
        : this(statusCode, path, ErrorCodes.UpstreamError, message)
    {
    }

    public DocUtilUpstreamException(
        HttpStatusCode statusCode,
        string path,
        string errorCode,
        string message)
        : base(message)
    {
        StatusCode = statusCode;
        Path = path;
        ErrorCode = string.IsNullOrWhiteSpace(errorCode) ? ErrorCodes.UpstreamError : errorCode;
    }

    public DocUtilUpstreamException(
        HttpStatusCode statusCode,
        string path,
        string message,
        Exception inner)
        : this(statusCode, path, ErrorCodes.UpstreamError, message, inner)
    {
    }

    public DocUtilUpstreamException(
        HttpStatusCode statusCode,
        string path,
        string errorCode,
        string message,
        Exception inner)
        : base(message, inner)
    {
        StatusCode = statusCode;
        Path = path;
        ErrorCode = string.IsNullOrWhiteSpace(errorCode) ? ErrorCodes.UpstreamError : errorCode;
    }

    /// <summary>
    /// 표준 errorCode 상수 — Controller 매핑 / Frontend 분기 / 운영자 알람 룰의 단일 사전.
    /// 신규 코드 추가 시 frontend i18n key 와 운영자 알람 룰도 함께 업데이트.
    /// </summary>
    public static class ErrorCodes
    {
        /// <summary>분류 불가능한 일반 DocUtil 호출 실패(폴백). 가능하면 더 구체적 코드 사용.</summary>
        public const string UpstreamError = "DOCUTIL_UPSTREAM_ERROR";

        /// <summary>JwtToken / ServiceUsername+Password / ApiKey 모두 미설정.
        /// 운영자에게 .env 확인을 안내. HTTP 503 매핑.</summary>
        public const string TokenMissing = "DOCUTIL_TOKEN_MISSING";

        /// <summary>토큰은 발급/시도되었으나 DocUtil 측이 401/403 으로 거절.
        /// 비밀번호 회전, 계정 잠금, ApiKey 폐기 등이 원인. HTTP 503 매핑.</summary>
        public const string TokenForbidden = "DOCUTIL_TOKEN_FORBIDDEN";

        /// <summary>DocUtil 서비스 자체 5xx / 네트워크 단절 / 타임아웃 / Circuit Breaker OPEN.
        /// 운영자에게 DocUtil 서비스 상태 확인을 안내. HTTP 502 매핑.</summary>
        public const string UpstreamUnreachable = "DOCUTIL_UPSTREAM_UNREACHABLE";

        /// <summary>FastAPI/Pydantic 422 validation error. 호출자(BFF) 입력 정정 필요. HTTP 422 매핑 고려.</summary>
        public const string ValidationError = "DOCUTIL_VALIDATION_ERROR";

        /// <summary>DocUtil 측 deprecate(410 Gone) 엔드포인트. HTTP 410 매핑.</summary>
        public const string Deprecated = "DOCUTIL_DEPRECATED";
    }
}
