using System.Text.RegularExpressions;

namespace AIAgentManagement.Services;

public class TextExtractionService : ITextExtractionService
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<TextExtractionService> _logger;

    public TextExtractionService(IHttpClientFactory httpClientFactory, ILogger<TextExtractionService> logger)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;
    }

    public async Task<string> ExtractTextFromUrlAsync(string url, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(url))
            return string.Empty;

        try
        {
            var client = _httpClientFactory.CreateClient();
            client.Timeout = TimeSpan.FromSeconds(15);
            client.DefaultRequestHeaders.TryAddWithoutValidation("User-Agent", "Mozilla/5.0 (compatible; PresentationBuilder/1.0)");
            var response = await client.GetAsync(url, cancellationToken);
            response.EnsureSuccessStatusCode();
            var html = await response.Content.ReadAsStringAsync(cancellationToken);
            return StripHtmlToText(html);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to extract text from URL: {Url}", url);
            throw new InvalidOperationException($"URL에서 텍스트를 가져올 수 없습니다: {ex.Message}", ex);
        }
    }

    private static string StripHtmlToText(string html)
    {
        if (string.IsNullOrEmpty(html))
            return string.Empty;

        // script, style 제거
        html = Regex.Replace(html, @"<script[^>]*>[\s\S]*?</script>", " ", RegexOptions.IgnoreCase);
        html = Regex.Replace(html, @"<style[^>]*>[\s\S]*?</style>", " ", RegexOptions.IgnoreCase);
        // 태그 제거
        html = Regex.Replace(html, @"<[^>]+>", " ");
        // HTML 엔티티 복원
        html = System.Net.WebUtility.HtmlDecode(html);
        // 연속 공백/줄바꿈 정리
        html = Regex.Replace(html, @"\s+", " ");
        return html.Trim();
    }
}
