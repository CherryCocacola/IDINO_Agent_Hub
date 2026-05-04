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
}
