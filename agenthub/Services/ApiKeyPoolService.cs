using System.Collections.Concurrent;
using AIAgentManagement.Data;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

/// <summary>
/// IApiKeyPoolService 구현체.
/// Singleton 으로 등록되어 애플리케이션 전체에서 상태를 공유합니다.
///
/// ── 동작 방식 (트랙 #91 — DB 통합 후) ─────────────────────────────────
/// 1. 부팅 시 생성자에서 <c>appsettings.json</c> 만 로드 (회귀 차단용 즉시 가용).
///    DB 는 부팅 직후 <c>app.Lifetime.ApplicationStarted</c> 가 `RefreshAsync` 1회 즉시 호출 → 비동기 적재.
/// 2. 이후 Hangfire <c>*/5 * * * *</c> 주기로 `RefreshAsync()` → DB+appsettings 합산 후 풀 원자적 교체.
/// 3. 운영자 등록/수정/삭제 시점에 `ApiKeyService` 가 즉시 `RefreshAsync()` 트리거.
/// 4. <c>GetNextKey()</c> 호출마다 인덱스를 하나씩 전진 (라운드로빈).
/// 5. 429 응답 시 <c>MarkAsCoolingDown()</c> → 해당 키를 X초간 제외.
/// 6. 모든 키가 냉각 중이면 가장 빨리 복귀하는 키 임시 사용 (서비스 중단 방지).
///
/// ── DI Lifetime 격리 (P4 / anti-pattern #7) ────────────────────────
/// 본 서비스는 Singleton 이지만 DB 접근이 필요하므로 <c>IServiceScopeFactory</c> 를 주입받아
/// `RefreshAsync()` 안에서만 Scoped 스코프(=`AIAgentManagementDbContext`)를 생성한다.
/// captive dependency 회피 — Scoped DbContext 를 Singleton 에 직접 주입하지 않는다.
/// </summary>
public class ApiKeyPoolService : IApiKeyPoolService
{
    private readonly ConcurrentDictionary<string, ProviderKeyPool> _pools;
    private readonly IServiceScopeFactory _scopeFactory;
    private readonly IConfiguration _configuration;
    private readonly ILogger<ApiKeyPoolService> _logger;

    // 지원 제공사: (서비스 코드, appsettings 섹션명) 쌍
    private static readonly (string Code, string Section)[] Providers =
    {
        ("openai",      "OpenAI"),
        ("claude",      "Claude"),
        ("gemini",      "Gemini"),
        ("mistral",     "Mistral"),
        ("perplexity",  "Perplexity"),
        ("azureopenai", "AzureOpenAI"),
        ("copilot",     "Copilot"),
    };

    public ApiKeyPoolService(
        IServiceScopeFactory scopeFactory,
        IConfiguration configuration,
        ILogger<ApiKeyPoolService> logger)
    {
        _scopeFactory = scopeFactory;
        _configuration = configuration;
        _logger = logger;
        _pools = new ConcurrentDictionary<string, ProviderKeyPool>(StringComparer.OrdinalIgnoreCase);

        // 부팅 즉시 가용: appsettings 만 먼저 적재 (회귀 차단). DB 는 ApplicationStarted 에서 비동기 로드.
        LoadFromConfiguration();
    }

    // ── 공개 API ─────────────────────────────────────────────────────────────

    public string? GetNextKey(string provider)
    {
        if (_pools.TryGetValue(provider, out var pool))
            return pool.GetNext();

        return null;
    }

    public void MarkAsCoolingDown(string provider, string apiKey, int cooldownSeconds = 60)
    {
        if (!_pools.TryGetValue(provider, out var pool)) return;

        pool.SetCooldown(apiKey, TimeSpan.FromSeconds(cooldownSeconds));
        _logger.LogWarning(
            "[ApiKeyPool] {Provider} 키 냉각 시작. {Seconds}초 후 복귀. Key=...{Suffix}",
            provider, cooldownSeconds, apiKey.Length > 8 ? apiKey[^8..] : "****");
    }

    public IReadOnlyDictionary<string, int> GetPoolStats()
    {
        return _pools.ToDictionary(
            p => p.Key,
            p => p.Value.TotalCount,
            StringComparer.OrdinalIgnoreCase);
    }

    public IReadOnlyDictionary<string, PoolStatEntry> GetPoolStatsWithSource()
    {
        return _pools.ToDictionary(
            p => p.Key,
            p => p.Value.GetSnapshot(),
            StringComparer.OrdinalIgnoreCase);
    }

    /// <summary>
    /// 트랙 #91 — DB(`KeyType="Provider"`) + appsettings 폴백을 합산하여 풀을 원자적으로 교체한다.
    /// 1. appsettings 항상 시드 (회귀 차단)
    /// 2. DB 에서 활성 Provider 키 조회 → AES-GCM 복호화 → ServiceCode 정규화 → 슬롯 매핑
    /// 3. 신규 ProviderKeyPool 인스턴스 생성 → `_pools[provider] = new ...` 한 줄로 교체 (lock-free)
    /// </summary>
    public async Task RefreshAsync(CancellationToken ct = default)
    {
        // 1) appsettings 베이스(provider → 키 리스트) — 회귀 차단 폴백.
        var appsettingsKeys = new Dictionary<string, List<string>>(StringComparer.OrdinalIgnoreCase);
        foreach (var (code, section) in Providers)
        {
            var keys = LoadKeys(_configuration, section);
            appsettingsKeys[code] = keys;
        }

        // 2) DB Provider 키 적재 — Scoped DbContext 를 명시 스코프로 생성 (anti-pattern #7).
        var dbKeysByProvider = new Dictionary<string, List<string>>(StringComparer.OrdinalIgnoreCase);
        var dbLoadFailures = 0;

        try
        {
            using var scope = _scopeFactory.CreateScope();
            var db = scope.ServiceProvider.GetRequiredService<AIAgentManagementDbContext>();
            var apiKeyService = scope.ServiceProvider.GetRequiredService<IApiKeyService>();

            // KeyType="Provider" + 활성 + 만료 안 됨.
            // ApiKeyService.DecryptForPoolAsync 가 LastUsedAt/UsageCount 를 갱신하지 않는 변종이므로
            // 5분 주기 풀 갱신이 사용량 카운터를 오염시키지 않는다.
            var now = DateTime.UtcNow;
            var rows = await db.ApiKeys
                .AsNoTracking()
                .Where(k => k.KeyType == "Provider"
                            && k.IsActive
                            && (k.ExpiresAt == null || k.ExpiresAt > now))
                .Select(k => new { k.ApiKeyId, k.ServiceCode })
                .ToListAsync(ct);

            foreach (var row in rows)
            {
                var provider = NormalizeServiceCode(row.ServiceCode);
                if (provider is null)
                {
                    _logger.LogWarning(
                        "[ApiKeyPool] 지원하지 않는 ServiceCode 로 등록된 Provider 키 skip. ApiKeyId={ApiKeyId}, ServiceCode={ServiceCode}",
                        row.ApiKeyId, row.ServiceCode);
                    continue;
                }

                // 복호화 실패 시 해당 키만 skip — 다른 키 적재 흐름은 보존.
                string? plaintext;
                try
                {
                    plaintext = await apiKeyService.DecryptForPoolAsync(row.ApiKeyId);
                }
                catch (InvalidOperationException ex)
                {
                    _logger.LogError(ex,
                        "[ApiKeyPool] Provider 키 복호화 실패 — skip. ApiKeyId={ApiKeyId}, Provider={Provider}",
                        row.ApiKeyId, provider);
                    dbLoadFailures++;
                    continue;
                }

                if (string.IsNullOrWhiteSpace(plaintext))
                {
                    _logger.LogWarning(
                        "[ApiKeyPool] Provider 키 평문 비어 있음 — skip. ApiKeyId={ApiKeyId}, Provider={Provider}",
                        row.ApiKeyId, provider);
                    dbLoadFailures++;
                    continue;
                }

                if (!dbKeysByProvider.TryGetValue(provider, out var bucket))
                {
                    bucket = new List<string>();
                    dbKeysByProvider[provider] = bucket;
                }
                bucket.Add(plaintext);
            }
        }
        catch (OperationCanceledException)
        {
            // CancellationToken 취소 — 정상 흐름이므로 그대로 전파.
            throw;
        }
        catch (Exception ex)
        {
            // DB 일시 장애 등 — 풀의 기존 상태(또는 appsettings 만) 유지. 죽지 않게 함.
            _logger.LogError(ex, "[ApiKeyPool] DB Provider 키 조회 실패 — appsettings 폴백 단독 적용.");
        }

        // 3) 풀 원자적 교체. provider 별 (appsettings + DB) 합본을 새 ProviderKeyPool 로 만들어 한 줄로 swap.
        var allProviders = new HashSet<string>(appsettingsKeys.Keys, StringComparer.OrdinalIgnoreCase);
        foreach (var k in dbKeysByProvider.Keys) allProviders.Add(k);

        foreach (var provider in allProviders)
        {
            var fromAppsettings = appsettingsKeys.TryGetValue(provider, out var aKeys) ? aKeys : new List<string>();
            var fromDb = dbKeysByProvider.TryGetValue(provider, out var dKeys) ? dKeys : new List<string>();

            if (fromAppsettings.Count == 0 && fromDb.Count == 0)
            {
                // 양쪽 다 비어 있으면 기존 풀 제거 — 키가 모두 사라진 상태 반영.
                _pools.TryRemove(provider, out _);
                continue;
            }

            var entries = new List<KeyEntry>(fromAppsettings.Count + fromDb.Count);
            foreach (var k in fromAppsettings) entries.Add(new KeyEntry(k, KeySource.Appsettings));
            foreach (var k in fromDb) entries.Add(new KeyEntry(k, KeySource.Db));

            _pools[provider] = new ProviderKeyPool(entries);
        }

        _logger.LogInformation(
            "[ApiKeyPool] DB 갱신 완료. {ProviderCount}개 제공사. DB 복호화 실패={Failures}.",
            allProviders.Count, dbLoadFailures);
    }

    // ── appsettings 적재 ─────────────────────────────────────────────────────

    /// <summary>
    /// 부팅 시 1회 — appsettings 만 풀에 적재. DB 적재는 <c>RefreshAsync</c> 에서 수행.
    /// </summary>
    private void LoadFromConfiguration()
    {
        foreach (var (code, section) in Providers)
        {
            var keys = LoadKeys(_configuration, section);
            if (keys.Count > 0)
            {
                var entries = keys.Select(k => new KeyEntry(k, KeySource.Appsettings)).ToList();
                _pools[code] = new ProviderKeyPool(entries);
                _logger.LogInformation(
                    "[ApiKeyPool] {Provider}: appsettings API 키 {Count}개 로드 완료", code, keys.Count);
            }
            else
            {
                _logger.LogDebug("[ApiKeyPool] {Provider}: appsettings 등록 키 없음", code);
            }
        }
    }

    /// <summary>
    /// appsettings.json 에서 API 키를 읽습니다.
    /// 우선순위: ApiKeys 배열 &gt; ApiKey 단일 값
    /// </summary>
    private static List<string> LoadKeys(IConfiguration config, string section)
    {
        var keys = new List<string>();

        // 다중 키: "AiApiSettings:OpenAI:ApiKeys": ["sk-1", "sk-2"]
        var arraySection = config.GetSection($"AiApiSettings:{section}:ApiKeys");
        if (arraySection.Exists())
        {
            keys.AddRange(
                arraySection.GetChildren()
                            .Select(c => c.Value ?? "")
                            .Where(v => !string.IsNullOrWhiteSpace(v)));
        }

        // 단일 키 폴백: "AiApiSettings:OpenAI:ApiKey": "sk-1"
        if (keys.Count == 0)
        {
            var single = config[$"AiApiSettings:{section}:ApiKey"];
            if (!string.IsNullOrWhiteSpace(single))
                keys.Add(single);
        }

        return keys;
    }

    // ── ServiceCode 정규화 ───────────────────────────────────────────────────

    /// <summary>
    /// DB <c>ApiKey.ServiceCode</c> 값을 풀 슬롯 코드로 정규화한다.
    /// <list type="bullet">
    /// <item><c>chatgpt</c> → <c>openai</c> (UI 호환 alias)</item>
    /// <item><c>gemini-image</c>/<c>imagen4</c> → <c>gemini</c> (동일 GEMINI_API_KEY 공유)</item>
    /// <item>지원 외 값 → <c>null</c> (skip)</item>
    /// </list>
    /// 표준 카탈로그는 <c>.claude/rules/domain-model.md</c> §"ServiceCode 표준 값" 참고.
    /// </summary>
    public static string? NormalizeServiceCode(string serviceCode)
    {
        if (string.IsNullOrWhiteSpace(serviceCode)) return null;

        return serviceCode.Trim().ToLowerInvariant() switch
        {
            "openai"        => "openai",
            "chatgpt"       => "openai",
            "claude"        => "claude",
            "gemini"        => "gemini",
            "google"        => "gemini",
            "gemini-image"  => "gemini",
            "imagen4"       => "gemini",
            "perplexity"    => "perplexity",
            "mistral"       => "mistral",
            "azureopenai"   => "azureopenai",
            "copilot"       => "copilot",
            _                => null
        };
    }

    // ── 내부: 키 출처 enum ───────────────────────────────────────────────────

    private enum KeySource
    {
        Appsettings,
        Db
    }

    // ── 내부 클래스: 제공사별 키 풀 ──────────────────────────────────────────

    private sealed class ProviderKeyPool
    {
        private readonly List<KeyEntry> _entries;
        private int _index = -1;
        private readonly object _lock = new();

        public int TotalCount => _entries.Count;

        public ProviderKeyPool(List<KeyEntry> entries)
        {
            _entries = entries;
        }

        /// <summary>사용 가능한 키 중에서 다음 키를 라운드로빈으로 반환합니다.</summary>
        public string GetNext()
        {
            lock (_lock)
            {
                var now = DateTime.UtcNow;
                // 냉각이 끝난 키 목록
                var available = _entries.Where(e => e.CooldownUntil <= now).ToList();

                if (available.Count == 0)
                {
                    // 전체 냉각 중: 가장 빨리 복귀하는 키 반환
                    return _entries.OrderBy(e => e.CooldownUntil).First().Key;
                }

                _index = (_index + 1) % available.Count;
                return available[_index].Key;
            }
        }

        /// <summary>특정 키를 냉각 상태로 설정합니다.</summary>
        public void SetCooldown(string key, TimeSpan duration)
        {
            lock (_lock)
            {
                var entry = _entries.FirstOrDefault(e => e.Key == key);
                if (entry != null)
                    entry.CooldownUntil = DateTime.UtcNow + duration;
            }
        }

        /// <summary>풀 통계 스냅샷 (appsettings/DB 출처 + 냉각 카운트).</summary>
        public PoolStatEntry GetSnapshot()
        {
            lock (_lock)
            {
                var now = DateTime.UtcNow;
                var fromAppsettings = _entries.Count(e => e.Source == KeySource.Appsettings);
                var fromDb = _entries.Count(e => e.Source == KeySource.Db);
                var cooling = _entries.Count(e => e.CooldownUntil > now);
                return new PoolStatEntry(_entries.Count, fromAppsettings, fromDb, cooling);
            }
        }
    }

    // 가변 상태를 가져야 하므로 record 가 아닌 class. 출처(Source) 컬럼은 풀 통계 분리용.
    private sealed class KeyEntry
    {
        public string Key { get; }
        public KeySource Source { get; }
        public DateTime CooldownUntil { get; set; } = DateTime.MinValue;

        public KeyEntry(string key, KeySource source)
        {
            Key = key;
            Source = source;
        }
    }
}
