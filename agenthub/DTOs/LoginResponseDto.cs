namespace AIAgentManagement.DTOs;

/// <summary>
/// 로그인 성공 응답.
/// 트랙 #89 C2 — TokenExpiresAt / RefreshTokenExpiresAt 추가:
/// 클라이언트가 만료 5분 전 사전 갱신을 수행할 수 있도록 만료 시점을 명시 전달.
/// 모든 시각은 UTC ISO-8601 (DateTimeOffset 직렬화).
/// </summary>
public class LoginResponseDto
{
    public string Token { get; set; } = string.Empty;
    public string RefreshToken { get; set; } = string.Empty;

    /// <summary>
    /// JWT (access token) 만료 시각 — UTC.
    /// JwtSettings:ExpirationInMinutes (default 60분) 후.
    /// </summary>
    public DateTimeOffset TokenExpiresAt { get; set; }

    /// <summary>
    /// Refresh token (UserSession) 만료 시각 — UTC.
    /// JwtSettings:RefreshTokenExpirationInDays (default 7일) 후.
    /// </summary>
    public DateTimeOffset RefreshTokenExpiresAt { get; set; }

    public UserDto User { get; set; } = null!;
}
