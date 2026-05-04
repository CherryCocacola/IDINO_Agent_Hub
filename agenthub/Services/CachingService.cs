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
}
