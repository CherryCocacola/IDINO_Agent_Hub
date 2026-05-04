using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IAgentService
{
    Task<List<AgentDto>> GetAgentsAsync(int? userId = null, bool? isPublic = null, string? search = null);
    Task<AgentDto?> GetAgentByIdAsync(int agentId);
    Task<AgentDto> CreateAgentAsync(CreateAgentRequestDto request, int createdBy);
    Task<AgentDto?> UpdateAgentAsync(int agentId, UpdateAgentRequestDto request, int userId, bool isAdmin = false);
    Task<bool> DeleteAgentAsync(int agentId, int userId, bool isAdmin = false);
}
