using System.ComponentModel.DataAnnotations;

namespace AIAgentManagement.DTOs;

/// <summary>
/// 외부 LLM 풀 키(`KeyType="Provider"`) 등록 요청 DTO — 트랙 #91 (ApiKeyPoolService DB 통합).
///
/// 운영자가 콘솔에서 OpenAI/Claude/Gemini 등 외부 LLM 호출용 평문 키를 등록할 때 사용한다.
/// 일반적인 외부 노출 키(`CreateApiKeyRequestDto`, `KeyType="External"`)와 등록 경로가 분리되어 있다.
///
/// 등록 흐름:
/// 1. 컨트롤러가 본 DTO 로 요청 수신 → `ApiKeyService.CreateProviderApiKeyAsync` 호출
/// 2. ServiceCode 화이트리스트 검증(openai/chatgpt/claude/gemini/...)
/// 3. AES-GCM 암호화 + SHA-256 KeyHash 산출 + DB INSERT (`KeyType="Provider"` 강제)
/// 4. <c>ValidateOnCreate=true</c> 시 등록 직후 `TestApiKeyAsync` 자동 호출하여 외부 LLM 호출 검증
/// 5. `IApiKeyPoolService.RefreshAsync()` 즉시 트리거 → 다음 LLM 호출부터 신규 키 사용 가능
/// </summary>
public class CreateProviderApiKeyRequestDto
{
    /// <summary>키 식별용 표시 이름 (예: "Gemini Prod #1"). 운영자 콘솔 UI 에만 노출.</summary>
    [Required(ErrorMessage = "키 이름은 필수 입력 항목입니다.")]
    [MaxLength(100, ErrorMessage = "키 이름은 100자를 초과할 수 없습니다.")]
    public string KeyName { get; set; } = string.Empty;

    /// <summary>
    /// 외부 LLM 제공사 코드 (소문자). 지원: openai / chatgpt / claude / gemini / gemini-image / imagen4 /
    /// perplexity / mistral / azureopenai / copilot.
    /// 서비스 단에서 화이트리스트 검증 후 풀 슬롯에 매핑 (chatgpt→openai, gemini-image/imagen4→gemini 등).
    /// </summary>
    [Required(ErrorMessage = "ServiceCode 는 필수 입력 항목입니다.")]
    [MaxLength(50, ErrorMessage = "ServiceCode 는 50자를 초과할 수 없습니다.")]
    public string ServiceCode { get; set; } = string.Empty;

    /// <summary>외부 LLM 제공사에서 발급받은 평문 API 키. 길이 ≥ 10. DB 에는 AES-GCM 으로 암호화 저장.</summary>
    [Required(ErrorMessage = "ApiKey 는 필수 입력 항목입니다.")]
    [MinLength(10, ErrorMessage = "ApiKey 는 10자 이상이어야 합니다.")]
    [MaxLength(500, ErrorMessage = "ApiKey 는 500자를 초과할 수 없습니다.")]
    public string ApiKey { get; set; } = string.Empty;

    /// <summary>(옵셔널) 운영자 메모 — 키 발급 출처, 회전 예정일 등.</summary>
    [MaxLength(500, ErrorMessage = "Description 은 500자를 초과할 수 없습니다.")]
    public string? Description { get; set; }

    /// <summary>(옵셔널) 만료 일시 (UTC). 만료된 키는 다음 `RefreshAsync` 에서 풀에서 자동 제외.</summary>
    public DateTime? ExpiresAt { get; set; }

    /// <summary>
    /// 등록 직후 외부 LLM 호출로 키 유효성 자동 검증 여부. 기본 <c>true</c>.
    /// 일부 제공사(azureopenai/copilot)는 본 트랙에서 테스트 미지원이므로 자동 검증이 skip 될 수 있다.
    /// </summary>
    public bool ValidateOnCreate { get; set; } = true;
}
