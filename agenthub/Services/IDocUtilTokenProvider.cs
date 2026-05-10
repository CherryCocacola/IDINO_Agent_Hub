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

    /// <summary>
    /// 현재 캐시된 DocUtil 운영자 토큰의 <c>org</c> claim(organization UUID)을 반환한다.
    /// <para>
    /// Phase 10.1a 사용 컨텍스트:
    ///   DocUtil <c>GET /api/v1/users</c> 는 <c>org_id</c> 쿼리 파라미터가 필수다(422).
    ///   AgentHub BFF 는 매 호출마다 운영자 토큰의 <c>org</c> 를 추출하여 자동으로 부착한다.
    ///   호출자(Controller)가 org 를 직접 다루지 않게 하여 표면을 단순화한다.
    /// </para>
    /// <para>
    /// 동작:
    ///   - GetTokenAsync 가 먼저 호출되어 토큰이 캐시 적재된 상태여야 정상 동작.
    ///   - 미적재/디코드 실패 시 null 반환(호출자는 502 로 매핑하거나 명시 로그).
    ///   - ApiKey 만 설정된 경우(JWT 가 아닌 영구 키) 도 null 반환 — 이 경우 호출자가
    ///     <c>DocUtil:DefaultOrganizationId</c> 설정값을 사용하도록 안내(향후 트랙).
    /// </para>
    /// </summary>
    Task<string?> GetOrganizationIdAsync(CancellationToken cancellationToken = default);
}
