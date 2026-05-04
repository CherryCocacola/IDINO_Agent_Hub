using System.Text.RegularExpressions;
using System.Text.Json;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;

namespace AIAgentManagement.Services;

public class PiiDetectionService : IPiiDetectionService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<PiiDetectionService> _logger;
    private readonly IConfiguration _configuration;

    // 개인정보 감지 정규식 패턴
    private static readonly Dictionary<string, Regex> DetectionPatterns = new()
    {
        // 휴대폰 번호: 010-1234-5678, 01012345678, +82-10-1234-5678 등
        ["PhoneNumber"] = new Regex(@"(\+82[-.\s]?)?(0[1-9]{1,2}[-.\s]?)?([0-9]{3,4}[-.\s]?[0-9]{4})", RegexOptions.Compiled | RegexOptions.IgnoreCase),
        
        // 주민등록번호: 123456-1234567, 1234561234567
        ["ResidentNumber"] = new Regex(@"\b([0-9]{6}[-.\s]?[1-4][0-9]{6})\b", RegexOptions.Compiled),
        
        // 신용카드 번호: 1234-5678-9012-3456, 1234567890123456 (13-19자리)
        ["CreditCard"] = new Regex(@"\b([0-9]{4}[-.\s]?[0-9]{4}[-.\s]?[0-9]{4}[-.\s]?[0-9]{4})\b|\b([0-9]{13,19})\b", RegexOptions.Compiled),
        
        // 이메일 주소: user@example.com
        ["Email"] = new Regex(@"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", RegexOptions.Compiled),
        
        // 계좌번호: 123-456-789012, 123456789012 등
        ["AccountNumber"] = new Regex(@"\b([0-9]{3,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{6,})\b", RegexOptions.Compiled),
        
        // 운전면허번호: 12-34-567890-12 (한국 형식)
        ["DriverLicense"] = new Regex(@"\b([0-9]{2}[-.\s]?[0-9]{2}[-.\s]?[0-9]{6}[-.\s]?[0-9]{2})\b", RegexOptions.Compiled),
        
        // 여권번호: M12345678, A123456789 등 (한국 여권 형식)
        ["PassportNumber"] = new Regex(@"\b([A-Z]{1}[0-9]{8,9})\b", RegexOptions.Compiled),
        
        // 외국인등록번호: 123456-1234567-8 (13자리)
        ["AlienRegistrationNumber"] = new Regex(@"\b([0-9]{6}[-.\s]?[0-9]{7}[-.\s]?[0-9])\b", RegexOptions.Compiled)
    };

    public PiiDetectionService(
        AIAgentManagementDbContext context,
        ILogger<PiiDetectionService> logger,
        IConfiguration configuration)
    {
        _context = context;
        _logger = logger;
        _configuration = configuration;
    }

    public async Task<PiiDetectionResult> DetectPiiAsync(string message, List<string>? detectionTypes = null)
    {
        if (string.IsNullOrWhiteSpace(message))
        {
            return new PiiDetectionResult { HasPii = false, MaskedMessage = message };
        }

        var result = new PiiDetectionResult
        {
            HasPii = false,
            DetectedItems = new List<PiiDetectionItem>(),
            MaskedMessage = message
        };

        // 감지할 유형이 지정되지 않으면 기본값 사용
        var typesToDetect = detectionTypes ?? new List<string> { "PhoneNumber", "ResidentNumber", "CreditCard", "Email", "AccountNumber" };

        foreach (var type in typesToDetect)
        {
            if (!DetectionPatterns.TryGetValue(type, out var pattern))
                continue;

            var matches = pattern.Matches(message);
            foreach (Match match in matches)
            {
                if (!match.Success) continue;

                var originalValue = match.Value;
                var maskedValue = MaskPii(type, originalValue);

                result.DetectedItems.Add(new PiiDetectionItem
                {
                    Type = type,
                    OriginalValue = originalValue,
                    MaskedValue = maskedValue,
                    StartIndex = match.Index,
                    EndIndex = match.Index + match.Length
                });

                result.HasPii = true;
            }
        }

        // 마스킹 처리: 뒤에서부터 처리하여 인덱스 변경 방지
        if (result.HasPii)
        {
            var maskedMessage = message;
            foreach (var item in result.DetectedItems.OrderByDescending(x => x.StartIndex))
            {
                maskedMessage = maskedMessage.Substring(0, item.StartIndex) + item.MaskedValue + maskedMessage.Substring(item.EndIndex);
            }
            result.MaskedMessage = maskedMessage;
        }

        return await Task.FromResult(result);
    }

    private string MaskPii(string type, string value)
    {
        return type switch
        {
            "PhoneNumber" => MaskPhoneNumber(value),
            "ResidentNumber" => MaskResidentNumber(value),
            "CreditCard" => MaskCreditCard(value),
            "Email" => MaskEmail(value),
            "AccountNumber" => MaskAccountNumber(value),
            "DriverLicense" => MaskDriverLicense(value),
            "PassportNumber" => MaskPassportNumber(value),
            "AlienRegistrationNumber" => MaskAlienRegistrationNumber(value),
            _ => new string('*', value.Length)
        };
    }

    private string MaskPhoneNumber(string phone)
    {
        // 하이픈 제거
        var digits = Regex.Replace(phone, @"[-.\s]", "");
        
        // 국가코드 제거
        if (digits.StartsWith("82"))
            digits = digits.Substring(2);
        if (digits.StartsWith("+82"))
            digits = digits.Substring(3);

        // 01012345678 형식
        if (digits.Length >= 10)
        {
            var prefix = digits.Substring(0, 3); // 010
            var suffix = digits.Substring(digits.Length - 4); // 마지막 4자리
            var masked = prefix + new string('*', digits.Length - 7) + suffix;
            
            // 원본 형식 유지 (하이픈이 있었으면 복원)
            if (phone.Contains("-"))
                return masked.Insert(3, "-").Insert(masked.Length - 4, "-");
            return masked;
        }
        
        return new string('*', phone.Length);
    }

    private string MaskResidentNumber(string residentNumber)
    {
        // 하이픈 제거
        var digits = Regex.Replace(residentNumber, @"[-.\s]", "");
        
        if (digits.Length == 13)
        {
            // 앞 7자리는 유지, 나머지는 마스킹
            var prefix = digits.Substring(0, 7);
            var masked = prefix + new string('*', 6);
            
            // 원본 형식 유지
            if (residentNumber.Contains("-"))
                return masked.Insert(6, "-");
            return masked;
        }
        
        return new string('*', residentNumber.Length);
    }

    private string MaskCreditCard(string cardNumber)
    {
        // 하이픈 제거
        var digits = Regex.Replace(cardNumber, @"[-.\s]", "");
        
        if (digits.Length >= 13 && digits.Length <= 19)
        {
            // 앞 4자리와 마지막 4자리는 유지, 나머지는 마스킹
            var prefix = digits.Substring(0, 4);
            var suffix = digits.Substring(digits.Length - 4);
            var masked = prefix + new string('*', digits.Length - 8) + suffix;
            
            // 원본 형식 유지 (하이픈이 있었으면 복원)
            if (cardNumber.Contains("-"))
            {
                // 1234-5678-9012-3456 형식
                return masked.Insert(4, "-").Insert(9, "-").Insert(14, "-");
            }
            return masked;
        }
        
        return new string('*', cardNumber.Length);
    }

    private string MaskEmail(string email)
    {
        var parts = email.Split('@');
        if (parts.Length == 2)
        {
            var localPart = parts[0];
            var domain = parts[1];
            
            // 로컬 부분: 앞 2자리만 유지, 나머지는 마스킹
            var maskedLocal = localPart.Length > 2 
                ? localPart.Substring(0, 2) + new string('*', localPart.Length - 2)
                : new string('*', localPart.Length);
            
            return $"{maskedLocal}@{domain}";
        }
        
        return new string('*', email.Length);
    }

    private string MaskAccountNumber(string accountNumber)
    {
        // 하이픈 제거
        var digits = Regex.Replace(accountNumber, @"[-.\s]", "");
        
        if (digits.Length >= 10)
        {
            // 앞 3자리는 유지, 나머지는 마스킹
            var prefix = digits.Substring(0, 3);
            var masked = prefix + new string('*', digits.Length - 3);
            
            // 원본 형식 유지 (하이픈이 있었으면 복원)
            if (accountNumber.Contains("-"))
            {
                // 123-456-789012 형식
                return masked.Insert(3, "-").Insert(7, "-");
            }
            return masked;
        }
        
        return new string('*', accountNumber.Length);
    }

    private string MaskDriverLicense(string driverLicense)
    {
        // 하이픈 제거
        var digits = Regex.Replace(driverLicense, @"[-.\s]", "");
        
        if (digits.Length == 12)
        {
            // 12-34-567890-12 형식: 앞 4자리와 마지막 2자리는 유지, 나머지는 마스킹
            var prefix = digits.Substring(0, 4);
            var suffix = digits.Substring(digits.Length - 2);
            var masked = prefix + new string('*', digits.Length - 6) + suffix;
            
            // 원본 형식 유지
            if (driverLicense.Contains("-"))
            {
                return masked.Insert(2, "-").Insert(5, "-").Insert(12, "-");
            }
            return masked;
        }
        
        return new string('*', driverLicense.Length);
    }

    private string MaskPassportNumber(string passportNumber)
    {
        // 여권번호: M12345678 → M****5678 (앞 1자리와 마지막 4자리 유지)
        if (passportNumber.Length >= 5)
        {
            var prefix = passportNumber.Substring(0, 1);
            var suffix = passportNumber.Substring(passportNumber.Length - 4);
            return prefix + new string('*', passportNumber.Length - 5) + suffix;
        }
        
        return new string('*', passportNumber.Length);
    }

    private string MaskAlienRegistrationNumber(string alienNumber)
    {
        // 외국인등록번호: 123456-1234567-8 → 123456-1******-8
        // 하이픈 제거
        var digits = Regex.Replace(alienNumber, @"[-.\s]", "");
        
        if (digits.Length == 14)
        {
            // 앞 6자리와 마지막 1자리는 유지, 나머지는 마스킹
            var prefix = digits.Substring(0, 7); // 1234561
            var suffix = digits.Substring(digits.Length - 1);
            var masked = prefix + new string('*', digits.Length - 8) + suffix;
            
            // 원본 형식 유지
            if (alienNumber.Contains("-"))
            {
                return masked.Insert(6, "-").Insert(14, "-");
            }
            return masked;
        }
        
        return new string('*', alienNumber.Length);
    }

    public async Task<PiiProtectionSettings> GetGlobalSettingsAsync()
    {
        try
        {
            var enabledSetting = await _context.SystemSettings
                .FirstOrDefaultAsync(s => s.SettingKey == "PiiProtection.Enabled");
            
            var modeSetting = await _context.SystemSettings
                .FirstOrDefaultAsync(s => s.SettingKey == "PiiProtection.Mode");
            
            var typesSetting = await _context.SystemSettings
                .FirstOrDefaultAsync(s => s.SettingKey == "PiiProtection.DetectionTypes");

            var settings = new PiiProtectionSettings
            {
                Enabled = enabledSetting?.SettingValue?.ToLower() == "true" || enabledSetting == null, // 기본값 true
                Mode = modeSetting?.SettingValue ?? "Block", // 기본값 Block
                DetectionTypes = new List<string>()
            };

            if (typesSetting?.SettingValue != null)
            {
                try
                {
                    settings.DetectionTypes = JsonSerializer.Deserialize<List<string>>(typesSetting.SettingValue) 
                        ?? GetDefaultDetectionTypes();
                }
                catch
                {
                    settings.DetectionTypes = GetDefaultDetectionTypes();
                }
            }
            else
            {
                settings.DetectionTypes = GetDefaultDetectionTypes();
            }

            return settings;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting global PII protection settings");
            // 기본값 반환
            return new PiiProtectionSettings
            {
                Enabled = true,
                Mode = "Block",
                DetectionTypes = GetDefaultDetectionTypes()
            };
        }
    }

    private List<string> GetDefaultDetectionTypes()
    {
        return new List<string> 
        { 
            "PhoneNumber", 
            "ResidentNumber", 
            "CreditCard", 
            "Email", 
            "AccountNumber",
            "DriverLicense",
            "PassportNumber",
            "AlienRegistrationNumber"
        };
    }

    public async Task<PiiProtectionSettings> GetAgentSettingsAsync(int? agentId)
    {
        var globalSettings = await GetGlobalSettingsAsync();

        if (!agentId.HasValue)
        {
            return globalSettings;
        }

        try
        {
            var agent = await _context.Agents
                .AsNoTracking()
                .FirstOrDefaultAsync(a => a.AgentId == agentId.Value);

            if (agent == null)
            {
                return globalSettings;
            }

            // Agent의 PII 보호가 비활성화되어 있으면 비활성화 반환
            if (!agent.PiiProtectionEnabled)
            {
                return new PiiProtectionSettings
                {
                    Enabled = false,
                    Mode = globalSettings.Mode,
                    DetectionTypes = globalSettings.DetectionTypes
                };
            }

            // Agent의 모드가 설정되어 있으면 사용, 없으면 전역 설정 사용
            return new PiiProtectionSettings
            {
                Enabled = true,
                Mode = !string.IsNullOrEmpty(agent.PiiProtectionMode) ? agent.PiiProtectionMode : globalSettings.Mode,
                DetectionTypes = globalSettings.DetectionTypes
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting agent PII protection settings for AgentId: {AgentId}", agentId);
            return new PiiProtectionSettings
            {
                Enabled = true,
                Mode = "Block",
                DetectionTypes = GetDefaultDetectionTypes()
            };
        }
    }
}
