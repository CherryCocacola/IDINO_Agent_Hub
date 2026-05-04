using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IAuthService
{
    Task<LoginResponseDto?> LoginAsync(LoginRequestDto request);
    Task<bool> RegisterAsync(RegisterRequestDto request);
    Task<bool> LogoutAsync(string token);
    Task<RefreshTokenResponseDto?> RefreshTokenAsync(string refreshToken);
    Task<bool> ForgotPasswordAsync(ForgotPasswordRequestDto request, string baseUrl);
    Task<bool> ResetPasswordAsync(ResetPasswordRequestDto request);
}
