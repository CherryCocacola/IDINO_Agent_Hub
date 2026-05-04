using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IUserService
{
    Task<List<UserDto>> GetUsersAsync(string? search = null, string? role = null, string? status = null);
    Task<UserDto?> GetUserByIdAsync(int userId);
    Task<UserDto> CreateUserAsync(CreateUserRequestDto request);
    Task<UserDto?> UpdateUserAsync(int userId, UpdateUserRequestDto request);
    Task<bool> DeleteUserAsync(int userId);
    Task<UserDto?> GetCurrentUserAsync(int userId);
}
