using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using Microsoft.EntityFrameworkCore;
using System.Security.Cryptography;
using System.Text;

namespace AIAgentManagement.Services;

public class ApiKeyAuthService : IApiKeyAuthService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<ApiKeyAuthService> _logger;
    private readonly string _encryptionKey;

    public ApiKeyAuthService(
        AIAgentManagementDbContext context,
        ILogger<ApiKeyAuthService> logger,
        IConfiguration configuration)
    {
        _context = context;
        _logger = logger;
        _encryptionKey = configuration["JwtSettings:SecretKey"]
            ?? throw new InvalidOperationException("JWT SecretKey not configured");
    }

    public async Task<ApiKeyValidationResult?> ValidateApiKeyAsync(string? apiKey)
    {
        if (string.IsNullOrWhiteSpace(apiKey))
            return null;

        try
        {
            // 모든 활성 API Key를 조회하여 복호화 후 비교
            var apiKeys = await _context.ApiKeys
                .Where(k => k.IsActive)
                .Where(k => k.ExpiresAt == null || k.ExpiresAt > DateTime.UtcNow)
                .ToListAsync();

            foreach (var key in apiKeys)
            {
                try
                {
                    var decrypted = DecryptString(key.EncryptedKey);
                    if (decrypted == apiKey)
                    {
                        // 사용 통계 업데이트
                        key.LastUsedAt = DateTime.UtcNow;
                        key.UsageCount++;
                        key.UpdatedAt = DateTime.UtcNow;
                        await _context.SaveChangesAsync();

                        _logger.LogInformation(
                            "API Key 인증 성공: ApiKeyId={ApiKeyId}, UserId={UserId}, AgentId={AgentId}",
                            key.ApiKeyId, key.UserId, key.AgentId);

                        return new ApiKeyValidationResult
                        {
                            UserId            = key.UserId,
                            ApiKeyId          = key.ApiKeyId,
                            AgentId           = key.AgentId,
                            Scopes            = key.Scopes,
                            AllowedIps        = key.AllowedIps,
                            RateLimitPerMinute = key.RateLimitPerMinute,
                            RateLimitPerDay   = key.RateLimitPerDay
                        };
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "API Key 복호화 실패: ApiKeyId={ApiKeyId}", key.ApiKeyId);
                }
            }

            _logger.LogWarning("유효하지 않은 API Key 시도");
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "API Key 검증 중 오류 발생");
            return null;
        }
    }

    private string DecryptString(string cipherText)
    {
        using (var aes = Aes.Create())
        {
            aes.Key = DeriveKeyFromPassword(_encryptionKey);
            aes.IV = new byte[16];

            using (var decryptor = aes.CreateDecryptor())
            using (var ms = new MemoryStream(Convert.FromBase64String(cipherText)))
            using (var cs = new CryptoStream(ms, decryptor, CryptoStreamMode.Read))
            using (var sr = new StreamReader(cs))
            {
                return sr.ReadToEnd();
            }
        }
    }

    private byte[] DeriveKeyFromPassword(string password)
    {
        using (var sha256 = SHA256.Create())
        {
            return sha256.ComputeHash(Encoding.UTF8.GetBytes(password));
        }
    }
}
