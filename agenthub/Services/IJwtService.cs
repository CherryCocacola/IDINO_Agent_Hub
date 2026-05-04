using System.Security.Claims;

namespace AIAgentManagement.Services;

public interface IJwtService
{
    string GenerateToken(int userId, string email, IList<string> roles);
    ClaimsPrincipal? ValidateToken(string token);
    string GenerateRefreshToken();
}
