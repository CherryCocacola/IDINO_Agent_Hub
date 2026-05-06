using System.Net.Http.Headers;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace AIAgentManagement.Services;

// ════════════════════════════════════════════════════════════════════════════
// NexusClient — INexusClient 구현체 (Phase 5.1)
//
// 책임 범위:
//   1. Named HttpClient "nexus" 사용(연결 풀링/타임아웃은 Program.cs 에서 관리)
//   2. ADR-13 공유 시크릿 인증(Authorization Bearer + X-Tenant-ID)
//   3. /v1/chat 비스트리밍 — JSON in/out
//   4. /v1/chat/stream SSE 파싱 — 프레임 단위 디시리얼라이즈, heartbeat 무시
//
// 책임 범위 밖(Phase 5.2 에서 처리):
//   - ChatMessageRequestDto -> NexusChatRequest 매핑 (AiProxyService.CallNexusAsync)
//   - HybridRouter 평가 / PII 강제 라우팅
//   - 사용량(ApiUsage) / 활동 로그 기록
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// Nexus chat 엔드포인트 클라이언트 구현. AiProxyService 가 합성하여 옵션 B 호출을 수행한다.
/// </summary>
public class NexusClient : INexusClient
{
    private const string HttpClientName = "nexus";

    // SSE 프레임 종결자 — Nexus 측은 표준 SSE 규격(`\n\n`) 을 따른다.
    private const string SseFrameSeparator = "\n\n";

    // SSE 주석 라인(heartbeat 등) — 표준 SSE 에서 콜론으로 시작.
    private const string SseCommentPrefix = ":";

    // SSE 데이터 라인 prefix.
    private const string SseDataPrefix = "data: ";

    // 스트림 종료 신호 — OpenAI 호환 컨벤션이지만 Nexus 도 채택 가능. 본 클라이언트는
    // type=done 이벤트와 [DONE] 마커 양쪽 모두를 종료 신호로 처리한다.
    private const string SseDoneMarker = "[DONE]";

    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IConfiguration _configuration;
    private readonly ILogger<NexusClient> _logger;

    // 직렬화/역직렬화 옵션 — Nexus 측은 snake_case(FastAPI 표준).
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        PropertyNameCaseInsensitive = true,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    public NexusClient(
        IHttpClientFactory httpClientFactory,
        IConfiguration configuration,
        ILogger<NexusClient> logger)
    {
        _httpClientFactory = httpClientFactory;
        _configuration = configuration;
        _logger = logger;
    }

    // ══════════════════════════════════════════════════════════════════════
    // 비스트리밍 — POST /v1/chat
    // ══════════════════════════════════════════════════════════════════════
    public async Task<NexusChatResponse> SendChatAsync(
        NexusChatRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = BuildHttpRequest(HttpMethod.Post, "/v1/chat", request);

        _logger.LogDebug(
            "Nexus 비스트리밍 호출 시작 - Model={Model}, SessionId={SessionId}, TenantId={TenantId}",
            request.Model, request.SessionId, request.TenantId);

        using var httpResponse = await client.SendAsync(
            httpRequest,
            HttpCompletionOption.ResponseContentRead,
            cancellationToken);

        if (!httpResponse.IsSuccessStatusCode)
        {
            var errorBody = await SafeReadErrorBodyAsync(httpResponse, cancellationToken);
            _logger.LogError(
                "Nexus /v1/chat 호출 실패 - Status={Status}, Body={Body}",
                (int)httpResponse.StatusCode, errorBody);
            throw new InvalidOperationException(
                $"Nexus 응답 실패 (HTTP {(int)httpResponse.StatusCode}): {errorBody}");
        }

        await using var responseStream = await httpResponse.Content.ReadAsStreamAsync(cancellationToken);
        var response = await JsonSerializer.DeserializeAsync<NexusChatResponse>(
            responseStream, JsonOptions, cancellationToken);

        if (response is null)
        {
            throw new InvalidOperationException("Nexus 응답 본문을 디시리얼라이즈하지 못했습니다.");
        }

        _logger.LogDebug(
            "Nexus 비스트리밍 응답 수신 - SessionId={SessionId}, TotalTokens={TotalTokens}",
            response.SessionId, response.Usage?.TotalTokens);

        return response;
    }

    // ══════════════════════════════════════════════════════════════════════
    // 스트리밍 — POST /v1/chat/stream (SSE)
    //
    // SSE 파서 설계:
    //   1. ResponseHeadersRead 모드로 응답을 받아 본문을 라인 단위 스트리밍.
    //   2. 라인 누적기(StringBuilder)에 모은 뒤 빈 줄(`\n\n`) 으로 프레임 분리.
    //   3. ":" 시작 라인은 SSE 주석(heartbeat) — 무시.
    //   4. "data: " prefix 의 라인을 페이로드로 추출.
    //   5. 페이로드가 "[DONE]" 이면 종료. 그 외엔 JSON -> NexusStreamEvent yield.
    //   6. type=done 이벤트도 종료 신호로 인정.
    //   7. CancellationToken 은 [EnumeratorCancellation] 으로 양 방향 전파.
    // ══════════════════════════════════════════════════════════════════════
    public async IAsyncEnumerable<NexusStreamEvent> SendChatStreamAsync(
        NexusChatRequest request,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = BuildHttpRequest(HttpMethod.Post, "/v1/chat/stream", request);
        // SSE 명시 — Nexus 측이 Accept 협상에 의존하진 않지만 캐시 미스/프록시 보호용.
        httpRequest.Headers.Accept.Clear();
        httpRequest.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("text/event-stream"));

        _logger.LogDebug(
            "Nexus 스트리밍 호출 시작 - Model={Model}, SessionId={SessionId}, TenantId={TenantId}",
            request.Model, request.SessionId, request.TenantId);

        using var httpResponse = await client.SendAsync(
            httpRequest,
            HttpCompletionOption.ResponseHeadersRead,
            cancellationToken);

        if (!httpResponse.IsSuccessStatusCode)
        {
            var errorBody = await SafeReadErrorBodyAsync(httpResponse, cancellationToken);
            _logger.LogError(
                "Nexus /v1/chat/stream 호출 실패 - Status={Status}, Body={Body}",
                (int)httpResponse.StatusCode, errorBody);
            throw new InvalidOperationException(
                $"Nexus 스트리밍 응답 실패 (HTTP {(int)httpResponse.StatusCode}): {errorBody}");
        }

        await using var responseStream = await httpResponse.Content.ReadAsStreamAsync(cancellationToken);
        using var reader = new StreamReader(responseStream, Encoding.UTF8);

        // 프레임 누적기 — 빈 줄(\n\n) 을 만나면 한 프레임 완성.
        var frameBuffer = new StringBuilder(capacity: 1024);

        while (!cancellationToken.IsCancellationRequested)
        {
            var line = await reader.ReadLineAsync(cancellationToken);
            if (line is null)
            {
                // 스트림 종료 — 누적된 마지막 프레임이 있으면 처리.
                if (frameBuffer.Length > 0)
                {
                    if (TryParseFrame(frameBuffer.ToString(), out var lastEvent))
                    {
                        if (lastEvent is not null) yield return lastEvent;
                    }
                }
                yield break;
            }

            // 빈 줄 = 프레임 종결자.
            if (string.IsNullOrEmpty(line))
            {
                if (frameBuffer.Length == 0)
                {
                    continue; // 연속된 빈 줄 무시
                }

                var frame = frameBuffer.ToString();
                frameBuffer.Clear();

                if (!TryParseFrame(frame, out var streamEvent))
                {
                    // 파싱 불가 — 디버그 레벨에서만 흘려둔다.
                    _logger.LogDebug("Nexus SSE 프레임 파싱 실패 (무시): {Frame}", frame);
                    continue;
                }

                // [DONE] 마커 → 본 클라이언트가 합성한 종료 이벤트(yield 후 break)
                if (streamEvent is null)
                {
                    yield break;
                }

                yield return streamEvent;

                // type=done 이벤트도 종료 신호로 처리.
                if (string.Equals(streamEvent.Type, "done", StringComparison.OrdinalIgnoreCase))
                {
                    yield break;
                }
            }
            else
            {
                // 주석 라인(heartbeat 등) — SSE 표준 ":" prefix.
                if (line.StartsWith(SseCommentPrefix, StringComparison.Ordinal))
                {
                    _logger.LogTrace("Nexus SSE 주석/heartbeat 수신 (무시): {Line}", line);
                    continue;
                }

                // 일반 라인 — 프레임 누적기에 줄바꿈 포함하여 추가.
                if (frameBuffer.Length > 0)
                {
                    frameBuffer.Append('\n');
                }
                frameBuffer.Append(line);
            }
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // 헬퍼
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// HttpRequestMessage 빌더 — 인증 헤더(ADR-13) + JSON body 를 조립한다.
    /// </summary>
    private HttpRequestMessage BuildHttpRequest(HttpMethod method, string relativePath, NexusChatRequest request)
    {
        var httpRequest = new HttpRequestMessage(method, relativePath);

        // X-Tenant-ID 헤더 — body.tenant_id 가 우선이지만, 미지정 시 헤더 폴백.
        var tenantId = !string.IsNullOrWhiteSpace(request.TenantId)
            ? request.TenantId
            : _configuration["Nexus:DefaultTenantId"];
        if (!string.IsNullOrWhiteSpace(tenantId))
        {
            httpRequest.Headers.Add("X-Tenant-ID", tenantId);
        }

        // 공유 시크릿 — 미설정 시 InfoLog 후 인증 헤더 생략(LAN 격리만으로 1차 방어).
        var sharedSecret = _configuration["Nexus:SharedSecret"];
        if (!string.IsNullOrWhiteSpace(sharedSecret))
        {
            httpRequest.Headers.Authorization = new AuthenticationHeaderValue("Bearer", sharedSecret);
        }
        else
        {
            _logger.LogWarning(
                "Nexus:SharedSecret 미설정 — LAN 격리에만 의존합니다. Phase 5+ 운영 적용 전 반드시 설정 필요.");
        }

        // JSON body — snake_case 직렬화로 Nexus FastAPI 모델과 1:1 매핑.
        var jsonBody = JsonSerializer.Serialize(request, JsonOptions);
        httpRequest.Content = new StringContent(jsonBody, Encoding.UTF8, "application/json");

        return httpRequest;
    }

    /// <summary>
    /// 단일 SSE 프레임을 NexusStreamEvent 로 디시리얼라이즈한다.
    /// 반환:
    ///   - true + event=null:  [DONE] 마커 (호출자가 yield break)
    ///   - true + event!=null: 정상 이벤트
    ///   - false:              파싱 불가 (호출자가 무시)
    /// </summary>
    private static bool TryParseFrame(string frame, out NexusStreamEvent? streamEvent)
    {
        streamEvent = null;
        if (string.IsNullOrWhiteSpace(frame)) return false;

        // 한 프레임이 여러 라인일 수 있으나, Nexus 의 chunk 프레임은 단일 data 라인이 일반적.
        // 안전하게 모든 라인 중 "data: " prefix 만 결합.
        var payloadBuilder = new StringBuilder();
        foreach (var rawLine in frame.Split('\n'))
        {
            var line = rawLine.TrimEnd('\r');
            if (line.StartsWith(SseDataPrefix, StringComparison.Ordinal))
            {
                if (payloadBuilder.Length > 0) payloadBuilder.Append('\n');
                payloadBuilder.Append(line.AsSpan(SseDataPrefix.Length));
            }
            // event: / id: / retry: 라인은 본 시점에선 미사용.
        }

        var payload = payloadBuilder.ToString().Trim();
        if (payload.Length == 0) return false;

        // [DONE] 마커.
        if (string.Equals(payload, SseDoneMarker, StringComparison.Ordinal))
        {
            return true; // streamEvent=null 로 종료 신호 표현
        }

        try
        {
            streamEvent = JsonSerializer.Deserialize<NexusStreamEvent>(payload, JsonOptions);
            return streamEvent is not null;
        }
        catch (JsonException)
        {
            return false;
        }
    }

    /// <summary>
    /// 오류 응답 본문을 안전하게 읽어온다(읽기 실패 시 빈 문자열).
    /// </summary>
    private static async Task<string> SafeReadErrorBodyAsync(
        HttpResponseMessage response,
        CancellationToken cancellationToken)
    {
        try
        {
            return await response.Content.ReadAsStringAsync(cancellationToken);
        }
        catch
        {
            return string.Empty;
        }
    }
}
