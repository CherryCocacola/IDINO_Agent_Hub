using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

public class TeamService : ITeamService
{
    private readonly AIAgentManagementDbContext _context;

    public TeamService(AIAgentManagementDbContext context)
    {
        _context = context;
    }

    public async Task<List<TeamDto>> GetTeamsAsync(string? search = null, bool? isActive = null)
    {
        var query = _context.Teams
            .Include(t => t.Manager)
            .Include(t => t.TeamMembers.Where(tm => tm.IsActive))
                .ThenInclude(tm => tm.User)
            .AsQueryable();

        if (!string.IsNullOrWhiteSpace(search))
        {
            query = query.Where(t => 
                t.TeamName.Contains(search) ||
                (t.Description != null && t.Description.Contains(search)) ||
                (t.Department != null && t.Department.Contains(search))
            );
        }

        if (isActive.HasValue)
        {
            query = query.Where(t => t.IsActive == isActive.Value);
        }

        var teams = await query
            .OrderBy(t => t.TeamName)
            .ToListAsync();

        return teams.Select(t => new TeamDto
        {
            TeamId = t.TeamId,
            TeamName = t.TeamName,
            Description = t.Description,
            Department = t.Department,
            ManagerId = t.ManagerId,
            ManagerName = t.Manager?.FullName,
            ManagerEmail = t.Manager?.Email,
            IsActive = t.IsActive,
            MemberCount = t.TeamMembers.Count(tm => tm.IsActive),
            CreatedAt = t.CreatedAt,
            UpdatedAt = t.UpdatedAt,
            Members = t.TeamMembers
                .Where(tm => tm.IsActive)
                .Select(tm => new TeamMemberDto
                {
                    TeamMemberId = tm.TeamMemberId,
                    TeamId = tm.TeamId,
                    UserId = tm.UserId,
                    UserName = tm.User.FullName,
                    UserEmail = tm.User.Email,
                    Role = tm.Role,
                    JoinedAt = tm.JoinedAt,
                    IsActive = tm.IsActive
                })
                .ToList()
        }).ToList();
    }

    public async Task<TeamDto?> GetTeamByIdAsync(int teamId)
    {
        var team = await _context.Teams
            .Include(t => t.Manager)
            .Include(t => t.TeamMembers.Where(tm => tm.IsActive))
                .ThenInclude(tm => tm.User)
            .FirstOrDefaultAsync(t => t.TeamId == teamId);

        if (team == null) return null;

        return new TeamDto
        {
            TeamId = team.TeamId,
            TeamName = team.TeamName,
            Description = team.Description,
            Department = team.Department,
            ManagerId = team.ManagerId,
            ManagerName = team.Manager?.FullName,
            ManagerEmail = team.Manager?.Email,
            IsActive = team.IsActive,
            MemberCount = team.TeamMembers.Count(tm => tm.IsActive),
            CreatedAt = team.CreatedAt,
            UpdatedAt = team.UpdatedAt,
            Members = team.TeamMembers
                .Where(tm => tm.IsActive)
                .Select(tm => new TeamMemberDto
                {
                    TeamMemberId = tm.TeamMemberId,
                    TeamId = tm.TeamId,
                    UserId = tm.UserId,
                    UserName = tm.User.FullName,
                    UserEmail = tm.User.Email,
                    Role = tm.Role,
                    JoinedAt = tm.JoinedAt,
                    IsActive = tm.IsActive
                })
                .ToList()
        };
    }

    public async Task<TeamDto> CreateTeamAsync(CreateTeamRequestDto request, int createdBy)
    {
        var team = new Models.Team
        {
            TeamName = request.TeamName,
            Description = request.Description,
            Department = request.Department,
            ManagerId = request.ManagerId,
            IsActive = true,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };

        _context.Teams.Add(team);
        await _context.SaveChangesAsync();

        return await GetTeamByIdAsync(team.TeamId) 
            ?? throw new InvalidOperationException("Failed to create team");
    }

    public async Task<TeamDto?> UpdateTeamAsync(int teamId, UpdateTeamRequestDto request, int userId)
    {
        var team = await _context.Teams.FindAsync(teamId);
        if (team == null) return null;

        if (!string.IsNullOrWhiteSpace(request.TeamName))
        {
            team.TeamName = request.TeamName;
        }
        if (request.Description != null)
        {
            team.Description = request.Description;
        }
        if (request.Department != null)
        {
            team.Department = request.Department;
        }
        if (request.ManagerId.HasValue)
        {
            team.ManagerId = request.ManagerId.Value;
        }
        if (request.IsActive.HasValue)
        {
            team.IsActive = request.IsActive.Value;
        }

        team.UpdatedAt = DateTime.UtcNow;
        await _context.SaveChangesAsync();

        return await GetTeamByIdAsync(teamId);
    }

    public async Task<bool> DeleteTeamAsync(int teamId, int userId)
    {
        var team = await _context.Teams
            .Include(t => t.TeamMembers)
            .FirstOrDefaultAsync(t => t.TeamId == teamId);

        if (team == null) return false;

        // 팀 멤버들을 비활성화
        foreach (var member in team.TeamMembers.Where(tm => tm.IsActive))
        {
            member.IsActive = false;
            member.LeftAt = DateTime.UtcNow;
        }

        // 팀을 비활성화
        team.IsActive = false;
        team.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync();
        return true;
    }

    public async Task<TeamMemberDto> AddTeamMemberAsync(int teamId, AddTeamMemberRequestDto request, int addedBy)
    {
        // 이미 팀에 속해있는지 확인
        var existingMember = await _context.TeamMembers
            .FirstOrDefaultAsync(tm => tm.TeamId == teamId && tm.UserId == request.UserId && tm.IsActive);

        if (existingMember != null)
        {
            throw new InvalidOperationException("User is already a member of this team");
        }

        var teamMember = new Models.TeamMember
        {
            TeamId = teamId,
            UserId = request.UserId,
            Role = request.Role,
            JoinedAt = DateTime.UtcNow,
            IsActive = true,
            AddedBy = addedBy
        };

        _context.TeamMembers.Add(teamMember);
        await _context.SaveChangesAsync();

        var member = await _context.TeamMembers
            .Include(tm => tm.User)
            .FirstOrDefaultAsync(tm => tm.TeamMemberId == teamMember.TeamMemberId);

        if (member == null)
        {
            throw new InvalidOperationException("Failed to create team member");
        }

        return new TeamMemberDto
        {
            TeamMemberId = member.TeamMemberId,
            TeamId = member.TeamId,
            UserId = member.UserId,
            UserName = member.User.FullName,
            UserEmail = member.User.Email,
            Role = member.Role,
            JoinedAt = member.JoinedAt,
            IsActive = member.IsActive
        };
    }

    public async Task<bool> RemoveTeamMemberAsync(int teamId, int userId, int removedBy)
    {
        var teamMember = await _context.TeamMembers
            .FirstOrDefaultAsync(tm => tm.TeamId == teamId && tm.UserId == userId && tm.IsActive);

        if (teamMember == null) return false;

        teamMember.IsActive = false;
        teamMember.LeftAt = DateTime.UtcNow;

        await _context.SaveChangesAsync();
        return true;
    }

    public async Task<bool> UpdateTeamMemberRoleAsync(int teamId, int userId, string? role, int updatedBy)
    {
        var teamMember = await _context.TeamMembers
            .FirstOrDefaultAsync(tm => tm.TeamId == teamId && tm.UserId == userId && tm.IsActive);

        if (teamMember == null) return false;

        teamMember.Role = role;
        await _context.SaveChangesAsync();

        return true;
    }
}
