using System.Text.Json.Serialization;

namespace AIAgentManagement.DTOs;

// ══════════════════════════════════════════════════════════════════════════════
// POST /v1/chat/completions — 요청
// ══════════════════════════════════════════════════════════════════════════════

public class OpenAIChatCompletionRequest
{
    /// <summary>
    /// Agent Hub에서 agentCode에 해당합니다.
    /// 예: "abc123ef"
    /// </summary>
    [JsonPropertyName("model")]
    public string Model { get; set; } = string.Empty;

    [JsonPropertyName("messages")]
    public List<OpenAIChatMessage> Messages { get; set; } = new();

    [JsonPropertyName("temperature")]
    public decimal? Temperature { get; set; }

    [JsonPropertyName("max_tokens")]
    public int? MaxTokens { get; set; }

    /// <summary>
    /// true이면 text/event-stream (SSE) 스트리밍으로 응답합니다.
    /// </summary>
    [JsonPropertyName("stream")]
    public bool Stream { get; set; } = false;

    // 하위 호환성을 위해 선언하되 실제 처리는 생략합니다.
    [JsonPropertyName("top_p")]
    public decimal? TopP { get; set; }

    [JsonPropertyName("n")]
    public int? N { get; set; }

    [JsonPropertyName("stop")]
    public object? Stop { get; set; }

    [JsonPropertyName("presence_penalty")]
    public decimal? PresencePenalty { get; set; }

    [JsonPropertyName("frequency_penalty")]
    public decimal? FrequencyPenalty { get; set; }

    [JsonPropertyName("user")]
    public string? User { get; set; }
}

public class OpenAIChatMessage
{
    /// <summary>system | user | assistant</summary>
    [JsonPropertyName("role")]
    public string Role { get; set; } = string.Empty;

    [JsonPropertyName("content")]
    public string? Content { get; set; }

    [JsonPropertyName("name")]
    public string? Name { get; set; }
}

// ══════════════════════════════════════════════════════════════════════════════
// POST /v1/chat/completions — 비스트리밍 응답
// ══════════════════════════════════════════════════════════════════════════════

public class OpenAIChatCompletionResponse
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("object")]
    public string Object { get; set; } = "chat.completion";

    [JsonPropertyName("created")]
    public long Created { get; set; }

    [JsonPropertyName("model")]
    public string Model { get; set; } = string.Empty;

    [JsonPropertyName("choices")]
    public List<OpenAIChoice> Choices { get; set; } = new();

    [JsonPropertyName("usage")]
    public OpenAIUsage? Usage { get; set; }
}

public class OpenAIChoice
{
    [JsonPropertyName("index")]
    public int Index { get; set; }

    [JsonPropertyName("message")]
    public OpenAIChatMessage? Message { get; set; }

    [JsonPropertyName("finish_reason")]
    public string FinishReason { get; set; } = "stop";
}

public class OpenAIUsage
{
    [JsonPropertyName("prompt_tokens")]
    public int PromptTokens { get; set; }

    [JsonPropertyName("completion_tokens")]
    public int CompletionTokens { get; set; }

    [JsonPropertyName("total_tokens")]
    public int TotalTokens { get; set; }
}

// ══════════════════════════════════════════════════════════════════════════════
// POST /v1/chat/completions — 스트리밍 청크 (SSE)
// ══════════════════════════════════════════════════════════════════════════════

public class OpenAIChatCompletionChunk
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("object")]
    public string Object { get; set; } = "chat.completion.chunk";

    [JsonPropertyName("created")]
    public long Created { get; set; }

    [JsonPropertyName("model")]
    public string Model { get; set; } = string.Empty;

    [JsonPropertyName("choices")]
    public List<OpenAIChunkChoice> Choices { get; set; } = new();
}

public class OpenAIChunkChoice
{
    [JsonPropertyName("index")]
    public int Index { get; set; }

    [JsonPropertyName("delta")]
    public OpenAIChunkDelta Delta { get; set; } = new();

    [JsonPropertyName("finish_reason")]
    public string? FinishReason { get; set; }
}

public class OpenAIChunkDelta
{
    [JsonPropertyName("role")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Role { get; set; }

    [JsonPropertyName("content")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Content { get; set; }
}

// ══════════════════════════════════════════════════════════════════════════════
// GET /v1/models
// ══════════════════════════════════════════════════════════════════════════════

public class OpenAIModelListResponse
{
    [JsonPropertyName("object")]
    public string Object { get; set; } = "list";

    [JsonPropertyName("data")]
    public List<OpenAIModelDto> Data { get; set; } = new();
}

public class OpenAIModelDto
{
    /// <summary>agentCode가 모델 ID로 사용됩니다.</summary>
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("object")]
    public string Object { get; set; } = "model";

    [JsonPropertyName("created")]
    public long Created { get; set; }

    [JsonPropertyName("owned_by")]
    public string OwnedBy { get; set; } = "agent-hub";

    [JsonPropertyName("description")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Description { get; set; }
}

// ══════════════════════════════════════════════════════════════════════════════
// POST /v1/embeddings — 요청 (Phase 7.5)
// ══════════════════════════════════════════════════════════════════════════════

/// <summary>
/// OpenAI 호환 Embeddings 요청. DocUtil/career 의 임베딩 위임 진입점.
///
/// model 필드는 다음 중 하나로 지정한다 (R2 단일 진입점):
///  1) AgentCode (예: "embedding-default") — Agents 테이블 룩업 후 ApiService 매핑.
///  2) OpenAI 모델명 (예: "text-embedding-3-small") — embedding-default Agent 로 자동 폴백.
///
/// input 필드는 OpenAI 명세상 string 또는 string[] 두 형태를 모두 허용한다.
/// 외부 SDK(LangChain/openai-python 등)가 단건/배치를 자유롭게 호출할 수 있도록 object 로 받는다.
/// </summary>
public class EmbeddingsRequestDto
{
    [JsonPropertyName("model")]
    public string Model { get; set; } = string.Empty;

    /// <summary>string 또는 string[] 둘 다 허용 (OpenAI 호환).</summary>
    [JsonPropertyName("input")]
    public object Input { get; set; } = string.Empty;

    /// <summary>"float" 만 지원 (Phase 7.5). "base64" 는 미지원.</summary>
    [JsonPropertyName("encoding_format")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? EncodingFormat { get; set; }

    /// <summary>호환용 — AgentHub 는 user 필드를 무시.</summary>
    [JsonPropertyName("user")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? User { get; set; }
}

// ══════════════════════════════════════════════════════════════════════════════
// POST /v1/embeddings — 응답 (Phase 7.5)
// ══════════════════════════════════════════════════════════════════════════════

/// <summary>OpenAI Embeddings API 와 100% 호환되는 응답 형식.</summary>
public class EmbeddingsResponseDto
{
    [JsonPropertyName("object")]
    public string Object { get; set; } = "list";

    [JsonPropertyName("data")]
    public List<EmbeddingItemDto> Data { get; set; } = new();

    [JsonPropertyName("model")]
    public string Model { get; set; } = string.Empty;

    [JsonPropertyName("usage")]
    public EmbeddingUsageDto Usage { get; set; } = new();
}

public class EmbeddingItemDto
{
    [JsonPropertyName("object")]
    public string Object { get; set; } = "embedding";

    [JsonPropertyName("index")]
    public int Index { get; set; }

    [JsonPropertyName("embedding")]
    public float[] Embedding { get; set; } = Array.Empty<float>();
}

public class EmbeddingUsageDto
{
    [JsonPropertyName("prompt_tokens")]
    public int PromptTokens { get; set; }

    [JsonPropertyName("total_tokens")]
    public int TotalTokens { get; set; }
}

// ══════════════════════════════════════════════════════════════════════════════
// POST /v1/images/generations — 요청 (Phase 7 — DU-14 R2 강제)
// ══════════════════════════════════════════════════════════════════════════════

/// <summary>
/// OpenAI Images API 와 100% 호환되는 이미지 생성 요청.
///
/// model 필드는 다음 중 하나로 지정한다 (R2 단일 진입점):
///  1) AgentCode (예: "docutil-image-generator") — Agents 테이블 룩업 후 ApiService 매핑
///  2) OpenAI 이미지 모델명 (예: "dall-e-3", "dall-e-2") — 자동 폴백 시 DefaultModel 로 사용
///
/// 본 DTO 는 OpenAI 호환 표면만 정의한다 — 내부적으로 ImageGenerationRequestDto 로 변환되어
/// 기존 IAiProxyService.SendImageGenerationAsync 분기를 그대로 재활용한다 (코드 중복 0).
/// </summary>
public class OpenAIImagesRequestDto
{
    /// <summary>AgentCode 또는 모델명. 빈 문자열 시 400.</summary>
    [JsonPropertyName("model")]
    public string Model { get; set; } = string.Empty;

    /// <summary>이미지 생성 프롬프트. 최대 4000자.</summary>
    [JsonPropertyName("prompt")]
    public string Prompt { get; set; } = string.Empty;

    /// <summary>생성할 이미지 수. OpenAI 명세: dall-e-3 은 n=1 강제, dall-e-2 는 1~10. 미지정 시 1.</summary>
    [JsonPropertyName("n")]
    public int? N { get; set; }

    /// <summary>이미지 크기. 기본 1024x1024.</summary>
    [JsonPropertyName("size")]
    public string? Size { get; set; }

    /// <summary>품질. "standard" | "hd". 미지정 시 standard.</summary>
    [JsonPropertyName("quality")]
    public string? Quality { get; set; }

    /// <summary>스타일. "natural" | "vivid". DALL-E 3 전용.</summary>
    [JsonPropertyName("style")]
    public string? Style { get; set; }

    /// <summary>
    /// 응답 형식. "url" (기본) 또는 "b64_json".
    /// "b64_json" 은 AgentHub 가 URL 응답을 GET 으로 다운로드 후 base64 인코딩하여 반환.
    /// 외부 LLM 의 응답이 b64 인 경우 (OpenAI) 그대로 통과.
    /// </summary>
    [JsonPropertyName("response_format")]
    public string? ResponseFormat { get; set; }

    /// <summary>호환용 — AgentHub 는 user 필드를 무시.</summary>
    [JsonPropertyName("user")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? User { get; set; }
}

// ══════════════════════════════════════════════════════════════════════════════
// POST /v1/images/generations — 응답 (Phase 7)
// ══════════════════════════════════════════════════════════════════════════════

/// <summary>OpenAI Images API 와 100% 호환되는 응답.</summary>
public class OpenAIImagesResponseDto
{
    /// <summary>OpenAI 표준: 생성 시각의 Unix epoch (초).</summary>
    [JsonPropertyName("created")]
    public long Created { get; set; }

    [JsonPropertyName("data")]
    public List<OpenAIImageItemDto> Data { get; set; } = new();
}

public class OpenAIImageItemDto
{
    /// <summary>response_format=url 인 경우 외부 LLM (예: OpenAI) 의 URL.</summary>
    [JsonPropertyName("url")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Url { get; set; }

    /// <summary>response_format=b64_json 인 경우 base64 인코딩된 PNG/JPEG 바이트.</summary>
    [JsonPropertyName("b64_json")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? B64Json { get; set; }

    /// <summary>OpenAI 가 revised_prompt 를 채워 보내는 경우 그대로 전달.</summary>
    [JsonPropertyName("revised_prompt")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? RevisedPrompt { get; set; }
}

// ══════════════════════════════════════════════════════════════════════════════
// 오류 응답
// ══════════════════════════════════════════════════════════════════════════════

public class OpenAIErrorResponse
{
    [JsonPropertyName("error")]
    public OpenAIErrorDetail Error { get; set; } = new();
}

public class OpenAIErrorDetail
{
    [JsonPropertyName("message")]
    public string Message { get; set; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; set; } = "invalid_request_error";

    [JsonPropertyName("code")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Code { get; set; }
}
