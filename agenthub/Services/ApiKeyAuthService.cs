using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using Microsoft.EntityFrameworkCore;
using System.Security.Cryptography;
using System.Text;

namespace AIAgentManagement.Services;

/// <summary>
/// API 키 인증 서비스. 인증 핫패스에서 KeyHash UNIQUE 인덱스 단건 조회로 동작한다.
/// Phase 3.3b/3.3c 변경:
///   - 기존: 활성 키 전체 로드 + foreach 복호화 비교(O(N) + 평문 풀 노출).
///   - 신규: SHA-256(평문) → KeyHash UNIQUE 단건 조회. AEAD(GCM) 무결성도 자동 보장.
///   - Legacy(KeyHash NULL) 폴백: 풀스캔 + 즉시 백필 분기. Phase 3.6 데이터 마이그레이션
///     완료 후 폴백 + DecryptLegacyCbc 제거 예정 (TECHSPEC §16 C1/C2/C3).
///   - AES Key: ApiKeyService 와 동일 정책으로 `Encryption:ApiKeyAesKey` 우선 + JWT 폴백.
/// </summary>
public class ApiKeyAuthService : IApiKeyAuthService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<ApiKeyAuthService> _logger;
    private readonly byte[] _aesKey;
    private readonly bool _usingFallbackKey;

    public ApiKeyAuthService(
        AIAgentManagementDbContext context,
        ILogger<ApiKeyAuthService> logger,
        IConfiguration configuration)
    {
        _context = context;
        _logger = logger;
        (_aesKey, _usingFallbackKey) = LoadAesKey(configuration, logger);
    }

    public async Task<ApiKeyValidationResult?> ValidateApiKeyAsync(string? apiKey)
    {
        if (string.IsNullOrWhiteSpace(apiKey))
            return null;

        try
        {
            var hash = ComputeKeyHash(apiKey);
            var now = DateTime.UtcNow;

            // 빠른 경로: KeyHash UNIQUE 인덱스 단건 조회 (TECHSPEC §16 C3 해소)
            var matched = await _context.ApiKeys
                .FirstOrDefaultAsync(k =>
                    k.KeyHash == hash &&
                    k.IsActive &&
                    (k.ExpiresAt == null || k.ExpiresAt > now));

            if (matched != null)
            {
                // KeyHash UNIQUE 매칭이 곧 평문 일치 — 추가 복호화 비교 불필요(SHA-256 충돌은 무시할 수준).
                return await TouchAndProjectAsync(matched);
            }

            // Legacy 폴백: KeyHash NULL 인 행이 남아 있는 동안만 풀스캔 비교.
            // TODO Phase 3.6 — 데이터 마이그레이션(KeyHash 백필) 완료 시 본 분기 + DecryptLegacyCbc 제거.
            var legacy = await _context.ApiKeys
                .Where(k =>
                    k.KeyHash == null &&
                    k.IsActive &&
                    (k.ExpiresAt == null || k.ExpiresAt > now))
                .ToListAsync();

            foreach (var key in legacy)
            {
                try
                {
                    string plaintext;
                    if (key.KeyIv is { Length: 12 } iv && key.KeyTag is { Length: 16 } tag)
                    {
                        plaintext = DecryptApiKey(Convert.FromBase64String(key.EncryptedKey), iv, tag);
                    }
                    else
                    {
                        plaintext = DecryptLegacyCbc(key.EncryptedKey);
                    }

                    if (plaintext != apiKey)
                        continue;

                    // 일치 — 즉시 백필 후 빠른 경로로 진입할 수 있도록 KeyHash 채우기.
                    BackfillRow(key, plaintext);
                    return await TouchAndProjectAsync(key);
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Legacy API Key 폴백 복호화 실패: ApiKeyId={ApiKeyId}", key.ApiKeyId);
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

    // ── 내부 ───────────────────────────────────────────────────────────

    /// <summary>
    /// 매칭된 키의 사용 통계(LastUsedAt/UsageCount/UpdatedAt)를 갱신하고 검증 결과 DTO 로 사상한다.
    /// SaveChanges 는 본 메서드에서 1회 — 빠른 경로/폴백 경로 모두 동일한 영속화 시점.
    /// </summary>
    private async Task<ApiKeyValidationResult> TouchAndProjectAsync(Models.ApiKey key)
    {
        key.LastUsedAt = DateTime.UtcNow;
        key.UsageCount++;
        key.UpdatedAt = DateTime.UtcNow;
        await _context.SaveChangesAsync();

        _logger.LogInformation(
            "API Key 인증 성공: ApiKeyId={ApiKeyId}, UserId={UserId}, AgentId={AgentId}",
            key.ApiKeyId, key.UserId, key.AgentId);

        return new ApiKeyValidationResult
        {
            UserId             = key.UserId,
            ApiKeyId           = key.ApiKeyId,
            AgentId            = key.AgentId,
            Scopes             = key.Scopes,
            AllowedIps         = key.AllowedIps,
            RateLimitPerMinute = key.RateLimitPerMinute,
            RateLimitPerDay    = key.RateLimitPerDay
        };
    }

    /// <summary>
    /// Legacy 행을 GCM + KeyHash 로 백필한다. SaveChanges 는 TouchAndProjectAsync 에서 일괄 커밋.
    /// TODO Phase 3.6 — 데이터 마이그레이션 완료 시 호출 분기 + 본 메서드 제거.
    /// </summary>
    private void BackfillRow(Models.ApiKey key, string plaintext)
    {
        var (ct, iv, tag) = EncryptApiKey(plaintext);
        key.EncryptedKey = Convert.ToBase64String(ct);
        key.KeyIv = iv;
        key.KeyTag = tag;
        key.KeyHash = ComputeKeyHash(plaintext);

        _logger.LogInformation(
            "Legacy ApiKey 자동 백필(인증 시점 CBC→GCM + KeyHash): ApiKeyId={ApiKeyId}, FallbackKey={FallbackKey}",
            key.ApiKeyId, _usingFallbackKey);
    }

    private (byte[] ciphertext, byte[] iv, byte[] tag) EncryptApiKey(string plaintext)
    {
        using var aes = new AesGcm(_aesKey, tagSizeInBytes: 16);
        var iv = RandomNumberGenerator.GetBytes(12);
        var plain = Encoding.UTF8.GetBytes(plaintext);
        var ct = new byte[plain.Length];
        var tag = new byte[16];
        aes.Encrypt(iv, plain, ct, tag);
        return (ct, iv, tag);
    }

    private string DecryptApiKey(byte[] ciphertext, byte[] iv, byte[] tag)
    {
        try
        {
            using var aes = new AesGcm(_aesKey, tagSizeInBytes: 16);
            var plain = new byte[ciphertext.Length];
            aes.Decrypt(iv, ciphertext, tag, plain);
            return Encoding.UTF8.GetString(plain);
        }
        catch (AuthenticationTagMismatchException)
        {
            throw new InvalidOperationException("API 키 무결성 검증 실패");
        }
    }

    /// <summary>
    /// Legacy CBC + 고정 IV 복호화. Phase 3.6 백필 완료 시 제거.
    /// </summary>
    private string DecryptLegacyCbc(string cipherText)
    {
        using var aes = Aes.Create();
        aes.Key = _aesKey;
        aes.IV = new byte[16];

        using var decryptor = aes.CreateDecryptor();
        using var ms = new MemoryStream(Convert.FromBase64String(cipherText));
        using var cs = new CryptoStream(ms, decryptor, CryptoStreamMode.Read);
        using var sr = new StreamReader(cs);
        return sr.ReadToEnd();
    }

    private static string ComputeKeyHash(string plaintext)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(plaintext));
        return Convert.ToHexString(bytes); // 64자 hex (대문자)
    }

    private static (byte[] key, bool usingFallback) LoadAesKey(IConfiguration config, ILogger logger)
    {
        var configured = config["Encryption:ApiKeyAesKey"];
        if (!string.IsNullOrWhiteSpace(configured))
        {
            byte[] bytes;
            try
            {
                bytes = Convert.FromBase64String(configured);
            }
            catch (FormatException)
            {
                throw new InvalidOperationException(
                    "Encryption:ApiKeyAesKey 값이 base64 형식이 아닙니다. 32바이트 AES-256 키를 base64 로 주입하세요.");
            }

            if (bytes.Length != 32)
            {
                throw new InvalidOperationException(
                    $"Encryption:ApiKeyAesKey 길이가 잘못되었습니다(현재 {bytes.Length} 바이트). AES-256 은 32 바이트가 필요합니다.");
            }

            return (bytes, false);
        }

        var jwtSecret = config["JwtSettings:SecretKey"];
        if (string.IsNullOrWhiteSpace(jwtSecret))
        {
            throw new InvalidOperationException(
                "Encryption:ApiKeyAesKey 와 JwtSettings:SecretKey 가 모두 비어 있어 AES 키를 결정할 수 없습니다.");
        }

        logger.LogWarning(
            "Encryption:ApiKeyAesKey 설정 부재 — JWT 키 폴백 사용 중. 운영 환경에서는 반드시 별도 키를 설정하세요. (TECHSPEC §16 C2)");

        var fallback = SHA256.HashData(Encoding.UTF8.GetBytes(jwtSecret));
        return (fallback, true);
    }
}
