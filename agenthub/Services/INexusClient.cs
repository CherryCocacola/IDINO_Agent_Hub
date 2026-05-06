namespace AIAgentManagement.Services;

// ════════════════════════════════════════════════════════════════════════════
// Nexus 사내 LLM 게이트웨이 클라이언트 (Phase 5.1, ADR-1 옵션 B)
//
// AgentHub ↔ Nexus 통합은 옵션 B 로 결정됨 — Nexus 의 네이티브 API(/v1/chat,
// /v1/chat/stream)를 변환 어댑터 없이 그대로 호출하여 세션/멀티테넌시 강점을
// 보존한다(.claude/rules/anti-patterns.md #2 참조).
//
// 인증: ADR-13 — LAN 격리 + 공유 시크릿. 헤더는 X-Tenant-ID + Authorization
//       Bearer {SharedSecret}. SharedSecret 은 IConfiguration["Nexus:SharedSecret"]
//       에서 로드한다(.gitignore 대상, appsettings.Development.json).
//
// 호출 흐름:
//   AgentHub Service (Phase 5.2 의 AiProxyService.CallNexusAsync)
//     -> INexusClient.SendChatAsync / SendChatStreamAsync
//     -> Named HttpClient "nexus" (Program.cs 등록)
//     -> Nexus FastAPI /v1/chat
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// Nexus(사내 LAN-only LLM) chat 엔드포인트 클라이언트 추상화.
/// 외부 노출 시그니처(IAiProxyService/IChatService)는 본 인터페이스에 의존하지 않으며,
/// AiProxyService 만이 본 클라이언트를 합성하여 옵션 B 호출을 수행한다.
/// </summary>
public interface INexusClient
{
    /// <summary>
    /// Nexus 비스트리밍 호출 — POST /v1/chat.
    /// Nexus 의 4-Tier AsyncGenerator 체인이 단일 응답을 모아 반환한다.
    /// 메시지 히스토리는 session_id 키로 Redis 에서 자동 복원되므로 호출자는
    /// 마지막 사용자 메시지만 전달한다.
    /// </summary>
    Task<NexusChatResponse> SendChatAsync(NexusChatRequest request, CancellationToken cancellationToken);

    /// <summary>
    /// Nexus 스트리밍 호출 — POST /v1/chat/stream (SSE).
    /// Nexus 측 큐 기반 producer-consumer 가 청크를 발행하며, 20초 주기 heartbeat
    /// 주석 라인은 본 클라이언트가 흡수한다. 마지막 type=done 이벤트 또는 응답 종료
    /// 시 Enumerable 이 자연 종료된다.
    /// </summary>
    // 주의: [EnumeratorCancellation] 은 async iterator 구현부에만 유효(CS8424).
    // 인터페이스 시그니처에는 부착하지 않으며 NexusClient 구현부에서 부착한다.
    IAsyncEnumerable<NexusStreamEvent> SendChatStreamAsync(
        NexusChatRequest request,
        CancellationToken cancellationToken);
}

// ── Nexus DTO (옵션 B 네이티브 스키마, nexus/web/app.py 기준) ───────────────────

/// <summary>
/// Nexus 호출 요청. Nexus ChatRequest 와 1:1 매핑.
/// </summary>
/// <param name="Message">단일 사용자 메시지(Conversation 히스토리는 SessionId 로 자동 복원).</param>
/// <param name="SessionId">기존 세션 식별자(없으면 Nexus 가 신규 발급).</param>
/// <param name="Model">"primary"(기본) | "auxiliary".</param>
/// <param name="TenantId">테넌트 식별자(없으면 X-Tenant-ID 헤더 또는 기본값 사용).</param>
public sealed record NexusChatRequest(
    string Message,
    string? SessionId = null,
    string Model = "primary",
    string? TenantId = null);

/// <summary>
/// Nexus 비스트리밍 응답. ChatResponse 와 1:1 매핑.
/// </summary>
public sealed record NexusChatResponse(
    string SessionId,
    string Response,
    object? ToolCalls,
    NexusUsage? Usage);

/// <summary>토큰 사용량(Nexus 가 4-Tier 마지막에 집계).</summary>
public sealed record NexusUsage(int PromptTokens, int CompletionTokens, int TotalTokens);

/// <summary>
/// Nexus 스트리밍 이벤트(SSE 프레임 1개에 대응).
/// Type 값:
///   - "chunk": Text 에 부분 응답 누적
///   - "usage": Usage 에 최종 토큰 카운트
///   - "error": ErrorCode + ErrorMessage
///   - "done": 스트림 종료 신호(Enumerable 도 함께 종료)
/// </summary>
public sealed record NexusStreamEvent(
    string Type,
    string SessionId,
    string? Text,
    NexusUsage? Usage,
    string? ErrorCode,
    string? ErrorMessage);
