using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace AIAgentManagement.DTOs;

public class DirectSendMessageRequestDto
{
    [JsonPropertyName("serviceId")]
    public int? ServiceId { get; set; }
    
    [JsonPropertyName("agentId")]
    public int? AgentId { get; set; }
    
    [JsonPropertyName("conversationId")]
    public int? ConversationId { get; set; } // 기존 대화 ID (있으면 해당 세션에 메시지 추가)
    
    [JsonPropertyName("model")]
    public string? Model { get; set; }
    
    [JsonPropertyName("temperature")]
    public decimal? Temperature { get; set; }
    
    [JsonPropertyName("maxTokens")]
    public int? MaxTokens { get; set; }
    
    [Required]
    [JsonPropertyName("messages")]
    public List<ChatMessageItemDto> Messages { get; set; } = new();
    
    [JsonPropertyName("stream")]
    public bool? Stream { get; set; }
    
    [JsonPropertyName("enableWebSearch")]
    public bool? EnableWebSearch { get; set; }
    
    [JsonPropertyName("enableRag")]
    public bool? EnableRag { get; set; }
    
    [JsonPropertyName("ragTopK")]
    public int? RagTopK { get; set; }
    
    [JsonPropertyName("documentIds")]
    public List<int>? DocumentIds { get; set; } // RAG 검색 시 사용할 문서 ID 목록
    
    [JsonPropertyName("language")]
    public string? Language { get; set; } // 'ko', 'en', 'auto'
    
    [JsonPropertyName("enableDeepResearch")]
    public bool? EnableDeepResearch { get; set; } // 심층 리서치: 다중 웹 검색 + RAG 통합 분석
    
    [JsonPropertyName("enableDeepThinking")]
    public bool? EnableDeepThinking { get; set; } // 더 오래 생각하기: Chain-of-Thought 프롬프팅
    
    [JsonPropertyName("thinkingMode")]
    public string? ThinkingMode { get; set; } // 'chain-of-thought', 'step-by-step' 등

    /// <summary>
    /// Primary 모델 실패(429·500·503) 시 자동 전환할 Fallback 모델 ID.
    /// null이면 기본 Fallback 매핑을 사용합니다.
    /// 예: "gpt-4o-mini", "claude-haiku-4-5-20251001"
    /// </summary>
    [JsonPropertyName("fallbackModel")]
    public string? FallbackModel { get; set; }

    /// <summary>
    /// 호출자가 보낸 system 메시지를 보존할지 여부(트랙 #102 — DocUtil RAG 컨텍스트 누락 fix).
    /// <para>
    /// 기본 false: AgentHub UI 등 일반 채팅 흐름은 Agent.SystemPrompt 로 system 메시지를 덮어쓴다.
    /// true: OpenAI 호환 `/v1/chat/completions` 같이 호출자가 직접 system prompt(RAG context 등)를
    /// 구성한 경우, 그 system 메시지를 그대로 유지하고 Agent.SystemPrompt 자동 inject 를 스킵한다.
    /// </para>
    /// </summary>
    [JsonPropertyName("preserveSystemMessage")]
    public bool PreserveSystemMessage { get; set; } = false;
}

public class ChatMessageItemDto
{
    [Required]
    [JsonPropertyName("role")]
    public string Role { get; set; } = string.Empty; // user, assistant, system
    
    [JsonPropertyName("content")]
    public string? Content { get; set; }
    
    [JsonPropertyName("contents")]
    public List<MessageContentDto>? Contents { get; set; } // 멀티모달 콘텐츠
    
    // Content와 Contents 중 하나는 반드시 있어야 함
    public bool IsValid()
    {
        return !string.IsNullOrEmpty(Content) || (Contents != null && Contents.Count > 0);
    }
}

public class MessageContentDto
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty; // "text", "image_url", "audio_url", "file"
    
    [JsonPropertyName("text")]
    public string? Text { get; set; }
    
    [JsonPropertyName("imageUrl")]
    public string? ImageUrl { get; set; }
    
    [JsonPropertyName("audioUrl")]
    public string? AudioUrl { get; set; }
    
    [JsonPropertyName("fileUrl")]
    public string? FileUrl { get; set; }
    
    [JsonPropertyName("fileName")]
    public string? FileName { get; set; }
}

public class DirectSendMessageResponseDto
{
    public int MessageId { get; set; }
    public int? ConversationId { get; set; }
    public string Content { get; set; } = string.Empty;
    public string Model { get; set; } = string.Empty;
    public int? TokensUsed { get; set; }
    public decimal? Cost { get; set; }
    public int ResponseTime { get; set; } // milliseconds
    public List<string>? Citations { get; set; } // Perplexity AI citations
}
