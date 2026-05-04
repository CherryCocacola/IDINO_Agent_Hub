using System.ComponentModel.DataAnnotations;

namespace AIAgentManagement.DTOs;

public class PresentationTemplateDto
{
    public int TemplateId { get; set; }
    public string TemplateName { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string TemplateFilePath { get; set; } = string.Empty;
    public TemplateStructureDto? TemplateStructure { get; set; }
    public string Category { get; set; } = "business";
    public bool IsPublic { get; set; }
    public int? CreatedBy { get; set; }
    public string? CreatedByName { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}

public class TemplateStructureDto
{
    public int SlideCount { get; set; }
    public List<TemplateSlideInfoDto> Slides { get; set; } = new();
    public string? ColorScheme { get; set; }
    public string? FontScheme { get; set; }
}

public class TemplateSlideInfoDto
{
    public int SlideNumber { get; set; }
    public string LayoutType { get; set; } = "title-content";
    public List<TemplatePlaceholderDto> Placeholders { get; set; } = new();
}

public class TemplatePlaceholderDto
{
    public string Type { get; set; } = string.Empty; // title, body, image
    public int Index { get; set; }
    public string? DefaultText { get; set; }
}

public class TemplateUploadRequestDto
{
    [Required(ErrorMessage = "템플릿 이름은 필수입니다.")]
    public string TemplateName { get; set; } = string.Empty;

    public string? Description { get; set; }

    public string Category { get; set; } = "business";

    public bool IsPublic { get; set; } = false;
}
