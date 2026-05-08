namespace AIAgentManagement.DTOs;

public class CreateConversationRequestDto
{
    public int? AgentId { get; set; }

    // AgentId 가 제공되면 Agent.ServiceId 를 자동 사용하므로 nullable.
    // 둘 다 null 이면 서비스 레이어에서 ArgumentException → ChatController 400 으로 매핑.
    // ([Required] int 패턴은 0 을 허용하여 FK 위반을 일으키므로 의도적으로 제거)
    public int? ServiceId { get; set; }

    public string? Title { get; set; }
    public string? Model { get; set; }
    public decimal? Temperature { get; set; }
    public int? MaxTokens { get; set; }
    public string? SystemPrompt { get; set; }
    public string? Language { get; set; } // 'ko', 'en', 'auto'
}
