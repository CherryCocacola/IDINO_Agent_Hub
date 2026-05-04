namespace AIAgentManagement.DTOs;

public class ExecuteWorkflowRequestDto
{
    public string? InputData { get; set; } // JSON 형식
    public bool? WaitForCompletion { get; set; } // false면 비동기 실행
}
