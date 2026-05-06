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
