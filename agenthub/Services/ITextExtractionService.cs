namespace AIAgentManagement.Services;

public interface ITextExtractionService
{
    /// <summary>URL에서 HTML 등을 가져와 본문 텍스트만 추출합니다.</summary>
    Task<string> ExtractTextFromUrlAsync(string url, CancellationToken cancellationToken = default);
}
