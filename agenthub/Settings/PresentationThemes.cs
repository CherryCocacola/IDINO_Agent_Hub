namespace AIAgentManagement.Settings;

/// <summary>프레젠테이션 테마 정의 (Phase 2). PPTX 생성 시 색상/폰트에 사용.
/// 고급 스타일: 제목용 FontHeading, 본문용 FontBody. 재생 PC에 설치된 폰트만 표시됨(맑은 고딕/Noto Sans KR/Pretendard 등).</summary>
public static class PresentationThemes
{
    public const string Default = "default";
    public const string BusinessBlue = "business-blue";
    public const string Dark = "dark";
    public const string Minimal = "minimal";
    public const string Marketing = "marketing";
    public const string Education = "education";

    /// <summary>화면 미리보기(presentation-builder-result.css)와 동일한 색상으로 PPT에도 적용</summary>
    public static IReadOnlyList<PresentationThemeConfig> All { get; } = new List<PresentationThemeConfig>
    {
        new PresentationThemeConfig
        {
            ThemeId = Default,
            Name = "기본",
            PrimaryColor = "3730A3",
            SecondaryColor = "4338CA",
            TitleColor = "3730A3",
            BodyColor = "4338CA",
            BackgroundColor = "F5F7FF",
            BackgroundGradientEndColor = "E8EAFE",
            UseDarkBackground = false,
            FontHeading = "맑은 고딕",
            FontBody = "맑은 고딕"
        },
        new PresentationThemeConfig
        {
            ThemeId = BusinessBlue,
            Name = "비즈니스 블루",
            PrimaryColor = "FFFFFF",
            SecondaryColor = "E0E7FF",
            TitleColor = "FFFFFF",
            BodyColor = "D9D9D9",
            BackgroundColor = "1D4ED8",
            BackgroundGradientEndColor = "1E40AF",
            UseDarkBackground = true,
            FontHeading = "맑은 고딕",
            FontBody = "맑은 고딕"
        },
        new PresentationThemeConfig
        {
            ThemeId = Dark,
            Name = "다크",
            PrimaryColor = "FFFFFF",
            SecondaryColor = "D1D5DB",
            TitleColor = "FFFFFF",
            BodyColor = "D9D9D9",
            BackgroundColor = "111827",
            BackgroundGradientEndColor = "1F2937",
            UseDarkBackground = true,
            FontHeading = "맑은 고딕",
            FontBody = "맑은 고딕"
        },
        new PresentationThemeConfig
        {
            ThemeId = Minimal,
            Name = "미니멀",
            PrimaryColor = "111827",
            SecondaryColor = "374151",
            TitleColor = "111827",
            BodyColor = "374151",
            BackgroundColor = "FFFFFF",
            BackgroundGradientEndColor = null,
            UseDarkBackground = false,
            FontHeading = "Pretendard",
            FontBody = "Pretendard"
        },
        new PresentationThemeConfig
        {
            ThemeId = Marketing,
            Name = "마케팅",
            PrimaryColor = "FFFFFF",
            SecondaryColor = "FFEDD5",
            TitleColor = "FFFFFF",
            BodyColor = "D9D9D9",
            BackgroundColor = "F97316",
            BackgroundGradientEndColor = "EF4444",
            UseDarkBackground = true,
            FontHeading = "맑은 고딕",
            FontBody = "맑은 고딕"
        },
        new PresentationThemeConfig
        {
            ThemeId = Education,
            Name = "교육",
            PrimaryColor = "FFFFFF",
            SecondaryColor = "CCFBF1",
            TitleColor = "FFFFFF",
            BodyColor = "D9D9D9",
            BackgroundColor = "059669",
            BackgroundGradientEndColor = "0D9488",
            UseDarkBackground = true,
            FontHeading = "나눔고딕",
            FontBody = "나눔고딕"
        }
    };

    public static PresentationThemeConfig? Get(string? themeId)
    {
        if (string.IsNullOrEmpty(themeId)) return All.FirstOrDefault(t => t.ThemeId == Default);
        return All.FirstOrDefault(t => string.Equals(t.ThemeId, themeId, StringComparison.OrdinalIgnoreCase))
            ?? All.FirstOrDefault(t => t.ThemeId == Default);
    }
}

public class PresentationThemeConfig
{
    public string ThemeId { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string PrimaryColor { get; set; } = string.Empty;
    public string SecondaryColor { get; set; } = string.Empty;
    /// <summary>배경 단색(그라데이션 없을 때). HEX without #.</summary>
    public string BackgroundColor { get; set; } = "FFFFFF";
    /// <summary>그라데이션 끝색. null/비어있으면 단색 배경.</summary>
    public string? BackgroundGradientEndColor { get; set; }
    /// <summary>다크 배경 테마 시 텍스트를 밝게 표시.</summary>
    public bool UseDarkBackground { get; set; }
    public string FontHeading { get; set; } = "맑은 고딕";
    public string FontBody { get; set; } = "맑은 고딕";
    /// <summary>제목 글자색. HEX without #. 화면 미리보기와 동일.</summary>
    public string TitleColor { get; set; } = "3730A3";
    /// <summary>본문 글자색. HEX without #. 화면 미리보기와 동일.</summary>
    public string BodyColor { get; set; } = "4338CA";
    /// <summary>제목 폰트 크기(100분의 1pt). 화면 22px ≈ 22pt = 2200.</summary>
    public int TitleFontSize { get; set; } = 2200;
    /// <summary>본문 폰트 크기(100분의 1pt). 화면 13px ≈ 13pt = 1300.</summary>
    public int BodyFontSize { get; set; } = 1300;
    /// <summary>제목 굵기. 화면 font-weight: 800(extra bold).</summary>
    public bool TitleBold { get; set; } = true;
}
