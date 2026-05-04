namespace AIAgentManagement.DTOs;

/// <summary>PRESENTATIONS 테이블 기반 목록 조회용 DTO. 슬라이드 본문은 로드하지 않음.</summary>
public class PresentationListItemDto
{
    public int PresentationId { get; set; }
    public int UserId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? ThemeId { get; set; }
    public int SlideCount { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}
