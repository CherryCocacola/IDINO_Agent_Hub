using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

public class UserService : IUserService
{
    private readonly AIAgentManagementDbContext _context;

    public UserService(AIAgentManagementDbContext context)
    {
        _context = context;
    }

    public async Task<List<UserDto>> GetUsersAsync(string? search = null, string? role = null, string? status = null)
    {
        var query = _context.Users
            .Include(u => u.UserRoles)
                .ThenInclude(ur => ur.Role)
            .Where(u => !u.IsDeleted)
            .AsQueryable();

        if (!string.IsNullOrEmpty(search))
        {
            query = query.Where(u => u.Email.Contains(search) || u.FullName.Contains(search));
        }

        if (!string.IsNullOrEmpty(status))
        {
            query = query.Where(u => u.Status == status);
        }

        if (!string.IsNullOrEmpty(role))
        {
            query = query.Where(u => u.UserRoles.Any(ur => ur.Role.RoleName == role));
        }

        var users = await query
            .Include(u => u.DepartmentRef)
                .ThenInclude(d => d!.ParentDepartment)
                    .ThenInclude(p => p!.ParentDepartment)
            .OrderByDescending(u => u.CreatedAt).ToListAsync();

        // 트랙 #98 — 부서 트리 path 계산을 위해 모든 Departments 캐시 (작은 마스터, 32행)
        var deptCache = await BuildDepartmentCacheAsync();

        return users.Select(u => MapToDto(u, deptCache)).ToList();
    }

    public async Task<UserDto?> GetUserByIdAsync(int userId)
    {
        var user = await _context.Users
            .Include(u => u.UserRoles)
                .ThenInclude(ur => ur.Role)
            .Include(u => u.DepartmentRef)
            .FirstOrDefaultAsync(u => u.UserId == userId && !u.IsDeleted);

        if (user == null) return null;

        var deptCache = await BuildDepartmentCacheAsync();
        return MapToDto(user, deptCache);
    }

    /// <summary>
    /// 트랙 #98 — Departments 마스터 캐시 (DepartmentId → (Name, ParentId)).
    /// 부서 트리 path 계산용. 작은 마스터(< 100행)이므로 메모리 캐시가 적합.
    /// </summary>
    private async Task<Dictionary<int, (string Name, int? ParentId)>> BuildDepartmentCacheAsync()
    {
        var all = await _context.Departments
            .AsNoTracking()
            .Select(d => new { d.DepartmentId, d.DepartmentName, d.ParentDepartmentId })
            .ToListAsync();
        return all.ToDictionary(d => d.DepartmentId, d => (d.DepartmentName, d.ParentDepartmentId));
    }

    /// <summary>
    /// 부서 트리 path 빌드: "아이디노(주) &gt; M.SI본부 &gt; Si 4팀" 형태.
    /// 재귀 부모 추적 + 순환 참조 방어 (depth &lt;= 10).
    /// </summary>
    private static string? BuildDepartmentPath(int? departmentId, Dictionary<int, (string Name, int? ParentId)> cache)
    {
        if (departmentId == null || !cache.ContainsKey(departmentId.Value)) return null;
        var parts = new List<string>();
        var currentId = departmentId;
        int depth = 0;
        while (currentId != null && depth < 10 && cache.TryGetValue(currentId.Value, out var dept))
        {
            parts.Insert(0, dept.Name);
            currentId = dept.ParentId;
            depth++;
        }
        return string.Join(" > ", parts);
    }

    /// <summary>User 엔티티 → UserDto 매핑 (Departments 캐시 활용).</summary>
    private static UserDto MapToDto(Models.User u, Dictionary<int, (string Name, int? ParentId)> deptCache)
    {
        string? deptName = null;
        if (u.DepartmentId != null && deptCache.TryGetValue(u.DepartmentId.Value, out var d))
            deptName = d.Name;

#pragma warning disable CS0618 // Department deprecated — 호환 위해 일시 유지
        return new UserDto
        {
            UserId = u.UserId,
            Email = u.Email,
            FullName = u.FullName,
            PhoneNumber = u.PhoneNumber,
            Department = u.Department,
            DepartmentId = u.DepartmentId,
            DepartmentName = deptName,
            DepartmentPath = BuildDepartmentPath(u.DepartmentId, deptCache),
            OrganizationId = u.OrganizationId,
            Language = u.Language,
            Bio = u.Bio,
            ProfileImageUrl = u.ProfileImageUrl,
            Status = u.Status,
            Roles = u.UserRoles.Select(ur => ur.Role.RoleName).ToList(),
            LastLoginAt = u.LastLoginAt,
            CreatedAt = u.CreatedAt
        };
#pragma warning restore CS0618
    }

    public async Task<UserDto> CreateUserAsync(CreateUserRequestDto request)
    {
        var user = new Models.User
        {
            Email = request.Email,
            PasswordHash = BCrypt.Net.BCrypt.HashPassword(request.Password),
            FullName = request.FullName,
            PhoneNumber = request.PhoneNumber,
            Department = request.Department,
            Status = request.Status ?? "Pending",
            IsEmailVerified = false,
            IsDeleted = false,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };

        _context.Users.Add(user);
        await _context.SaveChangesAsync();

        // Assign roles
        if (request.RoleIds != null && request.RoleIds.Any())
        {
            foreach (var roleId in request.RoleIds)
            {
                _context.UserRoles.Add(new Models.UserRole
                {
                    UserId = user.UserId,
                    RoleId = roleId,
                    AssignedAt = DateTime.UtcNow
                });
            }
            await _context.SaveChangesAsync();
        }

        return await GetUserByIdAsync(user.UserId) ?? throw new InvalidOperationException("Failed to create user");
    }

    public async Task<UserDto?> UpdateUserAsync(int userId, UpdateUserRequestDto request)
    {
        var user = await _context.Users
            .Include(u => u.UserRoles)
            .FirstOrDefaultAsync(u => u.UserId == userId && !u.IsDeleted);

        if (user == null) return null;

        user.FullName = request.FullName ?? user.FullName;
        user.PhoneNumber = request.PhoneNumber ?? user.PhoneNumber;
        user.Department = request.Department ?? user.Department;
        user.Bio = request.Bio ?? user.Bio;
        user.Status = request.Status ?? user.Status;
        user.UpdatedAt = DateTime.UtcNow;

        if (!string.IsNullOrEmpty(request.Password))
        {
            // CurrentPassword가 있으면 현재 비밀번호 검증 (본인 비밀번호 변경 시)
            if (!string.IsNullOrEmpty(request.CurrentPassword))
            {
                if (!BCrypt.Net.BCrypt.Verify(request.CurrentPassword, user.PasswordHash))
                {
                    throw new UnauthorizedAccessException("현재 비밀번호가 일치하지 않습니다.");
                }
            }
            user.PasswordHash = BCrypt.Net.BCrypt.HashPassword(request.Password);
        }

        // Update roles
        if (request.RoleIds != null)
        {
            var existingRoles = user.UserRoles.ToList();
            _context.UserRoles.RemoveRange(existingRoles);

            foreach (var roleId in request.RoleIds)
            {
                _context.UserRoles.Add(new Models.UserRole
                {
                    UserId = user.UserId,
                    RoleId = roleId,
                    AssignedAt = DateTime.UtcNow
                });
            }
        }

        await _context.SaveChangesAsync();
        return await GetUserByIdAsync(userId);
    }

    public async Task<bool> DeleteUserAsync(int userId)
    {
        var user = await _context.Users.FindAsync(userId);
        if (user == null) return false;

        user.IsDeleted = true;
        user.UpdatedAt = DateTime.UtcNow;
        await _context.SaveChangesAsync();

        return true;
    }

    public async Task<UserDto?> GetCurrentUserAsync(int userId)
    {
        return await GetUserByIdAsync(userId);
    }
}
