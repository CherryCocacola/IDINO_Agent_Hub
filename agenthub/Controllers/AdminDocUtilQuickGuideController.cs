using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilQuickGuideController — DocUtil 퀵 가이드 운영자 BFF (트랙 A1 Phase B)
//
// 통합 비전:
//   DocUtil 의 `/quick-guide` 페이지는 백엔드 호출 없는 정적 콘텐츠(4개 카드 + 도움말 링크).
//   AgentHub 운영자 콘솔로 흡수 시 동일 콘텐츠를 BFF 가 자체 반환 — DocUtil 호출 0건.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//   2. 정적 콘텐츠(한국어, DocUtil 원본 그대로 4개 가이드) 반환
//   3. 캐시 불필요 (콘텐츠가 코드에 박혀 있어 매 요청 동일)
//
// 향후 확장 여지:
//   콘텐츠를 DB 화하거나 i18n 다국어 리소스로 옮기는 작업은 별도 트랙. 현재는 DocUtil 사용자
//   경험 1:1 유지가 우선 — 코드 정의가 단일 진위(source of truth).
//
// IDocUtilClient 메서드 불필요 — DocUtil 측 endpoint 자체가 존재하지 않음.
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 DocUtil 퀵 가이드 BFF — 트랙 A1 Phase B (정적 콘텐츠).
/// AgentHub Vue 콘솔의 `/admin/docutil-quick-guide` 페이지가 호출하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/docutil/quick-guide")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminDocUtilQuickGuideController : ControllerBase
{
    private readonly ILogger<AdminDocUtilQuickGuideController> _logger;

    public AdminDocUtilQuickGuideController(ILogger<AdminDocUtilQuickGuideController> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// 퀵 가이드 콘텐츠 조회.
    /// <para>DocUtil `frontend/src/app/(admin)/quick-guide/page.tsx` 의 4개 카드 정의를 그대로 반영.</para>
    /// </summary>
    [HttpGet("")]
    public ActionResult<QuickGuideContent> GetQuickGuide()
    {
        var guides = new[]
        {
            new GuideCard(
                Icon: "FileText",
                Title: "문서 업로드",
                Description: "PDF, DOCX, TXT 등 다양한 형식의 문서를 업로드하고 관리합니다.",
                Steps: new[]
                {
                    "문서 관리 메뉴로 이동",
                    "프로젝트/보드/폴더 선택",
                    "'문서 업로드' 버튼 클릭",
                    "파일 선택 후 업로드",
                }),
            new GuideCard(
                Icon: "Search",
                Title: "검색 범위 설정",
                Description: "검색할 문서의 범위를 지정하여 정확한 검색 결과를 얻습니다.",
                Steps: new[]
                {
                    "검색 범위 설정 메뉴로 이동",
                    "'새 검색 범위' 버튼 클릭",
                    "포함할 문서/폴더 선택",
                    "검색 방식 설정 후 저장",
                }),
            new GuideCard(
                Icon: "MessageSquare",
                Title: "AI 채팅",
                Description: "업로드된 문서를 기반으로 AI와 대화하며 정보를 검색합니다.",
                Steps: new[]
                {
                    "채팅 메뉴로 이동",
                    "검색 범위 선택 (선택사항)",
                    "질문 입력",
                    "AI 응답 확인 및 출처 검토",
                }),
            new GuideCard(
                Icon: "Settings",
                Title: "API 키 관리",
                Description: "LLM API 키를 등록하고 관리합니다.",
                Steps: new[]
                {
                    "API 키 메뉴로 이동",
                    "'키 등록' 버튼 클릭",
                    "LLM 제공자 선택",
                    "API 키 입력 후 등록",
                }),
        };

        var additionalHelp = new AdditionalHelp(
            Icon: "BookOpen",
            Title: "추가 도움말",
            Description: "더 자세한 사용 방법은 도움말 페이지를 참조하세요. 문제가 발생한 경우 시스템 관리자에게 문의하세요.",
            HelpUrl: "/help");

        _logger.LogDebug("운영자 DocUtil 퀵 가이드 조회 - guideCount={Count}", guides.Length);
        return Ok(new QuickGuideContent(
            Title: "퀵 가이드",
            Subtitle: "시스템 사용 방법을 빠르게 익혀보세요",
            Guides: guides,
            AdditionalHelp: additionalHelp));
    }
}

// ── 응답 DTO ────────────────────────────────────────────────────────────────

/// <summary>
/// 가이드 카드 한 장 — 아이콘/제목/설명/단계.
/// </summary>
/// <param name="Icon">lucide-react 아이콘 이름(FileText/Search/MessageSquare/Settings 등).</param>
/// <param name="Title">카드 제목(한국어).</param>
/// <param name="Description">카드 설명(한국어).</param>
/// <param name="Steps">순차 단계 설명(한국어).</param>
public sealed record GuideCard(
    string Icon,
    string Title,
    string Description,
    string[] Steps);

/// <summary>
/// 추가 도움말 섹션 — 헬프 페이지 링크.
/// </summary>
public sealed record AdditionalHelp(
    string Icon,
    string Title,
    string Description,
    string HelpUrl);

/// <summary>
/// 퀵 가이드 전체 응답.
/// </summary>
public sealed record QuickGuideContent(
    string Title,
    string Subtitle,
    GuideCard[] Guides,
    AdditionalHelp AdditionalHelp);
