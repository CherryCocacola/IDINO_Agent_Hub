using System.Text.Json.Serialization;

namespace AIAgentManagement.Settings;

/// <summary>
/// PII 보호 설정을 위한 강타입 클래스
/// </summary>
public class PiiProtectionSettingsConfig
{
    [JsonPropertyName("enabled")]
    public bool Enabled { get; set; } = true;

    [JsonPropertyName("mode")]
    public string Mode { get; set; } = "Block"; // "Block" or "Mask"

    [JsonPropertyName("detectionTypes")]
    public List<string> DetectionTypes { get; set; } = new()
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

    /// <summary>
    /// 기본값 반환
    /// </summary>
    public static PiiProtectionSettingsConfig Default => new();
}
