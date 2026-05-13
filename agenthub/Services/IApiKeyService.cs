using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IApiKeyService
{
    Task<List<ApiKeyDto>> GetUserApiKeysAsync(int userId);
    Task<ApiKeyDto?> GetApiKeyByIdAsync(int apiKeyId, int userId);
    Task<ApiKeyDto> CreateApiKeyAsync(CreateApiKeyRequestDto request, int userId);
    Task<ApiKeyDto?> UpdateApiKeyAsync(int apiKeyId, UpdateApiKeyRequestDto request, int userId);
    Task<bool> DeleteApiKeyAsync(int apiKeyId, int userId);
    Task<string?> GetDecryptedApiKeyAsync(int apiKeyId, int userId);
    Task<CreateAgentApiKeyResponseDto> GenerateAgentApiKeyAsync(int agentId, int userId, CreateAgentApiKeyRequestDto request);
    Task<List<ApiKeyDto>> GetAgentApiKeysAsync(int agentId, int userId);
    Task<bool> DeleteAgentApiKeyAsync(int agentId, int apiKeyId, int userId);

    // ── 트랙 #91 — ApiKeyPoolService DB 통합 ─────────────────────────────────

    /// <summary>
    /// 외부 LLM 풀 키(<c>KeyType="Provider"</c>) 등록.
    /// <list type="number">
    /// <item>ServiceCode 화이트리스트 검증</item>
    /// <item>KeyHash UNIQUE 중복 검사 (다른 운영자가 같은 키 등록 차단)</item>
    /// <item>AES-GCM 암호화 + DB INSERT (<c>KeyType="Provider"</c> 강제)</item>
    /// <item><c>IApiKeyPoolService.RefreshAsync()</c> 즉시 트리거 → 다음 LLM 호출부터 신규 키 사용 가능</item>
    /// </list>
    /// </summary>
    Task<ApiKeyDto> CreateProviderApiKeyAsync(CreateProviderApiKeyRequestDto request, int operatorUserId, CancellationToken ct = default);

    /// <summary>
    /// 외부 LLM 키 유효성 검증 — 제공사별 가벼운 GET endpoint 1회 호출 (10초 타임아웃).
    /// 운영자가 콘솔에서 "테스트" 버튼을 누르면 호출된다.
    /// </summary>
    Task<TestApiKeyResponseDto> TestApiKeyAsync(int apiKeyId, int operatorUserId, CancellationToken ct = default);

    /// <summary>
    /// 풀 갱신 전용 복호화 변종. <c>GetDecryptedApiKeyAsync</c> 와 달리 LastUsedAt/UsageCount 를 갱신하지 않으므로
    /// 5분 주기 풀 적재가 사용량 카운터를 오염시키지 않는다.
    /// <c>IApiKeyPoolService.RefreshAsync</c> 내부에서만 호출된다 (그 외 호출처는 <c>GetDecryptedApiKeyAsync</c> 사용).
    /// 만료/비활성 키는 null 반환.
    /// </summary>
    Task<string?> DecryptForPoolAsync(int apiKeyId);
}
