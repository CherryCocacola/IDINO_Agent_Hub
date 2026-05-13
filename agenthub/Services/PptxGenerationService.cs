using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Presentation;
using A = DocumentFormat.OpenXml.Drawing;
using P = DocumentFormat.OpenXml.Presentation;
using AIAgentManagement.DTOs;
using AIAgentManagement.Settings;

namespace AIAgentManagement.Services;

public class PptxGenerationService
{
    /// <summary>빈 A.Text 대체용 (PowerPoint 복구 메시지 방지).</summary>
    private const string EmptyTextPlaceholder = "\u200B";

    private readonly ILogger<PptxGenerationService> _logger;
    private readonly IHttpClientFactory _httpClientFactory;

    public PptxGenerationService(ILogger<PptxGenerationService> logger, IHttpClientFactory httpClientFactory)
    {
        _logger = logger;
        _httpClientFactory = httpClientFactory;
    }

    public async Task<Stream> GeneratePptxAsync(PresentationDto presentation)
    {
        var stream = new MemoryStream();
        
        try
        {
            using (var presentationDocument = PresentationDocument.Create(stream, PresentationDocumentType.Presentation, true))
            {
                var presentationPart = presentationDocument.AddPresentationPart();
                var pres = new P.Presentation();
                
                // 슬라이드 마스터 추가
                var slideMasterPart = presentationPart.AddNewPart<SlideMasterPart>();
                
                // 테마 추가 (Phase 2: ThemeId 반영)
                var themePart = slideMasterPart.AddNewPart<ThemePart>();
                themePart.Theme = CreateTheme(presentation.ThemeId);
                
                var themeId = string.IsNullOrWhiteSpace(presentation.ThemeId) ? PresentationThemes.Default : presentation.ThemeId.Trim();
                var themeConfig = PresentationThemes.Get(themeId);
                if (string.IsNullOrWhiteSpace(presentation.ThemeId))
                    _logger.LogDebug("ThemeId not specified, using default theme: {ThemeId}", themeId);
                slideMasterPart.SlideMaster = CreateSlideMaster(themeConfig);
                
                pres.SlideMasterIdList = new P.SlideMasterIdList();
                pres.SlideMasterIdList.AppendChild(new P.SlideMasterId 
                { 
                    Id = 2147483648U, 
                    RelationshipId = presentationPart.GetIdOfPart(slideMasterPart) 
                });

                // 슬라이드 레이아웃 추가
                var slideLayoutPart = slideMasterPart.AddNewPart<SlideLayoutPart>();
                slideLayoutPart.SlideLayout = CreateSlideLayout(themeConfig);
                
                slideMasterPart.SlideMaster.SlideLayoutIdList = new P.SlideLayoutIdList();
                slideMasterPart.SlideMaster.SlideLayoutIdList.AppendChild(new P.SlideLayoutId 
                { 
                    Id = 2147483649U, 
                    RelationshipId = slideMasterPart.GetIdOfPart(slideLayoutPart) 
                });

                // 슬라이드 크기 설정 (Phase 1: 4:3, 16:9, 16:10)
                var (slideW, slideH) = GetSlideDimensions(presentation.SlideSize);

                // ECMA-376 §19.2.1.26 p:presentation 자식 순서:
                //   sldMasterIdLst → sldIdLst → sldSz → notesSz → defaultTextStyle
                // 슬라이드 ID 리스트는 마스터 ID 리스트 다음에 오며, SlideSize 는
                // 그 뒤에 위치해야 한다. ViewProperties / TextStyles 는 p:presentation
                // 의 직접 자식이 아니므로 절대 AppendChild 하면 안 된다 (PowerPoint
                // 가 "읽을 수 없는 콘텐츠" 로 인식하는 손상 원인 #1).
                //   - ViewProperties: 별도 ViewPropertiesPart 로 관리 (필수 아님)
                //   - TextStyles: SlideMaster 의 자식. Presentation 레벨은 DefaultTextStyle 사용
                pres.SlideIdList = new P.SlideIdList();

                // 슬라이드가 없는 경우 빈 슬라이드 하나 추가
                if (presentation.Slides == null || presentation.Slides.Count == 0)
                {
                    var emptySlideDto = new SlideDto
                    {
                        SlideId = Guid.NewGuid().ToString(),
                        SlideNumber = 1,
                        Title = "빈 슬라이드",
                        Content = "",
                        Layout = "title-content"
                    };
                    presentation.Slides = new List<SlideDto> { emptySlideDto };
                }

                // 각 슬라이드를 생성
                uint slideId = 256U;
                var fontHeading = presentation.FontHeading ?? themeConfig?.FontHeading ?? "맑은 고딕";
                var fontBody = presentation.FontBody ?? themeConfig?.FontBody ?? "맑은 고딕";
                foreach (var slideDto in presentation.Slides.OrderBy(s => s.SlideNumber))
                {
                    var slidePart = presentationPart.AddNewPart<SlidePart>();
                    slidePart.Slide = await CreateSlideAsync(slidePart, slideDto, themeConfig, slideW, slideH, fontHeading, fontBody);
                    
                    // 슬라이드 레이아웃 연결
                    var layoutRelId = slidePart.AddPart(slideLayoutPart);
                    
                    pres.SlideIdList.AppendChild(new P.SlideId 
                    { 
                        Id = slideId, 
                        RelationshipId = presentationPart.GetIdOfPart(slidePart) 
                    });
                    slideId++;
                }

                // ECMA-376 자식 순서: sldMasterIdLst → sldIdLst → sldSz → notesSz → defaultTextStyle
                // SlideSize / NotesSize / DefaultTextStyle 는 반드시 SlideIdList 이후에 위치.
                // (속성 setter 가 아닌 AppendChild 로 추가해 EF/OpenXml 의 child collection 에
                //  명시적으로 마지막에 붙도록 한다. 속성 setter 는 schema 가 정의한 위치에
                //  자동 정렬되지만, 명시 AppendChild 가 결정론적이라 디버깅에 유리.)
                pres.SlideSize = new P.SlideSize { Cx = (int)slideW, Cy = (int)slideH };

                // NotesSize 는 일부 PowerPoint 버전이 누락 시 손상으로 인식. 기본 노트 크기
                // (6858000 x 9144000 EMU = 7.5 x 10 인치, 세로 방향) 를 명시.
                pres.NotesSize = new P.NotesSize { Cx = 6858000L, Cy = 9144000L };

                // DefaultTextStyle 은 presentation 전역 기본 텍스트 스타일. 빈 ListStyle 로도
                // 충분하며, 없으면 일부 환경에서 복구 경고가 발생.
                pres.AppendChild(new P.DefaultTextStyle());

                presentationPart.Presentation = pres;
                presentationPart.Presentation.Save();
            }

            stream.Position = 0;
            return stream;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating PPTX file");
            stream?.Dispose();
            throw;
        }
    }

    private A.Theme CreateTheme(string? themeId)
    {
        var themeConfig = PresentationThemes.Get(themeId) ?? PresentationThemes.All.First();
        var p = NormalizeHexColor(themeConfig.PrimaryColor, "4F46E5") ?? "4F46E5";
        var s = NormalizeHexColor(themeConfig.SecondaryColor, "1E293B") ?? "1E293B";
        // 현대적이고 세련된 색상 스키마 (테마 색상 반영)
        var colorScheme = new A.ColorScheme { Name = themeConfig.Name + " Color Scheme" };
        colorScheme.Append(
            new A.Dark1Color(new A.RgbColorModelHex { Val = "1F1F1F" }),
            new A.Light1Color(new A.RgbColorModelHex { Val = "FFFFFF" }),
            new A.Dark2Color(new A.RgbColorModelHex { Val = s }),
            new A.Light2Color(new A.RgbColorModelHex { Val = "F5F7FA" }),
            new A.Accent1Color(new A.RgbColorModelHex { Val = p }),
            new A.Accent2Color(new A.RgbColorModelHex { Val = "ED7D31" }),
            new A.Accent3Color(new A.RgbColorModelHex { Val = "A5A5A5" }),
            new A.Accent4Color(new A.RgbColorModelHex { Val = "FFC000" }),
            new A.Accent5Color(new A.RgbColorModelHex { Val = "5B9BD5" }),
            new A.Accent6Color(new A.RgbColorModelHex { Val = "70AD47" }),
            new A.Hyperlink(new A.RgbColorModelHex { Val = p }),
            new A.FollowedHyperlinkColor(new A.RgbColorModelHex { Val = "954F72" })
        );

        var fontScheme = new A.FontScheme { Name = themeConfig.Name + " Font Scheme" };
        fontScheme.Append(
            new A.MajorFont(
                new A.LatinFont { Typeface = themeConfig.FontHeading },
                new A.EastAsianFont { Typeface = themeConfig.FontHeading },
                new A.ComplexScriptFont { Typeface = themeConfig.FontHeading }
            ),
            new A.MinorFont(
                new A.LatinFont { Typeface = themeConfig.FontBody },
                new A.EastAsianFont { Typeface = themeConfig.FontBody },
                new A.ComplexScriptFont { Typeface = themeConfig.FontBody }
            )
        );

        // 포맷 스키마 (PhColor 대신 Accent1 사용 - 일부 환경에서 PhColor가 검정으로 해석됨)
        var formatScheme = new A.FormatScheme { Name = "Modern Format Scheme" };
        formatScheme.Append(
            new A.FillStyleList(
                new A.SolidFill(new A.SchemeColor { Val = A.SchemeColorValues.Accent1 }),
                new A.GradientFill(new A.GradientStopList()),
                new A.NoFill()
            ),
            new A.LineStyleList(
                new A.Outline(new A.SolidFill(new A.SchemeColor { Val = A.SchemeColorValues.Accent1 }))
            ),
            new A.EffectStyleList(
                new A.EffectStyle(
                    new A.EffectList(
                        new A.OuterShadow(
                            new A.RgbColorModelHex { Val = "000000" },
                            new A.Alpha { Val = 38000 }
                        )
                    )
                )
            ),
            new A.BackgroundFillStyleList(
                new A.SolidFill(new A.SchemeColor { Val = A.SchemeColorValues.Accent1 }),
                new A.GradientFill(new A.GradientStopList()),
                new A.NoFill()
            )
        );

        var theme = new A.Theme { Name = themeConfig.Name + " Theme" };
        theme.Append(
            new A.ThemeElements(colorScheme, fontScheme, formatScheme),
            new A.ObjectDefaults(),
            new A.ExtraColorSchemeList()
        );

        return theme;
    }

    private static bool IsValidHexColor(string? val)
    {
        if (string.IsNullOrEmpty(val)) return false;
        var s = val.Trim().TrimStart('#');
        if (s.Length != 6) return false;
        foreach (var c in s)
            if (!char.IsAsciiHexDigit(c)) return false;
        return true;
    }

    /// <summary>HEX 색상을 6자리로 정규화. # 제거. fallback이 null이면 유효하지 않을 때 null 반환.</summary>
    private static string? NormalizeHexColor(string? val, string? fallback = "000000")
    {
        if (string.IsNullOrEmpty(val)) return fallback;
        var s = val.Trim().TrimStart('#');
        if (s.Length == 6 && s.All(char.IsAsciiHexDigit)) return s;
        if (s.Length == 3 && s.All(char.IsAsciiHexDigit))
            return new string(new[] { s[0], s[0], s[1], s[1], s[2], s[2] });
        return fallback;
    }

    /// <summary>OOXML 스펙에 맞게 p:bg > p:bgPr > fill 구조로 배경 생성. 복구 메시지 방지.</summary>
    private static P.Background CreateBackground(PresentationThemeConfig? themeConfig)
    {
        OpenXmlElement fill;
        if (themeConfig == null)
        {
            fill = new A.SolidFill(new A.RgbColorModelHex { Val = "FFFFFF" });
        }
        else
        {
            var bgStart = NormalizeHexColor(themeConfig.BackgroundColor, "FFFFFF");
            var bgEnd = NormalizeHexColor(themeConfig.BackgroundGradientEndColor, null);
            if (string.IsNullOrEmpty(bgEnd))
            {
                fill = new A.SolidFill(new A.RgbColorModelHex { Val = bgStart });
            }
            else
            {
                var lin = new A.LinearGradientFill { Angle = 8100000, Scaled = true };
                var gsList = new A.GradientStopList();
                var gs0 = new A.GradientStop { Position = 0 };
                gs0.AppendChild(new A.RgbColorModelHex { Val = bgStart });
                var gs1 = new A.GradientStop { Position = 100000 };
                gs1.AppendChild(new A.RgbColorModelHex { Val = bgEnd });
                gsList.AppendChild(gs0);
                gsList.AppendChild(gs1);
                fill = new A.GradientFill(gsList, lin);
            }
        }
        var bgPr = new P.BackgroundProperties();
        bgPr.AppendChild(fill);
        return new P.Background(bgPr);
    }

    private P.SlideMaster CreateSlideMaster(PresentationThemeConfig? themeConfig)
    {
        var slideMaster = new P.SlideMaster();

        var commonSlideData = new P.CommonSlideData();
        // ECMA-376 §19.3.1.45 p:spTree: ShapeTree 의 첫 두 자식은 반드시
        //   1) NonVisualGroupShapeProperties (p:nvGrpSpPr)
        //   2) GroupShapeProperties (p:grpSpPr)
        // 이후에야 Shape / Pic / GraphicFrame / GroupShape 등이 올 수 있다.
        // 이 두 요소가 없으면 PowerPoint 가 "PPTX 가 손상되어 읽을 수 없습니다"
        // 메시지를 띄운다 (손상 원인 #2).
        var shapeTree = new P.ShapeTree();
        AppendShapeTreeHeader(shapeTree);

        commonSlideData.Background = CreateBackground(themeConfig);

        commonSlideData.ShapeTree = shapeTree;
        slideMaster.CommonSlideData = commonSlideData;

        // ColorMap 은 12 개 속성이 모두 필수 (ECMA-376 §19.3.1.6 p:clrMap).
        // 누락 시 PowerPoint 가 스킴 컬러를 해석하지 못해 "복구가 필요" 또는
        // "읽을 수 없음" 메시지가 발생한다 (손상 원인 #3).
        // bg1 ↔ lt1, tx1 ↔ dk1, bg2 ↔ lt2, tx2 ↔ dk2 가 PowerPoint 기본 매핑.
        slideMaster.ColorMap = new P.ColorMap
        {
            Background1 = A.ColorSchemeIndexValues.Light1,
            Text1 = A.ColorSchemeIndexValues.Dark1,
            Background2 = A.ColorSchemeIndexValues.Light2,
            Text2 = A.ColorSchemeIndexValues.Dark2,
            Accent1 = A.ColorSchemeIndexValues.Accent1,
            Accent2 = A.ColorSchemeIndexValues.Accent2,
            Accent3 = A.ColorSchemeIndexValues.Accent3,
            Accent4 = A.ColorSchemeIndexValues.Accent4,
            Accent5 = A.ColorSchemeIndexValues.Accent5,
            Accent6 = A.ColorSchemeIndexValues.Accent6,
            Hyperlink = A.ColorSchemeIndexValues.Hyperlink,
            FollowedHyperlink = A.ColorSchemeIndexValues.FollowedHyperlink
        };

        // SlideLayoutIdList 초기화
        slideMaster.SlideLayoutIdList = new P.SlideLayoutIdList();

        // TextStyles 추가 (제목 및 본문 스타일 정의)
        slideMaster.TextStyles = new P.TextStyles(
            new P.TitleStyle(
                new A.ListStyle()
            ),
            new P.BodyStyle(
                new A.ListStyle()
            ),
            new P.OtherStyle(
                new A.ListStyle()
            )
        );

        return slideMaster;
    }

    /// <summary>
    /// ShapeTree 의 필수 헤더(NonVisualGroupShapeProperties + GroupShapeProperties)를
    /// 주어진 ShapeTree 에 추가한다. 모든 ShapeTree(SlideMaster / SlideLayout / Slide) 는
    /// 이 헤더로 시작해야 OOXML schema 가 유효해진다. ECMA-376 §19.3.1.45 (CT_GroupShape) 참조.
    /// 헤더가 없으면 PowerPoint 가 "PPTX 가 손상되어 읽을 수 없습니다" 를 띄운다.
    /// </summary>
    private static void AppendShapeTreeHeader(P.ShapeTree shapeTree)
    {
        // NonVisualGroupShapeProperties: 그룹 도형의 메타 정보. ID=1 은 spTree root 의 관용 ID.
        shapeTree.AppendChild(new P.NonVisualGroupShapeProperties(
            new P.NonVisualDrawingProperties { Id = 1U, Name = "" },
            new P.NonVisualGroupShapeDrawingProperties(),
            new P.ApplicationNonVisualDrawingProperties()
        ));

        // GroupShapeProperties: 빈 변환 (offset 0, extent 0) — 그룹 자체에 별도 변환이 없음.
        shapeTree.AppendChild(new P.GroupShapeProperties(
            new A.TransformGroup(
                new A.Offset { X = 0L, Y = 0L },
                new A.Extents { Cx = 0L, Cy = 0L },
                new A.ChildOffset { X = 0L, Y = 0L },
                new A.ChildExtents { Cx = 0L, Cy = 0L }
            )
        ));
    }

    /// <summary>Blank 레이아웃. Placeholder 없음. 슬라이드가 커스텀 Shape만 사용하므로 마스터-레이아웃 불일치 방지. 배경 상속 체인 명시.</summary>
    private P.SlideLayout CreateSlideLayout(PresentationThemeConfig? themeConfig)
    {
        var slideLayout = new P.SlideLayout();
        var commonSlideData = new P.CommonSlideData();
        var shapeTree = new P.ShapeTree();
        // ShapeTree 필수 헤더 (NonVisualGroupShapeProperties + GroupShapeProperties).
        // 자세한 내용은 BuildShapeTreeHeader() 주석 참조.
        AppendShapeTreeHeader(shapeTree);
        commonSlideData.Background = CreateBackground(themeConfig);
        // Placeholder 제거 - 슬라이드 Shape ID(1~)와 충돌 방지 및 복구 메시지 원인 제거
        commonSlideData.ShapeTree = shapeTree;
        slideLayout.CommonSlideData = commonSlideData;
        return slideLayout;
    }

    // EMU: 914400 EMU = 1인치. 슬라이드 사이즈별 (폭, 높이)
    private static readonly Dictionary<string, (long Width, long Height)> SlideSizes = new(StringComparer.OrdinalIgnoreCase)
    {
        ["4:3"] = (9144000L, 6858000L),
        ["16:9"] = (9144000L, 5143500L),
        ["16:10"] = (9144000L, 5715000L),
        ["A4"] = (9144000L, 6858000L)
    };
    private const long SlideWidth = 9144000L;
    private const long SlideHeight = 6858000L;
    private const long MarginSide = 914400L;

    private static (long Width, long Height) GetSlideDimensions(string? slideSize)
    {
        var key = (slideSize ?? "16:9").Trim();
        return SlideSizes.TryGetValue(key, out var dim) ? dim : SlideSizes["16:9"];
    }

    /// <summary>4:3 기준 Y/높이 값을 실제 슬라이드 높이에 맞게 스케일.</summary>
    private static long ScaleY(long value, long actualHeight) =>
        (long)(value * (double)actualHeight / SlideHeight);
    private const long MarginTop = 365125L;
    private const long ContentAreaWidth = 7315200L;
    private const int TitleFontSizeDefault = 2200;
    private const int TitleFontSizeDisplay = 2600;
    private const int TitleFontSizeImpact = 3200;
    private const int BodyFontSizeDefault = 1300;

    private async Task<P.Slide> CreateSlideAsync(SlidePart slidePart, SlideDto slideDto, PresentationThemeConfig? themeConfig, long slideW = 0, long slideH = 0, string? fontHeading = null, string? fontBody = null)
    {
        var w = slideW > 0 ? slideW : SlideWidth;
        var h = slideH > 0 ? slideH : SlideHeight;
        long sy(long v) => ScaleY(v, h);
        var contentW = w - 2 * MarginSide;
        var halfW = w / 2;
        var fHeading = fontHeading ?? themeConfig?.FontHeading ?? "맑은 고딕";
        var fBody = fontBody ?? themeConfig?.FontBody ?? "맑은 고딕";

        var layout = (slideDto.Layout ?? "title-content").Trim().ToLowerInvariant();
        var slide = new P.Slide();
        var commonSlideData = new P.CommonSlideData();
        var shapeTree = new P.ShapeTree();
        // ShapeTree 필수 헤더(NonVisualGroupShapeProperties + GroupShapeProperties).
        // 헤더는 ID=1 을 점유하므로 슬라이드의 사용자 도형 ID 는 2 부터 시작한다.
        AppendShapeTreeHeader(shapeTree);
        uint shapeId = 2;

        switch (layout)
        {
            case "title-only":
            case "section-header":
                if (!string.IsNullOrEmpty(slideDto.Title))
                {
                    var titleW = contentW;
                    var titleX = (w - titleW) / 2;
                    var titleShape = CreateTextShape(shapeId++, "Title", slideDto.Title, titleX, sy(2500000L), titleW, sy(2000000L), themeConfig, fHeading, fBody, titleFontSize: TitleFontSizeDisplay);
                    shapeTree.AppendChild(titleShape);
                }
                if (!string.IsNullOrWhiteSpace(slideDto.Content) && layout == "section-header")
                {
                    var sub = CreateTextShape(shapeId++, "Content", slideDto.Content, MarginSide, sy(4600000L), contentW, sy(1200000L), themeConfig, fHeading, fBody);
                    shapeTree.AppendChild(sub);
                }
                break;

            case "thank-you":
                if (!string.IsNullOrEmpty(slideDto.Title))
                {
                    var tw = w - 1828800L;
                    var tx = (w - tw) / 2;
                    var thankShape = CreateTextShape(shapeId++, "Title", slideDto.Title, tx, sy(2600000L), tw, sy(1600000L), themeConfig, fHeading, fBody, titleFontSize: TitleFontSizeImpact);
                    shapeTree.AppendChild(thankShape);
                }
                if (!string.IsNullOrWhiteSpace(slideDto.Content))
                {
                    var cw = w - 1828800L;
                    var cx = (w - cw) / 2;
                    var cap = CreateTextShape(shapeId++, "Content", slideDto.Content, cx, sy(4300000L), cw, sy(800000L), themeConfig, fHeading, fBody);
                    shapeTree.AppendChild(cap);
                }
                break;

            case "quote":
                if (!string.IsNullOrEmpty(slideDto.Title))
                {
                    var qTitle = CreateTextShape(shapeId++, "Title", slideDto.Title, MarginSide, sy(2500000L), contentW, sy(800000L), themeConfig, fHeading, fBody, titleFontSize: 3200);
                    shapeTree.AppendChild(qTitle);
                }
                if (!string.IsNullOrWhiteSpace(slideDto.Content))
                {
                    var qContent = CreateTextShape(shapeId++, "Content", slideDto.Content, MarginSide, sy(3400000L), contentW, sy(2000000L), themeConfig, fHeading, fBody);
                    shapeTree.AppendChild(qContent);
                }
                break;

            case "two-column":
            case "comparison":
                if (!string.IsNullOrEmpty(slideDto.Title))
                {
                    var tShape = CreateTextShape(shapeId++, "Title", slideDto.Title, 0, 0, w, sy(1600000L), themeConfig, fHeading, fBody, titleFontSize: TitleFontSizeDefault);
                    shapeTree.AppendChild(tShape);
                }
                var (leftContent, rightContent) = SplitContentForTwoColumns(slideDto.Content ?? "");
                if (!string.IsNullOrEmpty(leftContent))
                {
                    var left = CreateTextShape(shapeId++, "Content", leftContent, 0, sy(1800000L), halfW, sy(4500000L), themeConfig, fHeading, fBody);
                    shapeTree.AppendChild(left);
                }
                if (!string.IsNullOrEmpty(rightContent))
                {
                    var right = CreateTextShape(shapeId++, "Content", rightContent, halfW, sy(1800000L), halfW, sy(4500000L), themeConfig, fHeading, fBody);
                    shapeTree.AppendChild(right);
                }
                if (!string.IsNullOrWhiteSpace(slideDto.ImageUrl))
                {
                    try
                    {
                        var img = await AddImageFromUrlAsync(slidePart, slideDto.ImageUrl, shapeId++, "two-column", w, h);
                        if (img != null) shapeTree.AppendChild(img);
                    }
                    catch (Exception ex) { _logger.LogWarning(ex, "Could not add image to slide"); }
                }
                break;

            case "image-title":
                if (!string.IsNullOrEmpty(slideDto.Title))
                {
                    var itTitle = CreateTextShape(shapeId++, "Title", slideDto.Title, MarginSide, sy(400000L), contentW, sy(1200000L), themeConfig, fHeading, fBody);
                    shapeTree.AppendChild(itTitle);
                }
                if (!string.IsNullOrWhiteSpace(slideDto.ImageUrl))
                {
                    try
                    {
                        var img = await AddImageFromUrlAsync(slidePart, slideDto.ImageUrl, shapeId++, "image-title", w, h);
                        if (img != null) shapeTree.AppendChild(img);
                    }
                    catch (Exception ex) { _logger.LogWarning(ex, "Could not add image to slide"); }
                }
                if (!string.IsNullOrWhiteSpace(slideDto.Content))
                {
                    var cap = CreateTextShape(shapeId++, "Content", slideDto.Content, 1572000L, sy(5900000L), 6000000L, sy(600000L), themeConfig, fHeading, fBody);
                    shapeTree.AppendChild(cap);
                }
                break;

            case "title-content":
            default:
                if (!string.IsNullOrEmpty(slideDto.Title))
                {
                    var titleShape = CreateTextShape(shapeId++, "Title", slideDto.Title, 0, 0, w, sy(1600000L), themeConfig, fHeading, fBody, titleFontSize: TitleFontSizeDefault);
                    shapeTree.AppendChild(titleShape);
                }
                long contentWidth = w;
                long contentX = 0;
                if (!string.IsNullOrWhiteSpace(slideDto.ImageUrl))
                    contentWidth = halfW;
                if (!string.IsNullOrEmpty(slideDto.Content))
                {
                    var contentShape = CreateTextShape(shapeId++, "Content", slideDto.Content, contentX, sy(2000000L), contentWidth, sy(5000000L), themeConfig, fHeading, fBody);
                    shapeTree.AppendChild(contentShape);
                }
                if (!string.IsNullOrWhiteSpace(slideDto.ImageUrl))
                {
                    try
                    {
                        var imageShape = await AddImageFromUrlAsync(slidePart, slideDto.ImageUrl, shapeId++, "title-content", w, h);
                        if (imageShape != null)
                            shapeTree.AppendChild(imageShape);
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning(ex, "Could not add image to slide: {Url}", slideDto.ImageUrl);
                    }
                }
                break;
        }

        // Phase 2: Tables 렌더링 (title-content 또는 별도 레이아웃)
        if (slideDto.Tables != null && slideDto.Tables.Count > 0)
        {
            foreach (var tableDto in slideDto.Tables)
            {
                if (tableDto?.Rows == null || tableDto.Rows.Count == 0) continue;
                try
                {
                    var tableShape = CreateTableShape(shapeId++, tableDto, w, h, themeConfig, fHeading, fBody);
                    if (tableShape != null) shapeTree.AppendChild(tableShape);
                }
                catch (Exception ex) { _logger.LogWarning(ex, "Could not add table to slide"); }
            }
        }

        if (slideDto.Images != null && slideDto.Images.Count > 0)
            _logger.LogDebug("Images list count: {Count}", slideDto.Images.Count);

        commonSlideData.Background = CreateBackground(themeConfig);
        commonSlideData.ShapeTree = shapeTree;
        slide.CommonSlideData = commonSlideData;
        return slide;
    }

    /// <summary>Phase 2: TableDto를 OOXML GraphicFrame(Table)로 렌더링.</summary>
    private P.GraphicFrame? CreateTableShape(uint id, TableDto tableDto, long slideW, long slideH, PresentationThemeConfig? themeConfig, string? fontHeading, string? fontBody)
    {
        if (tableDto?.Rows == null || tableDto.Rows.Count == 0) return null;
        var rows = tableDto.Rows;
        var colCount = rows.Count > 0 ? rows.Max(r => r?.Count ?? 0) : 0;
        if (colCount == 0) return null;

        long sy(long v) => ScaleY(v, slideH);
        var tableW = slideW - 2 * MarginSide;
        var colWidth = tableW / Math.Max(1, colCount);
        const long rowHeight = 370840L;
        var tableH = Math.Min(sy(4500000L), rows.Count * rowHeight);

        var graphicFrame = new P.GraphicFrame();
        graphicFrame.NonVisualGraphicFrameProperties = new P.NonVisualGraphicFrameProperties(
            new P.NonVisualDrawingProperties { Id = id, Name = "Table 1" },
            new P.NonVisualGraphicFrameDrawingProperties(new A.GraphicFrameLocks { NoGrouping = true }),
            new P.ApplicationNonVisualDrawingProperties()
        );
        graphicFrame.Transform = new P.Transform(
            new A.Offset { X = MarginSide, Y = sy(3500000L) },
            new A.Extents { Cx = tableW, Cy = tableH }
        );

        var table = BuildDrawingTable(tableDto, colCount, colWidth, rowHeight, themeConfig, fontHeading ?? "맑은 고딕", fontBody ?? "맑은 고딕");
        graphicFrame.Graphic = new A.Graphic(
            new A.GraphicData(table) { Uri = "http://schemas.openxmlformats.org/drawingml/2006/table" }
        );
        return graphicFrame;
    }

    /// <summary>
    /// 테마 색상을 직접 추출하여 셀 배경·텍스트를 명시적으로 지정.
    /// TableStyleId 사용 시 Accent1(=PrimaryColor)이 테마에 따라 흰색 등으로 매핑되어
    /// 텍스트가 보이지 않는 문제가 있어 스타일 없이 직접 렌더링.
    /// </summary>
    private static A.Table BuildDrawingTable(TableDto dto, int colCount, long colWidth, long rowHeight, PresentationThemeConfig? themeConfig, string fontHeading, string fontBody)
    {
        var table = new A.Table();
        // TableStyleId 제거: 테마 의존 색상 충돌 방지 (스타일 없이 직접 색상 지정)
        table.TableProperties = new A.TableProperties { FirstRow = dto.HeaderRow, BandRow = false };

        var grid = new A.TableGrid();
        for (var i = 0; i < colCount; i++)
            grid.AppendChild(new A.GridColumn { Width = colWidth });
        table.AppendChild(grid);

        var bodyFontSize = themeConfig?.BodyFontSize ?? BodyFontSizeDefault;
        var isDarkBg = themeConfig?.UseDarkBackground ?? false;

        // 헤더 배경색 결정:
        //   다크 배경 테마(business-blue·dark·marketing·education)는 BackgroundColor가 실제 강조색(파랑·주황 등)
        //   라이트 배경 테마(default·minimal)는 PrimaryColor가 강조색(보라·검정 등)
        var headerBgHex = isDarkBg
            ? NormalizeHexColor(themeConfig?.BackgroundColor, "1D4ED8")
            : NormalizeHexColor(themeConfig?.PrimaryColor,   "3730A3");

        // 본문 셀은 슬라이드 배경에 무관하게 흰색 계열 → 어두운 텍스트로 가독성 보장
        const string HeaderTextHex = "FFFFFF";   // 헤더 텍스트: 항상 흰색
        const string BodyOddBgHex  = "FFFFFF";   // 홀수 본문 행: 흰색
        const string BodyEvenBgHex = "EFF6FF";   // 짝수 본문 행: 아주 연한 파랑(중립적)
        const string BodyTextHex   = "1E293B";   // 본문 텍스트: 어두운 남색 (모든 테마 가독성 OK)
        const string BorderHex     = "CBD5E1";   // 행 구분선: 연한 회색

        for (var rowIdx = 0; rowIdx < dto.Rows.Count; rowIdx++)
        {
            var row = dto.Rows[rowIdx];
            var isHeader  = dto.HeaderRow && rowIdx == 0;
            var isLastRow = rowIdx == dto.Rows.Count - 1;
            var tr = new A.TableRow { Height = rowHeight };

            string cellBgHex, cellTextHex;
            if (isHeader)
            {
                cellBgHex   = headerBgHex ?? "1D4ED8";
                cellTextHex = HeaderTextHex;
            }
            else
            {
                // header가 있으면 rowIdx 1이 body 첫 번째 행(0-based body index = 0 → ODD)
                var bodyIdx = rowIdx - (dto.HeaderRow ? 1 : 0);
                cellBgHex   = bodyIdx % 2 == 0 ? BodyOddBgHex : BodyEvenBgHex;
                cellTextHex = BodyTextHex;
            }

            for (var c = 0; c < colCount; c++)
            {
                var cellContent = (row != null && c < row.Count) ? (row[c] ?? "") : "";
                var cell = CreateTableCell(cellContent, isHeader, bodyFontSize, cellTextHex, cellBgHex, BorderHex, isLastRow, fontHeading, fontBody);
                tr.AppendChild(cell);
            }
            table.AppendChild(tr);
        }
        return table;
    }

    /// <summary>
    /// 개별 셀 생성. OOXML 스펙(CT_TableCellProperties) 순서:
    /// lnL → lnR → lnT → lnB → solidFill(배경)
    /// </summary>
    private static A.TableCell CreateTableCell(
        string text, bool isHeader, int bodyFontSize,
        string textHex, string bgHex, string borderHex,
        bool isLastRow, string fontHeading, string fontBody)
    {
        var cell = new A.TableCell();

        // ── 텍스트 런 ───────────────────────────────────────────────────
        var fontSize = isHeader ? 1200 : bodyFontSize;
        var font     = isHeader ? fontHeading : fontBody;
        var runProps = new A.RunProperties { FontSize = fontSize, Bold = isHeader };
        runProps.AppendChild(new A.SolidFill(new A.RgbColorModelHex { Val = textHex }));
        runProps.AppendChild(new A.LatinFont   { Typeface = font });
        runProps.AppendChild(new A.EastAsianFont { Typeface = font });

        var align   = isHeader ? A.TextAlignmentTypeValues.Center : A.TextAlignmentTypeValues.Left;
        var content = string.IsNullOrEmpty(text) ? EmptyTextPlaceholder : SanitizeForXml(text);

        var paragraph = new A.Paragraph(
            new A.ParagraphProperties { Alignment = align },
            new A.Run(runProps, new A.Text(content)),
            new A.EndParagraphRunProperties()
        );

        // BodyProperties: 안쪽 여백 + 세로 중앙 정렬
        var bodyProps = new A.BodyProperties
        {
            Wrap        = A.TextWrappingValues.Square,
            Anchor      = A.TextAnchoringTypeValues.Center,
            LeftInset   = 91440,  // 0.1인치 (EMU)
            RightInset  = 91440,
            TopInset    = 45720,  // 0.05인치
            BottomInset = 45720
        };

        var textBody = new A.TextBody(bodyProps, new A.ListStyle(), paragraph);
        cell.AppendChild(textBody);

        // ── 셀 속성 (OOXML 순서: 테두리 → 채우기) ──────────────────────
        var tcPr = new A.TableCellProperties();

        // lnL / lnR / lnT : 없음(NoFill)
        var lnL = new A.LeftBorderLineProperties  { Width = 12700 };
        lnL.AppendChild(new A.NoFill());
        tcPr.AppendChild(lnL);

        var lnR = new A.RightBorderLineProperties { Width = 12700 };
        lnR.AppendChild(new A.NoFill());
        tcPr.AppendChild(lnR);

        var lnT = new A.TopBorderLineProperties   { Width = 12700 };
        lnT.AppendChild(new A.NoFill());
        tcPr.AppendChild(lnT);

        // lnB : 행 구분선 (마지막 행 제외)
        var lnB = new A.BottomBorderLineProperties { Width = 12700 };
        if (!isLastRow)
            lnB.AppendChild(new A.SolidFill(new A.RgbColorModelHex { Val = borderHex }));
        else
            lnB.AppendChild(new A.NoFill());
        tcPr.AppendChild(lnB);

        // 배경 채우기 (OOXML 스펙: 테두리 다음에 fill)
        tcPr.AppendChild(new A.SolidFill(new A.RgbColorModelHex { Val = bgHex }));

        cell.AppendChild(tcPr);
        return cell;
    }

    /// <summary>2단 레이아웃용 콘텐츠 분할. **섹션헤더** 단위로 분할하여 좌/우 균형 유지.</summary>
    private static (string Left, string Right) SplitContentForTwoColumns(string content)
    {
        if (string.IsNullOrWhiteSpace(content)) return ("", "");
        var lines = content.Split(new[] { '\n', '\r' }, StringSplitOptions.None).ToList();
        if (lines.Count == 0) return ("", "");

        // **섹션헤더** 패턴으로 섹션 분리 (마크다운 볼드 헤더)
        var sections = new List<string>();
        var current = new List<string>();
        foreach (var line in lines)
        {
            var trimmed = line.Trim();
            if (trimmed.StartsWith("**") && trimmed.EndsWith("**") && trimmed.Length > 4)
            {
                if (current.Count > 0)
                {
                    sections.Add(string.Join("\n", current));
                    current.Clear();
                }
            }
            if (!string.IsNullOrEmpty(line) || current.Count > 0)
                current.Add(line);
        }
        if (current.Count > 0)
            sections.Add(string.Join("\n", current));

        if (sections.Count == 0)
        {
            var joined = string.Join("\n", lines.Where(l => !string.IsNullOrWhiteSpace(l)));
            if (string.IsNullOrEmpty(joined)) return ("", "");
            var allLines = joined.Split('\n');
            var splitAt = (allLines.Length + 1) / 2;
            return (string.Join("\n", allLines.Take(splitAt)), string.Join("\n", allLines.Skip(splitAt)));
        }

        if (sections.Count == 1)
        {
            var innerLines = sections[0].Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);
            var splitAt = (innerLines.Length + 1) / 2;
            return (string.Join("\n", innerLines.Take(splitAt)), string.Join("\n", innerLines.Skip(splitAt)));
        }

        var mid = (sections.Count + 1) / 2;
        return (string.Join("\n\n", sections.Take(mid)), string.Join("\n\n", sections.Skip(mid)));
    }

    private async Task<P.Picture?> AddImageFromUrlAsync(SlidePart slidePart, string imageUrl, uint shapeId, string? layout = null, long slideW = 0, long slideH = 0)
    {
        byte[]? bytes;
        string? mimeType = null;

        if (imageUrl.StartsWith("data:", StringComparison.OrdinalIgnoreCase))
        {
            var parsed = ParseDataUrl(imageUrl);
            if (parsed == null) return null;
            bytes = parsed.Value.Bytes;
            mimeType = parsed.Value.MimeType;
        }
        else
        {
            using var client = _httpClientFactory.CreateClient();
            client.Timeout = TimeSpan.FromSeconds(15);
            bytes = await client.GetByteArrayAsync(imageUrl);
        }

        if (bytes == null || bytes.Length == 0) return null;

        var partType = GetImagePartType(mimeType);
        var imagePart = slidePart.AddImagePart(partType);
        using (var ms = new MemoryStream(bytes))
            imagePart.FeedData(ms);
        var relId = slidePart.GetIdOfPart(imagePart);

        var w = slideW > 0 ? slideW : SlideWidth;
        var h = slideH > 0 ? slideH : SlideHeight;
        long sy(long v) => ScaleY(v, h);
        long x, y, cx, cy;
        var layoutNorm = (layout ?? "title-content").Trim().ToLowerInvariant();
        if (layoutNorm == "image-title")
        {
            cx = 6000000L;
            cy = sy(4000000L);
            x = (w - cx) / 2;
            y = sy(1800000L);
        }
        else if (layoutNorm == "two-column" || layoutNorm == "comparison")
        {
            cx = 4000000L;
            cy = sy(3000000L);
            x = w / 2 + 572000L;
            y = sy(1800000L);
        }
        else
        {
            x = w - 4000000L - 572000L;
            y = sy(1800000L);
            cx = 4000000L;
            cy = sy(3000000L);
        }

        var imgShapeProps = new P.ShapeProperties();
        imgShapeProps.AppendChild(new A.Transform2D(
            new A.Offset { X = x, Y = y },
            new A.Extents { Cx = cx, Cy = cy }
        ));
        imgShapeProps.AppendChild(new A.PresetGeometry { Preset = A.ShapeTypeValues.RoundRectangle });
        imgShapeProps.AppendChild(new A.EffectList(
            new A.OuterShadow(
                new A.RgbColorModelHex { Val = "000000" },
                new A.Alpha { Val = 20000 }
            )
            {
                BlurRadius = 50800L,
                Distance = 38100L,
                Direction = 270000
            }
        ));
        var picture = new P.Picture(
            new P.NonVisualPictureProperties(
                new P.NonVisualDrawingProperties { Id = shapeId, Name = "AI Image" },
                new P.NonVisualPictureDrawingProperties(new A.PictureLocks { NoChangeAspect = true }),
                new P.ApplicationNonVisualDrawingProperties()
            ),
            new P.BlipFill(
                new A.Blip { Embed = relId },
                new A.Stretch(new A.FillRectangle())
            ),
            imgShapeProps
        );
        return picture;
    }

    /// <summary>data:image/png;base64,... 형식 파싱. AI 이미지 생성이 반환하는 URL을 바이트로 변환.</summary>
    private static (byte[] Bytes, string MimeType)? ParseDataUrl(string dataUrl)
    {
        if (string.IsNullOrWhiteSpace(dataUrl) || !dataUrl.StartsWith("data:", StringComparison.OrdinalIgnoreCase))
            return null;
        var comma = dataUrl.IndexOf(',');
        if (comma < 0) return null;
        var header = dataUrl.Substring(5, comma - 5).Trim();
        var base64 = dataUrl.Substring(comma + 1);
        if (string.IsNullOrEmpty(base64)) return null;
        string mimeType = "image/png";
        if (header.StartsWith("image/", StringComparison.OrdinalIgnoreCase))
        {
            var semicolon = header.IndexOf(';');
            mimeType = semicolon > 0 ? header.Substring(0, semicolon).Trim() : header.Trim();
        }
        try
        {
            var bytes = Convert.FromBase64String(base64);
            return bytes.Length > 0 ? (bytes, mimeType) : null;
        }
        catch { return null; }
    }

    private static ImagePartType GetImagePartType(string? mimeType)
    {
        if (string.IsNullOrEmpty(mimeType)) return ImagePartType.Jpeg;
        if (mimeType.Contains("png", StringComparison.OrdinalIgnoreCase)) return ImagePartType.Png;
        if (mimeType.Contains("gif", StringComparison.OrdinalIgnoreCase)) return ImagePartType.Gif;
        return ImagePartType.Jpeg;
    }

    /// <summary>XML 1.0 금지 문자 제거. PowerPoint 복구 메시지 방지.</summary>
    private static string SanitizeForXml(string? text)
    {
        if (string.IsNullOrEmpty(text)) return text ?? string.Empty;
        // BOM(U+FEFF), null, C0/C1 제어문자 등 제거
        var cleaned = text.Replace("\uFEFF", "").Replace("\0", "");
        // C1 제어문자(0x80-0x9F) 제거
        cleaned = Regex.Replace(cleaned, @"[\u0080-\u009F]", "");
        // &#xHHHH; / &#DDD; 엔티티 중 XML 1.0 비허용 문자로 디코딩되는 패턴 제거
        cleaned = Regex.Replace(cleaned, @"&#x([0-9a-fA-F]+);", m =>
        {
            if (!int.TryParse(m.Groups[1].Value, System.Globalization.NumberStyles.HexNumber, null, out var code))
                return m.Value;
            return IsXmlChar(code) ? m.Value : "";
        });
        cleaned = Regex.Replace(cleaned, @"&#(\d+);", m =>
        {
            if (!int.TryParse(m.Groups[1].Value, out var code)) return m.Value;
            return IsXmlChar(code) ? m.Value : "";
        });
        var sb = new StringBuilder(cleaned.Length);
        for (var i = 0; i < cleaned.Length; i++)
        {
            var c = cleaned[i];
            // XML 1.0 허용 문자: Tab, LF, CR, 0x20-0xD7FF, 0xE000-0xFFFD, surrogate pairs
            if (c == 0x9 || c == 0xA || c == 0xD || (c >= 0x20 && c <= 0xD7FF) ||
                (c >= 0xE000 && c <= 0xFFFD))
                sb.Append(c);
            else if (char.IsHighSurrogate(c) && i + 1 < cleaned.Length && char.IsLowSurrogate(cleaned[i + 1]))
            {
                sb.Append(c).Append(cleaned[i + 1]);
                i++;
            }
        }
        return sb.ToString();
    }

    private static bool IsXmlChar(int code)
    {
        if (code < 0 || code > 0x10FFFF) return false;
        return code == 0x9 || code == 0xA || code == 0xD ||
               (code >= 0x20 && code <= 0xD7FF) || (code >= 0xE000 && code <= 0xFFFD) ||
               (code >= 0x10000 && code <= 0x10FFFF);
    }

    private static P.ShapeProperties CreateTextShapeProperties(long x, long y, long width, long height, PresentationThemeConfig? themeConfig, bool isTitle = false)
    {
        var shapeProps = new P.ShapeProperties();
        shapeProps.AppendChild(new A.Transform2D(
            new A.Offset { X = x, Y = y },
            new A.Extents { Cx = width, Cy = height }
        ));
        shapeProps.AppendChild(new A.PresetGeometry { Preset = A.ShapeTypeValues.RoundRectangle });
        // 미리보기와 동일: 박스 없이 텍스트만 표시 (배경이 그대로 보임)
        shapeProps.AppendChild(new A.NoFill());
        shapeProps.AppendChild(new A.Outline(new A.NoFill()));
        return shapeProps;
    }

    private P.Shape CreateTextShape(uint id, string name, string text, long x, long y, long width, long height, PresentationThemeConfig? themeConfig = null, string? fontHeading = null, string? fontBody = null, int? titleFontSize = null, int? bodyFontSize = null)
    {
        var shape = new P.Shape();
        shape.NonVisualShapeProperties = new P.NonVisualShapeProperties(
            new P.NonVisualDrawingProperties { Id = id, Name = name },
            new P.NonVisualShapeDrawingProperties(new A.ShapeLocks { NoGrouping = true }),
            new P.ApplicationNonVisualDrawingProperties()
        );

        bool isTitle = name.ToLower().Contains("title");
        int fontSize = isTitle
            ? (titleFontSize ?? themeConfig?.TitleFontSize ?? TitleFontSizeDefault)
            : (bodyFontSize ?? themeConfig?.BodyFontSize ?? BodyFontSizeDefault);
        bool isBold = isTitle && (themeConfig?.TitleBold ?? true);
        bool useThemeColor = themeConfig != null;

        shape.ShapeProperties = CreateTextShapeProperties(x, y, width, height, themeConfig, isTitle);

        var textBody = new P.TextBody(
            new A.BodyProperties 
            { 
                Wrap = A.TextWrappingValues.Square,
                Anchor = A.TextAnchoringTypeValues.Top,
                AnchorCenter = false
            },
            new A.ListStyle()
        );

        var fontFamily = isTitle ? (fontHeading ?? themeConfig?.FontHeading) : (fontBody ?? themeConfig?.FontBody);
        // 마크다운 파싱 및 텍스트 처리 (테마별 TitleColor/BodyColor 적용). XML 금지 문자 제거.
        var paragraphs = ParseMarkdownText(SanitizeForXml(text), fontSize, isBold, themeConfig, isTitle, fontFamily);
        foreach (var paragraph in paragraphs)
        {
            textBody.AppendChild(paragraph);
        }

        shape.TextBody = textBody;

        return shape;
    }

    private List<A.Paragraph> ParseMarkdownText(string text, int fontSize, bool defaultBold, PresentationThemeConfig? themeConfig, bool isTitle = false, string? fontFamily = null)
    {
        var paragraphs = new List<A.Paragraph>();

        if (string.IsNullOrEmpty(text))
        {
            paragraphs.Add(new A.Paragraph(
                new A.ParagraphProperties(CreateDefaultRunProperties(fontSize, defaultBold, themeConfig, isTitle, fontFamily)),
                new A.Run(CreateRunProperties(fontSize, defaultBold, themeConfig, isTitle, false, fontFamily), new A.Text(EmptyTextPlaceholder))
            ));
            return paragraphs;
        }

        var lines = text.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);
        if (lines.Length == 0)
        {
            paragraphs.Add(new A.Paragraph(
                new A.ParagraphProperties(CreateDefaultRunProperties(fontSize, defaultBold, themeConfig, isTitle, fontFamily)),
                new A.Run(CreateRunProperties(fontSize, defaultBold, themeConfig, isTitle, false, fontFamily), new A.Text(EmptyTextPlaceholder))
            ));
            return paragraphs;
        }

        foreach (var line in lines)
        {
            var paragraph = new A.Paragraph(
                new A.ParagraphProperties(CreateDefaultRunProperties(fontSize, defaultBold, themeConfig, isTitle, fontFamily))
            );
            var runs = ParseMarkdownRuns(line, fontSize, defaultBold, themeConfig, isTitle, fontFamily);
            foreach (var run in runs)
                paragraph.AppendChild(run);
            paragraphs.Add(paragraph);
        }

        return paragraphs;
    }

    private static A.DefaultRunProperties CreateDefaultRunProperties(int fontSize, bool bold, PresentationThemeConfig? themeConfig, bool isTitle = false, string? fontFamily = null)
    {
        var props = new A.DefaultRunProperties { FontSize = fontSize, Bold = bold };
        if (themeConfig != null)
        {
            var raw = isTitle ? themeConfig.TitleColor : themeConfig.BodyColor;
            var color = NormalizeHexColor(raw, isTitle ? "1E293B" : "374151");
            if (!string.IsNullOrEmpty(color))
                props.AppendChild(new A.SolidFill(new A.RgbColorModelHex { Val = color }));
        }
        if (!string.IsNullOrWhiteSpace(fontFamily))
        {
            props.AppendChild(new A.LatinFont { Typeface = fontFamily.Trim() });
            props.AppendChild(new A.EastAsianFont { Typeface = fontFamily.Trim() });
        }
        return props;
    }

    private static A.RunProperties CreateRunProperties(int fontSize, bool bold, PresentationThemeConfig? themeConfig, bool isTitle = false, bool italic = false, string? fontFamily = null)
    {
        var props = new A.RunProperties { FontSize = fontSize, Bold = bold, Italic = italic };
        if (themeConfig != null)
        {
            var raw = isTitle ? themeConfig.TitleColor : themeConfig.BodyColor;
            var color = NormalizeHexColor(raw, isTitle ? "1E293B" : "374151");
            if (!string.IsNullOrEmpty(color))
                props.AppendChild(new A.SolidFill(new A.RgbColorModelHex { Val = color }));
        }
        if (!string.IsNullOrWhiteSpace(fontFamily))
        {
            props.AppendChild(new A.LatinFont { Typeface = fontFamily.Trim() });
            props.AppendChild(new A.EastAsianFont { Typeface = fontFamily.Trim() });
        }
        return props;
    }

    /// <summary>선행/후행 공백이 있으면 xml:space=preserve 설정. 빈 문자열은 placeholder로 대체. PowerPoint 복구 메시지 방지.</summary>
    private static A.Text CreateTextElement(string text)
    {
        var content = string.IsNullOrEmpty(text) ? EmptyTextPlaceholder : text;
        var el = new A.Text(content);
        if (content.Length > 0 && (char.IsWhiteSpace(content[0]) || char.IsWhiteSpace(content[^1])))
            el.SetAttribute(new OpenXmlAttribute("xml", "space", "http://www.w3.org/XML/1998/namespace", "preserve"));
        return el;
    }

    private List<A.Run> ParseMarkdownRuns(string text, int fontSize, bool defaultBold, PresentationThemeConfig? themeConfig, bool isTitle = false, string? fontFamily = null)
    {
        var runs = new List<A.Run>();
        if (string.IsNullOrEmpty(text))
        {
            runs.Add(new A.Run(
                CreateRunProperties(fontSize, defaultBold, themeConfig, isTitle, false, fontFamily),
                new A.Text(EmptyTextPlaceholder)
            ));
            return runs;
        }

        // 1) Split by **bold** - process segments (alternating normal/bold)
        var boldPattern = @"\*\*(.*?)\*\*";
        var boldMatches = System.Text.RegularExpressions.Regex.Matches(text, boldPattern);
        var segments = new List<(string SegmentText, bool IsBold)>();
        int lastIdx = 0;
        foreach (System.Text.RegularExpressions.Match m in boldMatches)
        {
            if (m.Index > lastIdx)
                segments.Add((text.Substring(lastIdx, m.Index - lastIdx), false));
            segments.Add((m.Groups[1].Value, true));
            lastIdx = m.Index + m.Length;
        }
        if (lastIdx < text.Length)
            segments.Add((text.Substring(lastIdx), false));

        // 2) For each segment, parse *italic* and create runs
        foreach (var (segmentText, isBold) in segments)
        {
            var baseBold = isBold || defaultBold;
            var italicPattern = @"\*([^*]+)\*";
            var italicMatches = System.Text.RegularExpressions.Regex.Matches(segmentText, italicPattern);
            if (italicMatches.Count == 0)
            {
                if (!string.IsNullOrEmpty(segmentText))
                    runs.Add(new A.Run(
                        CreateRunProperties(fontSize, baseBold, themeConfig, isTitle, false, fontFamily),
                        CreateTextElement(segmentText)
                    ));
                continue;
            }
            int segLast = 0;
            foreach (System.Text.RegularExpressions.Match im in italicMatches)
            {
                if (im.Index > segLast)
                {
                    var normalPart = segmentText.Substring(segLast, im.Index - segLast);
                    if (!string.IsNullOrEmpty(normalPart))
                        runs.Add(new A.Run(
                            CreateRunProperties(fontSize, baseBold, themeConfig, isTitle, false, fontFamily),
                            CreateTextElement(normalPart)
                        ));
                }
                var italicPart = im.Groups[1].Value;
                runs.Add(new A.Run(
                    CreateRunProperties(fontSize, baseBold, themeConfig, isTitle, true, fontFamily),
                    CreateTextElement(italicPart)
                ));
                segLast = im.Index + im.Length;
            }
            if (segLast < segmentText.Length)
            {
                var remainder = segmentText.Substring(segLast);
                if (!string.IsNullOrEmpty(remainder))
                    runs.Add(new A.Run(
                        CreateRunProperties(fontSize, baseBold, themeConfig, isTitle, false, fontFamily),
                        CreateTextElement(remainder)
                    ));
            }
        }
        if (runs.Count == 0)
        {
            runs.Add(new A.Run(
                CreateRunProperties(fontSize, defaultBold, themeConfig, isTitle, false, fontFamily),
                CreateTextElement(text)
            ));
        }
        return runs;
    }

    public async Task<Stream> GeneratePptxFromTemplateAsync(PresentationDto presentation, string templateFilePath)
    {
        // 템플릿 파일 로드
        var templateStream = await LoadTemplateFileAsync(templateFilePath);
        if (templateStream == null)
        {
            _logger.LogWarning("Template file not found, using default generation: {TemplatePath}", templateFilePath);
            return await GeneratePptxAsync(presentation);
        }

        try
        {
            // 템플릿을 복사하여 새 스트림 생성
            var outputStream = new MemoryStream();
            await templateStream.CopyToAsync(outputStream);
            templateStream.Dispose();
            outputStream.Position = 0;

            // 템플릿 파일을 열어서 내용만 교체
            using (var templateDocument = PresentationDocument.Open(outputStream, true))
            {
                var presentationPart = templateDocument.PresentationPart;
                if (presentationPart?.Presentation?.SlideIdList == null)
                {
                    _logger.LogWarning("Invalid template structure, using default generation");
                    return await GeneratePptxAsync(presentation);
                }

                // 기존 슬라이드 제거 (선택적 - 또는 내용만 교체)
                // 여기서는 간단하게 템플릿 구조를 유지하고 내용만 업데이트
                // 실제 구현은 더 복잡할 수 있음

                presentationPart.Presentation.Save();
            }

            outputStream.Position = 0;
            return outputStream;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating PPTX from template, falling back to default");
            return await GeneratePptxAsync(presentation);
        }
    }

    private async Task<Stream?> LoadTemplateFileAsync(string templateFilePath)
    {
        try
        {
            // wwwroot 경로에서 템플릿 파일 찾기
            var wwwrootPath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot");
            var fullPath = Path.Combine(wwwrootPath, templateFilePath.TrimStart('/'));

            if (!File.Exists(fullPath))
            {
                _logger.LogWarning("Template file not found: {FullPath}", fullPath);
                return null;
            }

            var fileBytes = await File.ReadAllBytesAsync(fullPath);
            return new MemoryStream(fileBytes);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error loading template file: {TemplatePath}", templateFilePath);
            return null;
        }
    }
}
