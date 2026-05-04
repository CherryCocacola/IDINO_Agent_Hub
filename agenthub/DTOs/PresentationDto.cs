namespace AIAgentManagement.DTOs;

public class PresentationDto
{
    public int PresentationId { get; set; }
    public int UserId { get; set; }
    public string Title { get; set; } = string.Empty;
    public List<SlideDto> Slides { get; set; } = new();
    /// <summary>목록 조회 시 슬라이드 개수 (전체 Slides 로드 없이 표시용).</summary>
    [System.Text.Json.Serialization.JsonIgnore(Condition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingDefault)]
    public int? SlideCount { get; set; }
    /// <summary>적용된 테마 ID (Phase 2). 클라이언트 camelCase themeId와 매핑.</summary>
    [System.Text.Json.Serialization.JsonPropertyName("themeId")]
    public string? ThemeId { get; set; }
    /// <summary>슬라이드 비율: 4:3, 16:9, 16:10</summary>
    [System.Text.Json.Serialization.JsonPropertyName("slideSize")]
    public string? SlideSize { get; set; }
    /// <summary>제목 글꼴 (Phase 4)</summary>
    [System.Text.Json.Serialization.JsonPropertyName("fontHeading")]
    public string? FontHeading { get; set; }
    /// <summary>본문 글꼴 (Phase 4)</summary>
    [System.Text.Json.Serialization.JsonPropertyName("fontBody")]
    public string? FontBody { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}
