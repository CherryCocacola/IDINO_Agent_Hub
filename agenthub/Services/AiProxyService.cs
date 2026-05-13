using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Net.Http;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

public class AiProxyService : IAiProxyService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly IConfiguration _configuration;
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<AiProxyService> _logger;
    private readonly IRagService? _ragService;
    private readonly IApiKeyPoolService? _apiKeyPool;
    // Phase 5.2 — ADR-1 옵션 B 의 Nexus 사내 LLM 클라이언트.
    // null 허용은 Phase 5.1 등록(Program.cs) 이전의 단위 테스트 호환성을 위한 것이며,
    // 운영 환경에서는 항상 NexusClient 가 주입된다.
    private readonly INexusClient? _nexusClient;

    public AiProxyService(
        AIAgentManagementDbContext context,
        IConfiguration configuration,
        IHttpClientFactory httpClientFactory,
        ILogger<AiProxyService> logger,
        IRagService? ragService = null,
        IApiKeyPoolService? apiKeyPool = null,
        INexusClient? nexusClient = null)
    {
        _context = context;
        _configuration = configuration;
        _httpClientFactory = httpClientFactory;
        _logger = logger;
        _ragService = ragService;
        _apiKeyPool = apiKeyPool;
        _nexusClient = nexusClient;
    }

    // ── API 키 헬퍼: 풀 → 설정 순으로 키를 가져옵니다 ────────────────────────
    private string? GetApiKey(string provider, string configPath)
    {
        // 1순위: ApiKeyPoolService (다중 키 라운드로빈)
        var poolKey = _apiKeyPool?.GetNextKey(provider);
        if (!string.IsNullOrWhiteSpace(poolKey)) return poolKey;

        // 2순위: appsettings.json 단일 키 (폴백)
        return _configuration[configPath];
    }

    public async Task<AiResponseDto> SendChatMessageAsync(int serviceId, string model, ChatMessageRequestDto request, CancellationToken cancellationToken = default)
    {
        var service = await _context.ApiServices.FindAsync([serviceId], cancellationToken);
        if (service == null || !service.IsActive)
        {
            throw new InvalidOperationException($"Service {serviceId} not found or inactive");
        }

        var startTime = DateTime.UtcNow;

        // RAG가 활성화된 경우 문서 검색 수행 (모든 서비스에서 공통으로 실행)
        _logger.LogInformation("RAG check in SendChatMessageAsync: EnableRag={EnableRag}, RagService={RagService}, DocumentIds={DocumentIds}", 
            request.EnableRag, 
            _ragService != null ? "available" : "null",
            request.DocumentIds != null ? string.Join(", ", request.DocumentIds) : "null");
        
        if (request.EnableRag && _ragService != null)
        {
            var lastUserMessage = request.Messages.LastOrDefault(m => m.Role == "user");
            if (lastUserMessage != null)
            {
                // 사용자 메시지의 텍스트 추출
                string? queryText = null;
                if (!string.IsNullOrWhiteSpace(lastUserMessage.Content))
                {
                    queryText = lastUserMessage.Content;
                }
                else if (lastUserMessage.Contents != null && lastUserMessage.Contents.Count > 0)
                {
                    // 멀티모달 콘텐츠에서 텍스트 부분 추출
                    var textContents = lastUserMessage.Contents
                        .Where(c => c.Type.ToLower() == "text" && !string.IsNullOrWhiteSpace(c.Text))
                        .Select(c => c.Text)
                        .ToList();
                    if (textContents.Any())
                    {
                        queryText = string.Join("\n", textContents);
                    }
                }

                if (string.IsNullOrWhiteSpace(queryText))
                {
                    _logger.LogWarning("RAG enabled but queryText is empty. Cannot perform RAG search.");
                }

                if (!string.IsNullOrWhiteSpace(queryText))
                {
                    try
                    {
                        _logger.LogInformation("RAG search starting. EnableRag: {EnableRag}, Query: {Query}, DocumentIds: {DocumentIds}, UserId: {UserId}, AgentId: {AgentId}", 
                            request.EnableRag, 
                            queryText.Length > 100 ? queryText.Substring(0, 100) + "..." : queryText,
                            request.DocumentIds != null ? string.Join(", ", request.DocumentIds) : "null",
                            request.UserId,
                            request.AgentId);
                        
                        var topK = request.RagTopK ?? 3;
                        var ragResults = await _ragService.RetrieveAsync(queryText, topK, request.UserId, request.AgentId, request.DocumentIds, cancellationToken);
                        
                        if (ragResults != null && ragResults.Count > 0)
                        {
                            // RAG 검색 결과 포맷팅
                            var ragLabel = request.Language?.ToLower() == "ko" 
                                ? "[지식 기반 문서 검색 결과]"
                                : "[Knowledge Base Search Results]";
                            var ragNote = request.Language?.ToLower() == "ko" 
                                ? request.EnableDeepResearch
                                    ? "위 문서 검색 결과를 웹 검색 결과와 함께 종합적으로 분석하여 답변해주세요."
                                    : "위 문서 내용을 참고하여 답변해주세요. 문서에 없는 정보는 일반 지식으로 보완해도 됩니다."
                                : request.EnableDeepResearch
                                    ? "Please comprehensively analyze the above document search results together with web search results when answering."
                                    : "Please refer to the above document content when answering. You may supplement with general knowledge if the documents do not contain the information.";
                            
                            const int maxChunkLength = 800;
                            var ragContextParts = new List<string> { ragLabel };
                            for (int i = 0; i < ragResults.Count; i++)
                            {
                                var result = ragResults[i];
                                var sourceLabel = request.Language?.ToLower() == "ko" 
                                    ? $"출처 {i + 1}: {result.Title} (유사도: {result.Similarity:F2})"
                                    : $"Source {i + 1}: {result.Title} (Similarity: {result.Similarity:F2})";
                                // 토큰 과부하 방지: 청크 내용을 최대 800자로 절단
                                var truncatedContent = result.Content?.Length > maxChunkLength
                                    ? result.Content.Substring(0, maxChunkLength) + "..."
                                    : result.Content ?? "";
                                ragContextParts.Add($"\n{sourceLabel}\n{truncatedContent}");
                            }
                            ragContextParts.Add($"\n{ragNote}");
                            var ragContext = string.Join("\n", ragContextParts);
                            
                            // request.Messages에 직접 추가 (모든 서비스에서 사용)
                            var existingSystemMessage = request.Messages.FirstOrDefault(m => m.Role == "system");
                            if (existingSystemMessage != null)
                            {
                                // 기존 시스템 메시지에 RAG 검색 결과 추가
                                existingSystemMessage.Content = (existingSystemMessage.Content ?? "") + "\n\n" + ragContext;
                            }
                            else
                            {
                                // 기본 시스템 메시지
                                var defaultSystemMessage = request.Language?.ToLower() == "ko"
                                    ? """
당신은 전문적이고 친절한 AI 어시스턴트입니다.

## 응답 원칙
- 답변은 **마크다운 형식**으로 작성하세요. 제목(##), 굵게(**), 목록(-), 코드블록(```) 등을 적극 활용하세요.
- 복잡한 내용은 단계별로 나눠 설명하고, 핵심 정보는 표나 목록으로 정리하세요.
- 예시나 비교가 필요한 경우 구체적인 사례를 들어 설명하세요.
- 답변 길이는 질문의 복잡도에 맞게 조절하세요. 간단한 질문엔 간결하게, 복잡한 질문엔 충분히 상세하게 답하세요.
- 확실하지 않은 정보는 추측임을 명시하고, 필요 시 추가 확인을 권장하세요.
"""
                                    : """
You are a professional and helpful AI assistant.

## Response Guidelines
- Use **Markdown formatting** in your responses: headings (##), bold (**), lists (-), code blocks (```), etc.
- For complex topics, break explanations into clear steps and organize key information in tables or lists.
- Provide concrete examples or comparisons when helpful.
- Match response length to question complexity — concise for simple questions, detailed for complex ones.
- Clearly indicate when information is uncertain, and suggest verification when needed.
""";
                                // 새로운 시스템 메시지를 request.Messages에 추가
                                request.Messages.Insert(0, new ChatMessageDto
                                {
                                    Role = "system",
                                    Content = defaultSystemMessage + "\n\n" + ragContext
                                });
                            }
                            
                            _logger.LogInformation("RAG search completed and added to request.Messages. Found {Count} relevant chunks. DocumentIds: {DocumentIds}", 
                                ragResults.Count, 
                                request.DocumentIds != null ? string.Join(", ", request.DocumentIds) : "null");
                            
                            // RAG 컨텍스트가 제대로 포함되었는지 로깅
                            var ragContextPreview = ragContext.Length > 200 ? ragContext.Substring(0, 200) + "..." : ragContext;
                            _logger.LogDebug("RAG context preview: {Preview}", ragContextPreview);
                            
                            // request.Messages의 첫 번째 메시지 확인
                            var firstMsg = request.Messages.FirstOrDefault();
                            if (firstMsg != null && firstMsg.Role == "system")
                            {
                                var systemContentPreview = firstMsg.Content?.Length > 300 ? firstMsg.Content.Substring(0, 300) + "..." : firstMsg.Content;
                                _logger.LogDebug("System message in request.Messages preview: {Preview}", systemContentPreview);
                            }
                        }
                        else
                        {
                            _logger.LogWarning("RAG search completed but no relevant documents found. Query: {Query}, DocumentIds: {DocumentIds}, UserId: {UserId}, AgentId: {AgentId}", 
                                queryText, 
                                request.DocumentIds != null ? string.Join(", ", request.DocumentIds) : "null",
                                request.UserId,
                                request.AgentId);
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning(ex, "RAG search failed, continuing without RAG context");
                        // 검색 실패해도 계속 진행
                    }
                }
            }
        }

        try
        {
            return service.ServiceCode.ToLower() switch
            {
                "chatgpt" or "openai" => await CallOpenAiAsync(service, model, request, cancellationToken),
                "claude" or "anthropic" => await CallClaudeAsync(service, model, request, cancellationToken),
                "gemini" or "google" => await CallGeminiAsync(service, model, request, cancellationToken),
                "perplexity" => await CallPerplexityAsync(service, model, request, cancellationToken),
                "mistral" => await CallMistralAsync(service, model, request, cancellationToken),
                "copilot" => await CallAzureOpenAiAsync(service, model, request, cancellationToken), // Microsoft Copilot (Azure OpenAI)
                "cursor" => await CallCopilotAsync(service, model, request, cancellationToken), // GitHub Copilot API
                "azure-openai" or "microsoft-copilot" => await CallAzureOpenAiAsync(service, model, request, cancellationToken),
                // Phase 5.2 — Nexus 사내 LLM (ADR-1 옵션 B). 변환 어댑터 없이 네이티브 /v1/chat 호출.
                "nexus" => await CallNexusAsync(service, model, request, cancellationToken),
                _ => throw new NotSupportedException($"Service {service.ServiceCode} is not supported")
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calling AI service {ServiceCode}", service.ServiceCode);
            throw;
        }
    }

    [Obsolete("Use SendChatMessageStreamChunksAsync. This method bypasses ApiKeyPool/Cooldown and does not guarantee real-time streaming.")]
    public async Task<Stream> SendChatMessageStreamAsync(int serviceId, string model, ChatMessageRequestDto request, CancellationToken cancellationToken = default)
    {
        var service = await _context.ApiServices.FindAsync([serviceId], cancellationToken);
        if (service == null || !service.IsActive)
        {
            throw new InvalidOperationException($"Service {serviceId} not found or inactive");
        }

        return service.ServiceCode.ToLower() switch
        {
            "chatgpt" or "openai" => await CallOpenAiStreamAsync(service, model, request, cancellationToken),
            "claude" or "anthropic" => await CallClaudeStreamAsync(service, model, request, cancellationToken),
            "gemini" or "google" => await CallGeminiStreamAsync(service, model, request, cancellationToken),
            "perplexity" => await CallPerplexityStreamAsync(service, model, request, cancellationToken),
            "mistral" => await CallMistralStreamAsync(service, model, request, cancellationToken),
            "copilot" => await CallAzureOpenAiStreamAsync(service, model, request, cancellationToken), // Microsoft Copilot (Azure OpenAI)
            "cursor" => await CallCopilotStreamAsync(service, model, request, cancellationToken), // GitHub Copilot API
            "azure-openai" or "microsoft-copilot" => await CallAzureOpenAiStreamAsync(service, model, request, cancellationToken),
            _ => throw new NotSupportedException($"Service {service.ServiceCode} is not supported")
        };
    }

    // ════════════════════════════════════════════════════════════════════════════
    // 진짜 SSE 스트리밍 — IAsyncEnumerable<ChatChunk> 기반 (TECHSPEC §15.4 / §16 C9 / H5)
    // ════════════════════════════════════════════════════════════════════════════
    public async IAsyncEnumerable<ChatChunk> SendChatMessageStreamChunksAsync(
        int serviceId,
        string model,
        ChatMessageRequestDto request,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var service = await _context.ApiServices.FindAsync([serviceId], cancellationToken);
        if (service == null || !service.IsActive)
        {
            throw new InvalidOperationException($"Service {serviceId} not found or inactive");
        }

        var providerCode = service.ServiceCode.ToLowerInvariant();

        // OpenAI native streaming — chunk 단위 yield
        if (providerCode is "chatgpt" or "openai")
        {
            await foreach (var chunk in StreamOpenAiChunksAsync(service, model, request, cancellationToken)
                .WithCancellation(cancellationToken))
            {
                yield return chunk;
            }
            yield break;
        }

        // Phase 5.2 — Nexus 진짜 SSE 스트리밍 (ADR-1 옵션 B).
        // Nexus 의 /v1/chat/stream 은 4-Tier AsyncGenerator 체인을 SSE 로 직접 발행하므로
        // 비스트리밍 폴백이 아닌 native stream 을 그대로 전달한다.
        if (providerCode == "nexus")
        {
            await foreach (var chunk in StreamNexusChunksAsync(service, model, request, cancellationToken)
                .WithCancellation(cancellationToken))
            {
                yield return chunk;
            }
            yield break;
        }

        // TODO (Phase 5+): claude / gemini / perplexity / mistral / copilot / azure-openai 의
        // native streaming 응답 파서를 각각 구현. SSE 또는 line-delimited JSON 포맷이 provider별로 다름:
        //   - Anthropic: event-stream with `event: content_block_delta` etc.
        //   - Google Gemini: line-delimited JSON via streamGenerateContent endpoint
        //   - Perplexity / Mistral / Azure OpenAI: OpenAI 호환 SSE
        //   - GitHub Copilot: 자체 포맷
        // 본 단계에서는 비스트리밍 호출 결과를 단일 chunk로 폴백하여 yield 합니다(가짜 SSE 위장보다 정직).
        var nonStreaming = await SendChatMessageAsync(serviceId, model, request, cancellationToken);
        if (!string.IsNullOrEmpty(nonStreaming.Content))
        {
            yield return ChatChunk.Delta(nonStreaming.Content);
        }
        if (nonStreaming.TotalTokens > 0)
        {
            yield return ChatChunk.Usage(nonStreaming.PromptTokens, nonStreaming.CompletionTokens, nonStreaming.TotalTokens);
        }
        yield return ChatChunk.Stop(string.IsNullOrEmpty(nonStreaming.FinishReason) ? "stop" : nonStreaming.FinishReason);
    }

    /// <summary>
    /// OpenAI /v1/chat/completions 의 stream:true 응답을 파싱하여 ChatChunk 단위로 yield.
    /// stream_options.include_usage:true 로 마지막 chunk에 usage 동봉을 요청합니다.
    /// HttpCompletionOption.ResponseHeadersRead 로 즉시 헤더만 받고 본문은 chunk 단위로 흘립니다.
    /// ApiKeyPool 라운드로빈 + 429 Cooldown 적용(H5 해결).
    ///
    /// 한계 (Phase 5+ 정식 처리):
    /// - 본 메서드는 RAG / 웹검색 / DeepResearch 를 처리하지 않습니다(SendChatMessageAsync 의 흐름과 미동기화).
    ///   현재 streaming이 활성화되면 RAG 컨텍스트 주입이 누락됩니다.
    ///   Phase 5에서 RAG 컨텍스트 주입을 streaming 진입 직전 별도 단계로 분리하여 양 경로에서 공유할 예정.
    /// - 멀티모달(image_url): H3(5-3) 해소 — Contents 가 있으면 OpenAI Vision payload(content parts 배열)
    ///   로 변환하여 streaming 모델도 이미지를 인식하도록 한다. CallOpenAiAsync 와 동일한 변환 로직 사용.
    /// </summary>
    private async IAsyncEnumerable<ChatChunk> StreamOpenAiChunksAsync(
        ApiService service,
        string model,
        ChatMessageRequestDto request,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("openai", "AiApiSettings:OpenAI:ApiKey");
        var baseUrl = _configuration["AiApiSettings:OpenAI:BaseUrl"] ?? "https://api.openai.com/v1";

        if (string.IsNullOrEmpty(apiKey))
        {
            _logger.LogError("OpenAI API key is not configured (streaming)");
            throw new InvalidOperationException("OpenAI API key is not configured");
        }

        // 언어 지시 추가 (CallOpenAiAsync 와 동일 흐름)
        var messagesWithLanguage = AddLanguageInstruction(request.Messages.ToList(), request.Language);

        // H3(5-3) — Contents(멀티모달) 가 있는 메시지는 OpenAI Vision payload 로 변환.
        // 없으면 기존처럼 단일 텍스트 string content 로 유지(토큰/회귀 최소화).
        var messages = BuildOpenAiMessagesWithVision(messagesWithLanguage, model);

        var modelLower = model.ToLowerInvariant();
        var usesCompletionTokens = modelLower.StartsWith("o1") || modelLower.StartsWith("o3") || modelLower.StartsWith("gpt-5");
        var payloadDict = new Dictionary<string, object>
        {
            ["model"] = model,
            ["messages"] = messages,
            ["stream"] = true,
            // 마지막 chunk에 usage 정보 포함 — 가짜 SSE의 0.65 추정값 제거(C9 / D 항목)
            ["stream_options"] = new { include_usage = true }
        };

        if (usesCompletionTokens)
        {
            if (request.MaxTokens.HasValue) payloadDict["max_completion_tokens"] = request.MaxTokens.Value;
        }
        else
        {
            if (request.Temperature.HasValue) payloadDict["temperature"] = request.Temperature.Value;
            if (request.MaxTokens.HasValue) payloadDict["max_tokens"] = request.MaxTokens.Value;
        }

        var json = JsonSerializer.Serialize(payloadDict);

        var client = _httpClientFactory.CreateClient("openai");
        using var httpRequest = new HttpRequestMessage(HttpMethod.Post, $"{baseUrl}/chat/completions")
        {
            Content = new StringContent(json, Encoding.UTF8, "application/json")
        };
        httpRequest.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);

        // 핵심: ResponseHeadersRead — 본문 전체를 받기 전에 stream을 사용 가능
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseHeadersRead, cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            var errorBody = await response.Content.ReadAsStringAsync(cancellationToken);
            _logger.LogError("OpenAI streaming API error. Status: {StatusCode}, Response: {Response}, Model={Model}",
                response.StatusCode, errorBody, model);

            if (response.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
            {
                _apiKeyPool?.MarkAsCoolingDown("openai", apiKey ?? string.Empty);
                throw new HttpRequestException($"OpenAI API 429 Too Many Requests - {errorBody}", null, response.StatusCode);
            }

            throw new InvalidOperationException($"OpenAI streaming API error: {response.StatusCode} - {errorBody}");
        }

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        using var reader = new StreamReader(stream, Encoding.UTF8);

        var jsonOptions = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };

        while (!reader.EndOfStream && !cancellationToken.IsCancellationRequested)
        {
            var line = await reader.ReadLineAsync(cancellationToken);
            if (line == null) break;
            if (line.Length == 0) continue;
            if (!line.StartsWith("data:", StringComparison.Ordinal)) continue;

            // "data: {...}" 또는 "data: [DONE]"
            var payload = line.Substring(5).TrimStart();
            if (payload.Length == 0) continue;
            if (payload == "[DONE]")
            {
                yield break;
            }

            OpenAiStreamChunk? parsed = null;
            try
            {
                parsed = JsonSerializer.Deserialize<OpenAiStreamChunk>(payload, jsonOptions);
            }
            catch (JsonException ex)
            {
                _logger.LogWarning(ex, "OpenAI stream chunk parse failed. Payload prefix: {Prefix}",
                    payload.Length > 200 ? payload.Substring(0, 200) + "..." : payload);
                continue; // 잘못된 chunk 1건은 무시하고 다음 라인 진행
            }

            if (parsed == null) continue;

            // delta.content 가 있으면 텍스트 chunk
            var firstChoice = parsed.Choices?.FirstOrDefault();
            var deltaContent = firstChoice?.Delta?.Content;
            var finishReason = firstChoice?.FinishReason;

            if (!string.IsNullOrEmpty(deltaContent))
            {
                yield return ChatChunk.Delta(deltaContent);
            }

            // usage 동봉 chunk (stream_options.include_usage:true 일 때 마지막 즈음에 도착)
            if (parsed.Usage is { TotalTokens: > 0 })
            {
                yield return ChatChunk.Usage(parsed.Usage.PromptTokens, parsed.Usage.CompletionTokens, parsed.Usage.TotalTokens);
            }

            if (!string.IsNullOrEmpty(finishReason))
            {
                yield return ChatChunk.Stop(finishReason);
            }
        }
    }

    // OpenAI streaming chunk 응답 파서 (delta.content + finish_reason + 선택적 usage)
    private sealed class OpenAiStreamChunk
    {
        [System.Text.Json.Serialization.JsonPropertyName("choices")]
        public List<OpenAiStreamChoice>? Choices { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("usage")]
        public OpenAiUsage? Usage { get; set; }
    }

    private sealed class OpenAiStreamChoice
    {
        [System.Text.Json.Serialization.JsonPropertyName("delta")]
        public OpenAiStreamDelta? Delta { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("finish_reason")]
        public string? FinishReason { get; set; }
    }

    private sealed class OpenAiStreamDelta
    {
        [System.Text.Json.Serialization.JsonPropertyName("role")]
        public string? Role { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("content")]
        public string? Content { get; set; }
    }

    private string GetLanguageInstruction(string? language)
    {
        if (string.IsNullOrEmpty(language) || language == "auto")
        {
            return string.Empty; // 자동 감지인 경우 지시 없음
        }

        return language.ToLower() switch
        {
            "ko" => "Please respond in Korean (한국어).",
            "en" => "Please respond in English.",
            _ => string.Empty
        };
    }

    private List<ChatMessageDto> AddLanguageInstruction(List<ChatMessageDto> messages, string? language)
    {
        var instruction = GetLanguageInstruction(language);
        if (string.IsNullOrEmpty(instruction))
        {
            return messages;
        }

        // System message가 있는지 확인
        var systemMessage = messages.FirstOrDefault(m => m.Role == "system");
        if (systemMessage != null)
        {
            // 기존 system message에 언어 지시 추가
            systemMessage.Content = $"{systemMessage.Content}\n\n{instruction}";
        }
        else
        {
            // System message가 없으면 새로 추가
            messages.Insert(0, new ChatMessageDto
            {
                Role = "system",
                Content = instruction
            });
        }

        return messages;
    }

    /// <summary>
    /// H3(5-3) — OpenAI Chat Completions 의 messages 페이로드를 멀티모달(Vision) 형식으로 빌드한다.
    /// - 메시지에 Contents(이미지 등) 가 없으면 단일 텍스트 string content 로 유지(기존 호환).
    /// - Contents 가 있으면 OpenAI Vision content parts 배열 형식으로 변환:
    ///     [ {"type":"text","text":"..."}, {"type":"image_url","image_url":{"url":"..."}} ]
    /// - 비-vision 모델에 image 가 포함된 경우 경고 로그를 남기되 호출은 그대로 진행(사용자 선택 모델 존중).
    /// CallOpenAiAsync(비스트리밍) / StreamOpenAiChunksAsync(스트리밍) 양 경로에서 공유한다.
    /// </summary>
    private List<object> BuildOpenAiMessagesWithVision(List<ChatMessageDto> messagesWithLanguage, string model)
    {
        // 이미지 포함 여부 사전 점검 → 비-vision 모델 경고
        var hasImage = messagesWithLanguage.Any(m =>
            m.Contents != null && m.Contents.Any(c =>
                string.Equals(c.Type, "image_url", StringComparison.OrdinalIgnoreCase)));
        if (hasImage)
        {
            var visionModels = new[] { "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-4o", "gpt-4o-mini" };
            var modelLower = model.ToLowerInvariant();
            if (!visionModels.Any(vm => modelLower.Contains(vm.Replace("-", "")) || modelLower == vm))
            {
                _logger.LogWarning(
                    "Image detected but model {Model} may not support vision. Consider using gpt-4o or gpt-5.",
                    model);
            }
        }

        var messages = new List<object>();
        foreach (var m in messagesWithLanguage)
        {
            // Contents 가 비어있으면 기존 단일 텍스트 content 로 유지
            if (m.Contents == null || m.Contents.Count == 0)
            {
                messages.Add(new { role = m.Role, content = m.Content ?? string.Empty });
                continue;
            }

            // Contents 가 있는 경우 — vision content parts 배열로 변환
            var contentList = new List<object>();
            var textParts = new List<string>();
            var hasImageInMsg = false;

            foreach (var c in m.Contents)
            {
                var contentType = (c.Type ?? string.Empty).ToLowerInvariant();
                if (contentType == "text" && !string.IsNullOrEmpty(c.Text))
                {
                    textParts.Add(c.Text!);
                }
                else if (contentType == "image_url" && !string.IsNullOrEmpty(c.ImageUrl))
                {
                    var imageUrl = c.ImageUrl!;
                    // OpenAI Vision 은 data: 또는 http(s):// URL 만 허용
                    if (!imageUrl.StartsWith("data:", StringComparison.OrdinalIgnoreCase)
                        && !imageUrl.StartsWith("http://", StringComparison.OrdinalIgnoreCase)
                        && !imageUrl.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
                    {
                        _logger.LogWarning(
                            "Invalid image URL format (not data: or http(s)://) — skipped. Preview={Preview}",
                            imageUrl.Length > 100 ? imageUrl.Substring(0, 100) + "..." : imageUrl);
                        continue;
                    }
                    contentList.Add(new { type = "image_url", image_url = new { url = imageUrl } });
                    hasImageInMsg = true;
                }
                else if (contentType == "audio_url")
                {
                    textParts.Add($"[Audio: {c.AudioUrl ?? string.Empty}]");
                }
                else if (contentType == "file")
                {
                    if (!string.IsNullOrEmpty(c.FileName))
                    {
                        textParts.Add($"[첨부 파일: {c.FileName}]");
                    }
                }
            }

            // 텍스트 부분은 가장 앞에 합쳐서 단일 text part 로 추가(OpenAI 권장 패턴)
            if (textParts.Count > 0)
            {
                var combinedText = string.Join("\n", textParts);
                contentList.Insert(0, new { type = "text", text = combinedText });
            }

            if (contentList.Count == 0)
            {
                // Contents 가 있으나 유효한 part 가 없는 경우 → 텍스트 폴백
                messages.Add(new { role = m.Role, content = m.Content ?? string.Empty });
            }
            else if (contentList.Count == 1 && !hasImageInMsg && textParts.Count > 0)
            {
                // 텍스트 한 덩어리만 있으면 단일 string content 로 (배열 직렬화 오버헤드 절약)
                messages.Add(new { role = m.Role, content = string.Join("\n", textParts) });
            }
            else
            {
                messages.Add(new { role = m.Role, content = contentList });
            }
        }

        return messages;
    }

    private async Task<AiResponseDto> CallOpenAiAsync(ApiService service, string model, ChatMessageRequestDto request, CancellationToken cancellationToken)
    {
        var startTime = DateTime.UtcNow; // 응답 시간 측정 시작
        
        var apiKey = GetApiKey("openai", "AiApiSettings:OpenAI:ApiKey");
        var baseUrl = _configuration[$"AiApiSettings:OpenAI:BaseUrl"] ?? "https://api.openai.com/v1";

        if (string.IsNullOrEmpty(apiKey))
        {
            _logger.LogError("OpenAI API key is not configured");
            throw new InvalidOperationException("OpenAI API key is not configured");
        }

        var client = _httpClientFactory.CreateClient("openai");
        client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);

        // 언어 지시 추가
        var messagesWithLanguage = AddLanguageInstruction(request.Messages.ToList(), request.Language);

        // 이미지가 있는지 확인 (Vision API 모델 사용 필요)
        var hasImageInRequest = messagesWithLanguage.Any(m => 
            m.Contents != null && m.Contents.Any(c => c.Type.ToLower() == "image_url"));
        
        // 이미지가 있는데 Vision을 지원하지 않는 모델이면 경고 또는 모델 자동 변경
        if (hasImageInRequest)
        {
            var visionModels = new[] { "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-4o", "gpt-4o-mini" };
            if (!visionModels.Any(vm => model.ToLower().Contains(vm.ToLower().Replace("-", "")) || model.ToLower() == vm.ToLower()))
            {
                _logger.LogWarning("Image detected but model {Model} may not support vision. Consider using gpt-4o or gpt-5.", model);
                // Vision을 지원하는 모델로 자동 변경하지 않고 경고만 출력 (사용자가 선택한 모델 사용)
            }
        }

        // 멀티모달 메시지 변환
        var messages = new List<object>();
        
        foreach (var m in messagesWithLanguage)
        {
            // 멀티모달 콘텐츠가 있으면 사용, 없으면 기본 텍스트 콘텐츠 사용
            if (m.Contents != null && m.Contents.Count > 0)
            {
                var contentList = new List<object>();
                var textParts = new List<string>();
                var hasImage = false;
                
                foreach (var c in m.Contents)
                {
                    var contentType = c.Type.ToLower();
                    if (contentType == "text" && !string.IsNullOrEmpty(c.Text))
                    {
                        textParts.Add(c.Text);
                    }
                    else if (contentType == "image_url" && !string.IsNullOrEmpty(c.ImageUrl))
                    {
                        // OpenAI Vision API는 data URL (Base64) 또는 공개 URL을 지원
                        // Base64 형식: data:image/jpeg;base64,/9j/4AAQSkZJRg...
                        // 또는 공개 URL: https://example.com/image.jpg
                        var imageUrl = c.ImageUrl;
                        
                        // 로그 출력 (디버깅용)
                        _logger.LogDebug("Processing image_url content: Length={Length}, StartsWith data:={StartsWithData}, Preview={Preview}", 
                            imageUrl.Length,
                            imageUrl.StartsWith("data:", StringComparison.OrdinalIgnoreCase),
                            imageUrl.Length > 100 ? imageUrl.Substring(0, 100) + "..." : imageUrl);
                        
                        // Base64 data URL 형식 검증
                        if (!imageUrl.StartsWith("data:", StringComparison.OrdinalIgnoreCase) && 
                            !imageUrl.StartsWith("http://", StringComparison.OrdinalIgnoreCase) && 
                            !imageUrl.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
                        {
                            _logger.LogWarning("Invalid image URL format (not data: or http(s)://): {ImageUrl}", imageUrl.Length > 100 ? imageUrl.Substring(0, 100) + "..." : imageUrl);
                        }
                        
                        contentList.Add(new { type = "image_url", image_url = new { url = imageUrl } });
                        hasImage = true;
                    }
                    else if (contentType == "audio_url")
                    {
                        // OpenAI는 직접 오디오를 지원하지 않으므로 텍스트로 변환
                        textParts.Add($"[Audio: {c.AudioUrl ?? ""}]");
                    }
                    else if (contentType == "file")
                    {
                        // 파일 타입은 URL만 표시 (실제 파일 내용은 별도 text 타입으로 전송됨)
                        // 파싱된 내용이 있으면 text 타입으로 이미 전송되었으므로 여기서는 파일 참조만 추가
                        if (!string.IsNullOrEmpty(c.FileName))
                        {
                            textParts.Add($"[첨부 파일: {c.FileName}]");
                        }
                        // 파일 URL이 있으면 참조 정보 추가 (실제 내용은 이미 text로 전송됨)
                        // Note: 파일 내용은 프론트엔드에서 parsedContent로 text 타입에 포함되어 전송됨
                    }
                }
                
                // 텍스트 부분 추가
                if (textParts.Count > 0)
                {
                    var combinedText = string.Join("\n", textParts);
                    contentList.Insert(0, new { type = "text", text = combinedText });
                }

                // 이미지가 있거나 contentList에 여러 항목이 있으면 배열로, 그렇지 않으면 단일 텍스트 문자열로
                if (contentList.Count == 0)
                {
                    messages.Add(new { role = m.Role, content = m.Content ?? "" });
                }
                else if (contentList.Count == 1 && !hasImage && textParts.Count > 0)
                {
                    // 단일 텍스트 항목인 경우 - textParts를 직접 사용
                    messages.Add(new { role = m.Role, content = string.Join("\n", textParts) });
                }
                else
                {
                    // 여러 항목이 있거나 이미지가 있는 경우 배열로
                    messages.Add(new { role = m.Role, content = contentList });
                }
            }
            else
            {
                // 기본 텍스트 메시지
                messages.Add(new { role = m.Role, content = m.Content ?? "" });
            }
        }

        // 심층 리서치 또는 일반 웹 검색 처리
        if (request.EnableDeepResearch || request.EnableWebSearch)
        {
            var lastUserMessage = request.Messages.LastOrDefault(m => m.Role == "user");
            if (lastUserMessage != null && !string.IsNullOrWhiteSpace(lastUserMessage.Content))
            {
                try
                {
                    string? combinedSearchResults = null;
                    
                    if (request.EnableDeepResearch)
                    {
                        // 심층 리서치: 여러 검색 쿼리 생성 및 실행
                        combinedSearchResults = await PerformDeepResearchAsync(lastUserMessage.Content, cancellationToken);
                    }
                    else if (request.EnableWebSearch)
                    {
                        // 일반 웹 검색: 단일 쿼리
                        combinedSearchResults = await SearchWithTavilyAsync(lastUserMessage.Content, cancellationToken);
                    }
                    
                    if (combinedSearchResults != null && !string.IsNullOrEmpty(combinedSearchResults))
                    {
                        // 검색 결과를 시스템 메시지로 추가하거나 기존 시스템 메시지에 추가
                        var existingSystemMessageIndex = -1;
                        string? existingSystemContent = null;
                        
                        for (int i = 0; i < messages.Count; i++)
                        {
                            var msg = messages[i];
                            // dynamic을 사용하여 role 속성 접근
                            dynamic dynMsg = msg;
                            if (dynMsg.role == "system")
                            {
                                existingSystemMessageIndex = i;
                                existingSystemContent = dynMsg.content?.ToString();
                                break;
                            }
                        }
                        
                        // 언어에 따른 검색 결과 안내 추가
                        var languageNote = request.Language?.ToLower() == "ko" 
                            ? request.EnableDeepResearch
                                ? "위 검색 결과들을 종합적으로 분석하고 정리하여 답변해주세요. 여러 출처의 정보를 비교하고 일관성 있게 통합해주세요."
                                : "위 검색 결과를 참고하여 답변해주세요. 검색 결과가 없거나 불확실한 경우 명시해주세요."
                            : request.EnableDeepResearch
                                ? "Please comprehensively analyze and organize the above search results when answering. Compare information from multiple sources and integrate them consistently."
                                : "Please refer to the above search results when answering. If there are no search results or they are uncertain, please mention it.";
                        var searchLabel = request.Language?.ToLower() == "ko" 
                            ? request.EnableDeepResearch ? "[심층 리서치 결과 - 다중 출처]" : "[최신 웹 검색 결과]"
                            : request.EnableDeepResearch ? "[Deep Research Results - Multiple Sources]" : "[Latest Web Search Results]";
                        var searchContext = $"\n\n{searchLabel}\n{combinedSearchResults}\n\n{languageNote}";
                        
                        if (existingSystemMessageIndex >= 0 && existingSystemContent != null)
                        {
                            // 기존 시스템 메시지에 검색 결과 추가
                            messages[existingSystemMessageIndex] = new
                            {
                                role = "system",
                                content = existingSystemContent + searchContext
                            };
                        }
                        else
                        {
                            // 기본 시스템 메시지
                            var defaultSystemMessage = request.Language?.ToLower() == "ko"
                                ? """
당신은 전문적이고 친절한 AI 어시스턴트입니다.

## 응답 원칙
- 답변은 **마크다운 형식**으로 작성하세요. 제목(##), 굵게(**), 목록(-), 코드블록(```) 등을 적극 활용하세요.
- 복잡한 내용은 단계별로 나눠 설명하고, 핵심 정보는 표나 목록으로 정리하세요.
- 예시나 비교가 필요한 경우 구체적인 사례를 들어 설명하세요.
- 답변 길이는 질문의 복잡도에 맞게 조절하세요. 간단한 질문엔 간결하게, 복잡한 질문엔 충분히 상세하게 답하세요.
- 확실하지 않은 정보는 추측임을 명시하고, 필요 시 추가 확인을 권장하세요.
"""
                                : """
You are a professional and helpful AI assistant.

## Response Guidelines
- Use **Markdown formatting** in your responses: headings (##), bold (**), lists (-), code blocks (```), etc.
- For complex topics, break explanations into clear steps and organize key information in tables or lists.
- Provide concrete examples or comparisons when helpful.
- Match response length to question complexity — concise for simple questions, detailed for complex ones.
- Clearly indicate when information is uncertain, and suggest verification when needed.
""";
                            // 새로운 시스템 메시지 추가
                            messages.Insert(0, new
                            {
                                role = "system",
                                content = defaultSystemMessage + searchContext
                            });
                        }
                        
                        _logger.LogInformation("Search completed and added to context. DeepResearch={DeepResearch}", request.EnableDeepResearch);
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Search failed, continuing without search results");
                    // 검색 실패해도 계속 진행
                }
            }
        }


        // o1/o3/gpt-5 계열 추론 모델은 max_completion_tokens 사용, temperature 미지원
        var modelLower = model.ToLowerInvariant();
        var usesCompletionTokens = modelLower.StartsWith("o1") || modelLower.StartsWith("o3") || modelLower.StartsWith("gpt-5");
        var payloadDict = new Dictionary<string, object>
        {
            ["model"] = model,
            ["messages"] = messages,
            ["stream"] = false
        };

        if (usesCompletionTokens)
        {
            // o1/o3/gpt-5 추론 모델: max_completion_tokens 사용, temperature 미지원
            if (request.MaxTokens.HasValue)
            {
                payloadDict["max_completion_tokens"] = request.MaxTokens.Value;
            }
        }
        else
        {
            // 기타 모델: max_tokens와 temperature 사용
            if (request.Temperature.HasValue)
            {
                payloadDict["temperature"] = request.Temperature.Value;
            }
            if (request.MaxTokens.HasValue)
            {
                payloadDict["max_tokens"] = request.MaxTokens.Value;
            }
        }

        var json = JsonSerializer.Serialize(payloadDict);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        _logger.LogDebug("OpenAI API request: Model={Model}, MessagesCount={Count}, Temperature={Temp}, MaxTokens={MaxTokens}, UsesCompletionTokens={UsesCompletionTokens}", 
            model, messages.Count, request.Temperature, request.MaxTokens, usesCompletionTokens);

        var response = await client.PostAsync($"{baseUrl}/chat/completions", content, cancellationToken);
        
        var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);
        
        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError("OpenAI API error. Status: {StatusCode}, Response: {Response}, Model={Model}",
                response.StatusCode, responseJson, model);
            if (response.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
            {
                _apiKeyPool?.MarkAsCoolingDown("openai", apiKey ?? "");
                throw new HttpRequestException($"OpenAI API 429 Too Many Requests - {responseJson}", null, response.StatusCode);
            }
            throw new InvalidOperationException($"OpenAI API error: {response.StatusCode} - {responseJson}");
        }

        try
        {
            // OpenAI API는 snake_case를 사용하므로 PropertyNameCaseInsensitive 사용
            var jsonOptions = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            };
            
            _logger.LogDebug("OpenAI API response: {Response}", responseJson);
            
            var openAiResponse = JsonSerializer.Deserialize<OpenAiResponse>(responseJson, jsonOptions);

            if (openAiResponse == null)
            {
                _logger.LogError("Failed to deserialize OpenAI response. Response: {Response}", responseJson);
                throw new InvalidOperationException($"Failed to deserialize OpenAI response. Response: {responseJson}");
            }
            
            var usage = openAiResponse.Usage;
            string? extractedContent = null;
            string finishReason = "stop";

            // New Responses API 포맷 (gpt-5+): output 배열에서 텍스트 추출
            if (openAiResponse.Output != null && openAiResponse.Output.Count > 0)
            {
                var msgItem = openAiResponse.Output.FirstOrDefault(o => o.Type == "message");
                if (msgItem?.Content != null)
                {
                    var textPart = msgItem.Content.FirstOrDefault(c => c.Type == "output_text");
                    extractedContent = textPart?.Text;
                }
                _logger.LogDebug("OpenAI Responses API format detected (output array). Content length: {Len}", extractedContent?.Length ?? 0);
            }
            // 구 Chat Completions 포맷: choices 배열에서 텍스트 추출
            else if (openAiResponse.Choices != null && openAiResponse.Choices.Count > 0)
            {
                var choice = openAiResponse.Choices[0];
                finishReason = choice.FinishReason ?? "stop";
                // content가 비어있으면 reasoning_content 를 fallback으로 사용
                extractedContent = string.IsNullOrEmpty(choice.Message?.Content)
                    ? choice.Message?.ReasoningContent
                    : choice.Message?.Content;
            }
            else
            {
                _logger.LogError("Invalid OpenAI response structure - no choices or output. Response: {Response}", responseJson);
                throw new InvalidOperationException($"Invalid response from OpenAI - no choices or output in response. Response: {responseJson}");
            }

            var result = new AiResponseDto
            {
                Content = extractedContent ?? "",
                Model = openAiResponse.Model ?? model,
                FinishReason = finishReason,
                PromptTokens = usage?.PromptTokens > 0 ? usage.PromptTokens : (usage?.InputTokens ?? 0),
                CompletionTokens = usage?.CompletionTokens > 0 ? usage.CompletionTokens : (usage?.OutputTokens ?? 0),
                TotalTokens = usage?.TotalTokens > 0 ? usage.TotalTokens : ((usage?.InputTokens ?? 0) + (usage?.OutputTokens ?? 0)),
                ResponseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds
            };

            _logger.LogInformation("OpenAI API call successful. Model: {Model}, Tokens: {TotalTokens}, ContentLength: {Len}", result.Model, result.TotalTokens, result.Content.Length);
            return result;
        }
        catch (JsonException ex)
        {
            _logger.LogError(ex, "Failed to deserialize OpenAI response. Response: {Response}", responseJson);
            throw new InvalidOperationException($"Failed to parse OpenAI response: {ex.Message}. Response: {responseJson}", ex);
        }
    }

    private async Task<AiResponseDto> CallClaudeAsync(ApiService service, string model, ChatMessageRequestDto request, CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("claude", "AiApiSettings:Claude:ApiKey");
        var baseUrl = _configuration[$"AiApiSettings:Claude:BaseUrl"] ?? "https://api.anthropic.com/v1";

        var client = _httpClientFactory.CreateClient("claude");
        client.DefaultRequestHeaders.Add("x-api-key", apiKey);
        client.DefaultRequestHeaders.Add("anthropic-version", "2023-06-01");

        // 언어 지시 추가
        var messagesWithLanguage = AddLanguageInstruction(request.Messages.ToList(), request.Language);

        // Convert messages format for Claude
        var messages = messagesWithLanguage
            .Where(m => m.Role != "system")
            .Select(m => new
            {
                role = m.Role == "assistant" ? "assistant" : "user",
                content = m.Content
            }).ToList();

        var systemMessage = messagesWithLanguage.FirstOrDefault(m => m.Role == "system");

        var payload = new
        {
            model = model,
            messages = messages,
            system = systemMessage?.Content ?? "",
            max_tokens = request.MaxTokens ?? 4096,
            temperature = request.Temperature
        };

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await client.PostAsync($"{baseUrl}/messages", content, cancellationToken);
        var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);
        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError("Claude API error. Status: {StatusCode}, Response: {Response}", response.StatusCode, responseJson);
            if (response.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
            {
                _apiKeyPool?.MarkAsCoolingDown("claude", apiKey ?? "");
                throw new HttpRequestException($"Claude API 429 Too Many Requests - {responseJson}", null, response.StatusCode);
            }
            throw new InvalidOperationException($"Claude API error: {response.StatusCode} - {responseJson}");
        }

        var claudeResponse = JsonSerializer.Deserialize<ClaudeResponse>(responseJson);

        if (claudeResponse?.Content == null || claudeResponse.Content.Count == 0)
        {
            throw new InvalidOperationException("Invalid response from Claude");
        }

        var textContent = claudeResponse.Content.FirstOrDefault(c => c.Type == "text");

        return new AiResponseDto
        {
            Content = textContent?.Text ?? "",
            Model = claudeResponse.Model ?? model,
            FinishReason = claudeResponse.StopReason ?? "stop",
            PromptTokens = claudeResponse.Usage?.InputTokens ?? 0,
            CompletionTokens = claudeResponse.Usage?.OutputTokens ?? 0,
            TotalTokens = (claudeResponse.Usage?.InputTokens ?? 0) + (claudeResponse.Usage?.OutputTokens ?? 0),
            ResponseTime = 0 // Calculate if needed
        };
    }

    private async Task<Stream> CallOpenAiStreamAsync(ApiService service, string model, ChatMessageRequestDto request, CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("openai", "AiApiSettings:OpenAI:ApiKey");
        var baseUrl = _configuration[$"AiApiSettings:OpenAI:BaseUrl"] ?? "https://api.openai.com/v1";

        var client = _httpClientFactory.CreateClient("openai");
        client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);

        var messages = request.Messages.Select(m => new
        {
            role = m.Role,
            content = m.Content
        }).ToList();

        // o1/o3/gpt-5 계열 추론 모델은 max_completion_tokens 사용, temperature 미지원
        var modelLower = model.ToLowerInvariant();
        var usesCompletionTokens = modelLower.StartsWith("o1") || modelLower.StartsWith("o3") || modelLower.StartsWith("gpt-5");
        var payloadDict = new Dictionary<string, object>
        {
            ["model"] = model,
            ["messages"] = messages,
            ["stream"] = true
        };

        if (usesCompletionTokens)
        {
            // o1/o3/gpt-5 추론 모델: max_completion_tokens 사용, temperature 미지원
            if (request.MaxTokens.HasValue)
            {
                payloadDict["max_completion_tokens"] = request.MaxTokens.Value;
            }
        }
        else
        {
            // 기타 모델: max_tokens와 temperature 사용
            if (request.Temperature.HasValue)
            {
                payloadDict["temperature"] = request.Temperature.Value;
            }
            if (request.MaxTokens.HasValue)
            {
                payloadDict["max_tokens"] = request.MaxTokens.Value;
            }
        }

        var json = JsonSerializer.Serialize(payloadDict);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await client.PostAsync($"{baseUrl}/chat/completions", content, cancellationToken);
        response.EnsureSuccessStatusCode();

        return await response.Content.ReadAsStreamAsync(cancellationToken);
    }

    private async Task<Stream> CallClaudeStreamAsync(ApiService service, string model, ChatMessageRequestDto request, CancellationToken cancellationToken)
    {
        // Claude streaming implementation similar to OpenAI
        var apiKey = GetApiKey("claude", "AiApiSettings:Claude:ApiKey");
        var baseUrl = _configuration[$"AiApiSettings:Claude:BaseUrl"] ?? "https://api.anthropic.com/v1";

        var client = _httpClientFactory.CreateClient("claude");
        client.DefaultRequestHeaders.Add("x-api-key", apiKey);
        client.DefaultRequestHeaders.Add("anthropic-version", "2023-06-01");
        client.DefaultRequestHeaders.Add("anthropic-beta", "messages-2023-12-15");

        var messages = request.Messages
            .Where(m => m.Role != "system")
            .Select(m => new
            {
                role = m.Role == "assistant" ? "assistant" : "user",
                content = m.Content
            }).ToList();

        var systemMessage = request.Messages.FirstOrDefault(m => m.Role == "system");

        var payload = new
        {
            model = model,
            messages = messages,
            system = systemMessage?.Content ?? "",
            max_tokens = request.MaxTokens ?? 4096,
            temperature = request.Temperature,
            stream = true
        };

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await client.PostAsync($"{baseUrl}/messages", content, cancellationToken);
        response.EnsureSuccessStatusCode();

        return await response.Content.ReadAsStreamAsync(cancellationToken);
    }

    private async Task<AiResponseDto> CallGeminiAsync(ApiService service, string model, ChatMessageRequestDto request, CancellationToken cancellationToken)
    {
        var startTime = DateTime.UtcNow;
        
        var apiKey = GetApiKey("gemini", "AiApiSettings:Gemini:ApiKey");
        var baseUrl = _configuration["AiApiSettings:Gemini:BaseUrl"] ?? "https://generativelanguage.googleapis.com/v1beta";

        if (string.IsNullOrEmpty(apiKey))
        {
            throw new InvalidOperationException("Gemini API key is not configured");
        }

        var client = _httpClientFactory.CreateClient("gemini");

        // 언어 지시 추가
        var messagesWithLanguage = AddLanguageInstruction(request.Messages.ToList(), request.Language);

        // Gemini 3 Pro Image 모델인지 확인 (이미지 편집 지원)
        var isGeminiImageModel = model.Contains("gemini-3-pro-image", StringComparison.OrdinalIgnoreCase) ||
                                 model.Contains("gemini-3.0-pro-image", StringComparison.OrdinalIgnoreCase) ||
                                 model.Contains("gemini-3.1-pro-image", StringComparison.OrdinalIgnoreCase);
        
        // 이미지가 포함된 메시지가 있는지 확인
        var hasImageInRequest = messagesWithLanguage.Any(m => 
            m.Contents != null && m.Contents.Any(c => c.Type.ToLower() == "image_url"));

        // Gemini API는 메시지를 contents 배열로 변환
        var contents = new List<object>();
        var systemInstructions = new List<string>();

        foreach (var msg in messagesWithLanguage)
        {
            if (msg.Role == "system")
            {
                // 모든 system 메시지를 수집 (여러 개일 수 있음)
                if (!string.IsNullOrEmpty(msg.Content))
                {
                    systemInstructions.Add(msg.Content);
                }
            }
            else
            {
                // 멀티모달 콘텐츠가 있으면 이미지 포함 처리
                var parts = new List<object>();
                
                if (msg.Contents != null && msg.Contents.Count > 0)
                {
                    foreach (var c in msg.Contents)
                    {
                        var contentType = c.Type.ToLower();
                        if (contentType == "text" && !string.IsNullOrEmpty(c.Text))
                        {
                            parts.Add(new { text = c.Text });
                        }
                        else if (contentType == "image_url" && !string.IsNullOrEmpty(c.ImageUrl))
                        {
                            // Base64 data URL을 Gemini의 inlineData 형식으로 변환
                            var imageUrl = c.ImageUrl;
                            string base64Data = "";
                            string mimeType = "image/jpeg";
                            
                            if (imageUrl.StartsWith("data:", StringComparison.OrdinalIgnoreCase))
                            {
                                // data:image/jpeg;base64,/9j/4AAQSkZJRg... 형식 파싱
                                var parts_split = imageUrl.Split(new[] { ',' }, 2);
                                if (parts_split.Length == 2)
                                {
                                    base64Data = parts_split[1];
                                    
                                    // MIME 타입 추출
                                    var header = parts_split[0];
                                    if (header.Contains("image/png", StringComparison.OrdinalIgnoreCase))
                                        mimeType = "image/png";
                                    else if (header.Contains("image/jpeg", StringComparison.OrdinalIgnoreCase) || 
                                             header.Contains("image/jpg", StringComparison.OrdinalIgnoreCase))
                                        mimeType = "image/jpeg";
                                    else if (header.Contains("image/webp", StringComparison.OrdinalIgnoreCase))
                                        mimeType = "image/webp";
                                    else if (header.Contains("image/gif", StringComparison.OrdinalIgnoreCase))
                                        mimeType = "image/gif";
                                }
                            }
                            else if (imageUrl.StartsWith("http://", StringComparison.OrdinalIgnoreCase) || 
                                     imageUrl.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
                            {
                                // 공개 URL인 경우 그대로 사용 (Gemini가 지원하는 경우)
                                // 하지만 Gemini는 inlineData만 지원하므로 URL을 다운로드해야 함
                                // 현재는 Base64 data URL만 지원
                                _logger.LogWarning("Gemini API does not support public URLs directly. Please use Base64 data URL format.");
                                continue;
                            }
                            
                            if (!string.IsNullOrEmpty(base64Data))
                            {
                                parts.Add(new
                                {
                                    inlineData = new
                                    {
                                        mimeType = mimeType,
                                        data = base64Data
                                    }
                                });
                            }
                        }
                    }
                }
                
                // 텍스트 콘텐츠가 없으면 추가
                if (parts.Count == 0 && !string.IsNullOrEmpty(msg.Content))
                {
                    parts.Add(new { text = msg.Content });
                }
                
                // parts가 비어있지 않으면 추가
                if (parts.Count > 0)
                {
                    contents.Add(new
                    {
                        role = msg.Role == "assistant" ? "model" : "user",
                        parts = parts
                    });
                }
            }
        }

        // Gemini API 요청 페이로드
        var payload = new Dictionary<string, object>
        {
            ["contents"] = contents
        };

        // 모든 system instruction을 하나로 합침
        if (systemInstructions.Count > 0)
        {
            var combinedSystemInstruction = string.Join("\n\n", systemInstructions);
            
            // RAG 컨텍스트가 포함되어 있는지 확인하고 로깅
            var hasRagContext = combinedSystemInstruction.Contains("[지식 기반 문서 검색 결과]") || 
                               combinedSystemInstruction.Contains("[Knowledge Base Search Results]");
            if (hasRagContext)
            {
                _logger.LogInformation("RAG context detected in system instruction for Gemini. Length: {Length}, Contains RAG label: {HasRag}", 
                    combinedSystemInstruction.Length, hasRagContext);
                var preview = combinedSystemInstruction.Length > 500 ? combinedSystemInstruction.Substring(0, 500) + "..." : combinedSystemInstruction;
                _logger.LogDebug("System instruction preview: {Preview}", preview);
            }
            else
            {
                _logger.LogWarning("RAG was enabled but RAG context not found in system instructions for Gemini. System instruction count: {Count}", 
                    systemInstructions.Count);
                // 각 system instruction의 일부를 로깅
                for (int i = 0; i < systemInstructions.Count; i++)
                {
                    var preview = systemInstructions[i].Length > 200 ? systemInstructions[i].Substring(0, 200) + "..." : systemInstructions[i];
                    _logger.LogDebug("System instruction {Index} preview: {Preview}", i, preview);
                }
            }
            
            payload["systemInstruction"] = new
            {
                parts = new[]
                {
                    new { text = combinedSystemInstruction }
                }
            };
        }
        else
        {
            _logger.LogWarning("No system instructions found for Gemini API call. RAG may not be working correctly.");
        }

        // generationConfig 설정
        var generationConfig = new Dictionary<string, object>
        {
            ["temperature"] = request.Temperature ?? 0.7m,
            ["maxOutputTokens"] = request.MaxTokens ?? 2048
        };
        
        // Gemini 3 Pro Image 모델이고 이미지가 포함된 경우 responseModalities 추가
        if (isGeminiImageModel && hasImageInRequest)
        {
            generationConfig["responseModalities"] = new[] { "IMAGE" };
        }
        
        payload["generationConfig"] = generationConfig;

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        _logger.LogDebug("Gemini API request: Model={Model}, ContentsCount={Count}, SystemInstructionLength={SysLen}, Temperature={Temp}, MaxTokens={MaxTokens}", 
            model, contents.Count, systemInstructions.Count > 0 ? systemInstructions.Sum(s => s.Length) : 0, 
            request.Temperature ?? 0.7m, request.MaxTokens ?? 2048);

        // API 키를 쿼리 파라미터로 전달
        var response = await client.PostAsync($"{baseUrl}/models/{model}:generateContent?key={apiKey}", content, cancellationToken);
        
        var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError("Gemini API error. Status: {StatusCode}, Response: {Response}, Model={Model}",
                response.StatusCode, responseJson, model);
            if (response.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
            {
                _apiKeyPool?.MarkAsCoolingDown("gemini", apiKey ?? "");
                throw new HttpRequestException($"Gemini API 429 Too Many Requests - {responseJson}", null, response.StatusCode);
            }
            throw new InvalidOperationException($"Gemini API error: {response.StatusCode} - {responseJson}");
        }

        try
        {
            var jsonOptions = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            };

            _logger.LogDebug("Gemini API response: {Response}", responseJson);

            var geminiResponse = JsonSerializer.Deserialize<GeminiResponse>(responseJson, jsonOptions);

            if (geminiResponse == null || geminiResponse.Candidates == null || geminiResponse.Candidates.Count == 0)
            {
                _logger.LogError("Invalid Gemini response structure. Response: {Response}", responseJson);
                throw new InvalidOperationException($"Invalid response from Gemini - no candidates in response. Response: {responseJson}");
            }

            var candidate = geminiResponse.Candidates[0];
            var contentPart = candidate.Content?.Parts?.FirstOrDefault(p => !string.IsNullOrEmpty(p.Text));
            
            // 이미지 데이터 추출 (Gemini 3 Pro Image 편집 응답)
            var imageUrls = new List<string>();
            if (candidate.Content?.Parts != null)
            {
                foreach (var part in candidate.Content.Parts)
                {
                    if (part.InlineData != null && !string.IsNullOrEmpty(part.InlineData.Data))
                    {
                        // Base64 데이터를 data URL로 변환
                        var mimeType = part.InlineData.MimeType ?? "image/png";
                        imageUrls.Add($"data:{mimeType};base64,{part.InlineData.Data}");
                    }
                }
            }

            var usageMetadata = geminiResponse.UsageMetadata;

            return new AiResponseDto
            {
                Content = contentPart?.Text ?? "",
                Model = model,
                FinishReason = candidate.FinishReason ?? "stop",
                PromptTokens = usageMetadata?.PromptTokenCount ?? 0,
                CompletionTokens = usageMetadata?.CandidatesTokenCount ?? 0,
                TotalTokens = (usageMetadata?.PromptTokenCount ?? 0) + (usageMetadata?.CandidatesTokenCount ?? 0),
                ResponseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds,
                ImageUrls = imageUrls.Count > 0 ? imageUrls : null
            };
        }
        catch (JsonException ex)
        {
            _logger.LogError(ex, "Failed to deserialize Gemini response. Response: {Response}", responseJson);
            throw new InvalidOperationException($"Failed to parse Gemini response: {ex.Message}. Response: {responseJson}", ex);
        }
    }

    private async Task<Stream> CallGeminiStreamAsync(ApiService service, string model, ChatMessageRequestDto request, CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("gemini", "AiApiSettings:Gemini:ApiKey");
        var baseUrl = _configuration["AiApiSettings:Gemini:BaseUrl"] ?? "https://generativelanguage.googleapis.com/v1beta";

        if (string.IsNullOrEmpty(apiKey))
        {
            throw new InvalidOperationException("Gemini API key is not configured");
        }

        var client = _httpClientFactory.CreateClient("gemini");

        // Gemini API는 메시지를 contents 배열로 변환
        var contents = new List<object>();
        var systemInstruction = "";

        foreach (var msg in request.Messages)
        {
            if (msg.Role == "system")
            {
                systemInstruction = msg.Content;
            }
            else
            {
                contents.Add(new
                {
                    role = msg.Role == "assistant" ? "model" : "user",
                    parts = new[]
                    {
                        new { text = msg.Content }
                    }
                });
            }
        }

        var payload = new Dictionary<string, object>
        {
            ["contents"] = contents
        };

        if (!string.IsNullOrEmpty(systemInstruction))
        {
            payload["systemInstruction"] = new
            {
                parts = new[]
                {
                    new { text = systemInstruction }
                }
            };
        }

        if (request.Temperature.HasValue)
        {
            payload["generationConfig"] = new
            {
                temperature = request.Temperature.Value,
                maxOutputTokens = request.MaxTokens ?? 2048
            };
        }

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        // 스트리밍 엔드포인트 사용
        var response = await client.PostAsync($"{baseUrl}/models/{model}:streamGenerateContent?key={apiKey}", content, cancellationToken);
        response.EnsureSuccessStatusCode();

        return await response.Content.ReadAsStreamAsync(cancellationToken);
    }

    private async Task<AiResponseDto> CallPerplexityAsync(ApiService service, string model, ChatMessageRequestDto request, CancellationToken cancellationToken)
    {
        var startTime = DateTime.UtcNow;
        
        var apiKey = GetApiKey("perplexity", "AiApiSettings:Perplexity:ApiKey");
        var baseUrl = _configuration["AiApiSettings:Perplexity:BaseUrl"] ?? "https://api.perplexity.ai";

        if (string.IsNullOrEmpty(apiKey))
        {
            throw new InvalidOperationException("Perplexity API key is not configured");
        }

        var client = _httpClientFactory.CreateClient("perplexity");
        client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);

        // 언어 지시 추가
        var messagesWithLanguage = AddLanguageInstruction(request.Messages.ToList(), request.Language);

        // Perplexity는 OpenAI와 유사한 형식 사용
        var messages = messagesWithLanguage.Select(m => new
        {
            role = m.Role,
            content = m.Content
        }).ToList();

        var payload = new
        {
            model = model,
            messages = messages,
            temperature = request.Temperature,
            max_tokens = request.MaxTokens,
            stream = false
        };

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await client.PostAsync($"{baseUrl}/chat/completions", content, cancellationToken);
        
        var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError("Perplexity API error. Status: {StatusCode}, Response: {Response}", response.StatusCode, responseJson);
            if (response.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
            {
                _apiKeyPool?.MarkAsCoolingDown("perplexity", apiKey ?? "");
                throw new HttpRequestException($"Perplexity API 429 Too Many Requests - {responseJson}", null, response.StatusCode);
            }
            throw new InvalidOperationException($"Perplexity API error: {response.StatusCode} - {responseJson}");
        }

        try
        {
            var jsonOptions = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
            var perplexityResponse = JsonSerializer.Deserialize<OpenAiResponse>(responseJson, jsonOptions);

            if (perplexityResponse == null || perplexityResponse.Choices == null || perplexityResponse.Choices.Count == 0)
            {
                throw new InvalidOperationException($"Invalid response from Perplexity - no choices in response. Response: {responseJson}");
            }

            var choice = perplexityResponse.Choices[0];
            var usage = perplexityResponse.Usage;

            // Perplexity citations 추출 (response에 citations 필드가 있을 수 있음)
            List<string>? citations = null;
            try
            {
                using var doc = System.Text.Json.JsonDocument.Parse(responseJson);
                if (doc.RootElement.TryGetProperty("citations", out var citationsElement))
                {
                    citations = citationsElement.EnumerateArray()
                        .Select(c => c.GetString())
                        .Where(url => !string.IsNullOrEmpty(url))
                        .Select(url => url!)
                        .ToList();
                }
            }
            catch
            {
                // citations 추출 실패 시 무시
            }

            return new AiResponseDto
            {
                Content = choice.Message?.Content ?? "",
                Model = perplexityResponse.Model ?? model,
                FinishReason = choice.FinishReason ?? "stop",
                PromptTokens = usage?.PromptTokens ?? 0,
                CompletionTokens = usage?.CompletionTokens ?? 0,
                TotalTokens = usage?.TotalTokens ?? 0,
                ResponseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds,
                Citations = citations
            };
        }
        catch (JsonException ex)
        {
            _logger.LogError(ex, "Failed to deserialize Perplexity response. Response: {Response}", responseJson);
            throw new InvalidOperationException($"Failed to parse Perplexity response: {ex.Message}. Response: {responseJson}", ex);
        }
    }

    private async Task<Stream> CallPerplexityStreamAsync(ApiService service, string model, ChatMessageRequestDto request, CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("perplexity", "AiApiSettings:Perplexity:ApiKey");
        var baseUrl = _configuration["AiApiSettings:Perplexity:BaseUrl"] ?? "https://api.perplexity.ai";

        if (string.IsNullOrEmpty(apiKey))
        {
            throw new InvalidOperationException("Perplexity API key is not configured");
        }

        var client = _httpClientFactory.CreateClient("perplexity");
        client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);

        var messages = request.Messages.Select(m => new
        {
            role = m.Role,
            content = m.Content
        }).ToList();

        var payload = new
        {
            model = model,
            messages = messages,
            temperature = request.Temperature,
            max_tokens = request.MaxTokens,
            stream = true
        };

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await client.PostAsync($"{baseUrl}/chat/completions", content, cancellationToken);
        response.EnsureSuccessStatusCode();

        return await response.Content.ReadAsStreamAsync(cancellationToken);
    }

    private async Task<AiResponseDto> CallMistralAsync(ApiService service, string model, ChatMessageRequestDto request, CancellationToken cancellationToken)
    {
        var startTime = DateTime.UtcNow;
        
        var apiKey = GetApiKey("mistral", "AiApiSettings:Mistral:ApiKey");
        var baseUrl = _configuration["AiApiSettings:Mistral:BaseUrl"] ?? "https://api.mistral.ai/v1";

        if (string.IsNullOrEmpty(apiKey))
        {
            _logger.LogError("Mistral API key is not configured");
            throw new InvalidOperationException("Mistral API key is not configured");
        }

        var client = _httpClientFactory.CreateClient("mistral");
        client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);

        // 언어 지시 추가
        var messagesWithLanguage = AddLanguageInstruction(request.Messages.ToList(), request.Language);

        // Mistral은 OpenAI와 유사한 형식 사용
        var messages = messagesWithLanguage.Select(m => new
        {
            role = m.Role,
            content = m.Content
        }).ToList();

        var payload = new
        {
            model = model,
            messages = messages,
            temperature = request.Temperature,
            max_tokens = request.MaxTokens,
            stream = false
        };

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await client.PostAsync($"{baseUrl}/chat/completions", content, cancellationToken);
        
        var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError("Mistral API error. Status: {StatusCode}, Response: {Response}", response.StatusCode, responseJson);
            if (response.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
            {
                _apiKeyPool?.MarkAsCoolingDown("mistral", apiKey ?? "");
                throw new HttpRequestException($"Mistral API 429 Too Many Requests - {responseJson}", null, response.StatusCode);
            }
            throw new InvalidOperationException($"Mistral API error: {response.StatusCode} - {responseJson}");
        }

        try
        {
            // Mistral API는 OpenAI와 동일한 응답 형식 사용
            var jsonOptions = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
            var mistralResponse = JsonSerializer.Deserialize<OpenAiResponse>(responseJson, jsonOptions);

            if (mistralResponse == null || mistralResponse.Choices == null || mistralResponse.Choices.Count == 0)
            {
                throw new InvalidOperationException($"Invalid response from Mistral - no choices in response. Response: {responseJson}");
            }

            var choice = mistralResponse.Choices[0];
            var usage = mistralResponse.Usage;

            return new AiResponseDto
            {
                Content = choice.Message?.Content ?? "",
                Model = mistralResponse.Model ?? model,
                FinishReason = choice.FinishReason ?? "stop",
                PromptTokens = usage?.PromptTokens ?? 0,
                CompletionTokens = usage?.CompletionTokens ?? 0,
                TotalTokens = usage?.TotalTokens ?? 0,
                ResponseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds
            };
        }
        catch (JsonException ex)
        {
            _logger.LogError(ex, "Failed to deserialize Mistral response. Response: {Response}", responseJson);
            throw new InvalidOperationException($"Failed to parse Mistral response: {ex.Message}. Response: {responseJson}", ex);
        }
    }

    private async Task<Stream> CallMistralStreamAsync(ApiService service, string model, ChatMessageRequestDto request, CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("mistral", "AiApiSettings:Mistral:ApiKey");
        var baseUrl = _configuration["AiApiSettings:Mistral:BaseUrl"] ?? "https://api.mistral.ai/v1";

        if (string.IsNullOrEmpty(apiKey))
        {
            throw new InvalidOperationException("Mistral API key is not configured");
        }

        var client = _httpClientFactory.CreateClient("mistral");
        client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);

        // 언어 지시 추가
        var messagesWithLanguage = AddLanguageInstruction(request.Messages.ToList(), request.Language);

        var messages = messagesWithLanguage.Select(m => new
        {
            role = m.Role,
            content = m.Content
        }).ToList();

        var payload = new
        {
            model = model,
            messages = messages,
            temperature = request.Temperature,
            max_tokens = request.MaxTokens,
            stream = true
        };

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await client.PostAsync($"{baseUrl}/chat/completions", content, cancellationToken);
        response.EnsureSuccessStatusCode();

        return await response.Content.ReadAsStreamAsync(cancellationToken);
    }

    private async Task<AiResponseDto> CallCopilotAsync(ApiService service, string model, ChatMessageRequestDto request, CancellationToken cancellationToken)
    {
        var startTime = DateTime.UtcNow;
        
        // GitHub Copilot Chat API는 X-Github-Token 헤더 사용
        var githubToken = GetApiKey("copilot", "AiApiSettings:Copilot:ApiKey") ?? _configuration["AiApiSettings:Copilot:GithubToken"];
        var baseUrl = service.ApiEndpoint ?? _configuration["AiApiSettings:Copilot:BaseUrl"] ?? "https://api.githubcopilot.com";

        if (string.IsNullOrEmpty(githubToken))
        {
            _logger.LogError("GitHub Copilot API token is not configured");
            throw new InvalidOperationException("GitHub Copilot API token is not configured. Please set AiApiSettings:Copilot:ApiKey or AiApiSettings:Copilot:GithubToken in appsettings.json");
        }

        var client = _httpClientFactory.CreateClient("openai");
        // GitHub Copilot은 X-Github-Token 헤더 사용 (Bearer가 아님)
        client.DefaultRequestHeaders.Add("X-Github-Token", githubToken);

        // 언어 지시 추가
        var messagesWithLanguage = AddLanguageInstruction(request.Messages.ToList(), request.Language);

        // GitHub Copilot Chat API는 OpenAI API 형식 사용
        var messages = messagesWithLanguage.Select(m => new
        {
            role = m.Role,
            content = m.Content
        }).ToList();

        var payload = new
        {
            model = model ?? "gpt-4o", // 기본 모델
            messages = messages,
            temperature = request.Temperature,
            max_tokens = request.MaxTokens,
            stream = false
        };

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        _logger.LogInformation("Calling GitHub Copilot Chat API. Endpoint: {Endpoint}/chat/completions", baseUrl);

        var response = await client.PostAsync($"{baseUrl}/chat/completions", content, cancellationToken);
        
        var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError("GitHub Copilot API error. Status: {StatusCode}, Response: {Response}", response.StatusCode, responseJson);
            
            if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized || 
                response.StatusCode == System.Net.HttpStatusCode.Forbidden)
            {
                throw new InvalidOperationException(
                    $"GitHub Copilot API 인증 실패. GitHub 토큰이 유효하지 않거나 만료되었을 수 있습니다. " +
                    $"GitHub Settings > Developer settings > Personal access tokens에서 토큰을 발급받아주세요. " +
                    $"에러 응답: {responseJson}"
                );
            }
            
            throw new HttpRequestException($"GitHub Copilot API returned {response.StatusCode}: {responseJson}");
        }

        try
        {
            // GitHub Copilot Chat API는 OpenAI와 동일한 응답 형식 사용
            var jsonOptions = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
            var copilotResponse = JsonSerializer.Deserialize<OpenAiResponse>(responseJson, jsonOptions);

            if (copilotResponse == null || copilotResponse.Choices == null || copilotResponse.Choices.Count == 0)
            {
                throw new InvalidOperationException($"Invalid response from GitHub Copilot - no choices in response. Response: {responseJson}");
            }

            var choice = copilotResponse.Choices[0];
            var usage = copilotResponse.Usage;

            return new AiResponseDto
            {
                Content = choice.Message?.Content ?? "",
                Model = copilotResponse.Model ?? model ?? "gpt-4",
                FinishReason = choice.FinishReason ?? "stop",
                PromptTokens = usage?.PromptTokens ?? 0,
                CompletionTokens = usage?.CompletionTokens ?? 0,
                TotalTokens = usage?.TotalTokens ?? 0,
                ResponseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds
            };
        }
        catch (JsonException ex)
        {
            _logger.LogError(ex, "Failed to deserialize GitHub Copilot response. Response: {Response}", responseJson);
            throw new InvalidOperationException($"Failed to parse GitHub Copilot response: {ex.Message}. Response: {responseJson}", ex);
        }
    }

    private async Task<Stream> CallCopilotStreamAsync(ApiService service, string model, ChatMessageRequestDto request, CancellationToken cancellationToken)
    {
        var githubToken = GetApiKey("copilot", "AiApiSettings:Copilot:ApiKey") ?? _configuration["AiApiSettings:Copilot:GithubToken"];
        var baseUrl = service.ApiEndpoint ?? _configuration["AiApiSettings:Copilot:BaseUrl"] ?? "https://api.githubcopilot.com";

        if (string.IsNullOrEmpty(githubToken))
        {
            throw new InvalidOperationException("GitHub Copilot API token is not configured");
        }

        var client = _httpClientFactory.CreateClient("openai");
        client.DefaultRequestHeaders.Add("X-Github-Token", githubToken);

        // 언어 지시 추가
        var messagesWithLanguage = AddLanguageInstruction(request.Messages.ToList(), request.Language);

        var messages = messagesWithLanguage.Select(m => new
        {
            role = m.Role,
            content = m.Content
        }).ToList();

        var payload = new
        {
            model = model ?? "gpt-4o",
            messages = messages,
            temperature = request.Temperature,
            max_tokens = request.MaxTokens,
            stream = true
        };

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await client.PostAsync($"{baseUrl}/chat/completions", content, cancellationToken);
        response.EnsureSuccessStatusCode();

        return await response.Content.ReadAsStreamAsync(cancellationToken);
    }

    private async Task<bool> TestCopilotConnectionAsync(CancellationToken cancellationToken)
    {
        var githubToken = GetApiKey("copilot", "AiApiSettings:Copilot:ApiKey") ?? _configuration["AiApiSettings:Copilot:GithubToken"];
        if (string.IsNullOrEmpty(githubToken))
        {
            return false;
        }

        try
        {
            var client = _httpClientFactory.CreateClient("openai");
            client.DefaultRequestHeaders.Add("X-Github-Token", githubToken);
            client.Timeout = TimeSpan.FromSeconds(5);

            // 간단한 테스트 요청
            var payload = new
            {
                model = "gpt-4",
                messages = new[] { new { role = "user", content = "Hi" } },
                max_tokens = 1
            };

            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var response = await client.PostAsync("https://api.githubcopilot.com/chat/completions", content, cancellationToken);
            
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    private List<string> GetCopilotModels()
    {
        // Microsoft Copilot (Azure OpenAI)
        return new List<string>
        {
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4",
            "gpt-35-turbo"
        };
    }

    private async Task<AiResponseDto> CallAzureOpenAiAsync(ApiService service, string model, ChatMessageRequestDto request, CancellationToken cancellationToken)
    {
        var startTime = DateTime.UtcNow;
        
        // Azure OpenAI Service 설정
        var apiKey = GetApiKey("azureopenai", "AiApiSettings:AzureOpenAI:ApiKey");
        var resourceName = _configuration["AiApiSettings:AzureOpenAI:ResourceName"];
        var apiVersion = _configuration["AiApiSettings:AzureOpenAI:ApiVersion"] ?? "2024-02-15-preview";
        
        // BaseUrl이 설정되어 있으면 사용, 없으면 ResourceName으로 구성
        var baseUrl = service.ApiEndpoint;
        if (string.IsNullOrEmpty(baseUrl))
        {
            if (!string.IsNullOrEmpty(resourceName))
            {
                baseUrl = $"https://{resourceName}.openai.azure.com/openai/v1";
            }
            else
            {
                baseUrl = _configuration["AiApiSettings:AzureOpenAI:BaseUrl"];
            }
        }

        if (string.IsNullOrEmpty(apiKey))
        {
            _logger.LogError("Azure OpenAI API key is not configured");
            throw new InvalidOperationException(
                "Azure OpenAI API key is not configured. " +
                "Please set AiApiSettings:AzureOpenAI:ApiKey and AiApiSettings:AzureOpenAI:ResourceName in appsettings.json"
            );
        }

        if (string.IsNullOrEmpty(baseUrl))
        {
            throw new InvalidOperationException(
                "Azure OpenAI BaseUrl or ResourceName is not configured. " +
                "Please set AiApiSettings:AzureOpenAI:BaseUrl or AiApiSettings:AzureOpenAI:ResourceName in appsettings.json"
            );
        }

        var client = _httpClientFactory.CreateClient("openai");
        client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("api-key", apiKey);

        // 언어 지시 추가
        var messagesWithLanguage = AddLanguageInstruction(request.Messages.ToList(), request.Language);

        // Azure OpenAI는 OpenAI와 동일한 형식 사용
        var messages = new List<object>();
        
        foreach (var m in messagesWithLanguage)
        {
            if (m.Contents != null && m.Contents.Count > 0)
            {
                var contentList = new List<object>();
                var textParts = new List<string>();
                
                foreach (var c in m.Contents)
                {
                    var contentType = c.Type.ToLower();
                    if (contentType == "text" && !string.IsNullOrEmpty(c.Text))
                    {
                        textParts.Add(c.Text);
                    }
                    else if (contentType == "image_url" && !string.IsNullOrEmpty(c.ImageUrl))
                    {
                        contentList.Add(new { type = "image_url", image_url = new { url = c.ImageUrl } });
                    }
                }
                
                if (textParts.Count > 0)
                {
                    contentList.Insert(0, new { type = "text", text = string.Join("\n", textParts) });
                }
                
                if (contentList.Count > 0)
                {
                    messages.Add(new { role = m.Role, content = contentList });
                }
            }
            else if (!string.IsNullOrEmpty(m.Content))
            {
                messages.Add(new { role = m.Role, content = m.Content });
            }
        }

        // Azure OpenAI는 배포 이름을 모델로 사용 (예: gpt-4o, gpt-35-turbo)
        var deploymentName = model ?? service.DefaultModel ?? "gpt-4o";
        
        var payload = new
        {
            model = deploymentName,
            messages = messages,
            temperature = request.Temperature,
            max_tokens = request.MaxTokens,
            stream = false
        };

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        // Azure OpenAI는 api-version 쿼리 파라미터 필요
        var url = $"{baseUrl}/chat/completions?api-version={apiVersion}";
        
        _logger.LogInformation("Calling Azure OpenAI Service. Endpoint: {Url}, Deployment: {Deployment}", url, deploymentName);

        var response = await client.PostAsync(url, content, cancellationToken);
        
        var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError("Azure OpenAI API error. Status: {StatusCode}, Response: {Response}", response.StatusCode, responseJson);

            if (response.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
            {
                _apiKeyPool?.MarkAsCoolingDown("azureopenai", apiKey ?? "");
                throw new HttpRequestException($"Azure OpenAI API 429 Too Many Requests - {responseJson}", null, response.StatusCode);
            }

            if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized ||
                response.StatusCode == System.Net.HttpStatusCode.Forbidden)
            {
                throw new InvalidOperationException(
                    $"Azure OpenAI API 인증 실패. API 키 또는 리소스 이름이 올바르지 않을 수 있습니다. " +
                    $"Azure Portal에서 Azure OpenAI 리소스의 키와 엔드포인트를 확인해주세요. " +
                    $"에러 응답: {responseJson}"
                );
            }

            throw new HttpRequestException($"Azure OpenAI API returned {response.StatusCode}: {responseJson}");
        }

        try
        {
            var jsonOptions = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
            var azureResponse = JsonSerializer.Deserialize<OpenAiResponse>(responseJson, jsonOptions);

            if (azureResponse == null || azureResponse.Choices == null || azureResponse.Choices.Count == 0)
            {
                throw new InvalidOperationException($"Invalid response from Azure OpenAI - no choices in response. Response: {responseJson}");
            }

            var choice = azureResponse.Choices[0];
            var usage = azureResponse.Usage;

            return new AiResponseDto
            {
                Content = choice.Message?.Content ?? "",
                Model = azureResponse.Model ?? deploymentName,
                FinishReason = choice.FinishReason ?? "stop",
                PromptTokens = usage?.PromptTokens ?? 0,
                CompletionTokens = usage?.CompletionTokens ?? 0,
                TotalTokens = usage?.TotalTokens ?? 0,
                ResponseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds
            };
        }
        catch (JsonException ex)
        {
            _logger.LogError(ex, "Failed to deserialize Azure OpenAI response. Response: {Response}", responseJson);
            throw new InvalidOperationException($"Failed to parse Azure OpenAI response: {ex.Message}. Response: {responseJson}", ex);
        }
    }

    private async Task<Stream> CallAzureOpenAiStreamAsync(ApiService service, string model, ChatMessageRequestDto request, CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("azureopenai", "AiApiSettings:AzureOpenAI:ApiKey");
        var resourceName = _configuration["AiApiSettings:AzureOpenAI:ResourceName"];
        var apiVersion = _configuration["AiApiSettings:AzureOpenAI:ApiVersion"] ?? "2024-02-15-preview";
        
        var baseUrl = service.ApiEndpoint;
        if (string.IsNullOrEmpty(baseUrl))
        {
            if (!string.IsNullOrEmpty(resourceName))
            {
                baseUrl = $"https://{resourceName}.openai.azure.com/openai/v1";
            }
            else
            {
                baseUrl = _configuration["AiApiSettings:AzureOpenAI:BaseUrl"];
            }
        }

        if (string.IsNullOrEmpty(apiKey) || string.IsNullOrEmpty(baseUrl))
        {
            throw new InvalidOperationException("Azure OpenAI API key or BaseUrl is not configured");
        }

        var client = _httpClientFactory.CreateClient("openai");
        client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("api-key", apiKey);

        var messagesWithLanguage = AddLanguageInstruction(request.Messages.ToList(), request.Language);

        var messages = messagesWithLanguage.Select(m => new
        {
            role = m.Role,
            content = m.Content
        }).ToList();

        var deploymentName = model ?? service.DefaultModel ?? "gpt-4o";

        var payload = new
        {
            model = deploymentName,
            messages = messages,
            temperature = request.Temperature,
            max_tokens = request.MaxTokens,
            stream = true
        };

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var url = $"{baseUrl}/chat/completions?api-version={apiVersion}";
        var response = await client.PostAsync(url, content, cancellationToken);
        response.EnsureSuccessStatusCode();

        return await response.Content.ReadAsStreamAsync(cancellationToken);
    }

    private async Task<bool> TestAzureOpenAiConnectionAsync(CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("azureopenai", "AiApiSettings:AzureOpenAI:ApiKey");
        var resourceName = _configuration["AiApiSettings:AzureOpenAI:ResourceName"];
        var apiVersion = _configuration["AiApiSettings:AzureOpenAI:ApiVersion"] ?? "2024-02-15-preview";
        
        var baseUrl = _configuration["AiApiSettings:AzureOpenAI:BaseUrl"];
        if (string.IsNullOrEmpty(baseUrl) && !string.IsNullOrEmpty(resourceName))
        {
            baseUrl = $"https://{resourceName}.openai.azure.com/openai/v1";
        }

        if (string.IsNullOrEmpty(apiKey) || string.IsNullOrEmpty(baseUrl))
        {
            return false;
        }

        try
        {
            var client = _httpClientFactory.CreateClient("openai");
            client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("api-key", apiKey);
            client.Timeout = TimeSpan.FromSeconds(5);

            var payload = new
            {
                model = "gpt-4",
                messages = new[] { new { role = "user", content = "Hi" } },
                max_tokens = 1
            };

            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var url = $"{baseUrl}/chat/completions?api-version={apiVersion}";
            var response = await client.PostAsync(url, content, cancellationToken);
            
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    private List<string> GetAzureOpenAiModels()
    {
        // Azure OpenAI는 배포 이름을 사용하므로 일반적인 배포 이름 반환
        // 실제 배포 이름은 Azure Portal에서 확인 필요
        return new List<string>
        {
            "gpt-4",
            "gpt-4-turbo",
            "gpt-35-turbo",
            "gpt-4o",
            "gpt-4o-mini"
        };
    }

    public async Task<decimal> CalculateCostAsync(int serviceId, string model, int promptTokens, int completionTokens)
    {
        var service = await _context.ApiServices.FindAsync([serviceId]);
        if (service == null)
        {
            return 0;
        }

        // 간단한 비용 계산 (실제로는 모델별로 다른 가격 적용 필요)
        var totalTokens = promptTokens + completionTokens;
        return service.CostPerRequest * totalTokens / 1000; // per 1K tokens
    }

    public async Task<List<string>> GetAvailableModelsAsync(int serviceId, CancellationToken cancellationToken = default)
    {
        var service = await _context.ApiServices.FindAsync([serviceId], cancellationToken);
        if (service == null || !service.IsActive)
        {
            throw new InvalidOperationException($"Service {serviceId} not found or inactive");
        }

        // DB에서 활성화된 모델 목록 조회
        var dbModels = await _context.ApiServiceModels
            .Where(m => m.ServiceId == serviceId && m.IsActive)
            .OrderBy(m => m.SortOrder)
            .ThenBy(m => m.ModelName)
            .Select(m => m.ModelName)
            .ToListAsync(cancellationToken);

        if (dbModels.Any())
        {
            _logger.LogInformation("Found {Count} models in DB for service {ServiceId} ({ServiceCode})", 
                dbModels.Count, serviceId, service.ServiceCode);
            return dbModels;
        }

        // DB에 모델이 없으면 기존 API 호출 방식으로 폴백
        _logger.LogWarning("No models found in DB for service {ServiceId} ({ServiceCode}), falling back to API call", 
            serviceId, service.ServiceCode);

        var serviceCode = service.ServiceCode.ToLower();
        
        try
        {
            return serviceCode switch
            {
                "chatgpt" or "openai" => await GetOpenAiModelsAsync(cancellationToken),
                "claude" or "anthropic" => GetClaudeModels(),
                "gemini" or "google" => await GetGeminiModelsAsync(cancellationToken),
                "perplexity" => await GetPerplexityModelsAsync(cancellationToken),
                "mistral" => GetMistralModels(),
                "copilot" => GetAzureOpenAiModels(), // Microsoft Copilot (Azure OpenAI)
                "cursor" => GetCopilotModels(), // GitHub Copilot API
                "azure-openai" or "microsoft-copilot" => GetAzureOpenAiModels(),
                "dalle" => new List<string> { "dall-e-3", "dall-e-2" },
                "gemini-image" => await GetGeminiImageModelsAsync(cancellationToken),
                "imagen4" => new List<string> { "imagen-4.0" },
                "gen4-image" => new List<string> { "imagegeneration@006" },
                "flux2" => new List<string> { "flux-2", "flux-2.1" },
                "gen4-video" => new List<string> { "videogeneration@006", "videogeneration@006-hd" },
                "veo" => new List<string> { "veo-3.1", "veo-3.0" },
                "openai-video" or "sora" => new List<string> { "sora-2", "sora-1.5" },
                _ => GetDefaultModels(serviceCode, service.ServiceName)
            };
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Error fetching models for service {ServiceCode}, returning default models", serviceCode);
            return GetDefaultModels(serviceCode, service.ServiceName);
        }
    }

    public async Task<bool> TestServiceConnectionAsync(int serviceId, CancellationToken cancellationToken = default)
    {
        var service = await _context.ApiServices.FindAsync([serviceId], cancellationToken);
        if (service == null || !service.IsActive)
        {
            return false;
        }

        var serviceCode = service.ServiceCode.ToLower();
        
        try
        {
            return serviceCode switch
            {
                "chatgpt" or "openai" => await TestOpenAiConnectionAsync(cancellationToken),
                "claude" or "anthropic" => await TestClaudeConnectionAsync(cancellationToken),
                "gemini" or "google" => await TestGeminiConnectionAsync(cancellationToken),
                "perplexity" => await TestPerplexityConnectionAsync(cancellationToken),
                "mistral" => await TestMistralConnectionAsync(cancellationToken),
                "copilot" => await TestAzureOpenAiConnectionAsync(cancellationToken), // Microsoft Copilot (Azure OpenAI)
                "cursor" => await TestCopilotConnectionAsync(cancellationToken), // GitHub Copilot API
                "azure-openai" or "microsoft-copilot" => await TestAzureOpenAiConnectionAsync(cancellationToken),
                "dalle" => await TestOpenAiConnectionAsync(cancellationToken), // DALL-E는 OpenAI와 동일한 API 키 사용
                "gemini-image" => await TestGeminiConnectionAsync(cancellationToken),
                "imagen4" => await TestGeminiConnectionAsync(cancellationToken), // Imagen은 Google API 사용
                "gen4-image" => await TestGeminiConnectionAsync(cancellationToken),
                "gen4-video" => await TestGeminiConnectionAsync(cancellationToken),
                "veo" => await TestGeminiConnectionAsync(cancellationToken),
                "openai-video" or "sora" => await TestOpenAiConnectionAsync(cancellationToken), // OpenAI Video (Sora)는 OpenAI API 사용
                _ => false // 알 수 없는 서비스는 연결 불가로 처리
            };
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Error testing connection for service {ServiceCode}", serviceCode);
            return false;
        }
    }

    private async Task<bool> TestOpenAiConnectionAsync(CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("openai", "AiApiSettings:OpenAI:ApiKey");
        if (string.IsNullOrEmpty(apiKey))
        {
            return false;
        }

        try
        {
            var client = _httpClientFactory.CreateClient("openai");
            client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);
            client.Timeout = TimeSpan.FromSeconds(5);

            var response = await client.GetAsync("https://api.openai.com/v1/models?limit=1", cancellationToken);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    private async Task<bool> TestClaudeConnectionAsync(CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("claude", "AiApiSettings:Claude:ApiKey");
        if (string.IsNullOrEmpty(apiKey))
        {
            return false;
        }

        // Claude는 간단한 메시지 API 호출로 테스트
        try
        {
            var client = _httpClientFactory.CreateClient("claude");
            client.DefaultRequestHeaders.Add("x-api-key", apiKey);
            client.DefaultRequestHeaders.Add("anthropic-version", "2023-06-01");
            client.Timeout = TimeSpan.FromSeconds(5);

            var payload = new
            {
                model = "claude-3-haiku-20240307",
                max_tokens = 1,
                messages = new[] { new { role = "user", content = "Hi" } }
            };

            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var response = await client.PostAsync("https://api.anthropic.com/v1/messages", content, cancellationToken);
            
            // 401, 403은 API 키 문제, 200은 성공, 나머지는 실패
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    private async Task<bool> TestGeminiConnectionAsync(CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("gemini", "AiApiSettings:Gemini:ApiKey");
        if (string.IsNullOrEmpty(apiKey))
        {
            return false;
        }

        try
        {
            var client = _httpClientFactory.CreateClient("gemini");
            client.Timeout = TimeSpan.FromSeconds(5);

            var response = await client.GetAsync($"https://generativelanguage.googleapis.com/v1beta/models?key={apiKey}", cancellationToken);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    private async Task<bool> TestPerplexityConnectionAsync(CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("perplexity", "AiApiSettings:Perplexity:ApiKey");
        if (string.IsNullOrEmpty(apiKey))
        {
            return false;
        }

        // Perplexity는 간단한 채팅 API 호출로 테스트
        try
        {
            var client = _httpClientFactory.CreateClient("perplexity");
            client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);
            client.Timeout = TimeSpan.FromSeconds(5);

            var payload = new
            {
                model = "sonar",
                messages = new[] { new { role = "user", content = "Hi" } },
                max_tokens = 1
            };

            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var response = await client.PostAsync("https://api.perplexity.ai/chat/completions", content, cancellationToken);
            
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    private async Task<bool> TestMistralConnectionAsync(CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("mistral", "AiApiSettings:Mistral:ApiKey");
        if (string.IsNullOrEmpty(apiKey))
        {
            return false;
        }

        try
        {
            var client = _httpClientFactory.CreateClient("mistral");
            client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);
            client.Timeout = TimeSpan.FromSeconds(5);

            // Mistral은 모델 목록 API가 없으므로 간단한 채팅 요청으로 테스트
            var payload = new
            {
                model = "mistral-small-latest",
                messages = new[] { new { role = "user", content = "Hi" } },
                max_tokens = 1
            };

            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var response = await client.PostAsync("https://api.mistral.ai/v1/chat/completions", content, cancellationToken);
            
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    private async Task<List<string>> GetOpenAiModelsAsync(CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("openai", "AiApiSettings:OpenAI:ApiKey");
        var baseUrl = _configuration["AiApiSettings:OpenAI:BaseUrl"] ?? "https://api.openai.com/v1";

        if (string.IsNullOrEmpty(apiKey))
        {
            // API 키가 없으면 기본 모델 목록 반환
            return new List<string> { "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-4o", "gpt-4o-mini", "o3", "o3-mini", "o1", "o1-mini" };
        }

        try
        {
            var client = _httpClientFactory.CreateClient("openai");
            client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);
            client.Timeout = TimeSpan.FromSeconds(10); // 모델 목록 조회는 빠르게

            var response = await client.GetAsync($"{baseUrl}/models", cancellationToken);
            if (response.IsSuccessStatusCode)
            {
                var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);
                var jsonOptions = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                var modelsResponse = JsonSerializer.Deserialize<OpenAiModelsResponse>(responseJson, jsonOptions);

                if (modelsResponse?.Data != null)
                {
                    // 채팅에 사용 가능한 모델만 필터링 (gpt로 시작하는 모델)
                    var chatModels = modelsResponse.Data
                        .Where(m => m.Id != null && (m.Id.StartsWith("gpt-", StringComparison.OrdinalIgnoreCase)))
                        .Select(m => m.Id!)
                        .OrderBy(m => m)
                        .ToList();

                    if (chatModels.Any())
                    {
                        return chatModels;
                    }
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to fetch OpenAI models from API");
        }

        // 기본 모델 목록 반환
        return new List<string> { "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-4o", "gpt-4o-mini", "o3", "o3-mini", "o1", "o1-mini" };
    }

    private List<string> GetClaudeModels()
    {
        // Anthropic은 모델 목록 API가 없으므로 고정 목록 반환
        return new List<string>
        {
            "claude-opus-4-6",
            "claude-sonnet-4-6",
            "claude-haiku-4-5-20251001",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307"
        };
    }

    private async Task<List<string>> GetGeminiModelsAsync(CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("gemini", "AiApiSettings:Gemini:ApiKey");
        var baseUrl = _configuration["AiApiSettings:Gemini:BaseUrl"] ?? "https://generativelanguage.googleapis.com/v1beta";

        if (string.IsNullOrEmpty(apiKey))
        {
            return new List<string> { "gemini-3.1-pro-preview", "gemini-3.1-flash-lite-preview", "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash" };
        }

        try
        {
            var client = _httpClientFactory.CreateClient("gemini");
            client.Timeout = TimeSpan.FromSeconds(10);

            var response = await client.GetAsync($"{baseUrl}/models?key={apiKey}", cancellationToken);
            if (response.IsSuccessStatusCode)
            {
                var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);
                var jsonOptions = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                var modelsResponse = JsonSerializer.Deserialize<GeminiModelsResponse>(responseJson, jsonOptions);

                if (modelsResponse?.Models != null)
                {
                    // generateContent를 지원하는 모델만 필터링
                    var allModels = modelsResponse.Models
                        .Where(m => m.Name != null && 
                            (m.SupportedGenerationMethods?.Contains("generateContent") == true))
                        .Select(m => m.Name!.Replace("models/", ""))
                        .ToList();

                    // 안정적인 모델만 필터링 (preview, exp, experimental 제외 또는 별도 표시)
                    // 주요 안정 모델 우선 표시
                    var stableModels = allModels
                        .Where(m => !m.Contains("-exp-", StringComparison.OrdinalIgnoreCase) &&
                                   !m.Contains("-experimental", StringComparison.OrdinalIgnoreCase) &&
                                   !m.Contains("robotics", StringComparison.OrdinalIgnoreCase) &&
                                   !m.Contains("computer-use", StringComparison.OrdinalIgnoreCase) &&
                                   !m.Contains("gemma", StringComparison.OrdinalIgnoreCase) &&
                                   !m.Contains("nano-banana", StringComparison.OrdinalIgnoreCase) &&
                                   !m.Contains("deep-research", StringComparison.OrdinalIgnoreCase))
                        .OrderBy(m => 
                        {
                            // 주요 모델 우선순위
                            if (m.Contains("gemini-2.5-pro", StringComparison.OrdinalIgnoreCase) && !m.Contains("preview", StringComparison.OrdinalIgnoreCase)) return 1;
                            if (m.Contains("gemini-2.5-flash", StringComparison.OrdinalIgnoreCase) && !m.Contains("preview", StringComparison.OrdinalIgnoreCase)) return 2;
                            if (m.Contains("gemini-2.0-flash", StringComparison.OrdinalIgnoreCase) && !m.Contains("exp", StringComparison.OrdinalIgnoreCase)) return 3;
                            if (m.Contains("gemini-1.5-pro", StringComparison.OrdinalIgnoreCase)) return 4;
                            if (m.Contains("gemini-1.5-flash", StringComparison.OrdinalIgnoreCase)) return 5;
                            if (m.Contains("preview", StringComparison.OrdinalIgnoreCase)) return 100; // preview는 뒤로
                            return 50; // 기타
                        })
                        .ThenBy(m => m)
                        .ToList();

                    // Preview 모델도 포함하되 뒤에 배치
                    var previewModels = allModels
                        .Where(m => m.Contains("-preview", StringComparison.OrdinalIgnoreCase) ||
                                   m.Contains("-exp-", StringComparison.OrdinalIgnoreCase))
                        .Where(m => !m.Contains("robotics", StringComparison.OrdinalIgnoreCase) &&
                                   !m.Contains("computer-use", StringComparison.OrdinalIgnoreCase) &&
                                   !m.Contains("gemma", StringComparison.OrdinalIgnoreCase) &&
                                   !m.Contains("nano-banana", StringComparison.OrdinalIgnoreCase) &&
                                   !m.Contains("deep-research", StringComparison.OrdinalIgnoreCase))
                        .OrderBy(m => m)
                        .ToList();

                    // 안정 모델 + Preview 모델 결합
                    var result = stableModels.Concat(previewModels).Distinct().ToList();

                    if (result.Any())
                    {
                        _logger.LogInformation("Gemini models filtered: {StableCount} stable, {PreviewCount} preview, Total: {TotalCount}", 
                            stableModels.Count, previewModels.Count, result.Count);
                        return result;
                    }
                    
                    // 필터링 결과가 없으면 전체 모델 반환
                    if (allModels.Any())
                    {
                        _logger.LogWarning("No filtered Gemini models found, returning all {Count} models", allModels.Count);
                        return allModels.OrderBy(m => m).ToList();
                    }
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to fetch Gemini models from API");
        }

        return new List<string> { "gemini-3.1-pro-preview", "gemini-3.1-flash-lite-preview", "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash" };
    }

    private async Task<List<string>> GetGeminiImageModelsAsync(CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("gemini", "AiApiSettings:Gemini:ApiKey");
        var baseUrl = _configuration["AiApiSettings:Gemini:BaseUrl"] ?? "https://generativelanguage.googleapis.com/v1beta";

        if (string.IsNullOrEmpty(apiKey))
        {
            return new List<string> { "gemini-3.1-pro-image-preview", "gemini-2.5-flash-image-preview" };
        }

        try
        {
            var client = _httpClientFactory.CreateClient("gemini");
            client.Timeout = TimeSpan.FromSeconds(10);

            var response = await client.GetAsync($"{baseUrl}/models?key={apiKey}", cancellationToken);
            if (response.IsSuccessStatusCode)
            {
                var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);
                var jsonOptions = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                var modelsResponse = JsonSerializer.Deserialize<GeminiModelsResponse>(responseJson, jsonOptions);

                if (modelsResponse?.Models != null)
                {
                    // 이미지 생성을 지원하는 모델 필터링 (generateContent 지원 + 이미지 관련 키워드)
                    var imageModels = modelsResponse.Models
                        .Where(m => m.Name != null && 
                            (m.SupportedGenerationMethods?.Contains("generateContent") == true) &&
                            (m.Name.Contains("image", StringComparison.OrdinalIgnoreCase) || 
                             m.Name.Contains("flash-image", StringComparison.OrdinalIgnoreCase)))
                        .Select(m => m.Name!.Replace("models/", ""))
                        .OrderBy(m => m)
                        .ToList();

                    if (imageModels.Any())
                    {
                        return imageModels;
                    }
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to fetch Gemini image models from API");
        }

        // 기본 이미지 생성 모델 목록
        return new List<string> { "gemini-3-pro-image-preview", "gemini-2.5-flash-image" };
    }

    private List<string> GetPerplexityModels()
    {
        // Perplexity AI 모델 목록 (공식 문서 기준)
        // Perplexity는 sonar와 sonar-pro 모델을 기본으로 제공하며,
        // 특정 llama 모델은 더 이상 지원되지 않을 수 있습니다.
        return new List<string>
        {
            "sonar",
            "sonar-pro",
            "llama-3.1-sonar-large-128k-online",
            "llama-3.1-sonar-small-128k-online",
            "llama-3.1-sonar-huge-128k-online"
        };
    }

    private List<string> GetMistralModels()
    {
        // Mistral AI 모델 목록 (공식 문서 기준)
        // Mistral은 여러 모델을 제공하며, -latest 접미사가 있는 모델은 항상 최신 버전을 가리킵니다.
        return new List<string>
        {
            "mistral-large-latest",
            "mistral-medium-latest",
            "mistral-small-latest",
            "open-mixtral-8x7b",
            "open-mixtral-8x22b",
            "open-mistral-7b"
        };
    }

    private Task<List<string>> GetPerplexityModelsAsync(CancellationToken cancellationToken)
    {
        // Perplexity API는 모델 목록 API가 없으므로 기본 목록 반환
        // Perplexity 공식 문서에 따르면 기본적으로 지원되는 모델:
        // - sonar: 기본 모델
        // - sonar-pro: Pro 모델
        // llama 기반 모델들은 API 키 권한이나 구독 플랜에 따라 다를 수 있음
        var apiKey = GetApiKey("perplexity", "AiApiSettings:Perplexity:ApiKey");
        
        if (string.IsNullOrEmpty(apiKey))
        {
            // API 키가 없으면 기본 모델만 반환
            return Task.FromResult(new List<string> { "sonar", "sonar-pro" });
        }

        // API 키가 있으면 기본 모델 목록 반환
        // 실제로는 API를 통해 테스트해봐야 하지만, 공식 문서 기준 기본 모델
        return Task.FromResult(new List<string>
        {
            "sonar",
            "sonar-pro"
        });
    }

    private List<string> GetDefaultModels(string serviceCode, string serviceName)
    {
        // 알 수 없는 서비스의 경우 기본 모델 목록 반환
        _logger.LogWarning("Unknown service code: {ServiceCode}, service name: {ServiceName}", serviceCode, serviceName);
        return new List<string> { "default-model" };
    }

    // OpenAI Models Response
    private class OpenAiModelsResponse
    {
        [System.Text.Json.Serialization.JsonPropertyName("data")]
        public List<OpenAiModel>? Data { get; set; }
    }

    private class OpenAiModel
    {
        [System.Text.Json.Serialization.JsonPropertyName("id")]
        public string? Id { get; set; }
    }

    // Gemini Models Response
    private class GeminiModelsResponse
    {
        [System.Text.Json.Serialization.JsonPropertyName("models")]
        public List<GeminiModel>? Models { get; set; }
    }

    private class GeminiModel
    {
        [System.Text.Json.Serialization.JsonPropertyName("name")]
        public string? Name { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("supportedGenerationMethods")]
        public List<string>? SupportedGenerationMethods { get; set; }
    }

    // OpenAI Response Models (OpenAI API uses snake_case)
    private class OpenAiResponse
    {
        [System.Text.Json.Serialization.JsonPropertyName("model")]
        public string? Model { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("choices")]
        public List<OpenAiChoice>? Choices { get; set; }

        // New Responses API format (gpt-5 이후 모델)
        [System.Text.Json.Serialization.JsonPropertyName("output")]
        public List<OpenAiOutputItem>? Output { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("usage")]
        public OpenAiUsage? Usage { get; set; }
    }

    private class OpenAiChoice
    {
        [System.Text.Json.Serialization.JsonPropertyName("message")]
        public OpenAiMessage? Message { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("finish_reason")]
        public string? FinishReason { get; set; }
    }

    private class OpenAiMessage
    {
        [System.Text.Json.Serialization.JsonPropertyName("content")]
        public string? Content { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("role")]
        public string? Role { get; set; }

        // 추론 모델(o1/o3/gpt-5) 전용 reasoning 필드
        [System.Text.Json.Serialization.JsonPropertyName("reasoning_content")]
        public string? ReasoningContent { get; set; }
    }

    // New Responses API (gpt-5+) — output 배열 내 항목
    private class OpenAiOutputItem
    {
        [System.Text.Json.Serialization.JsonPropertyName("type")]
        public string? Type { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("role")]
        public string? Role { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("status")]
        public string? Status { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("content")]
        public List<OpenAiOutputContent>? Content { get; set; }
    }

    private class OpenAiOutputContent
    {
        [System.Text.Json.Serialization.JsonPropertyName("type")]
        public string? Type { get; set; }

        // output_text 타입의 실제 텍스트
        [System.Text.Json.Serialization.JsonPropertyName("text")]
        public string? Text { get; set; }
    }

    private class OpenAiUsage
    {
        [System.Text.Json.Serialization.JsonPropertyName("prompt_tokens")]
        public int PromptTokens { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("completion_tokens")]
        public int CompletionTokens { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("total_tokens")]
        public int TotalTokens { get; set; }

        // New Responses API usage 필드명
        [System.Text.Json.Serialization.JsonPropertyName("input_tokens")]
        public int InputTokens { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("output_tokens")]
        public int OutputTokens { get; set; }
    }

    // Claude Response Models
    private class ClaudeResponse
    {
        public string? Model { get; set; }
        public List<ClaudeContent>? Content { get; set; }
        public string? StopReason { get; set; }
        public ClaudeUsage? Usage { get; set; }
    }

    private class ClaudeContent
    {
        public string? Type { get; set; }
        public string? Text { get; set; }
    }

    private class ClaudeUsage
    {
        public int InputTokens { get; set; }
        public int OutputTokens { get; set; }
    }

    // Gemini Response Models
    private class GeminiResponse
    {
        [System.Text.Json.Serialization.JsonPropertyName("candidates")]
        public List<GeminiCandidate>? Candidates { get; set; }
        
        [System.Text.Json.Serialization.JsonPropertyName("usageMetadata")]
        public GeminiUsageMetadata? UsageMetadata { get; set; }
    }

    private class GeminiCandidate
    {
        [System.Text.Json.Serialization.JsonPropertyName("content")]
        public GeminiContent? Content { get; set; }
        
        [System.Text.Json.Serialization.JsonPropertyName("finishReason")]
        public string? FinishReason { get; set; }
    }

    private class GeminiContent
    {
        [System.Text.Json.Serialization.JsonPropertyName("parts")]
        public List<GeminiPart>? Parts { get; set; }
    }

    private class GeminiPart
    {
        [System.Text.Json.Serialization.JsonPropertyName("text")]
        public string? Text { get; set; }
        
        [System.Text.Json.Serialization.JsonPropertyName("inlineData")]
        public GeminiInlineData? InlineData { get; set; }
    }

    private class GeminiInlineData
    {
        [System.Text.Json.Serialization.JsonPropertyName("mimeType")]
        public string? MimeType { get; set; }
        
        [System.Text.Json.Serialization.JsonPropertyName("data")]
        public string? Data { get; set; }
    }

    private class GeminiUsageMetadata
    {
        [System.Text.Json.Serialization.JsonPropertyName("promptTokenCount")]
        public int PromptTokenCount { get; set; }
        
        [System.Text.Json.Serialization.JsonPropertyName("candidatesTokenCount")]
        public int CandidatesTokenCount { get; set; }
        
        [System.Text.Json.Serialization.JsonPropertyName("totalTokenCount")]
        public int TotalTokenCount { get; set; }
    }

    // Tavily 웹 검색 메서드
    private async Task<string?> SearchWithTavilyAsync(string query, CancellationToken cancellationToken)
    {
        try
        {
            var tavilyApiKey = _configuration["AiApiSettings:Tavily:ApiKey"];
            var tavilyBaseUrl = _configuration["AiApiSettings:Tavily:BaseUrl"] ?? "https://api.tavily.com";

            if (string.IsNullOrEmpty(tavilyApiKey))
            {
                _logger.LogWarning("Tavily API key is not configured");
                return null;
            }

            var client = _httpClientFactory.CreateClient();
            client.DefaultRequestHeaders.Add("api-key", tavilyApiKey);
            client.Timeout = TimeSpan.FromSeconds(30);

            var payload = new
            {
                api_key = tavilyApiKey,
                query = query,
                search_depth = "basic",
                include_answer = true,
                include_images = false,
                include_raw_content = false,
                max_results = 5
            };

            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var response = await client.PostAsync($"{tavilyBaseUrl}/search", content, cancellationToken);
            
            if (!response.IsSuccessStatusCode)
            {
                var errorContent = await response.Content.ReadAsStringAsync(cancellationToken);
                _logger.LogWarning("Tavily API error. Status: {StatusCode}, Response: {Response}", response.StatusCode, errorContent);
                return null;
            }

            var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);
            var jsonOptions = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            };

            var tavilyResponse = JsonSerializer.Deserialize<TavilySearchResponse>(responseJson, jsonOptions);

            if (tavilyResponse == null || tavilyResponse.Results == null || tavilyResponse.Results.Count == 0)
            {
                _logger.LogInformation("Tavily search returned no results");
                return null;
            }

            // 검색 결과를 포맷팅
            var searchResults = new StringBuilder();
            
            if (!string.IsNullOrEmpty(tavilyResponse.Answer))
            {
                searchResults.AppendLine($"검색 요약: {tavilyResponse.Answer}");
            }

            searchResults.AppendLine("\n참고 링크:");
            foreach (var result in tavilyResponse.Results)
            {
                searchResults.AppendLine($"- [{result.Title ?? "제목 없음"}]({result.Url})");
                if (!string.IsNullOrEmpty(result.Content))
                {
                    var contentPreview = result.Content.Length > 200 
                        ? result.Content.Substring(0, 200) + "..." 
                        : result.Content;
                    searchResults.AppendLine($"  {contentPreview}");
                }
            }

            return searchResults.ToString();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error performing Tavily search");
            return null;
        }
    }
    
    // 심층 리서치: 여러 검색 쿼리를 생성하고 각각 검색하여 결과 통합
    private async Task<string?> PerformDeepResearchAsync(string query, CancellationToken cancellationToken)
    {
        try
        {
            // 주요 키워드 추출 (간단한 방법: 명사, 동사 등 추출)
            // 실제로는 더 정교한 NLP가 필요하지만, 여기서는 간단히 쿼리를 분할
            var searchQueries = GenerateSearchQueries(query);
            
            var allSearchResults = new List<string>();
            
            // 각 검색 쿼리 실행 (병렬 처리)
            var searchTasks = searchQueries.Select(q => SearchWithTavilyAsync(q, cancellationToken));
            var searchResults = await Task.WhenAll(searchTasks);
            
            foreach (var result in searchResults)
            {
                if (!string.IsNullOrEmpty(result))
                {
                    allSearchResults.Add(result);
                }
            }
            
            if (allSearchResults.Count == 0)
            {
                return null;
            }
            
            // 모든 검색 결과 통합
            var combinedResults = new StringBuilder();
            combinedResults.AppendLine("=== 다중 출처 검색 결과 ===");
            for (int i = 0; i < allSearchResults.Count; i++)
            {
                combinedResults.AppendLine($"\n[검색 출처 {i + 1}]");
                combinedResults.AppendLine(allSearchResults[i]);
            }
            
            _logger.LogInformation("Deep research completed. QueriesCount={Count}, ResultsCount={Results}", 
                searchQueries.Count, allSearchResults.Count);
            
            return combinedResults.ToString();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error performing deep research");
            return null;
        }
    }
    
    // 검색 쿼리 생성 (주요 키워드 기반)
    private List<string> GenerateSearchQueries(string originalQuery)
    {
        var queries = new List<string> { originalQuery }; // 원본 쿼리 포함
        
        // 간단한 키워드 추출 및 변형
        // 예: "AI의 미래" -> ["AI의 미래", "AI 발전", "인공지능 미래"]
        var words = originalQuery.Split(new[] { ' ', ',', '.', '?', '!', '의', '는', '은', '이', '가', '을', '를' }, 
            StringSplitOptions.RemoveEmptyEntries);
        
        if (words.Length > 1)
        {
            // 주요 키워드 조합으로 추가 쿼리 생성
            var keywords = words.Where(w => w.Length > 1).Take(3).ToList();
            if (keywords.Count >= 2)
            {
                queries.Add(string.Join(" ", keywords));
            }
            if (keywords.Count >= 1)
            {
                queries.Add(keywords[0] + " 발전");
                queries.Add(keywords[0] + " 동향");
            }
        }
        
        // 최대 5개 쿼리로 제한
        return queries.Take(5).ToList();
    }

    public async Task<ImageGenerationResponseDto> SendImageGenerationAsync(int serviceId, string model, ImageGenerationRequestDto request, CancellationToken cancellationToken = default)
    {
        var service = await _context.ApiServices.FindAsync([serviceId], cancellationToken);
        if (service == null || !service.IsActive)
        {
            throw new InvalidOperationException($"Service {serviceId} not found or inactive");
        }

        var startTime = DateTime.UtcNow;

        // ServiceCode를 소문자로 변환하고 공백 제거
        var serviceCode = service.ServiceCode?.Trim().ToLower() ?? "";
        _logger.LogInformation("Processing image generation request for service: ServiceId={ServiceId}, ServiceCode='{ServiceCode}', ServiceType='{ServiceType}'", 
            service.ServiceId, serviceCode, service.ServiceType);

        try
        {
            return serviceCode switch
            {
                "dalle" or "openai" => await CallDallEAsync(service, model, request, cancellationToken),
                "gemini-image" or "gemini" => await CallGeminiImageAsync(service, model, request, cancellationToken),
                "imagen4" => await CallImagen4Async(service, model, request, cancellationToken),
                "gen4-image" => await CallGen4ImageAsync(service, model, request, cancellationToken),
                "flux2" => await CallFlux2Async(service, model, request, cancellationToken),
                _ => throw new NotSupportedException($"Image generation service '{serviceCode}' (ServiceId: {service.ServiceId}, Original ServiceCode: '{service.ServiceCode}') is not supported")
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calling image generation service {ServiceCode}", service.ServiceCode);
            throw;
        }
    }

    public async Task<decimal> CalculateImageGenerationCostAsync(int serviceId, string model, string size, string quality, int numberOfImages)
    {
        var service = await _context.ApiServices.FindAsync([serviceId]);
        if (service == null)
        {
            return 0;
        }

        // 간단한 비용 계산 (실제로는 서비스별, 모델별, 크기별로 다를 수 있음)
        var baseCost = service.CostPerRequest;
        var sizeMultiplier = size switch
        {
            "1024x1024" => 1.0m,
            "512x512" => 0.5m,
            "256x256" => 0.25m,
            _ => 1.0m
        };
        var qualityMultiplier = quality == "hd" ? 2.0m : 1.0m;

        return baseCost * sizeMultiplier * qualityMultiplier * numberOfImages;
    }

    private async Task<ImageGenerationResponseDto> CallDallEAsync(ApiService service, string model, ImageGenerationRequestDto request, CancellationToken cancellationToken)
    {
        var startTime = DateTime.UtcNow;
        var apiKey = GetApiKey("openai", "AiApiSettings:OpenAI:ApiKey");
        var baseUrl = service.ApiEndpoint ?? _configuration["AiApiSettings:OpenAI:BaseUrl"] ?? "https://api.openai.com/v1";

        if (string.IsNullOrEmpty(apiKey))
        {
            throw new InvalidOperationException("OpenAI API key is not configured");
        }

        var client = _httpClientFactory.CreateClient("openai");
        client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);

        // DALL-E 3 파라미터 (DALL-E 3는 n=1만 지원, size는 1024x1024, 1024x1792, 1792x1024만 지원)
        var dalleModel = !string.IsNullOrEmpty(model) ? model : (service.DefaultModel ?? "dall-e-3");
        var size = request.Size;
        var quality = request.Quality;
        var n = 1; // DALL-E 3는 항상 1개만 생성

        // DALL-E 3는 n=1만 지원
        if (request.NumberOfImages > 1 && dalleModel == "dall-e-3")
        {
            _logger.LogWarning("DALL-E 3 only supports n=1. NumberOfImages will be set to 1.");
        }

        // DALL-E 3 크기 검증 및 변환
        if (dalleModel == "dall-e-3" || dalleModel.StartsWith("dall-e-3"))
        {
            var supportedSizes = new[] { "1024x1024", "1024x1792", "1792x1024" };
            if (!supportedSizes.Contains(size))
            {
                _logger.LogWarning("DALL-E 3 does not support size '{Size}'. Converting to '1024x1024'.", size);
                size = "1024x1024";
            }
        }

        var payload = new
        {
            model = dalleModel,
            prompt = request.Prompt,
            n = n,
            size = size,
            quality = quality,
            response_format = "url"
        };

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await client.PostAsync($"{baseUrl}/images/generations", content, cancellationToken);
        
        var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);
        
        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError("DALL-E API error: StatusCode={StatusCode}, Response={Response}", response.StatusCode, responseJson);
            throw new HttpRequestException($"DALL-E API returned {response.StatusCode}: {responseJson}");
        }

        var jsonOptions = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        var dalleResponse = JsonSerializer.Deserialize<DallEResponse>(responseJson, jsonOptions);

        if (dalleResponse?.Data == null || dalleResponse.Data.Count == 0)
        {
            _logger.LogError("Invalid DALL-E API response: {Response}", responseJson);
            throw new InvalidOperationException($"Invalid response from DALL-E API: {responseJson}");
        }

        var imageUrls = dalleResponse.Data.Select(d => d.Url ?? "").Where(url => !string.IsNullOrEmpty(url)).ToList();
        var responseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
        var cost = await CalculateImageGenerationCostAsync(service.ServiceId, dalleModel, size, quality, n);

        return new ImageGenerationResponseDto
        {
            ImageUrls = imageUrls,
            Prompt = request.Prompt,
            Model = dalleModel,
            CreatedAt = DateTime.UtcNow,
            Cost = cost,
            ResponseTime = responseTime
        };
    }

    private async Task<ImageGenerationResponseDto> CallGeminiImageAsync(ApiService service, string model, ImageGenerationRequestDto request, CancellationToken cancellationToken)
    {
        var startTime = DateTime.UtcNow;
        var apiKey = GetApiKey("gemini", "AiApiSettings:Gemini:ApiKey");
        var baseUrl = service.ApiEndpoint ?? _configuration["AiApiSettings:Gemini:BaseUrl"] ?? "https://generativelanguage.googleapis.com/v1beta";

        if (string.IsNullOrEmpty(apiKey))
        {
            throw new InvalidOperationException("Gemini API key is not configured");
        }

        var client = _httpClientFactory.CreateClient("gemini");

        // Gemini Image API는 generateContent 엔드포인트를 사용
        var inputModel = !string.IsNullOrEmpty(model) ? model : (service.DefaultModel ?? "gemini-3.1-pro-image-preview");

        // 모델 이름 매핑 (구버전 이름을 새 이름으로 변환)
        var geminiImageModel = inputModel switch
        {
            "gemini-3.0-pro-image" => "gemini-3.1-pro-image-preview",
            "gemini-3-pro-image" => "gemini-3.1-pro-image-preview",
            "gemini-3-pro-image-preview" => "gemini-3.1-pro-image-preview",
            _ => inputModel
        };
        
        // 모델별 imageConfig 지원 여부 확인
        // gemini-3-pro-image-preview     : aspectRatio + imageSize 모두 지원, responseModalities ["IMAGE"]
        // gemini-2.5-flash-image         : aspectRatio만 지원 (imageSize 미지원), responseModalities ["TEXT","IMAGE"] 권장
        // gemini-2.5-flash-image-preview : imageConfig 전체 미지원
        // gemini-2.0-flash-exp-image-generation: imageConfig 전체 미지원, responseModalities ["TEXT","IMAGE"] 필수
        var isExpModel = geminiImageModel.Contains("-flash-exp-", StringComparison.OrdinalIgnoreCase);
        var isFlashImageModel = geminiImageModel.Contains("gemini-2.5-flash-image", StringComparison.OrdinalIgnoreCase) &&
                                !geminiImageModel.Contains("-preview", StringComparison.OrdinalIgnoreCase);
        var isPreviewOrExpModel = geminiImageModel.Contains("-flash-image-preview", StringComparison.OrdinalIgnoreCase) ||
                                  isExpModel;
        var supportsImageConfig = !isPreviewOrExpModel;
        var supportsImageSize = geminiImageModel.Contains("gemini-3-pro-image", StringComparison.OrdinalIgnoreCase) ||
                               geminiImageModel.Contains("gemini-3.1-pro-image", StringComparison.OrdinalIgnoreCase);
        
        // 지원되는 aspectRatio 값들 (gemini-2.5-flash-image 및 gemini-3-pro-image-preview)
        var supportedAspectRatios = new[] { "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9" };
        
        // 이미지 크기 파싱 (1024x1024 -> "1K", "2K", "4K" 등)
        var imageSize = "2K"; // 기본값
        var aspectRatio = "1:1"; // 기본값
        if (!string.IsNullOrEmpty(request.Size))
        {
            var parts = request.Size.Split('x');
            if (parts.Length == 2 && int.TryParse(parts[0], out var width) && int.TryParse(parts[1], out var height))
            {
                if (supportsImageSize)
                {
                    if (width >= 4096 || height >= 4096)
                        imageSize = "4K";
                    else if (width >= 2048 || height >= 2048)
                        imageSize = "2K";
                    else
                        imageSize = "1K";
                }

                // 종횡비 계산 (지원되는 값 중 가장 가까운 것으로 매핑)
                var ratio = (double)width / height;
                aspectRatio = ratio switch
                {
                    <= 0.6 => "2:3",
                    <= 0.75 => "3:4",
                    <= 0.85 => "4:5",
                    <= 1.15 => "1:1",
                    <= 1.35 => "4:3",
                    <= 1.6 => "3:2",
                    <= 1.85 => "16:9",
                    <= 2.5 => "21:9",
                    _ => "1:1"
                };
            }
        }

        // Gemini Image API 요청 형식 (generateContent 엔드포인트 사용)
        var generationConfig = new Dictionary<string, object>();
        
        // responseModalities 설정
        // gemini-3-pro-image-preview    : ["IMAGE"]
        // gemini-2.5-flash-image        : ["TEXT", "IMAGE"] — TEXT 포함해야 이미지 파트 반환됨
        // gemini-2.0-flash-exp-image-*  : ["TEXT", "IMAGE"] 필수
        if (isExpModel || isFlashImageModel)
        {
            // exp 모델과 2.5-flash-image 모델은 TEXT와 IMAGE 모두 필요
            generationConfig["responseModalities"] = new[] { "TEXT", "IMAGE" };
        }
        else if (supportsImageConfig || geminiImageModel.Contains("gemini-3-pro-image", StringComparison.OrdinalIgnoreCase) ||
                 geminiImageModel.Contains("gemini-3.1-pro-image", StringComparison.OrdinalIgnoreCase))
        {
            // gemini-3.1-pro-image-preview 등 일반 모델은 IMAGE만
            generationConfig["responseModalities"] = new[] { "IMAGE" };
        }

        // imageConfig는 모델에 따라 조건부로 추가
        if (supportsImageConfig)
        {
            var imageConfig = new Dictionary<string, object>
            {
                ["aspectRatio"] = aspectRatio
            };
            
            if (supportsImageSize)
            {
                imageConfig["imageSize"] = imageSize;
            }
            
            generationConfig["imageConfig"] = imageConfig;
        }
        
        // 대화 히스토리 구성 (Gemini Image는 채팅 API를 사용하므로 대화 히스토리 포함 가능)
        var contents = new List<object>();
        
        // 이전 대화 메시지가 있으면 포함
        if (request.Messages != null && request.Messages.Count > 0)
        {
            foreach (var msg in request.Messages)
            {
                // 시스템 메시지는 건너뛰기 (Gemini API는 시스템 메시지를 별도로 처리하지 않음)
                if (msg.Role?.ToLower() == "system")
                {
                    continue;
                }
                
                // 사용자/어시스턴트 메시지를 Gemini 형식으로 변환
                var role = msg.Role?.ToLower() == "assistant" ? "model" : "user";
                var parts = new List<object>();
                
                if (!string.IsNullOrEmpty(msg.Content))
                {
                    parts.Add(new { text = msg.Content });
                }
                
                if (parts.Count > 0)
                {
                    contents.Add(new
                    {
                        role = role,
                        parts = parts
                    });
                }
            }
        }
        
        // 현재 프롬프트와 첨부 이미지 추가
        var currentParts = new List<object>();
        
        // 텍스트 프롬프트 추가
        if (!string.IsNullOrEmpty(request.Prompt))
        {
            currentParts.Add(new { text = request.Prompt });
        }
        
        // 첨부 이미지 추가 (Gemini Image는 멀티모달 입력 지원)
        if (request.ImageAttachments != null && request.ImageAttachments.Count > 0)
        {
            _logger.LogInformation("Including {Count} image attachments in Gemini Image request", request.ImageAttachments.Count);
            foreach (var imageAttachment in request.ImageAttachments)
            {
                if (!string.IsNullOrEmpty(imageAttachment.Data))
                {
                    var dataLength = imageAttachment.Data.Length;
                    _logger.LogDebug("Adding image attachment: MimeType={MimeType}, DataLength={DataLength}", 
                        imageAttachment.MimeType, dataLength);
                    
                    currentParts.Add(new
                    {
                        inlineData = new
                        {
                            mimeType = imageAttachment.MimeType ?? "image/jpeg",
                            data = imageAttachment.Data
                        }
                    });
                }
            }
        }
        
        // parts가 비어있으면 기본 프롬프트 추가 (이론적으로는 발생하지 않아야 함)
        if (currentParts.Count == 0)
        {
            _logger.LogWarning("No prompt or image attachments found, adding default prompt");
            currentParts.Add(new { text = "이미지를 생성해주세요." });
        }
        
        contents.Add(new
        {
            role = "user",
            parts = currentParts
        });
        
        // generationConfig가 비어있으면 아예 보내지 않음
        var payload = new Dictionary<string, object>
        {
            ["contents"] = contents
        };
        
        if (generationConfig.Count > 0)
        {
            payload["generationConfig"] = generationConfig;
        }

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        _logger.LogInformation("Calling Gemini Image API. Model: {Model}, Payload: {Payload}", geminiImageModel, json);

        var response = await client.PostAsync($"{baseUrl}/models/{geminiImageModel}:generateContent?key={apiKey}", content, cancellationToken);
        
        var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);
        
        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError("Gemini Image API error. Model: {Model}, Status: {StatusCode}, Response: {Response}", 
                geminiImageModel, response.StatusCode, responseJson);
            throw new HttpRequestException($"Gemini Image API returned {response.StatusCode}: {responseJson}");
        }

        var jsonOptions = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        
        // Gemini Image API 응답 형식: candidates[].content.parts[].inlineData
        var geminiResponse = JsonSerializer.Deserialize<GeminiResponse>(responseJson, jsonOptions);

        if (geminiResponse?.Candidates == null || geminiResponse.Candidates.Count == 0)
        {
            _logger.LogError("Invalid Gemini Image API response. Response: {Response}", responseJson);
            throw new InvalidOperationException("Invalid response from Gemini Image API - no candidates");
        }

        var imageUrls = new List<string>();
        foreach (var candidate in geminiResponse.Candidates)
        {
            // finishReason 확인
            if (!string.IsNullOrEmpty(candidate.FinishReason) && candidate.FinishReason != "STOP")
            {
                _logger.LogWarning("Gemini Image API candidate finished with reason: {FinishReason}", candidate.FinishReason);
            }
            
            if (candidate.Content?.Parts != null)
            {
                foreach (var part in candidate.Content.Parts)
                {
                    // 텍스트 응답이 있는 경우 로깅 (디버깅용)
                    if (!string.IsNullOrEmpty(part.Text))
                    {
                        _logger.LogDebug("Gemini Image API returned text response: {Text}", part.Text.Substring(0, Math.Min(100, part.Text.Length)));
                    }
                    
                    if (part.InlineData != null && !string.IsNullOrEmpty(part.InlineData.Data))
                    {
                        // Base64 데이터를 data URL로 변환
                        var mimeType = part.InlineData.MimeType ?? "image/png";
                        imageUrls.Add($"data:{mimeType};base64,{part.InlineData.Data}");
                    }
                }
            }
        }

        if (imageUrls.Count == 0)
        {
            _logger.LogError("No image data found in Gemini Image API response. Model: {Model}, Response: {Response}, Candidates count: {CandidatesCount}", 
                geminiImageModel, responseJson, geminiResponse.Candidates?.Count ?? 0);
            
            // 응답 구조를 더 자세히 로깅
            if (geminiResponse.Candidates != null && geminiResponse.Candidates.Count > 0)
            {
                var candidate = geminiResponse.Candidates[0];
                _logger.LogError("First candidate - FinishReason: {FinishReason}, Content: {HasContent}, Parts: {PartsCount}", 
                    candidate.FinishReason, candidate.Content != null, candidate.Content?.Parts?.Count ?? 0);
                
                // 각 part의 내용 로깅
                if (candidate.Content?.Parts != null)
                {
                    foreach (var part in candidate.Content.Parts)
                    {
                        if (!string.IsNullOrEmpty(part.Text))
                        {
                            _logger.LogError("Part contains text (not image): {Text}", 
                                part.Text.Length > 200 ? part.Text.Substring(0, 200) + "..." : part.Text);
                        }
                        if (part.InlineData != null)
                        {
                            _logger.LogError("Part contains inlineData - MimeType: {MimeType}, DataLength: {DataLength}", 
                                part.InlineData.MimeType, part.InlineData.Data?.Length ?? 0);
                        }
                    }
                }
            }
            
            // 모델별 추가 안내
            string errorMessage;
            if (isExpModel)
                errorMessage = "No image data in response from Gemini Image API. gemini-2.0-flash-exp-image-generation 모델은 responseModalities를 ['TEXT', 'IMAGE']로 설정해야 합니다.";
            else if (isFlashImageModel)
                errorMessage = "No image data in response from Gemini Image API. gemini-2.5-flash-image 모델은 responseModalities를 ['TEXT', 'IMAGE']로 설정해야 합니다.";
            else
                errorMessage = "No image data in response from Gemini Image API";
            
            throw new InvalidOperationException(errorMessage);
        }

        var responseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
        var cost = await CalculateImageGenerationCostAsync(service.ServiceId, geminiImageModel, request.Size, request.Quality, imageUrls.Count);

        return new ImageGenerationResponseDto
        {
            ImageUrls = imageUrls,
            Prompt = request.Prompt,
            Model = geminiImageModel,
            CreatedAt = DateTime.UtcNow,
            Cost = cost,
            ResponseTime = responseTime
        };
    }

    private int GreatestCommonDivisor(int a, int b)
    {
        while (b != 0)
        {
            int temp = b;
            b = a % b;
            a = temp;
        }
        return a;
    }

    private async Task<ImageGenerationResponseDto> CallImagen4Async(ApiService service, string model, ImageGenerationRequestDto request, CancellationToken cancellationToken)
    {
        var startTime = DateTime.UtcNow;
        var apiKey = GetApiKey("gemini", "AiApiSettings:Gemini:ApiKey");
        // Imagen 4는 Gemini API의 generateContent 엔드포인트를 사용 (Gemini API를 통해 접근 가능)
        var baseUrl = service.ApiEndpoint ?? _configuration["AiApiSettings:Gemini:BaseUrl"] ?? "https://generativelanguage.googleapis.com/v1beta";

        if (string.IsNullOrEmpty(apiKey))
        {
            throw new InvalidOperationException("Google API key is not configured");
        }

        var client = _httpClientFactory.CreateClient("gemini");

        // Imagen 4 모델 이름 매핑
        var imagenModel = !string.IsNullOrEmpty(model) ? model : (service.DefaultModel ?? "imagen-4.0-generate-001");
        
        // 모델 이름 정규화
        var normalizedModel = imagenModel switch
        {
            "imagen-4.0" => "imagen-4.0-generate-001",
            "imagen4" => "imagen-4.0-generate-001",
            _ => imagenModel
        };

        // 이미지 크기 파싱
        var aspectRatio = "1:1"; // 기본값
        if (!string.IsNullOrEmpty(request.Size))
        {
            var sizeParts = request.Size.Split('x');
            if (sizeParts.Length == 2 && int.TryParse(sizeParts[0], out var width) && int.TryParse(sizeParts[1], out var height))
            {
                var ratio = (double)width / height;
                aspectRatio = ratio switch
                {
                    <= 0.6 => "2:3",
                    <= 0.75 => "3:4",
                    <= 0.85 => "4:5",
                    <= 1.15 => "1:1",
                    <= 1.35 => "4:3",
                    <= 1.6 => "3:2",
                    <= 1.85 => "16:9",
                    <= 2.5 => "21:9",
                    _ => "1:1"
                };
            }
        }

        // Imagen 4는 Gemini API의 generateContent 엔드포인트를 사용
        // contents 배열에 프롬프트와 이미지 설정 포함
        var contents = new List<object>();
        var parts = new List<object>();
        
        // 텍스트 프롬프트 추가
        if (!string.IsNullOrEmpty(request.Prompt))
        {
            parts.Add(new { text = request.Prompt });
        }
        
        // 첨부 이미지가 있으면 추가
        if (request.ImageAttachments != null && request.ImageAttachments.Count > 0)
        {
            foreach (var imageAttachment in request.ImageAttachments)
            {
                if (!string.IsNullOrEmpty(imageAttachment.Data))
                {
                    parts.Add(new
                    {
                        inlineData = new
                        {
                            mimeType = imageAttachment.MimeType ?? "image/jpeg",
                            data = imageAttachment.Data
                        }
                    });
                }
            }
        }
        
        if (parts.Count == 0)
        {
            throw new InvalidOperationException("Prompt is required for Imagen 4");
        }
        
        contents.Add(new
        {
            role = "user",
            parts = parts
        });

        // generationConfig 설정
        var generationConfig = new Dictionary<string, object>
        {
            ["responseModalities"] = new[] { "IMAGE" },
            ["imageConfig"] = new Dictionary<string, object>
            {
                ["aspectRatio"] = aspectRatio,
                ["numberOfImages"] = Math.Min(request.NumberOfImages, 4)
            }
        };

        var payload = new Dictionary<string, object>
        {
            ["contents"] = contents,
            ["generationConfig"] = generationConfig
        };

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        _logger.LogInformation("Calling Imagen 4 API. Model: {Model}, Payload: {Payload}", normalizedModel, json);

        // Gemini API를 통해 Imagen 4 모델 호출
        // 참고: Imagen 4는 Vertex AI를 통해 제공되지만, Gemini API를 통해서도 접근 가능할 수 있습니다.
        // 만약 404 오류가 발생하면 Vertex AI 엔드포인트를 사용해야 할 수 있습니다.
        var endpointUrl = $"{baseUrl}/models/{normalizedModel}:generateContent?key={apiKey}";
        _logger.LogInformation("Calling Imagen 4 API. Endpoint: {Endpoint}, Model: {Model}", endpointUrl, normalizedModel);
        
        var response = await client.PostAsync(endpointUrl, content, cancellationToken);
        
        var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);
        
        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError("Imagen 4 API error. Model: {Model}, Status: {StatusCode}, Response: {Response}", 
                normalizedModel, response.StatusCode, responseJson);
            
            // 404 오류인 경우 모델이 Gemini API를 통해 접근 불가능할 수 있음을 명시
            if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            {
                throw new InvalidOperationException(
                    $"Imagen 4 모델 '{normalizedModel}'을 찾을 수 없습니다 (404). " +
                    $"Imagen 4는 Vertex AI를 통해 제공되며, Gemini API를 통한 접근이 제한될 수 있습니다. " +
                    $"Vertex AI 엔드포인트를 사용하거나 다른 이미지 생성 모델(Gemini 3 Pro Image 등)을 사용해주세요. " +
                    $"에러 응답: {responseJson}"
                );
            }
            
            throw new HttpRequestException($"Imagen 4 API returned {response.StatusCode}: {responseJson}");
        }

        var jsonOptions = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        
        // Gemini API 응답 형식 사용 (candidates[].content.parts[].inlineData)
        var imagenResponse = JsonSerializer.Deserialize<GeminiResponse>(responseJson, jsonOptions);

        if (imagenResponse?.Candidates == null || imagenResponse.Candidates.Count == 0)
        {
            _logger.LogError("Invalid Imagen 4 API response. Response: {Response}", responseJson);
            throw new InvalidOperationException("Invalid response from Imagen 4 API - no candidates");
        }

        var imageUrls = new List<string>();
        foreach (var candidate in imagenResponse.Candidates)
        {
            if (candidate.Content?.Parts != null)
            {
                foreach (var part in candidate.Content.Parts)
                {
                    if (part.InlineData != null && !string.IsNullOrEmpty(part.InlineData.Data))
                    {
                        // Base64 데이터를 data URL로 변환
                        var mimeType = part.InlineData.MimeType ?? "image/png";
                        imageUrls.Add($"data:{mimeType};base64,{part.InlineData.Data}");
                    }
                }
            }
        }

        if (imageUrls.Count == 0)
        {
            _logger.LogError("No image data found in Imagen 4 API response. Model: {Model}, Response: {Response}", 
                normalizedModel, responseJson);
            throw new InvalidOperationException("No image data in response from Imagen 4 API");
        }

        var responseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
        var cost = await CalculateImageGenerationCostAsync(service.ServiceId, normalizedModel, request.Size, request.Quality, imageUrls.Count);

        return new ImageGenerationResponseDto
        {
            ImageUrls = imageUrls,
            Prompt = request.Prompt,
            Model = normalizedModel,
            CreatedAt = DateTime.UtcNow,
            Cost = cost,
            ResponseTime = responseTime
        };
    }

    private static string GetAspectRatioStringFromSize(string? size)
    {
        if (string.IsNullOrEmpty(size)) return "1:1";
        var sizeParts = size.Split('x');
        if (sizeParts.Length != 2 || !int.TryParse(sizeParts[0], out var width) || !int.TryParse(sizeParts[1], out var height))
            return "1:1";
        var ratio = (double)width / height;
        return ratio switch
        {
            <= 0.6 => "2:3",
            <= 0.75 => "3:4",
            <= 0.85 => "4:5",
            <= 1.15 => "1:1",
            <= 1.35 => "4:3",
            <= 1.6 => "3:2",
            <= 1.85 => "16:9",
            <= 2.5 => "21:9",
            _ => "1:1"
        };
    }

    private async Task<ImageGenerationResponseDto> CallGen4ImageAsync(ApiService service, string model, ImageGenerationRequestDto request, CancellationToken cancellationToken)
    {
        var startTime = DateTime.UtcNow;
        // Vertex AI는 OAuth 인증이 필요할 수 있으므로 임시 구현
        var apiKey = GetApiKey("gemini", "AiApiSettings:Gemini:ApiKey");
        var baseUrl = service.ApiEndpoint ?? "https://us-central1-aiplatform.googleapis.com/v1";

        if (string.IsNullOrEmpty(apiKey))
        {
            throw new InvalidOperationException("Google Cloud API key is not configured");
        }

        var client = _httpClientFactory.CreateClient("gemini");

        var gen4Model = !string.IsNullOrEmpty(model) ? model : (service.DefaultModel ?? "imagegeneration@006");
        // Vertex AI Gen4 Image API 엔드포인트 (실제 API 문서 확인 필요)
        var payload = new
        {
            prompt = request.Prompt,
            model = gen4Model,
            size = request.Size,
            numImages = Math.Min(request.NumberOfImages, 4)
        };

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        // Vertex AI Gen4 Image API는 다음이 필요합니다:
        // 1. Google Cloud 프로젝트 ID
        // 2. 위치 (예: us-central1)
        // 3. OAuth Bearer 토큰 (API 키가 아님)
        // 4. 올바른 엔드포인트 형식: projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL}:predict
        
        // 현재 구현은 사용 불가능합니다. Vertex AI 인증 및 프로젝트 설정이 필요합니다.
        var projectId = _configuration["AiApiSettings:VertexAI:ProjectId"];
        var location = _configuration["AiApiSettings:VertexAI:Location"] ?? "us-central1";
        var accessToken = _configuration["AiApiSettings:VertexAI:AccessToken"]; // gcloud auth print-access-token으로 얻은 토큰
        
        if (string.IsNullOrEmpty(projectId) || string.IsNullOrEmpty(accessToken))
        {
            throw new InvalidOperationException(
                "Gen4 Image (Vertex AI)는 현재 사용할 수 없습니다. " +
                "Vertex AI를 사용하려면 다음 설정이 필요합니다:\n" +
                "1. Google Cloud 프로젝트 ID (AiApiSettings:VertexAI:ProjectId)\n" +
                "2. 위치 (AiApiSettings:VertexAI:Location, 기본값: us-central1)\n" +
                "3. OAuth 액세스 토큰 (AiApiSettings:VertexAI:AccessToken)\n\n" +
                "또는 Gemini 3 Pro Image 또는 Imagen 4를 사용해주세요."
            );
        }
        
        // 올바른 Vertex AI 엔드포인트 형식 사용
        // 참고: imagegeneration@006은 deprecated되었을 수 있으며, imagen-4.0-generate-001 등을 사용해야 할 수 있습니다.
        var endpointUrl = $"{baseUrl}/projects/{projectId}/locations/{location}/publishers/google/models/{gen4Model}:predict";
        
        // OAuth Bearer 토큰 사용
        client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", accessToken);
        
        _logger.LogInformation("Calling Gen4 Image API. Endpoint: {Endpoint}, Model: {Model}", endpointUrl, gen4Model);
        
        // Vertex AI predict 엔드포인트 형식에 맞는 페이로드 구성
        var vertexPayload = new
        {
            instances = new[]
            {
                new
                {
                    prompt = request.Prompt
                }
            },
            parameters = new
            {
                sampleCount = Math.Min(request.NumberOfImages, 4),
                aspectRatio = GetAspectRatioStringFromSize(request.Size),
                negativePrompt = ""
            }
        };
        
        var vertexJson = JsonSerializer.Serialize(vertexPayload);
        var vertexContent = new StringContent(vertexJson, Encoding.UTF8, "application/json");
        
        var response = await client.PostAsync(endpointUrl, vertexContent, cancellationToken);
        
        var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);
        
        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError("Gen4 Image API error. Status: {StatusCode}, Response: {Response}", response.StatusCode, responseJson);
            
            if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized || 
                response.StatusCode == System.Net.HttpStatusCode.Forbidden)
            {
                throw new InvalidOperationException(
                    $"Vertex AI Gen4 Image API 인증 실패. " +
                    $"액세스 토큰이 유효하지 않거나 만료되었을 수 있습니다. " +
                    $"`gcloud auth print-access-token` 명령으로 새 토큰을 발급받아주세요. " +
                    $"에러 응답: {responseJson}"
                );
            }
            
            if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            {
                throw new InvalidOperationException(
                    $"Gen4 Image 모델 '{gen4Model}'을 찾을 수 없습니다 (404). " +
                    $"모델 이름이 올바른지 확인하거나, imagen-4.0-generate-001 등의 최신 모델을 사용해주세요. " +
                    $"에러 응답: {responseJson}"
                );
            }
            
            throw new HttpRequestException($"Gen4 Image API returned {response.StatusCode}: {responseJson}");
        }

        var jsonOptions = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        
        // Vertex AI predict API 응답 형식 파싱
        // 응답 형식: { "predictions": [{ "bytesBase64Encoded": "...", "mimeType": "image/png" }] }
        var vertexResponse = JsonSerializer.Deserialize<VertexAIImageResponse>(responseJson, jsonOptions);

        if (vertexResponse?.Predictions == null || vertexResponse.Predictions.Count == 0)
        {
            _logger.LogError("Invalid Gen4 Image API response. Response: {Response}", responseJson);
            throw new InvalidOperationException($"Invalid response from Gen4 Image API. Response: {responseJson}");
        }

        var imageUrls = vertexResponse.Predictions
            .Where(p => !string.IsNullOrEmpty(p.BytesBase64Encoded))
            .Select(p => $"data:{p.MimeType ?? "image/png"};base64,{p.BytesBase64Encoded}")
            .ToList();
        var responseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
        var cost = await CalculateImageGenerationCostAsync(service.ServiceId, gen4Model, request.Size, request.Quality, imageUrls.Count);

        return new ImageGenerationResponseDto
        {
            ImageUrls = imageUrls,
            Prompt = request.Prompt,
            Model = gen4Model,
            CreatedAt = DateTime.UtcNow,
            Cost = cost,
            ResponseTime = responseTime
        };
    }

    private async Task<ImageGenerationResponseDto> CallFlux2Async(ApiService service, string model, ImageGenerationRequestDto request, CancellationToken cancellationToken)
    {
        var startTime = DateTime.UtcNow;
        var apiKey = _configuration["AiApiSettings:Stability:ApiKey"];
        var baseUrl = service.ApiEndpoint ?? _configuration["AiApiSettings:Stability:BaseUrl"] ?? "https://api.stability.ai/v2beta";

        if (string.IsNullOrEmpty(apiKey))
        {
            throw new InvalidOperationException("Stability AI API key is not configured");
        }

        var client = _httpClientFactory.CreateClient();
        client.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");
        client.DefaultRequestHeaders.Add("Accept", "application/json");
        client.Timeout = TimeSpan.FromSeconds(_configuration.GetValue<int>("AiApiSettings:DefaultTimeout", 300));

        var fluxModel = !string.IsNullOrEmpty(model) ? model : (service.DefaultModel ?? "flux-2");
        // Flux 2 API 엔드포인트
        var payload = new
        {
            prompt = request.Prompt,
            model = fluxModel,
            width = GetWidthFromSize(request.Size),
            height = GetHeightFromSize(request.Size),
            num_images = Math.Min(request.NumberOfImages, 4),
            output_format = "url"
        };

        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        _logger.LogInformation("Calling Flux 2 API. Model: {Model}, Endpoint: {Endpoint}", fluxModel, $"{baseUrl}/stable-image/generation/ultra");

        var response = await client.PostAsync($"{baseUrl}/stable-image/generation/ultra", content, cancellationToken);
        
        var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);
        
        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError("Flux 2 API error. Model: {Model}, Status: {StatusCode}, Response: {Response}", 
                fluxModel, response.StatusCode, responseJson);
            
            if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized || 
                response.StatusCode == System.Net.HttpStatusCode.Forbidden)
            {
                throw new InvalidOperationException(
                    $"Stability AI API 인증 실패. API 키가 유효하지 않거나 만료되었을 수 있습니다. " +
                    $"Stability AI 개발자 플랫폼(platform.stability.ai)에서 API 키를 확인해주세요. " +
                    $"에러 응답: {responseJson}"
                );
            }
            
            if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            {
                throw new InvalidOperationException(
                    $"Flux 2 API 엔드포인트를 찾을 수 없습니다 (404). " +
                    $"엔드포인트가 변경되었거나 모델 이름이 올바르지 않을 수 있습니다. " +
                    $"현재 엔드포인트: {baseUrl}/stable-image/generation/ultra. " +
                    $"에러 응답: {responseJson}"
                );
            }
            
            throw new HttpRequestException($"Flux 2 API returned {response.StatusCode}: {responseJson}");
        }

        var jsonOptions = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        
        var fluxResponse = JsonSerializer.Deserialize<FluxResponse>(responseJson, jsonOptions);

        if (fluxResponse?.Images == null || fluxResponse.Images.Count == 0)
        {
            _logger.LogError("Invalid Flux 2 API response. Response: {Response}", responseJson);
            throw new InvalidOperationException($"Invalid response from Flux 2 API. Response: {responseJson}");
        }

        var imageUrls = fluxResponse.Images.Select(img => img.Url ?? (img.Base64 != null ? $"data:image/png;base64,{img.Base64}" : "")).Where(url => !string.IsNullOrEmpty(url)).ToList();
        var responseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
        var cost = await CalculateImageGenerationCostAsync(service.ServiceId, fluxModel, request.Size, request.Quality, imageUrls.Count);

        return new ImageGenerationResponseDto
        {
            ImageUrls = imageUrls,
            Prompt = request.Prompt,
            Model = fluxModel,
            CreatedAt = DateTime.UtcNow,
            Cost = cost,
            ResponseTime = responseTime
        };
    }

    private int GetWidthFromSize(string size)
    {
        var parts = size.Split('x');
        return parts.Length >= 1 && int.TryParse(parts[0], out var width) ? width : 1024;
    }

    private int GetHeightFromSize(string size)
    {
        var parts = size.Split('x');
        return parts.Length >= 2 && int.TryParse(parts[1], out var height) ? height : 1024;
    }

    // Gemini Image Response Models (임시 구조)
    private class GeminiImageResponse
    {
        [System.Text.Json.Serialization.JsonPropertyName("images")]
        public List<GeminiImageData>? Images { get; set; }
    }

    private class GeminiImageData
    {
        [System.Text.Json.Serialization.JsonPropertyName("url")]
        public string? Url { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("base64")]
        public string? Base64 { get; set; }
    }

    // Flux Response Models
    private class FluxResponse
    {
        [System.Text.Json.Serialization.JsonPropertyName("images")]
        public List<FluxImageData>? Images { get; set; }
    }

    private class FluxImageData
    {
        [System.Text.Json.Serialization.JsonPropertyName("url")]
        public string? Url { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("base64")]
        public string? Base64 { get; set; }
    }

    // Vertex AI Image Response Models
    private class VertexAIImageResponse
    {
        [System.Text.Json.Serialization.JsonPropertyName("predictions")]
        public List<VertexAIImagePrediction>? Predictions { get; set; }
    }

    private class VertexAIImagePrediction
    {
        [System.Text.Json.Serialization.JsonPropertyName("bytesBase64Encoded")]
        public string? BytesBase64Encoded { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("mimeType")]
        public string? MimeType { get; set; }
    }

    // DALL-E Response Models
    private class DallEResponse
    {
        [System.Text.Json.Serialization.JsonPropertyName("data")]
        public List<DallEData>? Data { get; set; }
    }

    private class DallEData
    {
        [System.Text.Json.Serialization.JsonPropertyName("url")]
        public string? Url { get; set; }

        [System.Text.Json.Serialization.JsonPropertyName("revised_prompt")]
        public string? RevisedPrompt { get; set; }
    }

    private class TavilySearchResponse
    {
        public string? Answer { get; set; }
        public List<TavilySearchResult>? Results { get; set; }
    }

    private class TavilySearchResult
    {
        public string? Title { get; set; }
        public string? Url { get; set; }
        public string? Content { get; set; }
    }

    // ════════════════════════════════════════════════════════════════════════════
    // Nexus 사내 LLM 호출 (Phase 5.2, ADR-1 옵션 B)
    //
    // 옵션 B 채택 이유: Nexus 의 4-Tier AsyncGenerator 체인 / 세션 / 멀티테넌시 강점을
    // 변환 어댑터로 잃지 않기 위함(.claude/rules/anti-patterns.md #2).
    //
    // 메시지 매핑 정책:
    //   - Nexus 는 단일 message string + session_id 키로 Redis 에서 히스토리를 자동 복원
    //   - 따라서 ChatMessageRequestDto.Messages 의 마지막 user 메시지만 추출
    //   - 시스템 메시지(system role) 가 있으면 prepend (Nexus 측 system_message 파라미터 미지원
    //     가정 — 향후 NexusChatRequest 확장 시 분리)
    //   - assistant 히스토리는 Nexus 측이 session_id 로 복원하므로 호출자가 다시 보낼 필요 없음
    //
    // Model 매핑:
    //   - Nexus 는 "primary" / "auxiliary" 두 카테고리만 사용
    //   - agenthub 의 model 파라미터가 둘 중 하나가 아니면 "primary" 폴백 + LogWarning
    //
    // TenantId:
    //   - 본 단계에서는 ChatMessageRequestDto 에 TenantId 필드가 없으므로
    //     IConfiguration["Nexus:DefaultTenantId"] 기본값 사용
    //
    // 비용:
    //   - Nexus 는 사내 모델이므로 cost=0 (ApiService.CostPerRequest=0)
    //
    // 예외 처리:
    //   - HttpRequestException(LAN 도달 불가) / TimeoutException / Nexus 5xx
    //     → InvalidOperationException("Nexus 응답 실패. 사내망 연결을 확인하세요.")
    //   - ApiKeyPool 미사용 (공유 시크릿이라 키 회전 무관)
    // ════════════════════════════════════════════════════════════════════════════

    /// <summary>
    /// Nexus 비스트리밍 호출 — INexusClient.SendChatAsync 위임.
    /// </summary>
    private async Task<AiResponseDto> CallNexusAsync(
        ApiService service,
        string model,
        ChatMessageRequestDto request,
        CancellationToken cancellationToken)
    {
        if (_nexusClient == null)
        {
            // 운영 환경에서는 도달하지 않는 경로(Phase 5.1 Program.cs DI 등록 완료).
            _logger.LogError("CallNexusAsync 호출됐지만 INexusClient 가 주입되지 않음 — DI 등록 누락");
            throw new InvalidOperationException(
                "Nexus 클라이언트가 등록되지 않았습니다. 사내망 연결을 확인하세요.");
        }

        var startTime = DateTime.UtcNow;

        // 메시지 변환: 시스템 + 마지막 user 만 결합.
        var (mergedMessage, hadSystem) = BuildNexusSingleMessage(request);
        if (string.IsNullOrWhiteSpace(mergedMessage))
        {
            throw new InvalidOperationException(
                "Nexus 호출에 실패했습니다. 전송할 사용자 메시지가 없습니다.");
        }

        // Model 정규화 — primary/auxiliary 가 아니면 primary 폴백.
        var nexusModel = NormalizeNexusModel(model);

        var tenantId = _configuration["Nexus:DefaultTenantId"];
        if (string.IsNullOrWhiteSpace(tenantId)) tenantId = "default";

        var nexusRequest = new NexusChatRequest(
            Message: mergedMessage,
            SessionId: null, // 향후 ChatMessageRequestDto.ConversationId 매핑 시점에 도입
            Model: nexusModel,
            TenantId: tenantId);

        try
        {
            var response = await _nexusClient.SendChatAsync(nexusRequest, cancellationToken);

            var responseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;

            return new AiResponseDto
            {
                Content = response.Response ?? string.Empty,
                Model = nexusModel,
                FinishReason = "stop",
                PromptTokens = response.Usage?.PromptTokens ?? 0,
                CompletionTokens = response.Usage?.CompletionTokens ?? 0,
                TotalTokens = response.Usage?.TotalTokens ?? 0,
                ResponseTime = responseTime,
                Cost = 0m, // Nexus 사내 모델 — 비용 0
            };
        }
        catch (HttpRequestException hrex)
        {
            _logger.LogError(hrex,
                "Nexus 호출 실패 (LAN 연결 불가). Service={ServiceCode}, Model={Model}, hadSystem={HadSystem}",
                service.ServiceCode, nexusModel, hadSystem);
            throw new InvalidOperationException(
                "Nexus 응답 실패. 사내망 연결을 확인하세요.", hrex);
        }
        catch (TaskCanceledException tcex) when (!cancellationToken.IsCancellationRequested)
        {
            // 사용자 취소가 아닌 타임아웃.
            _logger.LogError(tcex,
                "Nexus 호출 타임아웃. Service={ServiceCode}, Model={Model}",
                service.ServiceCode, nexusModel);
            throw new InvalidOperationException(
                "Nexus 응답이 시간 초과되었습니다. 잠시 후 다시 시도해주세요.", tcex);
        }
    }

    /// <summary>
    /// Nexus 스트리밍 호출 — INexusClient.SendChatStreamAsync 위임 + ChatChunk 변환.
    /// Phase 3.5b SSE 컨벤션(delta/usage/stop) 보존.
    /// </summary>
    private async IAsyncEnumerable<ChatChunk> StreamNexusChunksAsync(
        ApiService service,
        string model,
        ChatMessageRequestDto request,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (_nexusClient == null)
        {
            _logger.LogError("StreamNexusChunksAsync 호출됐지만 INexusClient 가 주입되지 않음");
            throw new InvalidOperationException(
                "Nexus 클라이언트가 등록되지 않았습니다. 사내망 연결을 확인하세요.");
        }

        var (mergedMessage, _) = BuildNexusSingleMessage(request);
        if (string.IsNullOrWhiteSpace(mergedMessage))
        {
            throw new InvalidOperationException(
                "Nexus 호출에 실패했습니다. 전송할 사용자 메시지가 없습니다.");
        }

        var nexusModel = NormalizeNexusModel(model);
        var tenantId = _configuration["Nexus:DefaultTenantId"];
        if (string.IsNullOrWhiteSpace(tenantId)) tenantId = "default";

        var nexusRequest = new NexusChatRequest(
            Message: mergedMessage,
            SessionId: null,
            Model: nexusModel,
            TenantId: tenantId);

        // 스트림 종료 시 마지막 finish_reason chunk 발행을 보장.
        // type=done 이벤트 또는 응답 종료 시 NexusClient 가 enumerator 를 자연 종료시킨다.
        bool sawUsage = false;

        await foreach (var evt in _nexusClient.SendChatStreamAsync(nexusRequest, cancellationToken)
            .WithCancellation(cancellationToken))
        {
            switch (evt.Type)
            {
                case "chunk":
                    if (!string.IsNullOrEmpty(evt.Text))
                    {
                        yield return ChatChunk.Delta(evt.Text);
                    }
                    break;

                case "usage":
                    if (evt.Usage != null)
                    {
                        sawUsage = true;
                        yield return ChatChunk.Usage(
                            evt.Usage.PromptTokens,
                            evt.Usage.CompletionTokens,
                            evt.Usage.TotalTokens);
                    }
                    break;

                case "error":
                    _logger.LogError(
                        "Nexus 스트림 에러 이벤트. Code={Code}, Message={Message}",
                        evt.ErrorCode, evt.ErrorMessage);
                    throw new InvalidOperationException(
                        evt.ErrorMessage ?? "Nexus 스트리밍 중 에러가 발생했습니다.");

                case "done":
                    // Enumerator 자연 종료 신호 — 추가 처리 없음.
                    break;

                default:
                    _logger.LogDebug("알 수 없는 Nexus 스트림 이벤트 타입 무시: {Type}", evt.Type);
                    break;
            }
        }

        // Phase 3.5b 컨벤션 — finish_reason chunk 항상 발행.
        // sawUsage 여부와 무관하게 stop chunk 를 통해 ChatService 의 finishReason 변수가 채워진다.
        yield return ChatChunk.Stop("stop");

        // sawUsage 가 false 이면 ChatService 가 cost 계산 시 totalTokens=0 폴백을 사용한다.
        // Nexus 가 usage 이벤트를 발행하지 않을 가능성에 대비해 별도 경고만 남긴다.
        if (!sawUsage)
        {
            _logger.LogDebug(
                "Nexus 스트림 종료 — usage 이벤트 미발행. Service={ServiceCode}, Model={Model}",
                service.ServiceCode, nexusModel);
        }
    }

    /// <summary>
    /// ChatMessageRequestDto 의 messages 를 Nexus 단일 message string 으로 합친다.
    /// 시스템 메시지가 있으면 prepend, 그 외에는 마지막 user 메시지만.
    /// </summary>
    /// <returns>(merged, hadSystem) — merged 가 비면 호출자가 InvalidOperationException 발생.</returns>
    private static (string Merged, bool HadSystem) BuildNexusSingleMessage(ChatMessageRequestDto request)
    {
        if (request.Messages == null || request.Messages.Count == 0)
        {
            return (string.Empty, false);
        }

        var systemMsg = request.Messages.FirstOrDefault(m => m.Role == "system");
        var lastUserMsg = request.Messages.LastOrDefault(m => m.Role == "user");

        // 마지막 user 의 텍스트(멀티모달 포함) 추출.
        string? userText = null;
        if (lastUserMsg != null)
        {
            if (!string.IsNullOrWhiteSpace(lastUserMsg.Content))
            {
                userText = lastUserMsg.Content;
            }
            else if (lastUserMsg.Contents != null && lastUserMsg.Contents.Count > 0)
            {
                var parts = lastUserMsg.Contents
                    .Where(c => string.Equals(c.Type, "text", StringComparison.OrdinalIgnoreCase)
                                && !string.IsNullOrWhiteSpace(c.Text))
                    .Select(c => c.Text);
                userText = string.Join("\n", parts);
            }
        }

        if (string.IsNullOrWhiteSpace(userText))
        {
            return (string.Empty, systemMsg != null);
        }

        if (systemMsg != null && !string.IsNullOrWhiteSpace(systemMsg.Content))
        {
            // Nexus 측 message 에 시스템 컨텍스트 prepend.
            return ($"{systemMsg.Content}\n\n{userText}", true);
        }
        return (userText, false);
    }

    /// <summary>
    /// Nexus 가 인식하는 model 카테고리("primary"/"auxiliary") 로 정규화.
    /// 미인식 모델은 LogWarning 후 "primary" 폴백.
    /// </summary>
    private string NormalizeNexusModel(string? raw)
    {
        if (string.IsNullOrWhiteSpace(raw)) return "primary";
        var lower = raw.Trim().ToLowerInvariant();
        if (lower is "primary" or "auxiliary") return lower;

        _logger.LogWarning(
            "Nexus 가 인식하지 못하는 모델 '{Model}' — 'primary' 로 폴백. " +
            "Agent.DefaultModel 설정을 'primary' 또는 'auxiliary' 로 변경 권장.",
            raw);
        return "primary";
    }

    // ════════════════════════════════════════════════════════════════════════════
    // Phase 7.5 — Embeddings 위임 (OpenAI 호환)
    //
    // 사용처:
    //   /v1/embeddings 컨트롤러 → 본 메서드 호출 → ApiService.ServiceCode 분기
    //
    // 지원 프로바이더 (현재):
    //   - "openai" / "chatgpt"  : POST {BaseUrl}/embeddings
    //   - "azureopenai" / "azure-openai" / "microsoft-copilot" / "copilot"
    //                            : POST {BaseUrl}/openai/deployments/{model}/embeddings?api-version=...
    //
    // 미지원 프로바이더 (향후 트랙):
    //   - claude/gemini/perplexity/mistral/nexus → NotSupportedException
    //   - 임베딩 모델은 OpenAI/Azure OpenAI 가 사실상 표준 (Anthropic 미제공, Gemini 별도 SDK)
    //
    // OpenAI Embeddings API 응답 형식:
    //   {"object":"list","data":[{"object":"embedding","index":0,"embedding":[..1536..]}],
    //    "model":"text-embedding-3-small","usage":{"prompt_tokens":N,"total_tokens":N}}
    // ════════════════════════════════════════════════════════════════════════════
    public async Task<EmbeddingResultDto> GenerateEmbeddingAsync(
        ApiService service,
        string model,
        string[] inputs,
        CancellationToken cancellationToken = default)
    {
        if (service == null)
            throw new ArgumentNullException(nameof(service));
        if (inputs == null || inputs.Length == 0)
            throw new ArgumentException("inputs 는 최소 1건의 텍스트를 포함해야 합니다.", nameof(inputs));

        var providerCode = service.ServiceCode?.Trim().ToLowerInvariant() ?? string.Empty;

        return providerCode switch
        {
            "openai" or "chatgpt" => await CallOpenAiEmbeddingsAsync(model, inputs, cancellationToken),
            "azureopenai" or "azure-openai" or "copilot" or "microsoft-copilot"
                => await CallAzureOpenAiEmbeddingsAsync(service, model, inputs, cancellationToken),
            _ => throw new NotSupportedException(
                $"임베딩 프로바이더 '{service.ServiceCode}' 미지원 (Phase 7.5). " +
                "현재 OpenAI / Azure OpenAI 만 지원합니다 — Agent.ServiceId 를 'openai' 로 변경하세요.")
        };
    }

    /// <summary>
    /// OpenAI Embeddings API 호출. ApiKeyPool 라운드로빈 + 429 cooldown 적용.
    /// </summary>
    private async Task<EmbeddingResultDto> CallOpenAiEmbeddingsAsync(
        string model,
        string[] inputs,
        CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("openai", "AiApiSettings:OpenAI:ApiKey");
        var baseUrl = _configuration["AiApiSettings:OpenAI:BaseUrl"] ?? "https://api.openai.com/v1";

        if (string.IsNullOrEmpty(apiKey))
        {
            _logger.LogError("OpenAI API key is not configured (embeddings)");
            throw new InvalidOperationException("OpenAI API 키가 설정되지 않았습니다.");
        }

        // OpenAI Embeddings API 는 input 으로 string 또는 string[] 모두 허용.
        // 단건/배치 분기 없이 항상 배열로 전송하면 응답이 항상 동일 schema 가 된다.
        var payload = new
        {
            model,
            input = inputs,
        };
        var json = JsonSerializer.Serialize(payload);
        using var content = new StringContent(json, Encoding.UTF8, "application/json");

        var client = _httpClientFactory.CreateClient("openai");
        client.DefaultRequestHeaders.Authorization =
            new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);

        var startTime = DateTime.UtcNow;
        var response = await client.PostAsync($"{baseUrl}/embeddings", content, cancellationToken);
        var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError(
                "OpenAI Embeddings API error. Status: {StatusCode}, Response: {Response}, Model={Model}, Inputs={Count}",
                response.StatusCode, responseJson, model, inputs.Length);

            if (response.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
            {
                _apiKeyPool?.MarkAsCoolingDown("openai", apiKey ?? string.Empty);
                throw new HttpRequestException(
                    $"OpenAI Embeddings 429 Too Many Requests - {responseJson}",
                    null, response.StatusCode);
            }
            throw new InvalidOperationException(
                $"OpenAI Embeddings API error: {response.StatusCode} - {responseJson}");
        }

        return ParseOpenAiEmbeddingsResponse(responseJson, model, inputs.Length, startTime);
    }

    /// <summary>
    /// Azure OpenAI Embeddings API 호출. deployment 별도 path 사용.
    /// </summary>
    private async Task<EmbeddingResultDto> CallAzureOpenAiEmbeddingsAsync(
        ApiService service,
        string model,
        string[] inputs,
        CancellationToken cancellationToken)
    {
        var apiKey = GetApiKey("azureopenai", "AiApiSettings:AzureOpenAI:ApiKey")
                     ?? _configuration["AiApiSettings:AzureOpenAI:ApiKey"];
        var endpoint = _configuration["AiApiSettings:AzureOpenAI:Endpoint"] ?? service.ApiEndpoint;
        var apiVersion = _configuration["AiApiSettings:AzureOpenAI:ApiVersion"] ?? "2024-02-15-preview";

        if (string.IsNullOrEmpty(apiKey) || string.IsNullOrEmpty(endpoint))
        {
            _logger.LogError("Azure OpenAI API key or endpoint not configured (embeddings)");
            throw new InvalidOperationException("Azure OpenAI 설정이 누락되었습니다.");
        }

        var payload = new { input = inputs };
        var json = JsonSerializer.Serialize(payload);
        using var content = new StringContent(json, Encoding.UTF8, "application/json");

        var client = _httpClientFactory.CreateClient("azureopenai");
        client.DefaultRequestHeaders.Remove("api-key");
        client.DefaultRequestHeaders.Add("api-key", apiKey);

        var url = $"{endpoint.TrimEnd('/')}/openai/deployments/{model}/embeddings?api-version={apiVersion}";
        var startTime = DateTime.UtcNow;

        var response = await client.PostAsync(url, content, cancellationToken);
        var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError(
                "Azure OpenAI Embeddings API error. Status: {StatusCode}, Response: {Response}, Deployment={Model}",
                response.StatusCode, responseJson, model);
            if (response.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
            {
                _apiKeyPool?.MarkAsCoolingDown("azureopenai", apiKey ?? string.Empty);
                throw new HttpRequestException(
                    $"Azure OpenAI Embeddings 429 - {responseJson}",
                    null, response.StatusCode);
            }
            throw new InvalidOperationException(
                $"Azure OpenAI Embeddings API error: {response.StatusCode} - {responseJson}");
        }

        return ParseOpenAiEmbeddingsResponse(responseJson, model, inputs.Length, startTime);
    }

    /// <summary>
    /// OpenAI Embeddings API 응답(JSON) 파싱 — Azure OpenAI 도 동일 schema.
    /// 입력 순서를 보존하기 위해 data[].index 로 재정렬.
    /// </summary>
    private EmbeddingResultDto ParseOpenAiEmbeddingsResponse(
        string responseJson, string requestedModel, int inputCount, DateTime startTime)
    {
        try
        {
            using var doc = JsonDocument.Parse(responseJson);
            var root = doc.RootElement;

            // 입력 순서 보존: index 별로 슬롯에 끼워넣기.
            var ordered = new float[inputCount][];
            if (root.TryGetProperty("data", out var dataElem) && dataElem.ValueKind == JsonValueKind.Array)
            {
                foreach (var item in dataElem.EnumerateArray())
                {
                    int index = item.TryGetProperty("index", out var idxElem) ? idxElem.GetInt32() : 0;
                    if (index < 0 || index >= inputCount) continue;

                    if (!item.TryGetProperty("embedding", out var embedElem)
                        || embedElem.ValueKind != JsonValueKind.Array)
                    {
                        continue;
                    }

                    var vec = new float[embedElem.GetArrayLength()];
                    int vi = 0;
                    foreach (var v in embedElem.EnumerateArray())
                    {
                        vec[vi++] = (float)v.GetDouble();
                    }
                    ordered[index] = vec;
                }
            }

            // 누락 슬롯 방어 — 0 벡터로 채워 client 가 IndexError 를 보지 않도록.
            for (int i = 0; i < inputCount; i++)
            {
                ordered[i] ??= Array.Empty<float>();
            }

            string echoedModel = root.TryGetProperty("model", out var modelElem)
                ? modelElem.GetString() ?? requestedModel
                : requestedModel;

            int promptTokens = 0, totalTokens = 0;
            if (root.TryGetProperty("usage", out var usageElem) && usageElem.ValueKind == JsonValueKind.Object)
            {
                if (usageElem.TryGetProperty("prompt_tokens", out var pt)) promptTokens = pt.GetInt32();
                if (usageElem.TryGetProperty("total_tokens", out var tt)) totalTokens = tt.GetInt32();
            }

            var elapsedMs = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
            _logger.LogInformation(
                "Embeddings API success. Model={Model}, Inputs={Count}, Tokens={Tokens}, ElapsedMs={Elapsed}",
                echoedModel, inputCount, totalTokens, elapsedMs);

            return new EmbeddingResultDto
            {
                Embeddings = ordered,
                Model = echoedModel,
                PromptTokens = promptTokens,
                TotalTokens = totalTokens,
            };
        }
        catch (JsonException ex)
        {
            _logger.LogError(ex, "Failed to parse Embeddings response. Response={Response}",
                responseJson.Length > 500 ? responseJson.Substring(0, 500) : responseJson);
            throw new InvalidOperationException(
                "임베딩 응답 파싱에 실패했습니다 — 프로바이더 응답 형식을 확인하세요.", ex);
        }
    }
}
