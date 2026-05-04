using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IToolService
{
    Task<List<ToolDto>> GetToolsAsync(int? userId = null, bool? isPublic = null, string? toolType = null, string? search = null);
    Task<ToolDto?> GetToolByIdAsync(int toolId);
    Task<ToolDto> CreateToolAsync(CreateToolRequestDto request, int createdBy);
    Task<ToolDto?> UpdateToolAsync(int toolId, UpdateToolRequestDto request, int userId);
    Task<bool> DeleteToolAsync(int toolId, int userId);
    Task<ToolVersionDto> CreateToolVersionAsync(int toolId, string version, string? code, string? config);
    Task<List<ToolVersionDto>> GetToolVersionsAsync(int toolId);
    Task<bool> SetActiveVersionAsync(int toolId, int versionId);
}
