namespace AIAgentManagement.Services;

/// <summary>
/// 동일 AI 제공사에 여러 API 키를 등록하고 라운드로빈으로 순환하는 서비스.
///
/// appsettings.json 설정 예시 (다중 키):
/// "AiApiSettings": {
///   "OpenAI": {
///     "ApiKeys": ["sk-key1", "sk-key2", "sk-key3"]
///   }
/// }
///
/// 단일 키 설정은 기존 방식과 동일하게 동작합니다:
/// "AiApiSettings": {
///   "OpenAI": { "ApiKey": "sk-key1" }
/// }
/// </summary>
public interface IApiKeyPoolService
{
    /// <summary>
    /// 제공사 코드로 다음 API 키를 가져옵니다 (라운드로빈).
    /// 냉각 중인 키는 자동으로 건너뜁니다.
    /// </summary>
    /// <param name="provider">제공사 코드 (openai / claude / gemini / mistral / perplexity / azureopenai / copilot)</param>
    /// <returns>API 키 문자열. 등록된 키가 없으면 null.</returns>
    string? GetNextKey(string provider);

    /// <summary>
    /// 특정 키를 일정 시간 동안 냉각(사용 제외) 상태로 설정합니다.
    /// 429 Too Many Requests 응답을 받았을 때 호출합니다.
    /// </summary>
    /// <param name="provider">제공사 코드</param>
    /// <param name="apiKey">냉각할 API 키</param>
    /// <param name="cooldownSeconds">냉각 시간(초). 기본값 60초.</param>
    void MarkAsCoolingDown(string provider, string apiKey, int cooldownSeconds = 60);

    /// <summary>
    /// 제공사별 등록된 키 개수를 반환합니다 (모니터링용).
    /// </summary>
    IReadOnlyDictionary<string, int> GetPoolStats();
}
