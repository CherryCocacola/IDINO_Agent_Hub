using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface ITeamService
{
    Task<List<TeamDto>> GetTeamsAsync(string? search = null, bool? isActive = null);
    Task<TeamDto?> GetTeamByIdAsync(int teamId);
    Task<TeamDto> CreateTeamAsync(CreateTeamRequestDto request, int createdBy);
    Task<TeamDto?> UpdateTeamAsync(int teamId, UpdateTeamRequestDto request, int userId);
    Task<bool> DeleteTeamAsync(int teamId, int userId);
    Task<TeamMemberDto> AddTeamMemberAsync(int teamId, AddTeamMemberRequestDto request, int addedBy);
    Task<bool> RemoveTeamMemberAsync(int teamId, int userId, int removedBy);
    Task<bool> UpdateTeamMemberRoleAsync(int teamId, int userId, string? role, int updatedBy);
}
