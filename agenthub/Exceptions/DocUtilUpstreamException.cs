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

    public DocUtilUpstreamException(HttpStatusCode statusCode, string path, string message)
        : base(message)
    {
        StatusCode = statusCode;
        Path = path;
    }

    public DocUtilUpstreamException(
        HttpStatusCode statusCode,
        string path,
        string message,
        Exception inner)
        : base(message, inner)
    {
        StatusCode = statusCode;
        Path = path;
    }
}
