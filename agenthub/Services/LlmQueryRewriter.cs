using AIAgentManagement.DTOs;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Memory;
using System.Security.Cryptography;
using System.Text;

namespace AIAgentManagement.Services;

/// <summary>
/// IQueryRewriter 의 LLM 기반 구현체.
/// <para>
/// IAiProxyService 를 통해 OpenAI(또는 ApiServices 카탈로그의 다른 LLM) 호출.
/// EnableRag=false 로 호출하여 RagService 와의 순환 의존을 차단한다.
/// </para>
/// <para>
/// LLM 호출은 짧은 system + user 메시지(약 100~150 tokens) + max_tokens=120 로
/// 비용을 최소화한다. 응답은 줄 단위로 split 후 비어있지 않은 1~2건 사용.
/// </para>
/// </summary>
public sealed class LlmQueryRewriter : IQueryRewriter
{
    // 순환 의존성(AiProxyService → RagService → QueryRewriter → AiProxyService) 차단을
    // 위해 IAiProxyService 를 ctor 주입하지 않고 IServiceScopeFactory 로 매 호출 시 lazy 해결.
    private readonly IServiceScopeFactory _scopeFactory;
    private readonly IMemoryCache _cache;
    private readonly IConfiguration _configuration;
    private readonly IRagMetrics _ragMetrics;
    private readonly ILogger<LlmQueryRewriter> _logger;

    private static readonly TimeSpan CacheTtl = TimeSpan.FromMinutes(60);

    private const string SystemPrompt =
        "You are a multilingual search query rewriter. " +
        "Given the user's short search query, output up to 2 alternative queries that broaden the recall:\n" +
        "- If the input is Korean (한글), output the most natural English translation.\n" +
        "- If the input is English, output the most natural Korean translation.\n" +
        "- Preserve key entities (project names, places, technical terms).\n" +
        "- Output ONLY the rewritten queries, one per line. No numbering, no explanation, no quotes.\n" +
        "If the input is already mixed-language or no useful rewrite is possible, output a single empty line.";

    public LlmQueryRewriter(
        IServiceScopeFactory scopeFactory,
        IMemoryCache cache,
        IConfiguration configuration,
        IRagMetrics ragMetrics,
        ILogger<LlmQueryRewriter> logger)
    {
        _scopeFactory = scopeFactory;
        _cache = cache;
        _configuration = configuration;
        _ragMetrics = ragMetrics;
        _logger = logger;
    }

    public async Task<IReadOnlyList<string>> RewriteAsync(string query, CancellationToken cancellationToken = default)
    {
        var trimmed = (query ?? string.Empty).Trim();
        if (trimmed.Length == 0)
        {
            return Array.Empty<string>();
        }

        // 캐시 hit
        var cacheKey = $"qr:{Sha256Short(trimmed)}";
        if (_cache.TryGetValue<List<string>>(cacheKey, out var cached) && cached != null)
        {
            _ragMetrics.IncrementQueryRewriteCacheHit();
            return cached;
        }
        _ragMetrics.IncrementQueryRewriteCacheMiss();

        var result = new List<string> { trimmed };
        try
        {
            var serviceCode = _configuration["QueryRewriter:ServiceCode"] ?? "chatgpt";
            var model = _configuration["QueryRewriter:Model"] ?? "gpt-4o-mini";

            // IAiProxyService + DbContext 를 새 스코프에서 lazy 해결 (순환 의존 차단)
            using var scope = _scopeFactory.CreateScope();
            var sp = scope.ServiceProvider;
            var context = sp.GetRequiredService<Data.AIAgentManagementDbContext>();

            var service = await context.ApiServices
                .Where(s => s.ServiceCode == serviceCode && s.IsActive)
                .Select(s => new { s.ServiceId })
                .FirstOrDefaultAsync(cancellationToken);

            if (service == null)
            {
                _logger.LogWarning(
                    "QueryRewriter 비활성 — ApiService '{Code}' 미등록 또는 비활성. 원본 query 만 반환.",
                    serviceCode);
                return CacheAndReturn(cacheKey, result);
            }

            var aiRequest = new ChatMessageRequestDto
            {
                Messages = new List<ChatMessageDto>
                {
                    new() { Role = "system", Content = SystemPrompt },
                    new() { Role = "user", Content = trimmed }
                },
                Temperature = 0.0m,
                MaxTokens = 120,
                EnableRag = false,           // 순환 의존 차단(런타임 RAG 호출 안 함)
                EnableWebSearch = false,
                EnableDeepResearch = false,
                Stream = false,
                Language = "auto",
            };

            var aiProxy = sp.GetRequiredService<IAiProxyService>();
            // LLM 호출 시도 카운터 — 실패 catch 분기에서 별도 IncrementQueryRewriteFailure() 호출.
            _ragMetrics.IncrementQueryRewriteCall();
            var aiResponse = await aiProxy.SendChatMessageAsync(
                service.ServiceId, model, aiRequest, cancellationToken);

            var rewrittenLines = (aiResponse.Content ?? string.Empty)
                .Split('\n', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
                .Where(line => !string.IsNullOrWhiteSpace(line)
                    && !string.Equals(line, trimmed, StringComparison.OrdinalIgnoreCase))
                .Take(2)
                .ToList();

            result.AddRange(rewrittenLines);

            _logger.LogInformation(
                "QueryRewriter PASS — 원본 '{Original}' → +{Count}건 추가 ({Rewrites})",
                trimmed.Length > 60 ? trimmed[..60] + "..." : trimmed,
                rewrittenLines.Count,
                string.Join(" | ", rewrittenLines.Select(s => s.Length > 40 ? s[..40] + "..." : s)));
        }
        catch (Exception ex)
        {
            // RAG 검색 자체는 계속 진행하도록 graceful 폴백
            _ragMetrics.IncrementQueryRewriteFailure();
            _logger.LogWarning(ex, "QueryRewriter 실패 — 원본 query 만 사용");
        }

        return CacheAndReturn(cacheKey, result);
    }

    private List<string> CacheAndReturn(string cacheKey, List<string> result)
    {
        _cache.Set(cacheKey, result, CacheTtl);
        return result;
    }

    private static string Sha256Short(string input)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(input));
        return Convert.ToHexString(bytes, 0, 8);
    }
}
