using AIAgentManagement.DTOs;

namespace AIAgentManagement.Exceptions;

/// <summary>
/// 개인정보가 포함된 메시지에 대한 예외
/// </summary>
public class PiiDetectionException : InvalidOperationException
{
    public PiiDetectionResult DetectionResult { get; }
    public List<string> DetectedTypes { get; }

    public PiiDetectionException(PiiDetectionResult detectionResult, List<string> detectedTypes) 
        : base($"메시지에 개인정보가 포함되어 있습니다: {string.Join(", ", detectedTypes)}")
    {
        DetectionResult = detectionResult;
        DetectedTypes = detectedTypes;
    }
}
