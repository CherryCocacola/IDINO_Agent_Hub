using System.ComponentModel.DataAnnotations;

namespace AIAgentManagement.DTOs;

public class ImageGenerationRequestDto
{
    [Required]
    [MaxLength(4000, ErrorMessage = "프롬프트는 최대 4000자까지 입력 가능합니다.")]
    public string Prompt { get; set; } = string.Empty;

    public string? Model { get; set; }

    public string Size { get; set; } = "1024x1024"; // 1024x1024, 512x512, 256x256 등

    public string Quality { get; set; } = "standard"; // standard, hd 등

    public string? Style { get; set; } // 서비스별 스타일 옵션

    [Range(1, 4, ErrorMessage = "이미지 수는 1~4 사이여야 합니다.")]
    public int NumberOfImages { get; set; } = 1;

    public int? UserId { get; set; } // 할당량 관리용

    public int ServiceId { get; set; } // 이미지 생성 서비스 ID

    public int? ConversationId { get; set; } // 기존 대화에 추가할 경우

    public int? AgentId { get; set; } // Agent 기반 대화인 경우

    public List<ChatMessageDto>? Messages { get; set; } // 대화 히스토리 (Gemini Image 등 채팅 API 사용 모델용)

    public List<ImageAttachmentDto>? ImageAttachments { get; set; } // 첨부 이미지 (Gemini Image 등 멀티모달 지원 모델용)

    public bool EnableWebSearch { get; set; } = false; // 웹 검색 활성화 여부
}

public class ImageAttachmentDto
{
    public string MimeType { get; set; } = "image/jpeg"; // image/jpeg, image/png 등
    public string Data { get; set; } = string.Empty; // Base64 인코딩된 이미지 데이터
}
