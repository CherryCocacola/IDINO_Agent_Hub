namespace AIAgentManagement.Services;

/// <summary>
/// 동일 AI 제공사에 여러 API 키를 등록하고 라운드로빈으로 순환하는 서비스.
///
/// 트랙 #91 (ApiKeyPoolService DB 통합) 이후 풀의 키 출처는 두 가지:
///   1. <c>appsettings.json</c> 의 <c>AiApiSettings:{Provider}:ApiKey(s)</c> — 회귀 차단용 폴백
///   2. DB 의 <c>ApiKeys</c> 테이블 중 <c>KeyType="Provider"</c> 행 — 운영자가 콘솔에서 등록한 키
///
/// 적재 시점:
///   - 부팅 직후 <c>app.Lifetime.ApplicationStarted</c> 에서 1회 즉시 실행
///   - Hangfire <c>*/5 * * * *</c> 주기 갱신
///   - 운영자 등록/수정/삭제 시 즉시 트리거 (<c>ApiKeyService.CreateProviderApiKeyAsync</c> 등)
///
/// appsettings.json 설정 예시 (다중 키):
/// <code>
/// "AiApiSettings": {
///   "OpenAI": { "ApiKeys": ["sk-key1", "sk-key2", "sk-key3"] }
/// }
/// </code>
/// </summary>
public interface IApiKeyPoolService
{
    /// <summary>
    /// 제공사 코드로 다음 API 키를 가져옵니다 (라운드로빈).
    /// 냉각 중인 키는 자동으로 건너뜁니다.
    /// </summary>
    /// <param name="provider">제공사 코드 (openai / claude / gemini / mistral / perplexity / azureopenai / copilot)</param>
    /// <returns>API 키 문자열. 등록된 키가 없으면 null.</returns>
    string? GetNextKey(string provider);

    /// <summary>
    /// 특정 키를 일정 시간 동안 냉각(사용 제외) 상태로 설정합니다.
    /// 429 Too Many Requests 응답을 받았을 때 호출합니다.
    /// </summary>
    /// <param name="provider">제공사 코드</param>
    /// <param name="apiKey">냉각할 API 키</param>
    /// <param name="cooldownSeconds">냉각 시간(초). 기본값 60초.</param>
    void MarkAsCoolingDown(string provider, string apiKey, int cooldownSeconds = 60);

    /// <summary>
    /// 제공사별 등록된 키 개수를 반환합니다 (모니터링용 — 단순 카운트).
    /// </summary>
    IReadOnlyDictionary<string, int> GetPoolStats();

    /// <summary>
    /// DB 의 외부 LLM 키(`KeyType="Provider"`)와 appsettings 폴백을 합산하여 풀을 원자적으로 갱신한다.
    /// 트랙 #91 — Hangfire 5분 주기 + 부팅 직후 1회 + 운영자 등록 직후 즉시 트리거에서 호출.
    /// 만료/비활성 키는 자동 제외. AES-GCM 복호화 실패 시 해당 키만 skip 하고 다른 키는 계속 적재.
    /// </summary>
    Task RefreshAsync(CancellationToken ct = default);

    /// <summary>
    /// 제공사별 상세 통계 (appsettings/DB 출처 분리 + 냉각 카운트) — 운영자 콘솔 풀 통계 카드용.
    /// </summary>
    IReadOnlyDictionary<string, PoolStatEntry> GetPoolStatsWithSource();
}

/// <summary>
/// 풀 통계 1건 — 트랙 #91.
/// </summary>
/// <param name="TotalCount">제공사 풀의 총 키 개수.</param>
/// <param name="FromAppsettings">appsettings.json 로부터 적재된 키 개수.</param>
/// <param name="FromDb">DB(`KeyType="Provider"`)에서 적재된 키 개수.</param>
/// <param name="CoolingDownCount">현재 냉각 상태인 키 개수.</param>
public sealed record PoolStatEntry(
    int TotalCount,
    int FromAppsettings,
    int FromDb,
    int CoolingDownCount);
