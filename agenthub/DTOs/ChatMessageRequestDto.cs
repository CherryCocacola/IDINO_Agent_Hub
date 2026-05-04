namespace AIAgentManagement.DTOs;

public class ChatMessageRequestDto
{
    public List<ChatMessageDto> Messages { get; set; } = new();
    public decimal? Temperature { get; set; } = 0.7m;
    public int? MaxTokens { get; set; } = 4096;
    public bool Stream { get; set; } = false;
    public bool EnableWebSearch { get; set; } = false;
    public bool EnableRag { get; set; } = false;
    public int? RagTopK { get; set; } = 3;
    public string? Language { get; set; } // 'ko', 'en', 'auto'
    public int? UserId { get; set; } // RAG 검색 시 사용자별 문서 필터링용
    public int? AgentId { get; set; } // RAG 검색 시 Agent에 연결된 문서 사용
    public List<int>? DocumentIds { get; set; } // RAG 검색 시 사용할 문서 ID 목록
    public bool EnableDeepResearch { get; set; } = false; // 심층 리서치: 다중 웹 검색 + RAG 통합 분석
    public bool EnableDeepThinking { get; set; } = false; // 더 오래 생각하기: Chain-of-Thought 프롬프팅
    public string? ThinkingMode { get; set; } // 'chain-of-thought', 'step-by-step' 등
}

public class ChatMessageDto
{
    public int MessageId { get; set; }
    public int ConversationId { get; set; }
    public string Role { get; set; } = string.Empty; // user, assistant, system
    public string? Content { get; set; }
    public List<MessageContentDto>? Contents { get; set; } // 멀티모달 콘텐츠
    public string? Attachments { get; set; } // JSON 문자열 (이미지 URL 목록 등)
    public int? TokensUsed { get; set; }
    public string? Model { get; set; }
    public string? FinishReason { get; set; }
    public DateTime CreatedAt { get; set; }
}
