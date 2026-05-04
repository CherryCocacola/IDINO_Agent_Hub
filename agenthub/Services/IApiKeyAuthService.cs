using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IApiKeyAuthService
{
    /// <summary>
    /// API 키를 검증하고 유효한 경우 검증 결과(UserId, ApiKeyId, Scopes 등)를 반환합니다.
    /// 유효하지 않은 경우 null을 반환합니다.
    /// </summary>
    Task<ApiKeyValidationResult?> ValidateApiKeyAsync(string? apiKey);
}
