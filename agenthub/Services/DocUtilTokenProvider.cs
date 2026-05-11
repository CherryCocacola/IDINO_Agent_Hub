using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;

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

            // 2) appsettings:DocUtil:JwtToken — 캐시 미적재 상태에서만 적용
            //    (한 번 적재되면 자동 갱신 흐름으로 넘어가서 stale 한 manual 토큰을 다시 읽지 않음)
            if (string.IsNullOrEmpty(_cachedAccessToken))
            {
                var manualJwt = _configuration["DocUtil:JwtToken"];
                if (!string.IsNullOrWhiteSpace(manualJwt))
                {
                    var manualExp = TryDecodeJwtExp(manualJwt);
                    if (manualExp > DateTimeOffset.UtcNow.Add(RefreshSkew))
                    {
                        _cachedAccessToken = manualJwt;
                        _expiresAt = manualExp;
                        _logger.LogInformation("DocUtil 토큰 - appsettings:JwtToken 적재 (남은 {Min}분)",
                            (int)(manualExp - DateTimeOffset.UtcNow).TotalMinutes);
                        return _cachedAccessToken;
                    }
                    _logger.LogWarning("DocUtil:JwtToken 만료 또는 임박 — refresh_token / ServiceAccount 폴백");
                }
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
            if (!string.IsNullOrWhiteSpace(username) && !string.IsNullOrWhiteSpace(password))
            {
                var login = await TryLoginAsync(username, password, cancellationToken);
                if (login != null)
                {
                    _cachedAccessToken = login.AccessToken;
                    _cachedRefreshToken = login.RefreshToken;
                    _expiresAt = TryDecodeJwtExp(login.AccessToken);
                    _logger.LogInformation("DocUtil 토큰 - login PASS (사용자={User}, 남은 {Min}분)",
                        username, (int)(_expiresAt - DateTimeOffset.UtcNow).TotalMinutes);
                    return _cachedAccessToken;
                }
            }

            // 모두 실패 시: 캐시 유지 (이미 만료된 토큰을 반환하더라도 호출자가 401 받고
            // 다음 호출 때 재시도 — 본 메서드를 호출하는 DocUtilClient.EnsureSuccessOrThrow 가
            // 한국어 메시지로 안내). 캐시 자체가 비었으면 null 반환.
            if (!string.IsNullOrEmpty(_cachedAccessToken))
            {
                _logger.LogWarning("DocUtil 토큰 갱신 모든 경로 실패 — 만료된 캐시 토큰 반환");
                return _cachedAccessToken;
            }
            _logger.LogWarning("DocUtil 토큰 미설정 — JwtToken / refresh_token / ServiceAccount / ApiKey 모두 비어있음");
            return null;
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
