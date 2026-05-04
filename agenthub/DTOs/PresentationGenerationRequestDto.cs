using System.ComponentModel.DataAnnotations;

namespace AIAgentManagement.DTOs;

/// <summary>생성 방식: topic=주제로 생성, paste=텍스트 붙여넣기, import=URL/파일 가져오기</summary>
public class PresentationGenerationRequestDto
{
    /// <summary>주제 (topic 모드에서 필수)</summary>
    public string Prompt { get; set; } = string.Empty;

    /// <summary>붙여넣은 텍스트 (paste 모드에서 필수)</summary>
    public string? PasteContent { get; set; }

    /// <summary>가져올 URL (import 모드에서 필수)</summary>
    public string? ImportUrl { get; set; }

    /// <summary>생성 방식: topic | paste | import (기본 topic)</summary>
    public string SourceType { get; set; } = "topic";

    public int SlideCount { get; set; } = 5;

    public int? TemplateId { get; set; }

    [Required]
    public int ServiceId { get; set; }

    public string? Model { get; set; }

    public string Style { get; set; } = "business"; // business, education, marketing, creative

    /// <summary>슬라이드 비율: 4:3, 16:9, 16:10 (기본 16:9)</summary>
    public string SlideSize { get; set; } = "16:9";

    /// <summary>테마 ID (Phase 2). 미지정 시 기본 테마</summary>
    public string? ThemeId { get; set; }

    /// <summary>제목 글꼴 (선택). 맑은 고딕, Noto Sans KR, Pretendard 등</summary>
    public string? FontHeading { get; set; }

    /// <summary>본문 글꼴 (선택)</summary>
    public string? FontBody { get; set; }

    /// <summary>AI 이미지 자동 삽입 여부 (Phase 3)</summary>
    public bool IncludeAiImages { get; set; }

    /// <summary>이미지 생성용 서비스 ID (IncludeAiImages일 때 사용)</summary>
    public int? ImageServiceId { get; set; }

    /// <summary>이미지 생성 모델 (예: dall-e-3)</summary>
    public string? ImageModel { get; set; }

    public int? UserId { get; set; }
}
