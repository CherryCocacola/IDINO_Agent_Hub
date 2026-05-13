using System.Diagnostics;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

/// <summary>
/// 사용자/Agent API 키 발급·수정·복호화·삭제 서비스.
/// Phase 3.3b/3.3c 변경:
///   - AES-CBC + 고정 IV(`new byte[16]`) → AES-GCM + per-record 무작위 nonce(`KeyIv`)
///     + 인증 태그(`KeyTag`) 분리 저장. 결정적 암호화 + AEAD 부재 결함 해소 (TECHSPEC §16 C1).
///   - AES Key 를 JWT SecretKey 에서 SHA-256 유도하던 결합을 차단하고 별도 설정 키
///     `Encryption:ApiKeyAesKey` 우선 사용. JWT 키 노출 시 ApiKey 평문 전체가
///     복호화되던 위험 차단 (TECHSPEC §16 C2).
///   - 평문 SHA-256 해시(`KeyHash`)를 함께 저장하여 인증 핫패스의 풀스캔 비교를
///     UNIQUE 인덱스 단건 조회로 단축 (TECHSPEC §16 C3, ApiKeyAuthService).
/// </summary>
public class ApiKeyService : IApiKeyService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<ApiKeyService> _logger;
    private readonly byte[] _aesKey;
    private readonly bool _usingFallbackKey;
    private readonly IApiKeyPoolService _apiKeyPool;
    private readonly IHttpClientFactory _httpClientFactory;

    // 외부 LLM 키 등록 시 허용되는 ServiceCode 화이트리스트 (트랙 #91).
    // ApiKeyPoolService.NormalizeServiceCode 와 동기화 유지.
    private static readonly HashSet<string> SupportedProviderServiceCodes =
        new(StringComparer.OrdinalIgnoreCase)
        {
            "openai", "chatgpt",
            "claude",
            "gemini", "google", "gemini-image", "imagen4",
            "perplexity",
            "mistral",
            "azureopenai",
            "copilot"
        };

    public ApiKeyService(
        AIAgentManagementDbContext context,
        ILogger<ApiKeyService> logger,
        IConfiguration configuration,
        IApiKeyPoolService apiKeyPool,
        IHttpClientFactory httpClientFactory)
    {
        _context = context;
        _logger = logger;
        _apiKeyPool = apiKeyPool;
        _httpClientFactory = httpClientFactory;
        (_aesKey, _usingFallbackKey) = LoadAesKey(configuration, logger);
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
        var (ciphertext, iv, tag) = EncryptApiKey(request.ApiKey);
        var keyHash = ComputeKeyHash(request.ApiKey);

        // 트랙 #91 — KeyType 미지정 시 "External" 기본값. 운영자가 Provider 키 등록 시에는
        // 전용 endpoint(`CreateProviderApiKeyAsync`)를 사용하므로 본 메서드 사용자는 일반적으로 External.
        var keyType = string.IsNullOrWhiteSpace(request.KeyType) ? "External" : request.KeyType.Trim();

        var apiKey = new ApiKey
        {
            UserId            = userId,
            KeyName           = request.KeyName,
            ServiceCode       = request.ServiceCode,
            KeyType           = keyType,
            EncryptedKey      = Convert.ToBase64String(ciphertext),
            KeyIv             = iv,
            KeyTag            = tag,
            KeyHash           = keyHash,
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

        _logger.LogInformation("API 키 생성: UserId={UserId}, ServiceCode={ServiceCode}, KeyName={KeyName}, KeyType={KeyType}",
            userId, request.ServiceCode, request.KeyName, keyType);

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
        var (ciphertext, iv, tag) = EncryptApiKey(plainKey);
        var keyHash = ComputeKeyHash(plainKey);
        var keyName = !string.IsNullOrWhiteSpace(request.KeyName)
            ? request.KeyName.Trim()
            : $"Agent API Key {DateTime.UtcNow:yyyy-MM-dd HH:mm}";

        var apiKey = new ApiKey
        {
            UserId            = userId,
            KeyName           = keyName,
            ServiceCode       = "agent-api",
            KeyType           = "External", // Agent API 키도 외부 노출 ak- 키 → External 카테고리.
            AgentId           = agentId,
            EncryptedKey      = Convert.ToBase64String(ciphertext),
            KeyIv             = iv,
            KeyTag            = tag,
            KeyHash           = keyHash,
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
            // GCM 신규 형식: KeyIv + KeyTag 가 모두 채워진 경우 → AEAD 복호화
            // Legacy(CBC+고정 IV) 형식: KeyIv 또는 KeyTag 가 NULL → 폴백 + 즉시 백필
            string plaintext;
            if (apiKey.KeyIv is { Length: 12 } iv && apiKey.KeyTag is { Length: 16 } tag)
            {
                plaintext = DecryptApiKey(Convert.FromBase64String(apiKey.EncryptedKey), iv, tag);
            }
            else
            {
                plaintext = DecryptLegacyCbc(apiKey.EncryptedKey);
                // TODO Phase 3.6 — 데이터 마이그레이션 완료 시 본 폴백 분기 + DecryptLegacyCbc 메서드 제거.
                // 회수한 평문을 즉시 GCM 으로 재암호화 + KeyHash 산출하여 후속 호출에서 빠른 경로 사용.
                BackfillToGcm(apiKey, plaintext);
            }

            apiKey.LastUsedAt = DateTime.UtcNow;
            apiKey.UsageCount++;
            apiKey.UpdatedAt = DateTime.UtcNow;
            await _context.SaveChangesAsync();

            return plaintext;
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
            KeyType            = apiKey.KeyType,
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

    /// <summary>
    /// 평문을 AES-GCM 으로 암호화하여 (ciphertext, iv, tag) 트리플을 반환한다.
    /// nonce(=iv)는 매 호출마다 12바이트 무작위로 생성되어 결정적 암호화를 차단한다.
    /// tag(16바이트)는 ciphertext 무결성 보장 — 변조 시 복호화에서 AuthenticationTagMismatchException.
    /// </summary>
    private (byte[] ciphertext, byte[] iv, byte[] tag) EncryptApiKey(string plaintext)
    {
        // .NET 8 권장 시그니처: tagSizeInBytes 명시. 매개변수 없는 ctor 는 [Obsolete] 경고.
        using var aes = new AesGcm(_aesKey, tagSizeInBytes: 16);
        var iv = RandomNumberGenerator.GetBytes(12);
        var plain = Encoding.UTF8.GetBytes(plaintext);
        var ct = new byte[plain.Length];
        var tag = new byte[16];
        aes.Encrypt(iv, plain, ct, tag);
        return (ct, iv, tag);
    }

    /// <summary>
    /// AES-GCM 복호화. 인증 태그 검증에 실패하면 InvalidOperationException 으로 변환한다.
    /// </summary>
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
    /// 평문 API 키의 SHA-256 해시(대문자 16진수, 64자)를 산출한다.
    /// 인증 핫패스에서 UNIQUE 인덱스 단건 조회 키로 사용 (TECHSPEC §16 C3).
    /// </summary>
    internal static string ComputeKeyHash(string plaintext)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(plaintext));
        return Convert.ToHexString(bytes); // 64자 hex (대문자)
    }

    /// <summary>
    /// 운영 환경에서는 `Encryption:ApiKeyAesKey` 설정에 base64 인코딩된 32바이트(AES-256) 키를 주입해야 한다.
    /// 미설정 시 호환성을 위해 `JwtSettings:SecretKey` 를 SHA-256 유도하여 폴백하지만 시작 시 1회 경고를 남긴다.
    /// 이 폴백은 TECHSPEC §16 C2(JWT 키 노출 = ApiKey 평문 노출) 위험을 일시적으로 완화하기 위한 호환 분기이며,
    /// Phase 3.6 까지 운영 키 주입을 마쳐야 한다.
    /// </summary>
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

    /// <summary>
    /// Legacy CBC + 고정 IV(16 바이트 0) 형식 복호화. Phase 3.6 백필 완료 시 본 메서드 제거 예정.
    /// 폴백 키 사용 중에는 기존 데이터를 그대로 복호화 가능 — JWT SecretKey → SHA-256 유도가 이전과 동일.
    /// 운영 키로 교체된 환경에서는 legacy 행 복호화가 실패하여 호출처에서 null 반환 — Phase 3.6 백필 필요.
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

    // ── 트랙 #91 — ApiKeyPoolService DB 통합 ─────────────────────────────────

    /// <summary>
    /// 외부 LLM 풀 키(`KeyType="Provider"`) 등록.
    /// 등록 후 즉시 `IApiKeyPoolService.RefreshAsync` 를 트리거하여 다음 LLM 호출부터 신규 키 사용 가능.
    /// `ValidateOnCreate=true` 인 경우 등록 후 한 번 ping 검증을 수행하지만, 검증 실패가 등록 실패로 이어지진 않는다
    /// (운영자가 의도적으로 미사용 키 등록할 수 있음 — 결과는 응답 메시지로 안내).
    /// </summary>
    public async Task<ApiKeyDto> CreateProviderApiKeyAsync(
        CreateProviderApiKeyRequestDto request,
        int operatorUserId,
        CancellationToken ct = default)
    {
        // 1) 입력 검증 — ServiceCode 화이트리스트.
        if (string.IsNullOrWhiteSpace(request.KeyName))
            throw new ArgumentException("키 이름은 필수 입력 항목입니다.", nameof(request));

        if (string.IsNullOrWhiteSpace(request.ApiKey) || request.ApiKey.Length < 10)
            throw new ArgumentException("ApiKey 는 10자 이상이어야 합니다.", nameof(request));

        if (string.IsNullOrWhiteSpace(request.ServiceCode)
            || !SupportedProviderServiceCodes.Contains(request.ServiceCode))
        {
            throw new ArgumentException(
                $"지원하지 않는 ServiceCode 입니다: '{request.ServiceCode}'. " +
                $"허용 값: {string.Join(", ", SupportedProviderServiceCodes)}",
                nameof(request));
        }

        // 2) KeyHash 중복 검사 — 같은 키 재등록 차단 (UNIQUE 인덱스 위반 방지 + 명확한 한국어 응답).
        var keyHash = ComputeKeyHash(request.ApiKey);
        var duplicate = await _context.ApiKeys
            .AsNoTracking()
            .AnyAsync(k => k.KeyHash == keyHash, ct);
        if (duplicate)
        {
            throw new InvalidOperationException("이미 등록된 API 키입니다. 다른 키를 사용하세요.");
        }

        // 3) AES-GCM 암호화 + DB INSERT (KeyType="Provider" 강제).
        var (ciphertext, iv, tag) = EncryptApiKey(request.ApiKey);

        var apiKey = new ApiKey
        {
            UserId            = operatorUserId,
            KeyName           = request.KeyName.Trim(),
            ServiceCode       = request.ServiceCode.Trim().ToLowerInvariant(),
            KeyType           = "Provider", // 트랙 #91 — 풀 키 전용 분류.
            EncryptedKey      = Convert.ToBase64String(ciphertext),
            KeyIv             = iv,
            KeyTag            = tag,
            KeyHash           = keyHash,
            Description       = NormalizeNullable(request.Description),
            ExpiresAt         = request.ExpiresAt,
            // Provider 키는 외부 노출되지 않으므로 AllowedIps / Scopes / RateLimit 미사용.
            IsActive          = true,
            CreatedAt         = DateTime.UtcNow,
            UpdatedAt         = DateTime.UtcNow
        };

        _context.ApiKeys.Add(apiKey);
        await _context.SaveChangesAsync(ct);

        _logger.LogInformation(
            "[Provider ApiKey] 등록 완료: ApiKeyId={ApiKeyId}, ServiceCode={ServiceCode}, OperatorUserId={UserId}",
            apiKey.ApiKeyId, apiKey.ServiceCode, operatorUserId);

        // 4) 풀 즉시 갱신 — 다음 LLM 호출부터 신규 키 사용 가능.
        try
        {
            await _apiKeyPool.RefreshAsync(ct);
        }
        catch (Exception ex)
        {
            // 풀 갱신 실패가 등록 실패로 이어지면 안 됨 — 5분 주기 다음 RefreshAsync 가 메꿔준다.
            _logger.LogError(ex,
                "[Provider ApiKey] 등록 직후 풀 갱신 실패 — 다음 주기 갱신을 기다림. ApiKeyId={ApiKeyId}",
                apiKey.ApiKeyId);
        }

        return await MapToDtoAsync(apiKey);
    }

    /// <summary>
    /// 외부 LLM 키 유효성 검증 — 제공사별 가벼운 GET endpoint 1회 호출 (10초 타임아웃).
    /// </summary>
    public async Task<TestApiKeyResponseDto> TestApiKeyAsync(
        int apiKeyId,
        int operatorUserId,
        CancellationToken ct = default)
    {
        // 1) DB 에서 키 조회 (모든 사용자 — 운영자 콘솔 권한이므로 본인 소유 제약 없음).
        var apiKey = await _context.ApiKeys
            .FirstOrDefaultAsync(k => k.ApiKeyId == apiKeyId, ct);

        if (apiKey == null)
        {
            return new TestApiKeyResponseDto(false, "지정한 API 키를 찾을 수 없습니다.", null, 0);
        }

        if (!apiKey.IsActive)
        {
            return new TestApiKeyResponseDto(false, "비활성화된 API 키는 검증할 수 없습니다.", apiKey.ServiceCode, 0);
        }

        // 2) 평문 복호화. LastUsedAt 미갱신 변종 사용.
        var plaintext = await DecryptForPoolAsync(apiKeyId);
        if (string.IsNullOrWhiteSpace(plaintext))
        {
            return new TestApiKeyResponseDto(false, "API 키 복호화에 실패했습니다.", apiKey.ServiceCode, 0);
        }

        // 3) 정규화된 제공사 코드.
        var provider = ApiKeyPoolService.NormalizeServiceCode(apiKey.ServiceCode);
        if (provider == null)
        {
            return new TestApiKeyResponseDto(
                false,
                $"지원하지 않는 ServiceCode 입니다: '{apiKey.ServiceCode}'",
                apiKey.ServiceCode,
                0);
        }

        // 4) 제공사별 ping. 10초 강제 타임아웃 — 운영자 UI 응답성 보장.
        using var timeoutCts = CancellationTokenSource.CreateLinkedTokenSource(ct);
        timeoutCts.CancelAfter(TimeSpan.FromSeconds(10));

        var stopwatch = Stopwatch.StartNew();
        try
        {
            return provider switch
            {
                "openai"       => await PingOpenAiAsync(plaintext, stopwatch, timeoutCts.Token),
                "claude"       => await PingClaudeAsync(plaintext, stopwatch, timeoutCts.Token),
                "gemini"       => await PingGeminiAsync(plaintext, stopwatch, timeoutCts.Token),
                "perplexity"   => await PingPerplexityAsync(plaintext, stopwatch, timeoutCts.Token),
                "mistral"      => await PingMistralAsync(plaintext, stopwatch, timeoutCts.Token),
                "azureopenai"  => new TestApiKeyResponseDto(false,
                                    "AzureOpenAI 키 자동 검증은 본 트랙에서 미지원입니다. 별도 endpoint URL 이 필요합니다.",
                                    provider, stopwatch.ElapsedMilliseconds),
                "copilot"      => new TestApiKeyResponseDto(false,
                                    "Copilot 키 자동 검증은 본 트랙에서 미지원입니다.",
                                    provider, stopwatch.ElapsedMilliseconds),
                _              => new TestApiKeyResponseDto(false,
                                    "지원하지 않는 제공사입니다.", provider, stopwatch.ElapsedMilliseconds)
            };
        }
        catch (TaskCanceledException) when (timeoutCts.IsCancellationRequested && !ct.IsCancellationRequested)
        {
            return new TestApiKeyResponseDto(false,
                "검증 타임아웃 (10초 초과). 외부 LLM 서비스 상태를 확인하세요.",
                provider, stopwatch.ElapsedMilliseconds);
        }
        catch (HttpRequestException ex)
        {
            _logger.LogWarning(ex,
                "[Provider ApiKey Test] 외부 LLM 호출 실패. ApiKeyId={ApiKeyId}, Provider={Provider}",
                apiKeyId, provider);
            return new TestApiKeyResponseDto(false,
                $"외부 LLM 서비스 연결 실패: {ex.Message}",
                provider, stopwatch.ElapsedMilliseconds);
        }
    }

    /// <summary>
    /// 풀 갱신 전용 복호화 변종 — LastUsedAt / UsageCount 미갱신.
    /// `IApiKeyPoolService.RefreshAsync` 가 5분마다 호출하므로 사용량 카운터 오염을 차단한다.
    /// </summary>
    public async Task<string?> DecryptForPoolAsync(int apiKeyId)
    {
        var apiKey = await _context.ApiKeys
            .AsNoTracking()
            .FirstOrDefaultAsync(k => k.ApiKeyId == apiKeyId);

        if (apiKey == null || !apiKey.IsActive)
            return null;

        if (apiKey.ExpiresAt.HasValue && apiKey.ExpiresAt.Value < DateTime.UtcNow)
            return null;

        try
        {
            // GCM 신규 형식: KeyIv + KeyTag 가 모두 채워진 경우 → AEAD 복호화
            // Legacy(CBC) 형식: 폴백 분기로 복호화 — DB 백필은 GetDecryptedApiKeyAsync 핫패스에서만 수행.
            //   본 메서드는 AsNoTracking 이므로 SaveChanges 의도하지 않음 (사용량 카운터 오염 방지).
            if (apiKey.KeyIv is { Length: 12 } iv && apiKey.KeyTag is { Length: 16 } tag)
            {
                return DecryptApiKey(Convert.FromBase64String(apiKey.EncryptedKey), iv, tag);
            }

            return DecryptLegacyCbc(apiKey.EncryptedKey);
        }
        catch (InvalidOperationException ex)
        {
            // AuthenticationTagMismatchException 으로부터 변환된 무결성 실패 등.
            _logger.LogError(ex, "[DecryptForPool] API 키 복호화 실패: ApiKeyId={ApiKeyId}", apiKeyId);
            return null;
        }
        catch (FormatException ex)
        {
            _logger.LogError(ex, "[DecryptForPool] base64 디코딩 실패: ApiKeyId={ApiKeyId}", apiKeyId);
            return null;
        }
    }

    // ── 제공사별 ping 헬퍼 (트랙 #91) ─────────────────────────────────────

    /// <summary>OpenAI: GET https://api.openai.com/v1/models — 200 이면 키 유효.</summary>
    private async Task<TestApiKeyResponseDto> PingOpenAiAsync(string apiKey, Stopwatch sw, CancellationToken ct)
    {
        var client = _httpClientFactory.CreateClient(); // 기본 HttpClient — 외부 URL 직접 호출용.
        using var req = new HttpRequestMessage(HttpMethod.Get, "https://api.openai.com/v1/models");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);
        using var resp = await client.SendAsync(req, ct);
        sw.Stop();
        return BuildPingResult(resp, sw.ElapsedMilliseconds, "openai");
    }

    /// <summary>Claude: GET https://api.anthropic.com/v1/models — 200 이면 키 유효.</summary>
    private async Task<TestApiKeyResponseDto> PingClaudeAsync(string apiKey, Stopwatch sw, CancellationToken ct)
    {
        var client = _httpClientFactory.CreateClient();
        using var req = new HttpRequestMessage(HttpMethod.Get, "https://api.anthropic.com/v1/models");
        req.Headers.Add("x-api-key", apiKey);
        req.Headers.Add("anthropic-version", "2023-06-01");
        using var resp = await client.SendAsync(req, ct);
        sw.Stop();
        return BuildPingResult(resp, sw.ElapsedMilliseconds, "claude");
    }

    /// <summary>Gemini: GET https://generativelanguage.googleapis.com/v1beta/models?key={key} — 200 이면 키 유효.</summary>
    private async Task<TestApiKeyResponseDto> PingGeminiAsync(string apiKey, Stopwatch sw, CancellationToken ct)
    {
        var client = _httpClientFactory.CreateClient();
        var url = $"https://generativelanguage.googleapis.com/v1beta/models?key={Uri.EscapeDataString(apiKey)}";
        using var req = new HttpRequestMessage(HttpMethod.Get, url);
        using var resp = await client.SendAsync(req, ct);
        sw.Stop();
        return BuildPingResult(resp, sw.ElapsedMilliseconds, "gemini");
    }

    /// <summary>Perplexity: GET https://api.perplexity.ai/models — 200 이면 키 유효.</summary>
    private async Task<TestApiKeyResponseDto> PingPerplexityAsync(string apiKey, Stopwatch sw, CancellationToken ct)
    {
        var client = _httpClientFactory.CreateClient();
        using var req = new HttpRequestMessage(HttpMethod.Get, "https://api.perplexity.ai/models");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);
        using var resp = await client.SendAsync(req, ct);
        sw.Stop();
        return BuildPingResult(resp, sw.ElapsedMilliseconds, "perplexity");
    }

    /// <summary>Mistral: GET https://api.mistral.ai/v1/models — 200 이면 키 유효.</summary>
    private async Task<TestApiKeyResponseDto> PingMistralAsync(string apiKey, Stopwatch sw, CancellationToken ct)
    {
        var client = _httpClientFactory.CreateClient();
        using var req = new HttpRequestMessage(HttpMethod.Get, "https://api.mistral.ai/v1/models");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);
        using var resp = await client.SendAsync(req, ct);
        sw.Stop();
        return BuildPingResult(resp, sw.ElapsedMilliseconds, "mistral");
    }

    /// <summary>HTTP 응답을 사용자(운영자) 친화 한국어 메시지로 변환.</summary>
    private static TestApiKeyResponseDto BuildPingResult(HttpResponseMessage resp, long latencyMs, string provider)
    {
        var status = (int)resp.StatusCode;
        if (resp.IsSuccessStatusCode)
        {
            return new TestApiKeyResponseDto(true, $"검증 PASS · {provider} 응답 {status} · {latencyMs}ms", provider, latencyMs);
        }

        var detail = status switch
        {
            401 => "인증 실패 (401) — API 키가 유효하지 않습니다.",
            403 => "권한 거부 (403) — API 키에 해당 endpoint 접근 권한이 없습니다.",
            404 => "검증 endpoint 를 찾을 수 없습니다 (404).",
            429 => "Rate limit 초과 (429) — 잠시 후 다시 시도하세요.",
            >= 500 => $"외부 LLM 서버 오류 ({status}).",
            _ => $"검증 실패 ({status})."
        };

        return new TestApiKeyResponseDto(false, $"{provider}: {detail}", provider, latencyMs);
    }

    // ── 기존 유틸 ───────────────────────────────────────────────────────

    /// <summary>
    /// Legacy CBC 행을 GCM 으로 즉시 재암호화하고 KeyHash 를 백필한다.
    /// SaveChanges 는 호출자(`GetDecryptedApiKeyAsync`)가 기존 LastUsedAt 갱신과 함께 1회로 커밋.
    /// TODO Phase 3.6 — 데이터 마이그레이션 완료 시 본 메서드 + 호출 분기 제거.
    /// </summary>
    private void BackfillToGcm(ApiKey apiKey, string plaintext)
    {
        var (ct, iv, tag) = EncryptApiKey(plaintext);
        apiKey.EncryptedKey = Convert.ToBase64String(ct);
        apiKey.KeyIv = iv;
        apiKey.KeyTag = tag;
        apiKey.KeyHash = ComputeKeyHash(plaintext);

        _logger.LogInformation(
            "Legacy ApiKey 자동 백필 완료(CBC→GCM + KeyHash): ApiKeyId={ApiKeyId}, FallbackKey={FallbackKey}",
            apiKey.ApiKeyId, _usingFallbackKey);
    }
}
