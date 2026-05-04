using System.Text.Json;
using AIAgentManagement.Data;
using AIAgentManagement.Models;
using AIAgentManagement.Settings;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

/// <summary>
/// 시스템 설정 관리 서비스 구현
/// </summary>
public class SystemSettingsService : ISystemSettingsService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<SystemSettingsService> _logger;

    public SystemSettingsService(
        AIAgentManagementDbContext context,
        ILogger<SystemSettingsService> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<PiiProtectionSettingsConfig> GetPiiProtectionSettingsAsync()
    {
        try
        {
            var enabledSetting = await _context.SystemSettings
                .FirstOrDefaultAsync(s => s.SettingKey == "PiiProtection.Enabled");
            
            var modeSetting = await _context.SystemSettings
                .FirstOrDefaultAsync(s => s.SettingKey == "PiiProtection.Mode");
            
            var typesSetting = await _context.SystemSettings
                .FirstOrDefaultAsync(s => s.SettingKey == "PiiProtection.DetectionTypes");

            var settings = new PiiProtectionSettingsConfig
            {
                Enabled = enabledSetting?.SettingValue?.ToLower() == "true" || enabledSetting == null,
                Mode = modeSetting?.SettingValue ?? "Block",
                DetectionTypes = new List<string>()
            };

            if (typesSetting?.SettingValue != null)
            {
                try
                {
                    settings.DetectionTypes = JsonSerializer.Deserialize<List<string>>(typesSetting.SettingValue) 
                        ?? PiiProtectionSettingsConfig.Default.DetectionTypes;
                }
                catch (JsonException ex)
                {
                    _logger.LogWarning(ex, "Failed to deserialize PiiProtection.DetectionTypes, using default");
                    settings.DetectionTypes = PiiProtectionSettingsConfig.Default.DetectionTypes;
                }
            }
            else
            {
                settings.DetectionTypes = PiiProtectionSettingsConfig.Default.DetectionTypes;
            }

            return settings;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving PII protection settings");
            return PiiProtectionSettingsConfig.Default;
        }
    }

    public async Task UpdatePiiProtectionSettingsAsync(PiiProtectionSettingsConfig settings)
    {
        try
        {
            // Enabled 설정 업데이트
            var enabledSetting = await _context.SystemSettings
                .FirstOrDefaultAsync(s => s.SettingKey == "PiiProtection.Enabled");
            
            if (enabledSetting == null)
            {
                enabledSetting = new SystemSetting
                {
                    SettingKey = "PiiProtection.Enabled",
                    SettingValue = settings.Enabled.ToString(),
                    DataType = "Boolean",
                    Category = "Privacy",
                    Description = "개인정보 보호 활성화 여부",
                    IsEncrypted = false,
                    CreatedAt = DateTime.UtcNow,
                    UpdatedAt = DateTime.UtcNow
                };
                _context.SystemSettings.Add(enabledSetting);
            }
            else
            {
                enabledSetting.SettingValue = settings.Enabled.ToString();
                enabledSetting.UpdatedAt = DateTime.UtcNow;
            }

            // Mode 설정 업데이트
            var modeSetting = await _context.SystemSettings
                .FirstOrDefaultAsync(s => s.SettingKey == "PiiProtection.Mode");
            
            if (modeSetting == null)
            {
                modeSetting = new SystemSetting
                {
                    SettingKey = "PiiProtection.Mode",
                    SettingValue = settings.Mode,
                    DataType = "String",
                    Category = "Privacy",
                    Description = "개인정보 보호 모드 (Block 또는 Mask)",
                    IsEncrypted = false,
                    CreatedAt = DateTime.UtcNow,
                    UpdatedAt = DateTime.UtcNow
                };
                _context.SystemSettings.Add(modeSetting);
            }
            else
            {
                modeSetting.SettingValue = settings.Mode;
                modeSetting.UpdatedAt = DateTime.UtcNow;
            }

            // DetectionTypes 설정 업데이트
            var typesSetting = await _context.SystemSettings
                .FirstOrDefaultAsync(s => s.SettingKey == "PiiProtection.DetectionTypes");
            
            var typesJson = JsonSerializer.Serialize(settings.DetectionTypes);
            
            if (typesSetting == null)
            {
                typesSetting = new SystemSetting
                {
                    SettingKey = "PiiProtection.DetectionTypes",
                    SettingValue = typesJson,
                    DataType = "JSON",
                    Category = "Privacy",
                    Description = "감지할 개인정보 유형 목록 (JSON 배열)",
                    IsEncrypted = false,
                    CreatedAt = DateTime.UtcNow,
                    UpdatedAt = DateTime.UtcNow
                };
                _context.SystemSettings.Add(typesSetting);
            }
            else
            {
                typesSetting.SettingValue = typesJson;
                typesSetting.UpdatedAt = DateTime.UtcNow;
            }

            await _context.SaveChangesAsync();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating PII protection settings");
            throw;
        }
    }

    public async Task<T?> GetSettingAsync<T>(string key, T? defaultValue = default) where T : class
    {
        try
        {
            var setting = await _context.SystemSettings
                .FirstOrDefaultAsync(s => s.SettingKey == key);

            if (setting?.SettingValue == null)
            {
                return defaultValue;
            }

            return JsonSerializer.Deserialize<T>(setting.SettingValue) ?? defaultValue;
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Error retrieving setting {Key}, returning default", key);
            return defaultValue;
        }
    }

    public async Task SetSettingAsync<T>(string key, T value, string dataType = "JSON", string? category = null, string? description = null)
    {
        try
        {
            var setting = await _context.SystemSettings
                .FirstOrDefaultAsync(s => s.SettingKey == key);

            var valueJson = JsonSerializer.Serialize(value);

            if (setting == null)
            {
                setting = new SystemSetting
                {
                    SettingKey = key,
                    SettingValue = valueJson,
                    DataType = dataType,
                    Category = category,
                    Description = description,
                    IsEncrypted = false,
                    CreatedAt = DateTime.UtcNow,
                    UpdatedAt = DateTime.UtcNow
                };
                _context.SystemSettings.Add(setting);
            }
            else
            {
                setting.SettingValue = valueJson;
                setting.DataType = dataType;
                setting.Category = category;
                setting.Description = description;
                setting.UpdatedAt = DateTime.UtcNow;
            }

            await _context.SaveChangesAsync();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error saving setting {Key}", key);
            throw;
        }
    }
}
