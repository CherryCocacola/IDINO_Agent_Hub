using AIAgentManagement.Settings;

namespace AIAgentManagement.Services;

/// <summary>
/// 시스템 설정 관리 서비스 인터페이스
/// </summary>
public interface ISystemSettingsService
{
    /// <summary>
    /// PII 보호 설정 조회
    /// </summary>
    Task<PiiProtectionSettingsConfig> GetPiiProtectionSettingsAsync();

    /// <summary>
    /// PII 보호 설정 업데이트
    /// </summary>
    Task UpdatePiiProtectionSettingsAsync(PiiProtectionSettingsConfig settings);

    /// <summary>
    /// 설정 값 조회 (제네릭)
    /// </summary>
    Task<T?> GetSettingAsync<T>(string key, T? defaultValue = default) where T : class;

    /// <summary>
    /// 설정 값 저장 (제네릭)
    /// </summary>
    Task SetSettingAsync<T>(string key, T value, string dataType = "JSON", string? category = null, string? description = null);
}
