namespace AIAgentManagement.DTOs;

/// <summary>
/// 외부 LLM 키 유효성 검증 결과 — 트랙 #91.
/// 운영자가 콘솔에서 "테스트" 버튼을 눌러 키 유효성을 확인할 때 반환한다.
/// </summary>
/// <param name="Success">외부 LLM 응답 2xx 여부. 401/403/429 등 4xx 5xx 는 모두 false.</param>
/// <param name="Message">사용자(운영자)에게 표시할 한국어 메시지 (예: "검증 PASS · OpenAI 응답 200").</param>
/// <param name="Provider">정규화된 제공사 코드 (openai/claude/gemini/...). 응답 본문이 비어 있을 때도 비어있지 않도록 보장.</param>
/// <param name="LatencyMs">외부 LLM 호출 ping 라운드 트립 시간(밀리초). 운영자가 응답 속도를 가늠하기 위함.</param>
public sealed record TestApiKeyResponseDto(
    bool Success,
    string Message,
    string? Provider,
    long LatencyMs);
