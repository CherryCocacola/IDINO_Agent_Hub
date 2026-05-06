using System.Text.Json;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;

namespace AIAgentManagement.Services;

// ════════════════════════════════════════════════════════════════════════════
// HybridRouter 구현 (Phase 5.2)
//
// RoutingPolicyJson 스키마 (.claude/rules/domain-model.md):
// {
//   "piiThreshold": "block" | "mask" | "off",
//   "piiAction": "internal" | "external",
//   "dataLabels": {
//     "confidential": "internal",
//     "internal": "internal",
//     "public": "external"
//   },
//   "modelCapability": {
//     "vision": "external",
//     "longContext": "external",
//     "longContextThreshold": 32000
//   },
//   "costThreshold": {
//     "perRequest": 0.10,
//     "exceedAction": "internal"
//   },
//   "default": "external"
// }
//
// 데이터 라벨 입력 경로:
//   - 본 단계에서는 ChatMessageRequestDto 확장 없이 HTTP 헤더 X-Data-Label 만 지원.
//     IHttpContextAccessor 를 통해 헤더값 조회 → "confidential"/"internal"/"public" 셋 중 하나.
//   - 헤더 없으면 데이터 라벨 단계는 스킵하고 다음 우선순위로 진행.
//   - DTO 확장은 별도 트랙(향후 ConsumerSystem 단위 표준화 후 도입).
//
// 모델 capability 단순 휴리스틱:
//   - vision 모델: model 이름에 "vision" / "4o" / "o1" / "claude-3-5-sonnet" 포함 시 external 강제
//   - longContext: request.MaxTokens > longContextThreshold(기본 32000) 시 external 강제
//
// 비용 임계치:
//   - estimated cost = (대략적 prompt token 추정) × 비용 단가(휴리스틱 0.000002 USD/token)
//   - 추정 토큰 = sum(messages.Content.Length) / 4
//   - 본 휴리스틱은 OpenAI tokenizer 의 영어 평균(4 char/token)을 한국어에 단순 적용한 것으로
//     정밀 토큰 계산은 별도 트랙(tiktoken-csharp 도입 시점).
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// HybridRouter 구현체. PII 감지/라벨/capability/비용 5단계 결정을 수행한다.
/// </summary>
public class HybridRouter : IHybridRouter
{
    private readonly IPiiDetectionService _piiService;
    private readonly IHttpContextAccessor _httpContextAccessor;
    private readonly ILogger<HybridRouter> _logger;

    // RoutingPolicyJson 파싱 옵션 — JSON 표준은 camelCase 이지만 사용자가 PascalCase 로
    // 작성할 수도 있으므로 case-insensitive 비교 활성화.
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
    };

    // 영어 평균 1 토큰 ≈ 4 chars 휴리스틱.
    private const int CharsPerTokenHeuristic = 4;

    // 비용 추정 단가(USD/token). 외부 모델 평균값 — 정확한 단가는 ApiService.CostPerRequest
    // 또는 ApiServiceModel 에 별도 컬럼 필요(향후 트랙).
    private const decimal EstimatedCostPerToken = 0.000002m;

    // longContext 기본 임계치(RoutingPolicyJson 미명시 시 사용).
    private const int DefaultLongContextThreshold = 32_000;

    // vision capability 모델 이름 휴리스틱 — 소문자 비교.
    private static readonly string[] VisionModelHints =
    {
        "vision", "4o", "o1", "claude-3-5-sonnet", "gemini-2.5-pro", "gemini-3"
    };

    public HybridRouter(
        IPiiDetectionService piiService,
        IHttpContextAccessor httpContextAccessor,
        ILogger<HybridRouter> logger)
    {
        _piiService = piiService;
        _httpContextAccessor = httpContextAccessor;
        _logger = logger;
    }

    public async Task<HybridRoutingDecision> DecideAsync(
        Agent agent,
        ChatMessageRequestDto request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(agent);
        ArgumentNullException.ThrowIfNull(request);

        // ── 정책 JSON 파싱 ────────────────────────────────────────────────────
        var policyJson = agent.RoutingPolicyJson;
        if (string.IsNullOrWhiteSpace(policyJson))
        {
            _logger.LogWarning(
                "Agent {AgentId} 가 Hybrid 모드인데 RoutingPolicyJson 이 비어있음 — external 폴백",
                agent.AgentId);
            return new HybridRoutingDecision("external", "empty_policy");
        }

        JsonElement policy;
        try
        {
            policy = JsonSerializer.Deserialize<JsonElement>(policyJson, JsonOptions);
        }
        catch (JsonException jx)
        {
            _logger.LogWarning(jx,
                "Agent {AgentId} 의 RoutingPolicyJson 파싱 실패 — external 폴백. JSON: {Json}",
                agent.AgentId,
                policyJson.Length > 200 ? policyJson[..200] + "..." : policyJson);
            return new HybridRoutingDecision("external", "invalid_policy", jx.Message);
        }

        // ── 1단계: PII 감지 ────────────────────────────────────────────────────
        var piiThreshold = TryGetString(policy, "piiThreshold", "off")?.ToLowerInvariant() ?? "off";
        if (piiThreshold is "block" or "mask")
        {
            var piiAction = TryGetString(policy, "piiAction", "internal")?.ToLowerInvariant() ?? "internal";
            var lastUserContent = ExtractLastUserText(request);

            if (!string.IsNullOrWhiteSpace(lastUserContent))
            {
                try
                {
                    var piiResult = await _piiService.DetectPiiAsync(lastUserContent);
                    if (piiResult.HasPii)
                    {
                        _logger.LogInformation(
                            "HybridRouter: Agent {AgentId} — PII 감지로 {Action} 라우팅. 검출 타입: {Types}",
                            agent.AgentId,
                            piiAction,
                            string.Join(",", piiResult.DetectedItems.Select(i => i.Type).Distinct()));
                        return new HybridRoutingDecision(
                            NormalizeDecision(piiAction),
                            "pii_detected",
                            string.Join(",", piiResult.DetectedItems.Select(i => i.Type).Distinct()));
                    }
                }
                catch (Exception ex)
                {
                    // PII 검출 실패는 보수적으로 internal 강제(데이터 누설 방지).
                    _logger.LogWarning(ex,
                        "HybridRouter: PII 검출 실패 — 보수적으로 internal 라우팅. AgentId={AgentId}",
                        agent.AgentId);
                    return new HybridRoutingDecision("internal", "pii_detected", "pii_check_failed");
                }
            }
        }

        // ── 2단계: 데이터 라벨 ─────────────────────────────────────────────────
        var dataLabel = ReadDataLabelFromHeader();
        if (!string.IsNullOrWhiteSpace(dataLabel)
            && policy.TryGetProperty("dataLabels", out var dataLabelsEl)
            && dataLabelsEl.ValueKind == JsonValueKind.Object)
        {
            // 라벨 케이스 무관 매칭 — domain-model.md 표준은 소문자.
            foreach (var prop in dataLabelsEl.EnumerateObject())
            {
                if (string.Equals(prop.Name, dataLabel, StringComparison.OrdinalIgnoreCase)
                    && prop.Value.ValueKind == JsonValueKind.String)
                {
                    var mapped = NormalizeDecision(prop.Value.GetString());
                    _logger.LogInformation(
                        "HybridRouter: Agent {AgentId} — 데이터 라벨 '{Label}' → {Decision}",
                        agent.AgentId, dataLabel, mapped);
                    return new HybridRoutingDecision(mapped, "data_label", dataLabel);
                }
            }
        }

        // ── 3단계: 모델 capability ─────────────────────────────────────────────
        if (policy.TryGetProperty("modelCapability", out var capabilityEl)
            && capabilityEl.ValueKind == JsonValueKind.Object)
        {
            var modelLower = (agent.DefaultModel ?? string.Empty).ToLowerInvariant();

            // vision 매칭
            if (capabilityEl.TryGetProperty("vision", out var visionEl)
                && visionEl.ValueKind == JsonValueKind.String
                && VisionModelHints.Any(h => modelLower.Contains(h)))
            {
                var mapped = NormalizeDecision(visionEl.GetString());
                _logger.LogInformation(
                    "HybridRouter: Agent {AgentId} — vision 모델 '{Model}' → {Decision}",
                    agent.AgentId, modelLower, mapped);
                return new HybridRoutingDecision(mapped, "capability_required", $"vision:{modelLower}");
            }

            // longContext 매칭
            if (capabilityEl.TryGetProperty("longContext", out var longCtxEl)
                && longCtxEl.ValueKind == JsonValueKind.String)
            {
                var threshold = capabilityEl.TryGetProperty("longContextThreshold", out var threshEl)
                    && threshEl.ValueKind == JsonValueKind.Number
                    && threshEl.TryGetInt32(out var thr)
                    ? thr
                    : DefaultLongContextThreshold;

                var requested = request.MaxTokens ?? 0;
                if (requested > threshold)
                {
                    var mapped = NormalizeDecision(longCtxEl.GetString());
                    _logger.LogInformation(
                        "HybridRouter: Agent {AgentId} — longContext (MaxTokens={MaxTokens} > {Threshold}) → {Decision}",
                        agent.AgentId, requested, threshold, mapped);
                    return new HybridRoutingDecision(mapped, "capability_required",
                        $"longContext:{requested}>{threshold}");
                }
            }
        }

        // ── 4단계: 비용 임계치 ─────────────────────────────────────────────────
        if (policy.TryGetProperty("costThreshold", out var costEl)
            && costEl.ValueKind == JsonValueKind.Object
            && costEl.TryGetProperty("perRequest", out var perReqEl)
            && perReqEl.ValueKind == JsonValueKind.Number
            && perReqEl.TryGetDecimal(out var costThreshold))
        {
            var estTokens = EstimateTokens(request);
            var estCost = estTokens * EstimatedCostPerToken;

            if (estCost > costThreshold)
            {
                var exceedAction = costEl.TryGetProperty("exceedAction", out var actEl)
                    && actEl.ValueKind == JsonValueKind.String
                    ? actEl.GetString()
                    : "internal";

                var mapped = NormalizeDecision(exceedAction);
                _logger.LogInformation(
                    "HybridRouter: Agent {AgentId} — 비용 추정 {EstCost:F4} > {Threshold:F4} → {Decision}",
                    agent.AgentId, estCost, costThreshold, mapped);
                return new HybridRoutingDecision(mapped, "cost_exceeded",
                    $"est={estCost:F4},threshold={costThreshold:F4}");
            }
        }

        // ── 5단계: default ─────────────────────────────────────────────────────
        var defaultDecision = NormalizeDecision(TryGetString(policy, "default", "external"));
        _logger.LogDebug(
            "HybridRouter: Agent {AgentId} — 모든 규칙 미매치, default={Decision}",
            agent.AgentId, defaultDecision);
        return new HybridRoutingDecision(defaultDecision, "default");
    }

    // ══════════════════════════════════════════════════════════════════════
    // 헬퍼 메서드
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>JSON object 에서 문자열 속성을 안전하게 읽고 fallback 적용.</summary>
    private static string? TryGetString(JsonElement obj, string propertyName, string? fallback)
    {
        if (obj.ValueKind != JsonValueKind.Object) return fallback;
        if (!obj.TryGetProperty(propertyName, out var el)) return fallback;
        if (el.ValueKind != JsonValueKind.String) return fallback;
        return el.GetString() ?? fallback;
    }

    /// <summary>
    /// 결정값을 "external" / "internal" 로 정규화한다.
    /// 알 수 없는 값은 보수적으로 "external" 로 폴백(외부 LLM 이 default 동작이라 가정).
    /// </summary>
    private static string NormalizeDecision(string? raw)
    {
        if (string.IsNullOrWhiteSpace(raw)) return "external";
        var lower = raw.Trim().ToLowerInvariant();
        return lower switch
        {
            "internal" => "internal",
            "external" => "external",
            _ => "external",
        };
    }

    /// <summary>마지막 user 메시지의 텍스트(멀티모달 포함)를 추출.</summary>
    private static string? ExtractLastUserText(ChatMessageRequestDto request)
    {
        if (request.Messages == null || request.Messages.Count == 0) return null;
        var last = request.Messages.LastOrDefault(m => m.Role == "user");
        if (last == null) return null;
        if (!string.IsNullOrWhiteSpace(last.Content)) return last.Content;
        if (last.Contents == null || last.Contents.Count == 0) return null;

        // 멀티모달 — 텍스트 부분만 결합.
        var parts = last.Contents
            .Where(c => string.Equals(c.Type, "text", StringComparison.OrdinalIgnoreCase)
                        && !string.IsNullOrWhiteSpace(c.Text))
            .Select(c => c.Text);
        return string.Join("\n", parts);
    }

    /// <summary>HTTP 요청 헤더 X-Data-Label 에서 데이터 라벨을 읽는다.</summary>
    private string? ReadDataLabelFromHeader()
    {
        var ctx = _httpContextAccessor.HttpContext;
        if (ctx == null) return null;
        if (!ctx.Request.Headers.TryGetValue("X-Data-Label", out var values)) return null;
        var label = values.ToString();
        return string.IsNullOrWhiteSpace(label) ? null : label.Trim();
    }

    /// <summary>모든 메시지의 글자수 합 / 4 휴리스틱으로 토큰 수 추정.</summary>
    private static int EstimateTokens(ChatMessageRequestDto request)
    {
        if (request.Messages == null || request.Messages.Count == 0) return 0;
        var totalChars = 0;
        foreach (var msg in request.Messages)
        {
            if (!string.IsNullOrEmpty(msg.Content))
            {
                totalChars += msg.Content.Length;
            }
            if (msg.Contents != null)
            {
                foreach (var c in msg.Contents)
                {
                    if (!string.IsNullOrEmpty(c.Text))
                    {
                        totalChars += c.Text.Length;
                    }
                }
            }
        }
        return Math.Max(1, totalChars / CharsPerTokenHeuristic);
    }
}
