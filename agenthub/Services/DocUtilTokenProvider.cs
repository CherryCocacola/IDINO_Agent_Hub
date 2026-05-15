using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using AIAgentManagement.Exceptions;

namespace AIAgentManagement.Services;

/// <summary>
/// IDocUtilTokenProvider 의 표준 구현체.
/// <para>
/// 다음 시나리오를 모두 대응:
///   - 시연용 수동 JWT 주입(JwtToken) — 만료 30분 짜리. 만료 5분 전부터 자동 갱신
///   - ServiceAccount(ServiceUsername/ServicePassword) — refresh_token 또는 재로그인
///   - 영구 ApiKey — refresh 무관, 그대로 사용
/// </para>
/// <para>
/// 동시 갱신은 SemaphoreSlim 으로 직렬화하여 중복 로그인을 방지한다.
/// </para>
/// </summary>
public sealed class DocUtilTokenProvider : IDocUtilTokenProvider
{
    private readonly IConfiguration _configuration;
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<DocUtilTokenProvider> _logger;
    private readonly SemaphoreSlim _refreshLock = new(1, 1);

    private string? _cachedAccessToken;
    private string? _cachedRefreshToken;
    private DateTimeOffset _expiresAt = DateTimeOffset.MinValue;

    private static readonly TimeSpan RefreshSkew = TimeSpan.FromMinutes(5);

    public DocUtilTokenProvider(
        IConfiguration configuration,
        IHttpClientFactory httpClientFactory,
        ILogger<DocUtilTokenProvider> logger)
    {
        _configuration = configuration;
        _httpClientFactory = httpClientFactory;
        _logger = logger;
    }

    public async Task<string?> GetTokenAsync(CancellationToken cancellationToken = default)
    {
        // (캐시 hit) 만료 5분 전이면 그대로 반환
        if (!string.IsNullOrEmpty(_cachedAccessToken)
            && DateTimeOffset.UtcNow.Add(RefreshSkew) < _expiresAt)
        {
            return _cachedAccessToken;
        }

        // 5) ApiKey 우선순위 — refresh 무관, 영구 키
        var apiKey = _configuration["DocUtil:ApiKey"];
        if (!string.IsNullOrWhiteSpace(apiKey))
        {
            return apiKey;
        }

        await _refreshLock.WaitAsync(cancellationToken);
        try
        {
            // 락 획득 후 다시 캐시 확인 (다른 thread 가 갱신했을 수 있음)
            if (!string.IsNullOrEmpty(_cachedAccessToken)
                && DateTimeOffset.UtcNow.Add(RefreshSkew) < _expiresAt)
            {
                return _cachedAccessToken;
            }

            // 2) appsettings:DocUtil:JwtToken — 만료 임박 시점마다 매번 재평가한다.
            //
            //    Phase 10.x Task #9 회귀 수정 (2026-05-15):
            //      이전 구현은 `if (string.IsNullOrEmpty(_cachedAccessToken))` 가드 안에서만
            //      manualJwt 를 읽었다. 결과적으로 한 번 캐시가 적재되면 manual 토큰을 다시
            //      읽지 않아, 운영자가 .env 에 새 JwtToken 을 갱신해도 35시간 후(JWT exp
            //      도래) refresh / ServiceAccount 폴백이 모두 실패할 때 stale 토큰을
            //      그대로 반환하던 문제가 있었다 (DocUtil 측 502 회귀의 직접 원인).
            //
            //    수정: 캐시 만료 임박(RefreshSkew 5분) 으로 본 분기에 진입한 모든 경우에
            //          .env 의 최신 JwtToken 을 재평가한다. 같은 토큰이라도 idempotent
            //          이며, 새 토큰이라면 즉시 반영된다.
            var manualJwt = _configuration["DocUtil:JwtToken"];
            if (!string.IsNullOrWhiteSpace(manualJwt))
            {
                var manualExp = TryDecodeJwtExp(manualJwt);
                if (manualExp > DateTimeOffset.UtcNow.Add(RefreshSkew))
                {
                    // 기존 캐시 값과 다르면 갱신, 같으면 idempotent 재적재.
                    var isReload = !string.Equals(_cachedAccessToken, manualJwt, StringComparison.Ordinal);
                    _cachedAccessToken = manualJwt;
                    _expiresAt = manualExp;
                    if (isReload)
                    {
                        _logger.LogInformation(
                            "DocUtil 토큰 - appsettings:JwtToken 재로드 (남은 {Min}분) — 환경변수 갱신 반영",
                            (int)(manualExp - DateTimeOffset.UtcNow).TotalMinutes);
                    }
                    else
                    {
                        _logger.LogDebug(
                            "DocUtil 토큰 - appsettings:JwtToken 적재 (남은 {Min}분)",
                            (int)(manualExp - DateTimeOffset.UtcNow).TotalMinutes);
                    }
                    return _cachedAccessToken;
                }
                _logger.LogWarning("DocUtil:JwtToken 만료 또는 임박 — refresh_token / ServiceAccount 폴백");
            }

            // 3) refresh_token 으로 갱신 시도
            if (!string.IsNullOrWhiteSpace(_cachedRefreshToken))
            {
                var refreshed = await TryRefreshAsync(_cachedRefreshToken, cancellationToken);
                if (refreshed != null)
                {
                    _cachedAccessToken = refreshed.AccessToken;
                    _expiresAt = TryDecodeJwtExp(refreshed.AccessToken);
                    _logger.LogInformation("DocUtil 토큰 - refresh PASS (남은 {Min}분)",
                        (int)(_expiresAt - DateTimeOffset.UtcNow).TotalMinutes);
                    return _cachedAccessToken;
                }
                _logger.LogWarning("DocUtil 토큰 - refresh 실패 → ServiceAccount 폴백");
            }

            // 4) ServiceAccount 로 재로그인
            var username = _configuration["DocUtil:ServiceUsername"];
            var password = _configuration["DocUtil:ServicePassword"];
            var hasServiceCredential = !string.IsNullOrWhiteSpace(username)
                                       && !string.IsNullOrWhiteSpace(password);
            var loginRejectedByDocUtil = false; // 401/403 응답 식별용
            if (hasServiceCredential)
            {
                var login = await TryLoginAsync(username!, password!, cancellationToken);
                if (login != null)
                {
                    _cachedAccessToken = login.AccessToken;
                    _cachedRefreshToken = login.RefreshToken;
                    _expiresAt = TryDecodeJwtExp(login.AccessToken);
                    _logger.LogInformation("DocUtil 토큰 - login PASS (사용자={User}, 남은 {Min}분)",
                        username, (int)(_expiresAt - DateTimeOffset.UtcNow).TotalMinutes);
                    return _cachedAccessToken;
                }
                // null 반환은 1) 자격 거절(401/403) 2) 네트워크 장애 모두 포함하나,
                // 보수적으로 "자격 거절" 가능성을 가정하여 운영자에게 분명한 신호를 보낸다.
                loginRejectedByDocUtil = true;
            }

            // Phase 10.x Task #9 회귀 수정 (2026-05-15):
            //   이전 구현은 갱신 모든 경로 실패 시 stale 캐시 토큰을 그대로 반환했다.
            //   이렇게 되면 DocUtilClient 가 stale 토큰으로 HTTP 호출 → 401 5회 →
            //   Polly Circuit Breaker OPEN(30s) → half-open → 401 → 재차단 사이클이
            //   30초마다 반복되어 사용자에게 502 가 고착되었다.
            //
            //   수정: 폴백 모두 실패 시 stale 캐시를 반환하지 않고 즉시 한국어
            //         DocUtilUpstreamException 을 던진다. ErrorCode 를 두 카테고리로
            //         분류하여 운영자가 진단을 좁힐 수 있게 한다.
            //     - 자격 자체가 비어있음 → DOCUTIL_TOKEN_MISSING (운영자: .env 확인 필요)
            //     - 자격이 있었으나 거절됨 → DOCUTIL_TOKEN_FORBIDDEN (운영자: 비밀번호 회전 / 계정 잠금 의심)
            //
            //   본 예외는 DocUtil 측 HTTP 호출 자체를 시도하지 않으므로 Polly CB 카운터를
            //   증가시키지 않는다 → 운영자가 ServiceAccount 자격을 정상화하면 즉시 회복.
            if (loginRejectedByDocUtil)
            {
                _logger.LogError(
                    "DocUtil 토큰 — ServiceAccount 로그인 거절(401/403 유력). 비밀번호 회전 또는 계정 잠금 의심.");
                throw new DocUtilUpstreamException(
                    HttpStatusCode.Forbidden,
                    "/api/v1/auth/login",
                    DocUtilUpstreamException.ErrorCodes.TokenForbidden,
                    "DocUtil 운영자 자격이 거절되었습니다. ServiceAccount 비밀번호 회전 또는 계정 잠금 상태를 확인하세요.");
            }

            _logger.LogError(
                "DocUtil 토큰 미설정 — JwtToken / refresh_token / ServiceAccount / ApiKey 모두 비어있음");
            throw new DocUtilUpstreamException(
                HttpStatusCode.ServiceUnavailable,
                "(token-provider)",
                DocUtilUpstreamException.ErrorCodes.TokenMissing,
                "DocUtil 인증 정보가 비어 있습니다. JwtToken / ServiceUsername+Password / ApiKey 중 하나를 설정하세요.");
        }
        finally
        {
            _refreshLock.Release();
        }
    }

    private async Task<TokenResponse?> TryRefreshAsync(string refreshToken, CancellationToken ct)
    {
        try
        {
            var client = _httpClientFactory.CreateClient("docutil");
            var resp = await client.PostAsJsonAsync(
                "/api/v1/auth/refresh",
                new { refresh_token = refreshToken },
                ct);
            if (!resp.IsSuccessStatusCode)
            {
                _logger.LogDebug("DocUtil refresh HTTP {Status}", (int)resp.StatusCode);
                return null;
            }
            return await resp.Content.ReadFromJsonAsync<TokenResponse>(JsonOpts, ct);
        }
        catch (Exception ex)
        {
            _logger.LogDebug(ex, "DocUtil refresh 예외");
            return null;
        }
    }

    private async Task<TokenResponse?> TryLoginAsync(string username, string password, CancellationToken ct)
    {
        try
        {
            var client = _httpClientFactory.CreateClient("docutil");
            var resp = await client.PostAsJsonAsync(
                "/api/v1/auth/login",
                new { username, password },
                ct);
            if (!resp.IsSuccessStatusCode)
            {
                _logger.LogWarning("DocUtil login HTTP {Status} — ServiceAccount 자격 확인 필요", (int)resp.StatusCode);
                return null;
            }
            return await resp.Content.ReadFromJsonAsync<TokenResponse>(JsonOpts, ct);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "DocUtil login 예외");
            return null;
        }
    }

    /// <summary>
    /// Phase 10.1a — 캐시된 운영자 토큰의 <c>org</c> claim 추출.
    /// <para>
    /// 호출 흐름: 매 BFF API 호출마다 GetTokenAsync (fast path: cache hit) 후
    /// 본 메서드가 캐시 토큰을 디코드하여 organization UUID 반환. JWT 만료/refresh 가
    /// 발생해도 _cachedAccessToken 이 항상 최신 상태라 일관 동작.
    /// </para>
    /// <para>
    /// 폴백 우선순위 (Phase 10.x 보강, 2026-05-11):
    ///   1. JWT 의 <c>org</c> claim    — 가장 정확(운영자 컨텍스트와 정확히 일치)
    ///   2. appsettings <c>DocUtil:DefaultOrganizationId</c> — ApiKey-only 모드(JWT 가
    ///      아님)에서 운영자 콘솔이 동작하도록 하는 명시적 폴백.
    ///   3. null — 호출자가 502 ErrorResponseDto 로 매핑하여 "DocUtil 운영자 자격 확인 필요" 안내.
    /// </para>
    /// </summary>
    public async Task<string?> GetOrganizationIdAsync(CancellationToken cancellationToken = default)
    {
        // 토큰이 캐시 적재되도록 먼저 GetTokenAsync 트리거 — fast path 는 캐시 hit.
        await GetTokenAsync(cancellationToken);

        var token = _cachedAccessToken;
        if (!string.IsNullOrEmpty(token))
        {
            var orgFromJwt = TryDecodeJwtClaim(token, "org");
            if (!string.IsNullOrWhiteSpace(orgFromJwt))
            {
                return orgFromJwt;
            }
        }

        // 폴백 — ApiKey-only 모드 또는 JWT 에 org claim 미부착 시:
        // appsettings 의 DocUtil:DefaultOrganizationId 값 사용.
        // (배포 환경마다 하나의 운영 조직만 다루는 단순 시나리오에 적합)
        var defaultOrgId = _configuration["DocUtil:DefaultOrganizationId"];
        if (!string.IsNullOrWhiteSpace(defaultOrgId))
        {
            _logger.LogDebug(
                "DocUtil org_id — JWT claim 미부착 → DocUtil:DefaultOrganizationId 폴백 사용");
            return defaultOrgId;
        }

        return null;
    }

    /// <summary>
    /// JWT payload 에서 단일 string claim 추출. 디코드/파싱 실패 시 null.
    /// 본 메서드는 ApiKey(JWT 가 아닌 영구 키) 입력 시에도 안전하게 null 을 반환한다(parts.Length &lt; 2).
    /// </summary>
    private static string? TryDecodeJwtClaim(string jwt, string claimName)
    {
        try
        {
            var parts = jwt.Split('.');
            if (parts.Length < 2) return null;
            var payload = parts[1].Replace('-', '+').Replace('_', '/');
            payload += new string('=', (4 - payload.Length % 4) % 4);
            var bytes = Convert.FromBase64String(payload);
            using var doc = JsonDocument.Parse(bytes);
            if (doc.RootElement.TryGetProperty(claimName, out var el)
                && el.ValueKind == JsonValueKind.String)
            {
                return el.GetString();
            }
        }
        catch
        {
            // JWT decode 실패 시 null — 호출자가 502 매핑.
        }
        return null;
    }

    private static DateTimeOffset TryDecodeJwtExp(string jwt)
    {
        try
        {
            var parts = jwt.Split('.');
            if (parts.Length < 2) return DateTimeOffset.MinValue;
            var payload = parts[1].Replace('-', '+').Replace('_', '/');
            payload += new string('=', (4 - payload.Length % 4) % 4);
            var bytes = Convert.FromBase64String(payload);
            using var doc = JsonDocument.Parse(bytes);
            if (doc.RootElement.TryGetProperty("exp", out var expEl)
                && expEl.TryGetInt64(out var exp))
            {
                return DateTimeOffset.FromUnixTimeSeconds(exp);
            }
        }
        catch
        {
            // JWT decode 실패 시 만료된 것으로 처리 → 갱신 흐름 진입
        }
        return DateTimeOffset.MinValue;
    }

    private static readonly JsonSerializerOptions JsonOpts = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    private sealed class TokenResponse
    {
        [JsonPropertyName("access_token")] public string AccessToken { get; set; } = string.Empty;
        [JsonPropertyName("refresh_token")] public string? RefreshToken { get; set; }
        [JsonPropertyName("token_type")] public string? TokenType { get; set; }
    }
}
