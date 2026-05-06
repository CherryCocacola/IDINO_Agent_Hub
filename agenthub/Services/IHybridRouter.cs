using AIAgentManagement.DTOs;
using AIAgentManagement.Models;

namespace AIAgentManagement.Services;

// ════════════════════════════════════════════════════════════════════════════
// HybridRouter — Agent.LlmRouting="Hybrid" 일 때만 호출되는 결정 엔진 (Phase 5.2)
//
// 책임 범위:
//   - Agent.RoutingPolicyJson 을 평가하여 "external" 또는 "internal" 결정
//   - PII / 데이터 라벨 / 모델 capability / 비용 임계치 / default 5단계 판정
//   - 결정 결과의 사유(Reason) 를 호출자(ChatService.ResolveServiceCodeAsync)에 반환하여
//     로그/감사 추적이 가능하도록 한다
//
// 책임 범위 밖:
//   - 실제 라우팅 분기(ChatService 가 결정에 따라 ApiService 룩업 후 AiProxyService 호출)
//   - PII 감지 자체(IPiiDetectionService 위임)
//   - External/Internal 모드의 즉시 폴백(ChatService 가 LlmRouting 값으로 사전 분기)
//
// 결정 우선순위(첫 매치가 최종 판정):
//   1. PII 감지   → piiAction (기본 "internal")
//   2. 데이터 라벨 → dataLabels[label] 매핑
//   3. 모델 capability(vision/longContext) → "external" 강제
//   4. 비용 임계치 초과 → exceedAction (기본 "internal")
//   5. default → "external"
//
// 본 인터페이스는 .claude/rules/domain-model.md 의 RoutingPolicyJson 스키마와
// TECHSPEC §10.3 / §15.4 의 결정 단계를 따른다.
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// LlmRouting="Hybrid" Agent 의 라우팅 결정 엔진.
/// AgentHub 의 단일 라우팅 진입점은 ChatService 이며, HybridRouter 는 합성 컴포넌트로만 사용된다.
/// </summary>
public interface IHybridRouter
{
    /// <summary>
    /// Agent + 요청 컨텍스트를 평가하여 외부/내부 라우팅 결정을 반환한다.
    /// LlmRouting 이 External/Internal 인 Agent 는 호출하지 않는다(상위 ChatService 가 사전 분기).
    /// </summary>
    /// <param name="agent">대상 Agent (LlmRouting="Hybrid" 가정).</param>
    /// <param name="request">전달된 ChatMessageRequestDto — 메시지/언어/멀티모달/MaxTokens 평가에 사용.</param>
    /// <param name="cancellationToken">취소 토큰.</param>
    /// <returns>결정값(external/internal) + 사유 + 디테일.</returns>
    Task<HybridRoutingDecision> DecideAsync(
        Agent agent,
        ChatMessageRequestDto request,
        CancellationToken cancellationToken);
}

/// <summary>
/// HybridRouter 의 결정 결과. Decision 은 항상 소문자("external" 또는 "internal").
/// Reason 은 호출자가 로그/감사 추적에 사용할 수 있도록 표준 enum-like 문자열을 반환한다:
/// <list type="bullet">
///   <item><description>"pii_detected" — PII 검출로 internal 강제</description></item>
///   <item><description>"data_label" — 데이터 라벨 매핑 적용</description></item>
///   <item><description>"capability_required" — vision/longContext 등 외부 모델 필요</description></item>
///   <item><description>"cost_exceeded" — 비용 임계치 초과</description></item>
///   <item><description>"default" — 어떤 규칙도 매치되지 않아 default 적용</description></item>
///   <item><description>"invalid_policy" — RoutingPolicyJson 파싱 실패 → external 폴백</description></item>
///   <item><description>"empty_policy" — RoutingPolicyJson NULL/빈 문자열 → external 폴백</description></item>
/// </list>
/// </summary>
/// <param name="Decision">"external" 또는 "internal" (소문자 강제).</param>
/// <param name="Reason">결정 사유(enum-like 문자열).</param>
/// <param name="Detail">선택적 디테일(예: 매치된 dataLabel 값, 추정 토큰 수).</param>
public sealed record HybridRoutingDecision(
    string Decision,
    string Reason,
    string? Detail = null);
