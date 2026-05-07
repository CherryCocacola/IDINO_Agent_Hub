namespace AIAgentManagement.Services;

/// <summary>
/// DocUtil 운영자 인증 토큰을 캐시 + 자동 갱신하는 단일 진입점.
/// <para>
/// 우선순위:
///   1) 메모리 캐시(만료 5분 전이면 그대로 사용)
///   2) appsettings:DocUtil:JwtToken (만료 검증 후 캐시 적재)
///   3) refresh_token + POST /api/v1/auth/refresh (있을 때만)
///   4) DocUtil:ServiceUsername / ServicePassword + POST /api/v1/auth/login
///   5) DocUtil:ApiKey (영구 키 — Bearer 로 그대로 부착)
/// </para>
/// </summary>
public interface IDocUtilTokenProvider
{
    /// <summary>
    /// DocUtil API 호출에 부착할 Bearer 토큰을 반환한다.
    /// 만료 임박 시 자동 갱신, 실패 시 InvalidOperationException(한국어 메시지).
    /// </summary>
    Task<string?> GetTokenAsync(CancellationToken cancellationToken = default);
}
