namespace AIAgentManagement.Exceptions;

/// <summary>
/// Tool 자체가 존재하지 않거나 비활성 상태일 때 발생.
/// 컨트롤러에서 404 NotFound 로 매핑한다.
/// </summary>
public class ToolNotFoundException : InvalidOperationException
{
    public int ToolId { get; }

    public ToolNotFoundException(int toolId)
        : base($"도구를 찾을 수 없거나 비활성 상태입니다. (ToolId={toolId})")
    {
        ToolId = toolId;
    }
}

/// <summary>
/// Tool 은 존재하지만 활성 ToolVersion 이 등록되지 않은 상태에서 실행을 시도할 때 발생.
/// 운영자가 버전을 먼저 등록·활성화하도록 안내해야 한다.
/// 컨트롤러에서 400 BadRequest (도메인 검증 실패) 로 매핑한다.
/// </summary>
public class ToolVersionNotActiveException : InvalidOperationException
{
    public int ToolId { get; }

    public ToolVersionNotActiveException(int toolId)
        : base($"활성 버전이 등록되지 않은 도구입니다. 도구 버전을 먼저 등록·활성화하세요. (ToolId={toolId})")
    {
        ToolId = toolId;
    }
}
