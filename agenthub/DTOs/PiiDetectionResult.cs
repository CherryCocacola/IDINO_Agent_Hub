namespace AIAgentManagement.DTOs;

public class PiiDetectionResult
{
    public bool HasPii { get; set; }
    public List<PiiDetectionItem> DetectedItems { get; set; } = new();
    public string MaskedMessage { get; set; } = string.Empty;
}

public class PiiDetectionItem
{
    public string Type { get; set; } = string.Empty; // PhoneNumber, ResidentNumber, CreditCard, Email, AccountNumber
    public string OriginalValue { get; set; } = string.Empty;
    public string MaskedValue { get; set; } = string.Empty;
    public int StartIndex { get; set; }
    public int EndIndex { get; set; }
}

public class PiiProtectionSettings
{
    public bool Enabled { get; set; } = true;
    public string Mode { get; set; } = "Block"; // "Block" or "Mask"
    public List<string> DetectionTypes { get; set; } = new() { "PhoneNumber", "ResidentNumber", "CreditCard", "Email", "AccountNumber" };
}
