namespace AIAgentManagement.DTOs;

public class UpdatePiiProtectionSettingsRequestDto
{
    public bool Enabled { get; set; } = true;
    public string Mode { get; set; } = "Block"; // "Block" or "Mask"
    public List<string>? DetectionTypes { get; set; }
}
