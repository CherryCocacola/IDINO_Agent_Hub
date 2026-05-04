namespace AIAgentManagement.Exceptions;

/// <summary>
/// 금칙어가 포함된 메시지에 대한 예외
/// </summary>
public class BannedWordException : InvalidOperationException
{
    public List<string> BlockedWords { get; }

    public BannedWordException(List<string> blockedWords) 
        : base($"메시지에 금칙어가 포함되어 있습니다: {string.Join(", ", blockedWords)}")
    {
        BlockedWords = blockedWords;
    }
}
