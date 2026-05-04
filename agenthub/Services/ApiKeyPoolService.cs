using System.Collections.Concurrent;

namespace AIAgentManagement.Services;

/// <summary>
/// IApiKeyPoolService 구현체.
/// Singleton으로 등록되어 애플리케이션 전체에서 상태를 공유합니다.
///
/// ── 동작 방식 ──────────────────────────────────────────────────────
/// 1. 시작 시 appsettings.json에서 제공사별 API 키 목록을 읽어 풀 생성
/// 2. GetNextKey() 호출마다 인덱스를 하나씩 전진 (라운드로빈)
/// 3. 429 응답 시 MarkAsCoolingDown() → 해당 키를 X초간 제외
/// 4. 모든 키가 냉각 중이면 첫 번째 키를 임시 사용 (서비스 중단 방지)
/// ──────────────────────────────────────────────────────────────────
/// </summary>
public class ApiKeyPoolService : IApiKeyPoolService
{
    private readonly Dictionary<string, ProviderKeyPool> _pools;
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

    public ApiKeyPoolService(IConfiguration configuration, ILogger<ApiKeyPoolService> logger)
    {
        _logger = logger;
        _pools  = new Dictionary<string, ProviderKeyPool>(StringComparer.OrdinalIgnoreCase);

        foreach (var (code, section) in Providers)
        {
            var keys = LoadKeys(configuration, section);
            if (keys.Count > 0)
            {
                _pools[code] = new ProviderKeyPool(keys);
                _logger.LogInformation(
                    "[ApiKeyPool] {Provider}: API 키 {Count}개 로드 완료", code, keys.Count);
            }
            else
            {
                _logger.LogDebug("[ApiKeyPool] {Provider}: 등록된 API 키 없음", code);
            }
        }
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

    // ── 설정 로드 ─────────────────────────────────────────────────────────────

    /// <summary>
    /// appsettings.json에서 API 키를 읽습니다.
    /// 우선순위: ApiKeys 배열 > ApiKey 단일 값
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

    // ── 내부 클래스: 제공사별 키 풀 ──────────────────────────────────────────

    private sealed class ProviderKeyPool
    {
        private readonly List<KeyEntry> _entries;
        private int _index = -1;
        private readonly object _lock = new();

        public int TotalCount => _entries.Count;

        public ProviderKeyPool(List<string> keys)
        {
            _entries = keys.Select(k => new KeyEntry(k)).ToList();
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

        // 가변 상태를 가져야 하므로 record가 아닌 class 사용
        private sealed class KeyEntry
        {
            public string Key { get; }
            public DateTime CooldownUntil { get; set; } = DateTime.MinValue;

            public KeyEntry(string key) => Key = key;
        }
    }
}
