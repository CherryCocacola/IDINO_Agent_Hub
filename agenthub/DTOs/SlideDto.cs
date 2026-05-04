namespace AIAgentManagement.DTOs;

public class SlideDto
{
    public string SlideId { get; set; } = Guid.NewGuid().ToString();
    public int SlideNumber { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    /// <summary>title-content, title-only, two-column, image-title, section-header, pyramid, funnel, comparison, quote, thank-you</summary>
    public string Layout { get; set; } = "title-content";
    public List<string> Images { get; set; } = new();
    public List<ChartDto> Charts { get; set; } = new();
    public List<TableDto> Tables { get; set; } = new();
    public string? ImageDescription { get; set; }
    /// <summary>AI 생성 이미지 URL (Phase 3)</summary>
    public string? ImageUrl { get; set; }
    /// <summary>이미지 생성에 사용한 프롬프트</summary>
    public string? ImagePrompt { get; set; }
}

public class ChartDto
{
    public string ChartId { get; set; } = Guid.NewGuid().ToString();
    public string ChartType { get; set; } = "bar"; // bar, line, pie
    public string Title { get; set; } = string.Empty;
    public Dictionary<string, object> Data { get; set; } = new();
}

/// <summary>슬라이드 표(Table) DTO. Phase 2.</summary>
public class TableDto
{
    public bool HeaderRow { get; set; } = true;
    public List<List<string>> Rows { get; set; } = new();
}
