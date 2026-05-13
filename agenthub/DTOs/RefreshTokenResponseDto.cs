namespace AIAgentManagement.DTOs;

/// <summary>
/// Refresh token 갱신 응답.
/// 트랙 #89 C2 — Refresh token 회전(rotation) 정책 적용:
/// 1) 새 access token(Token) 발급
/// 2) 새 refresh token(RefreshToken) 발급, 기존 UserSession 은 비활성화
/// 3) 클라이언트가 다음 갱신 시점을 알 수 있도록 두 만료 시각을 명시
/// </summary>
public class RefreshTokenResponseDto
{
    public string Token { get; set; } = string.Empty;

    /// <summary>
    /// 회전된 신규 refresh token. 클라이언트는 이 값으로 기존 refresh token 을 교체 저장한다.
    /// </summary>
    public string RefreshToken { get; set; } = string.Empty;

    /// <summary>
    /// JWT (access token) 만료 시각 — UTC.
    /// </summary>
    public DateTimeOffset TokenExpiresAt { get; set; }

    /// <summary>
    /// Refresh token (UserSession) 만료 시각 — UTC.
    /// </summary>
    public DateTimeOffset RefreshTokenExpiresAt { get; set; }
}
