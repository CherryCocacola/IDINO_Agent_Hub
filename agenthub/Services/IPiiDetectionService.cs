using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IPiiDetectionService
{
    Task<PiiDetectionResult> DetectPiiAsync(string message, List<string>? detectionTypes = null);
    Task<PiiProtectionSettings> GetGlobalSettingsAsync();
    Task<PiiProtectionSettings> GetAgentSettingsAsync(int? agentId);
}
