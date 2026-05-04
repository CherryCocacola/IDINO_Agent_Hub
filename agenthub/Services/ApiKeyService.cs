using System.Security.Cryptography;
using System.Text;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

public class ApiKeyService : IApiKeyService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<ApiKeyService> _logger;
    private readonly string _encryptionKey;

    public ApiKeyService(
        AIAgentManagementDbContext context,
        ILogger<ApiKeyService> logger,
        IConfiguration configuration)
    {
        _context = context;
        _logger = logger;
        // JWT SecretKey를 암호화 키로 사용 (실제 운영에서는 별도 키 사용 권장)
        _encryptionKey = configuration["JwtSettings:SecretKey"]
            ?? throw new InvalidOperationException("JWT SecretKey not configured");
    }

    public async Task<List<ApiKeyDto>> GetUserApiKeysAsync(int userId)
    {
        var apiKeys = await _context.ApiKeys
            .Where(k => k.UserId == userId)
            .OrderByDescending(k => k.CreatedAt)
            .ToListAsync();

        var result = new List<ApiKeyDto>();
        foreach (var key in apiKeys)
            result.Add(await MapToDtoAsync(key));

        return result;
    }

    public async Task<ApiKeyDto?> GetApiKeyByIdAsync(int apiKeyId, int userId)
    {
        var apiKey = await _context.ApiKeys
            .FirstOrDefaultAsync(k => k.ApiKeyId == apiKeyId && k.UserId == userId);

        return apiKey == null ? null : await MapToDtoAsync(apiKey);
    }

    public async Task<ApiKeyDto> CreateApiKeyAsync(CreateApiKeyRequestDto request, int userId)
    {
        var encryptedKey = EncryptString(request.ApiKey);

        var apiKey = new ApiKey
        {
            UserId            = userId,
            KeyName           = request.KeyName,
            ServiceCode       = request.ServiceCode,
            EncryptedKey      = encryptedKey,
            Description       = request.Description,
            ExpiresAt         = request.ExpiresAt,
            AllowedIps        = NormalizeNullable(request.AllowedIps),
            Scopes            = NormalizeNullable(request.Scopes),
            RateLimitPerMinute = request.RateLimitPerMinute,
            RateLimitPerDay   = request.RateLimitPerDay,
            IsActive          = true,
            CreatedAt         = DateTime.UtcNow,
            UpdatedAt         = DateTime.UtcNow
        };

        _context.ApiKeys.Add(apiKey);
        await _context.SaveChangesAsync();

        _logger.LogInformation("API 키 생성: UserId={UserId}, ServiceCode={ServiceCode}, KeyName={KeyName}",
            userId, request.ServiceCode, request.KeyName);

        return await MapToDtoAsync(apiKey);
    }

    public async Task<ApiKeyDto?> UpdateApiKeyAsync(int apiKeyId, UpdateApiKeyRequestDto request, int userId)
    {
        var apiKey = await _context.ApiKeys
            .FirstOrDefaultAsync(k => k.ApiKeyId == apiKeyId && k.UserId == userId);

        if (apiKey == null) return null;

        if (!string.IsNullOrEmpty(request.KeyName))
            apiKey.KeyName = request.KeyName;

        if (request.Description != null)
            apiKey.Description = request.Description;

        if (request.IsActive.HasValue)
            apiKey.IsActive = request.IsActive.Value;

        if (request.ExpiresAt.HasValue)
            apiKey.ExpiresAt = request.ExpiresAt;

        // 보안 확장 필드 업데이트
        if (request.AllowedIps != null)
            apiKey.AllowedIps = NormalizeNullable(request.AllowedIps);

        if (request.Scopes != null)
            apiKey.Scopes = NormalizeNullable(request.Scopes);

        if (request.RateLimitPerMinute.HasValue)
            apiKey.RateLimitPerMinute = request.RateLimitPerMinute == 0 ? null : request.RateLimitPerMinute;

        if (request.RateLimitPerDay.HasValue)
            apiKey.RateLimitPerDay = request.RateLimitPerDay == 0 ? null : request.RateLimitPerDay;

        apiKey.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync();

        _logger.LogInformation("API 키 수정: ApiKeyId={ApiKeyId}, UserId={UserId}", apiKeyId, userId);

        return await MapToDtoAsync(apiKey);
    }

    public async Task<bool> DeleteApiKeyAsync(int apiKeyId, int userId)
    {
        var apiKey = await _context.ApiKeys
            .FirstOrDefaultAsync(k => k.ApiKeyId == apiKeyId && k.UserId == userId);

        if (apiKey == null) return false;

        _context.ApiKeys.Remove(apiKey);
        await _context.SaveChangesAsync();

        _logger.LogInformation("API 키 삭제: ApiKeyId={ApiKeyId}, UserId={UserId}", apiKeyId, userId);
        return true;
    }

    public async Task<CreateAgentApiKeyResponseDto> GenerateAgentApiKeyAsync(int agentId, int userId, CreateAgentApiKeyRequestDto request)
    {
        var plainKey = GenerateRandomAgentApiKey();
        var encryptedKey = EncryptString(plainKey);
        var keyName = !string.IsNullOrWhiteSpace(request.KeyName)
            ? request.KeyName.Trim()
            : $"Agent API Key {DateTime.UtcNow:yyyy-MM-dd HH:mm}";

        var apiKey = new ApiKey
        {
            UserId            = userId,
            KeyName           = keyName,
            ServiceCode       = "agent-api",
            AgentId           = agentId,
            EncryptedKey      = encryptedKey,
            Description       = request.Description,
            ExpiresAt         = request.ExpiresAt,
            AllowedIps        = NormalizeNullable(request.AllowedIps),
            Scopes            = NormalizeNullable(request.Scopes),
            RateLimitPerMinute = request.RateLimitPerMinute,
            RateLimitPerDay   = request.RateLimitPerDay,
            IsActive          = true,
            CreatedAt         = DateTime.UtcNow,
            UpdatedAt         = DateTime.UtcNow
        };

        _context.ApiKeys.Add(apiKey);
        await _context.SaveChangesAsync();

        _logger.LogInformation("Agent API 키 생성: ApiKeyId={ApiKeyId}, AgentId={AgentId}, UserId={UserId}",
            apiKey.ApiKeyId, agentId, userId);

        return new CreateAgentApiKeyResponseDto
        {
            ApiKeyId           = apiKey.ApiKeyId,
            ApiKey             = plainKey,
            KeyName            = apiKey.KeyName,
            AgentId            = agentId,
            ExpiresAt          = apiKey.ExpiresAt,
            Scopes             = apiKey.Scopes,
            AllowedIps         = apiKey.AllowedIps,
            RateLimitPerMinute = apiKey.RateLimitPerMinute,
            RateLimitPerDay    = apiKey.RateLimitPerDay,
            Warning            = "이 키는 이번에만 표시됩니다. 안전한 곳에 저장하세요."
        };
    }

    public async Task<List<ApiKeyDto>> GetAgentApiKeysAsync(int agentId, int userId)
    {
        var apiKeys = await _context.ApiKeys
            .Where(k => k.AgentId == agentId && k.UserId == userId && k.ServiceCode == "agent-api")
            .OrderByDescending(k => k.CreatedAt)
            .ToListAsync();

        var result = new List<ApiKeyDto>();
        foreach (var key in apiKeys)
            result.Add(await MapToDtoAsync(key));

        return result;
    }

    public async Task<bool> DeleteAgentApiKeyAsync(int agentId, int apiKeyId, int userId)
    {
        var apiKey = await _context.ApiKeys
            .FirstOrDefaultAsync(k =>
                k.ApiKeyId == apiKeyId &&
                k.AgentId == agentId &&
                k.UserId == userId &&
                k.ServiceCode == "agent-api");

        if (apiKey == null) return false;

        _context.ApiKeys.Remove(apiKey);
        await _context.SaveChangesAsync();

        _logger.LogInformation("Agent API 키 삭제: ApiKeyId={ApiKeyId}, AgentId={AgentId}, UserId={UserId}",
            apiKeyId, agentId, userId);
        return true;
    }

    public async Task<string?> GetDecryptedApiKeyAsync(int apiKeyId, int userId)
    {
        var apiKey = await _context.ApiKeys
            .FirstOrDefaultAsync(k => k.ApiKeyId == apiKeyId && k.UserId == userId);

        if (apiKey == null || !apiKey.IsActive)
            return null;

        if (apiKey.ExpiresAt.HasValue && apiKey.ExpiresAt.Value < DateTime.UtcNow)
            return null;

        try
        {
            var decrypted = DecryptString(apiKey.EncryptedKey);

            apiKey.LastUsedAt = DateTime.UtcNow;
            apiKey.UsageCount++;
            apiKey.UpdatedAt = DateTime.UtcNow;
            await _context.SaveChangesAsync();

            return decrypted;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "API 키 복호화 실패: ApiKeyId={ApiKeyId}", apiKeyId);
            return null;
        }
    }

    // ── 유틸 ───────────────────────────────────────────────────────────

    private async Task<ApiKeyDto> MapToDtoAsync(ApiKey apiKey)
    {
        var masked = apiKey.AgentId.HasValue && apiKey.ServiceCode == "agent-api"
            ? MaskAgentApiKey(apiKey.EncryptedKey)
            : MaskApiKey(apiKey.EncryptedKey);

        var dto = new ApiKeyDto
        {
            ApiKeyId           = apiKey.ApiKeyId,
            UserId             = apiKey.UserId,
            KeyName            = apiKey.KeyName,
            ServiceCode        = apiKey.ServiceCode,
            AgentId            = apiKey.AgentId,
            Description        = apiKey.Description,
            ExpiresAt          = apiKey.ExpiresAt,
            IsActive           = apiKey.IsActive,
            LastUsedAt         = apiKey.LastUsedAt,
            UsageCount         = apiKey.UsageCount,
            CreatedAt          = apiKey.CreatedAt,
            UpdatedAt          = apiKey.UpdatedAt,
            MaskedKey          = masked,
            AllowedIps         = apiKey.AllowedIps,
            Scopes             = apiKey.Scopes,
            RateLimitPerMinute = apiKey.RateLimitPerMinute,
            RateLimitPerDay    = apiKey.RateLimitPerDay
        };

        if (apiKey.ServiceCode != "agent-api")
        {
            var service = await _context.ApiServices
                .FirstOrDefaultAsync(s => s.ServiceCode == apiKey.ServiceCode);
            if (service != null)
                dto.ServiceName = service.ServiceName;
        }
        else
        {
            dto.ServiceName = "Agent API";
        }

        return dto;
    }

    private static string GenerateRandomAgentApiKey()
    {
        var bytes = new byte[32];
        RandomNumberGenerator.Fill(bytes);
        var base64 = Convert.ToBase64String(bytes)
            .Replace("+", "-")
            .Replace("/", "_")
            .Replace("=", "");
        return $"ak-{base64}";
    }

    private static string? NormalizeNullable(string? value)
        => string.IsNullOrWhiteSpace(value) ? null : value.Trim();

    private string MaskApiKey(string encryptedKey)
    {
        if (encryptedKey.Length <= 10) return "***";
        return encryptedKey[..4] + "..." + encryptedKey[^4..];
    }

    private string MaskAgentApiKey(string encryptedKey)
    {
        if (encryptedKey.Length <= 10) return "ak-****";
        return "ak-" + encryptedKey[..4] + "..." + encryptedKey[^4..];
    }

    private string EncryptString(string plainText)
    {
        using var aes = Aes.Create();
        aes.Key = DeriveKeyFromPassword(_encryptionKey);
        aes.IV = new byte[16];

        using var encryptor = aes.CreateEncryptor();
        using var ms = new MemoryStream();
        using (var cs = new CryptoStream(ms, encryptor, CryptoStreamMode.Write))
        using (var sw = new StreamWriter(cs))
            sw.Write(plainText);

        return Convert.ToBase64String(ms.ToArray());
    }

    private string DecryptString(string cipherText)
    {
        using var aes = Aes.Create();
        aes.Key = DeriveKeyFromPassword(_encryptionKey);
        aes.IV = new byte[16];

        using var decryptor = aes.CreateDecryptor();
        using var ms = new MemoryStream(Convert.FromBase64String(cipherText));
        using var cs = new CryptoStream(ms, decryptor, CryptoStreamMode.Read);
        using var sr = new StreamReader(cs);
        return sr.ReadToEnd();
    }

    private byte[] DeriveKeyFromPassword(string password)
    {
        using var sha256 = SHA256.Create();
        return sha256.ComputeHash(Encoding.UTF8.GetBytes(password));
    }
}
