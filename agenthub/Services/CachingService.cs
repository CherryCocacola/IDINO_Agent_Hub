using Microsoft.Extensions.Caching.Distributed;
using System.Text.Json;

namespace AIAgentManagement.Services;

public class CachingService
{
    private readonly IDistributedCache _cache;
    private readonly ILogger<CachingService> _logger;

    public CachingService(IDistributedCache cache, ILogger<CachingService> logger)
    {
        _cache = cache;
        _logger = logger;
    }

    public async Task<T?> GetAsync<T>(string key) where T : class
    {
        try
        {
            var cached = await _cache.GetStringAsync(key);
            if (string.IsNullOrEmpty(cached))
            {
                return null;
            }

            return JsonSerializer.Deserialize<T>(cached);
        }
        catch (System.Net.Sockets.SocketException ex)
        {
            // Redis 연결 오류는 경고로 처리 (Redis가 없어도 정상 작동)
            _logger.LogWarning(ex, "Redis connection error when getting cache for key {Key}. Redis may be unavailable. Falling back to direct database query. Socket error: {SocketError}", 
                key, ex.SocketErrorCode);
            return null;
        }
        catch (StackExchange.Redis.RedisConnectionException ex)
        {
            // Redis 연결 예외는 경고로 처리 (Redis가 없어도 정상 작동)
            _logger.LogWarning(ex, "Redis connection exception when getting cache for key {Key}. Redis server may be down or unreachable. Falling back to direct database query.", key);
            return null;
        }
        catch (StackExchange.Redis.RedisTimeoutException ex)
        {
            // Redis 타임아웃은 경고로 처리 (Redis가 없어도 정상 작동)
            _logger.LogWarning(ex, "Redis timeout when getting cache for key {Key}. Redis server may be slow or overloaded. Falling back to direct database query.", key);
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting cache for key {Key}. Exception type: {ExceptionType}, Message: {Message}", 
                key, ex.GetType().Name, ex.Message);
            return null;
        }
    }

    public async Task SetAsync<T>(string key, T value, TimeSpan? expiration = null) where T : class
    {
        try
        {
            var options = new DistributedCacheEntryOptions();
            if (expiration.HasValue)
            {
                options.AbsoluteExpirationRelativeToNow = expiration;
            }
            else
            {
                options.AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(30);
            }

            var serialized = JsonSerializer.Serialize(value);
            
            // 직렬화된 데이터 크기 확인 (너무 크면 경고)
            var sizeInBytes = System.Text.Encoding.UTF8.GetByteCount(serialized);
            if (sizeInBytes > 1024 * 1024) // 1MB 이상
            {
                _logger.LogWarning("Cache value size is large: {Size} bytes for key {Key}", sizeInBytes, key);
            }
            
            await _cache.SetStringAsync(key, serialized, options);
            _logger.LogDebug("Cache set successfully for key {Key}, size: {Size} bytes", key, sizeInBytes);
        }
        catch (System.Net.Sockets.SocketException ex)
        {
            // Redis 연결 오류는 경고로 처리 (Redis가 없어도 정상 작동)
            _logger.LogWarning(ex, "Redis connection error when setting cache for key {Key}. Redis may be unavailable. Falling back to in-memory cache. Socket error: {SocketError}", 
                key, ex.SocketErrorCode);
        }
        catch (StackExchange.Redis.RedisConnectionException ex)
        {
            // Redis 연결 예외는 경고로 처리 (Redis가 없어도 정상 작동)
            _logger.LogWarning(ex, "Redis connection exception when setting cache for key {Key}. Redis server may be down or unreachable. Falling back to in-memory cache.", key);
        }
        catch (StackExchange.Redis.RedisTimeoutException ex)
        {
            // Redis 타임아웃은 경고로 처리 (Redis가 없어도 정상 작동)
            _logger.LogWarning(ex, "Redis timeout when setting cache for key {Key}. Redis server may be slow or overloaded. Falling back to in-memory cache.", key);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error setting cache for key {Key}. Exception type: {ExceptionType}, Message: {Message}", 
                key, 
                ex.GetType().Name, 
                ex.Message);
            
            // 내부 예외가 있으면 추가 로깅
            if (ex.InnerException != null)
            {
                _logger.LogError("Inner exception: {InnerType}, Message: {InnerMessage}", 
                    ex.InnerException.GetType().Name, 
                    ex.InnerException.Message);
            }
        }
    }

    public async Task RemoveAsync(string key)
    {
        try
        {
            await _cache.RemoveAsync(key);
        }
        catch (System.Net.Sockets.SocketException ex)
        {
            // Redis 연결 오류는 경고로 처리 (Redis가 없어도 정상 작동)
            _logger.LogWarning(ex, "Redis connection error when removing cache for key {Key}. Redis may be unavailable. Socket error: {SocketError}", 
                key, ex.SocketErrorCode);
        }
        catch (StackExchange.Redis.RedisConnectionException ex)
        {
            // Redis 연결 예외는 경고로 처리 (Redis가 없어도 정상 작동)
            _logger.LogWarning(ex, "Redis connection exception when removing cache for key {Key}. Redis server may be down or unreachable.", key);
        }
        catch (StackExchange.Redis.RedisTimeoutException ex)
        {
            // Redis 타임아웃은 경고로 처리 (Redis가 없어도 정상 작동)
            _logger.LogWarning(ex, "Redis timeout when removing cache for key {Key}. Redis server may be slow or overloaded.", key);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error removing cache for key {Key}. Exception type: {ExceptionType}, Message: {Message}", 
                key, ex.GetType().Name, ex.Message);
        }
    }

    public string GetQuotaKey(int userId, int serviceId) => $"quota:user:{userId}:service:{serviceId}";
    public string GetUserKey(int userId) => $"user:{userId}";
    public string GetStatsKey(string type) => $"stats:{type}";
    public string GetEmbeddingKey(string queryHash) => $"embedding:{queryHash}";
    public string GetRagResultKey(string queryHash, int? agentId, int? userId) => $"rag:{agentId}:{userId}:{queryHash}";

    // ════════════════════════════════════════════════════════════════════
    // 후속 트랙 — 캐시 버전 키(version-key namespacing) 패턴
    //
    // 목적:
    //   prefix iteration / SCAN / KEYS 비효율을 우회하면서 다수의 캐시 키를
    //   일괄 무효화한다. 호출자는 자신의 캐시 키에 현재 version 을 prefix 로
    //   포함하고(예: `du:s:v{N}:{hash}`), 무효화가 필요할 때 IncrementVersionAsync
    //   를 호출한다. 이전 version 의 키들은 자동으로 stale 처리되어 TTL 자연
    //   expire 또는 LRU eviction 으로 정리된다.
    //
    // 설계 선택:
    //   - IDistributedCache 만 사용(StackExchange.Redis 의 IConnectionMultiplexer
    //     를 별도 등록하지 않는 현재 패턴 보존). 결과적으로 INCR atomic 은
    //     불가능하나 단순한 Get→Increment→Set 으로도 무효화 효과는 동일
    //     (race condition 으로 두 INCR 가 같은 N+1 로 수렴해도 N 이하 키는 모두
    //     stale 처리됨 — 캐시 무효화의 본질은 보존됨).
    //   - 키 prefix 는 `cv:` (cache-version) — 다른 도메인 키와 충돌 회피.
    //   - 본 헬퍼 자체는 캐시 백엔드(Redis / MemoryCache 폴백) 어느 쪽이든
    //     동일하게 동작한다. MemoryCache 폴백 환경에서는 인스턴스 재시작 시
    //     0 으로 초기화되지만 그 시점에 캐시 데이터도 함께 초기화되므로 무해.
    //   - 무한 TTL — 버전 키 자체는 만료시키지 않음(만료되면 0 으로 reset 되어
    //     새 버전이 이전 버전과 충돌할 위험). MemoryCache 백엔드는 LRU eviction
    //     가능성이 있으나 실사용에서는 매우 드물고, eviction 발생 시에도 0 부터
    //     재시작 + 모든 종속 캐시 키도 동시에 stale 처리되므로 정합성 보장.
    // ════════════════════════════════════════════════════════════════════

    private const string VersionKeyPrefix = "cv:";

    /// <summary>
    /// 지정 namespace 의 현재 캐시 버전 반환. 키가 없거나 파싱 실패 시 0 반환.
    /// 이 값을 캐시 키 prefix 에 포함시키면 IncrementVersionAsync 호출 시
    /// 이전 버전의 키가 자동으로 stale 처리된다.
    /// </summary>
    /// <param name="ns">버전 격리 단위(예: "docutil-search").</param>
    public async Task<long> GetVersionAsync(string ns)
    {
        if (string.IsNullOrWhiteSpace(ns))
        {
            throw new ArgumentException("namespace 가 비어 있습니다.", nameof(ns));
        }

        var key = $"{VersionKeyPrefix}{ns}";
        try
        {
            var raw = await _cache.GetStringAsync(key);
            if (string.IsNullOrEmpty(raw))
            {
                return 0L;
            }
            return long.TryParse(raw, out var v) ? v : 0L;
        }
        catch (System.Net.Sockets.SocketException ex)
        {
            _logger.LogWarning(ex, "Redis 연결 오류 (version key {Key}) — 폴백 0 반환", key);
            return 0L;
        }
        catch (StackExchange.Redis.RedisConnectionException ex)
        {
            _logger.LogWarning(ex, "Redis 연결 예외 (version key {Key}) — 폴백 0 반환", key);
            return 0L;
        }
        catch (StackExchange.Redis.RedisTimeoutException ex)
        {
            _logger.LogWarning(ex, "Redis 타임아웃 (version key {Key}) — 폴백 0 반환", key);
            return 0L;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "캐시 버전 조회 실패 - key={Key}, type={Type}", key, ex.GetType().Name);
            return 0L;
        }
    }

    /// <summary>
    /// 지정 namespace 의 캐시 버전을 +1 증가시키고 새 값을 반환한다.
    /// IDistributedCache 한계로 atomic INCR 아님 — 동시 호출 시 동일 N+1 로 수렴할
    /// 수 있으나 캐시 무효화의 본질(이전 버전 키 일괄 stale)은 보장된다.
    /// 실패 시 LogWarning + 0 반환(best-effort, 호출자 흐름 차단 금지).
    /// </summary>
    /// <param name="ns">버전 격리 단위(예: "docutil-search").</param>
    public async Task<long> IncrementVersionAsync(string ns)
    {
        if (string.IsNullOrWhiteSpace(ns))
        {
            throw new ArgumentException("namespace 가 비어 있습니다.", nameof(ns));
        }

        var key = $"{VersionKeyPrefix}{ns}";
        try
        {
            // Get + Increment + Set — IDistributedCache 의 atomic INCR 미지원 한계 수용.
            // 캐시 무효화 용도이므로 race condition 으로 두 INCR 가 같은 N+1 에 수렴해도
            // 이전 N 이하 키들은 모두 stale 처리되어 본 작업의 의도는 보존됨.
            var current = await GetVersionAsync(ns);
            var next = current + 1L;

            // 무한 TTL — 버전 키 자체는 만료되지 않아야 함.
            // (만료되면 0 으로 reset 되며 새 버전이 이전 버전과 충돌할 위험)
            await _cache.SetStringAsync(
                key,
                next.ToString(System.Globalization.CultureInfo.InvariantCulture),
                new DistributedCacheEntryOptions());

            _logger.LogDebug("캐시 버전 증가 - namespace={Namespace}, newVersion={Version}", ns, next);
            return next;
        }
        catch (System.Net.Sockets.SocketException ex)
        {
            _logger.LogWarning(ex, "Redis 연결 오류 (version key {Key}) — 무효화 실패(best-effort)", key);
            return 0L;
        }
        catch (StackExchange.Redis.RedisConnectionException ex)
        {
            _logger.LogWarning(ex, "Redis 연결 예외 (version key {Key}) — 무효화 실패(best-effort)", key);
            return 0L;
        }
        catch (StackExchange.Redis.RedisTimeoutException ex)
        {
            _logger.LogWarning(ex, "Redis 타임아웃 (version key {Key}) — 무효화 실패(best-effort)", key);
            return 0L;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "캐시 버전 증가 실패 - key={Key}, type={Type}", key, ex.GetType().Name);
            return 0L;
        }
    }
}
