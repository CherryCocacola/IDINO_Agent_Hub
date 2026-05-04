using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IToolExecutionService
{
    Task<ToolExecutionDto> ExecuteToolAsync(int toolId, ExecuteToolRequestDto request, int? userId = null);
    Task<ToolExecutionDto?> GetExecutionByIdAsync(long executionId);
    Task<List<ToolExecutionDto>> GetExecutionsAsync(int? toolId = null, int? userId = null, string? status = null, int skip = 0, int take = 50);
}
