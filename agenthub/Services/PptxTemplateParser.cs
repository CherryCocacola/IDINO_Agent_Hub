using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Presentation;
using A = DocumentFormat.OpenXml.Drawing;
using P = DocumentFormat.OpenXml.Presentation;
using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public class PptxTemplateParser : IPptxTemplateParser
{
    private readonly ILogger<PptxTemplateParser> _logger;

    public PptxTemplateParser(ILogger<PptxTemplateParser> logger)
    {
        _logger = logger;
    }

    public async Task<TemplateStructureDto> ParseTemplateAsync(Stream pptxStream, CancellationToken cancellationToken = default)
    {
        var structure = new TemplateStructureDto();
        var slides = new List<TemplateSlideInfoDto>();

        try
        {
            // 스트림 위치 확인
            if (pptxStream.CanSeek && pptxStream.Position > 0)
            {
                pptxStream.Position = 0;
            }

            using (var presentationDocument = PresentationDocument.Open(pptxStream, false))
            {
                var presentationPart = presentationDocument.PresentationPart;
                if (presentationPart?.Presentation?.SlideIdList == null)
                {
                    throw new InvalidOperationException("Invalid PPTX file: No slides found");
                }

                var slideIdList = presentationPart.Presentation.SlideIdList;
                structure.SlideCount = slideIdList.ChildElements.Count;

                // 각 슬라이드 분석
                var slideIdArray = slideIdList.Elements<P.SlideId>().ToArray();
                for (int i = 0; i < slideIdArray.Length; i++)
                {
                    var slideId = slideIdArray[i];
                    var relationshipId = slideId.RelationshipId?.Value;
                    if (string.IsNullOrEmpty(relationshipId))
                        continue;

                    var slidePart = presentationPart.GetPartById(relationshipId) as SlidePart;
                    if (slidePart?.Slide == null)
                        continue;

                    var slideInfo = await ParseSlideAsync(slidePart.Slide, i + 1);
                    slides.Add(slideInfo);
                }

                // 테마 정보 추출
                var slideMasterPart = presentationPart.SlideMasterParts?.FirstOrDefault();
                if (slideMasterPart?.ThemePart?.Theme != null)
                {
                    var theme = slideMasterPart.ThemePart.Theme;
                    if (theme.ThemeElements?.ColorScheme != null)
                    {
                        structure.ColorScheme = theme.ThemeElements.ColorScheme.Name?.Value ?? "Default";
                    }
                    if (theme.ThemeElements?.FontScheme != null)
                    {
                        structure.FontScheme = theme.ThemeElements.FontScheme.Name?.Value ?? "Default";
                    }
                }
            }

            structure.Slides = slides;
            return structure;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing PPTX template");
            throw;
        }
    }

    private Task<TemplateSlideInfoDto> ParseSlideAsync(P.Slide slide, int slideNumber)
    {
        var slideInfo = new TemplateSlideInfoDto
        {
            SlideNumber = slideNumber,
            LayoutType = "title-content" // 기본값
        };

        var placeholders = new List<TemplatePlaceholderDto>();

        // CommonSlideData에서 ShapeTree 찾기
        var commonSlideData = slide.CommonSlideData;
        if (commonSlideData?.ShapeTree != null)
        {
            foreach (var element in commonSlideData.ShapeTree.Elements())
            {
                if (element is P.Shape shape)
                {
                    var placeholder = ExtractPlaceholder(shape);
                    if (placeholder != null)
                    {
                        placeholders.Add(placeholder);
                    }
                }
            }
        }

        // 레이아웃 타입 결정
        if (placeholders.Any(p => p.Type == "title") && placeholders.Any(p => p.Type == "body"))
        {
            slideInfo.LayoutType = "title-content";
        }
        else if (placeholders.Any(p => p.Type == "title") && !placeholders.Any(p => p.Type == "body"))
        {
            slideInfo.LayoutType = "title-only";
        }
        else if (placeholders.Count(p => p.Type == "body") >= 2)
        {
            slideInfo.LayoutType = "two-column";
        }
        else if (placeholders.Any(p => p.Type == "image"))
        {
            slideInfo.LayoutType = "image-title";
        }

        slideInfo.Placeholders = placeholders;
        return Task.FromResult(slideInfo);
    }

    private TemplatePlaceholderDto? ExtractPlaceholder(P.Shape shape)
    {
        var appNonVisualProps = shape.NonVisualShapeProperties?.ApplicationNonVisualDrawingProperties;
        var placeholderShape = appNonVisualProps?.GetFirstChild<P.PlaceholderShape>();

        if (placeholderShape == null)
            return null;

        var placeholderType = placeholderShape.Type != null ? placeholderShape.Type.Value.ToString() : "body";
        var index = placeholderShape.Index?.Value ?? 0;

        // 텍스트 내용 추출 (있는 경우)
        string? defaultText = null;
        var textBody = shape.TextBody;
        if (textBody != null)
        {
            var paragraphs = textBody.Elements<A.Paragraph>();
            var texts = paragraphs
                .SelectMany(p => p.Elements<A.Run>())
                .SelectMany(r => r.Elements<A.Text>())
                .Select(t => t.Text)
                .Where(t => !string.IsNullOrEmpty(t));
            
            defaultText = string.Join(" ", texts);
        }

        return new TemplatePlaceholderDto
        {
            Type = MapPlaceholderType(placeholderType),
            Index = (int)index,
            DefaultText = defaultText
        };
    }

    private string MapPlaceholderType(string? openXmlType)
    {
        return openXmlType?.ToLower() switch
        {
            "title" or "ctrtitle" => "title",
            "body" or "obj" => "body",
            "pic" or "object" => "image",
            _ => "body"
        };
    }
}
