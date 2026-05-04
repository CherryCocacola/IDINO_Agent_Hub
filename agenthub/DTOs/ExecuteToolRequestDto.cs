namespace AIAgentManagement.DTOs;

public class ExecuteToolRequestDto
{
    public int? VersionId { get; set; } // 특정 버전 실행, 없으면 활성 버전 사용
    public string? InputData { get; set; } // JSON 형식
}
