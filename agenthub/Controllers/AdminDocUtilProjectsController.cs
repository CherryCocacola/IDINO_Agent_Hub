using System.Net;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Exceptions;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilProjectsController — DocUtil 프로젝트/보드 운영자 BFF (Phase 10.1c)
//
// 통합 비전(P1 Control Plane / P5 인증 / R2 단일 진입점):
//   AgentHub 운영자 콘솔이 DocUtil 의 프로젝트(=collection) 카탈로그 + 멤버십 +
//   부서 매핑 + 보드(KB collection 내부 권한 단위) 를 모두 단일 진입점에서 관리.
//   10.1a/10.1b 와 동일 BFF 패턴으로 운영자가 DocUtil 콘솔 별도 로그인 불필요.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//   2. TTL 캐시(`du:projects:` prefix, 10분) + version-key invalidate
//      (`docutil-collections` namespace — DocUtilClient.ListCollectionsAsync 와 통합)
//   3. DocUtil DTO → JSON camelCase 직렬화(Program.cs JsonNamingPolicy 적용)
//   4. 4xx/5xx → 502 ErrorResponseDto 한국어 매핑(InvalidOperationException 변환)
//   5. mutation(POST/PUT/DELETE) 의 성공/실패 모두 invalidate (10.1b ghost 처리 패턴 — DocUtil
//      404 ghost 보드/프로젝트가 캐시에 남아있는 일을 방지)
//
// 캐시 namespace 통합 효과(중요):
//   `docutil-collections` 는 DocUtilClient.ListCollectionsAsync(AgentBuilder dropdown UX)
//   와 본 컨트롤러의 모든 GET 캐시가 공유한다. 본 화면에서 프로젝트/보드 mutation 시
//   IncrementVersionAsync 한 번 호출 → AgentBuilder dropdown(`du:c:vN:*`) + 본 화면(`du:projects:vN:*`)
//   양쪽이 동시에 stale → 운영자는 어느 화면이든 즉시 신규 데이터 확인 가능.
//   기존 ListCollectionsAsync 시그니처/응답 형태 보존 — version 통합은 캐시 키 내부 변화일 뿐.
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 DocUtil 프로젝트/보드 관리 BFF — Phase 10.1c.
/// AgentHub Vue 콘솔의 `/admin/docutil-projects` 페이지가 호출하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/docutil")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminDocUtilProjectsController : ControllerBase
{
    // 본 컨트롤러의 자체 캐시 prefix — DocUtilClient.ListCollectionsAsync 의 `du:c:` 와 분리.
    private const string CacheKeyPrefix = "du:projects:";
    // version-key namespace — DocUtilClient.CollectionCacheVersionNamespace 와 통합(중요).
    public const string CacheVersionNamespace = DocUtilClient.CollectionCacheVersionNamespace;
    private static readonly TimeSpan CacheTtl = TimeSpan.FromMinutes(10);

    private readonly IDocUtilClient _docUtilClient;
    private readonly CachingService _cachingService;
    private readonly ILogger<AdminDocUtilProjectsController> _logger;

    public AdminDocUtilProjectsController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        ILogger<AdminDocUtilProjectsController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _logger = logger;
    }

    /// <summary>
    /// DocUtil 4xx 응답을 그대로 client status 로 전달(트랙 #101 F4 fix).
    /// <para>
    /// 이전 결함: 모든 <see cref="DocUtilUpstreamException"/> 을 <c>InvalidOperationException</c> 으로 잡아
    /// 일괄 502 변환 → 409(이미 멤버), 404(사용자/프로젝트 미존재), 400(잘못된 요청) 같은 호출자 책임
    /// 시나리오가 "외부 서버 오류" 처럼 보였다. 이제 4xx 는 그대로 전달, 5xx 만 502 폴백.
    /// </para>
    /// <para>
    /// 5xx 폴백 메시지는 호출자(컨트롤러 catch 블록)가 작업 컨텍스트에 맞춰 전달.
    /// </para>
    /// </summary>
    /// <param name="upstreamEx">DocUtilClient 가 throw 한 upstream 예외.</param>
    /// <param name="upstreamFallbackMessage">5xx/분류 불가 일 때 client 에 노출할 한국어 메시지.</param>
    private ActionResult MapDocUtilUpstreamError(
        DocUtilUpstreamException upstreamEx,
        string upstreamFallbackMessage)
    {
        var status = (int)upstreamEx.StatusCode;

        // 4xx 영역: 호출자 책임 — status 그대로 + 한국어 메시지(예외 본문) 그대로 전달.
        // (예: 409 중복 멤버, 404 미존재, 400 잘못된 요청, 422 검증 실패)
        if (status >= 400 && status < 500)
        {
            return StatusCode(status, new ErrorResponseDto(
                upstreamEx.Message,
                upstreamEx.ErrorCode,
                new { upstream = upstreamEx.Message, path = upstreamEx.Path }));
        }

        // 5xx 또는 분류 불가 — 502 폴백.
        return StatusCode(502, new ErrorResponseDto(
            upstreamFallbackMessage,
            upstreamEx.ErrorCode,
            new { upstream = upstreamEx.Message, path = upstreamEx.Path }));
    }

    /// <summary>
    /// 프로젝트/보드 캐시 + AgentBuilder dropdown 캐시 일괄 무효화 — version-key 패턴.
    /// mutation(프로젝트/보드 생성/수정/삭제) 의 성공/실패 모두 호출(10.1b ghost 정합성 보장).
    /// 실패는 swallow + 경고 로그(캐시 무효화는 best-effort, 본 mutation 자체를 죽이지 않음).
    /// </summary>
    private async Task InvalidateProjectsCacheAsync()
    {
        try
        {
            var v = await _cachingService.IncrementVersionAsync(CacheVersionNamespace);
            _logger.LogInformation("DocUtil 프로젝트/컬렉션 캐시 invalidate - newVersion={V}", v);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "DocUtil 프로젝트/컬렉션 캐시 invalidate 실패(무시)");
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 프로젝트 — GET 목록 / GET 트리 / GET 상세 / POST / PUT / DELETE
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 프로젝트 목록 조회(페이징) — DocUtil `/api/v1/projects` 위임 + TTL 캐시.
    /// </summary>
    [HttpGet("projects")]
    public async Task<ActionResult<DocUtilProjectList>> ListProjects(
        [FromQuery] int page = 1,
        [FromQuery] int size = 20,
        [FromQuery] string? search = null,
        CancellationToken ct = default)
    {
        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        // 검색어 포함 캐시 키 — 빈/미지정/공백은 동일 키.
        var searchKey = string.IsNullOrWhiteSpace(search) ? "_" : search.Trim().ToLowerInvariant();
        var cacheKey = $"{CacheKeyPrefix}v{version}:list:{page}|{size}|{searchKey}";

        var cached = await _cachingService.GetAsync<CachedProjectListDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 프로젝트 목록 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 프로젝트 목록 캐시 miss - key={Key}", cacheKey);

        try
        {
            var list = await _docUtilClient.ListProjectsAsync(page, size, search, ct);
            await _cachingService.SetAsync(cacheKey, CachedProjectListDto.From(list), CacheTtl);
            return Ok(list);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 프로젝트 목록 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 프로젝트 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 프로젝트 트리 조회 — DocUtil `/api/v1/projects/tree` 위임 + TTL 캐시.
    /// 응답: List of {id, name, boards: [...]}. 프로젝트 부모-자식 관계 없음(평면 + 보드 sub-array).
    /// </summary>
    [HttpGet("projects/tree")]
    public async Task<ActionResult<List<DocUtilProjectTreeNode>>> GetProjectTree(CancellationToken ct = default)
    {
        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{CacheKeyPrefix}v{version}:tree";

        var cached = await _cachingService.GetAsync<CachedProjectTreeDto>(cacheKey);
        if (cached?.Items != null)
        {
            _logger.LogDebug("DocUtil 프로젝트 트리 캐시 hit - key={Key}, count={Count}", cacheKey, cached.Items.Length);
            return Ok(cached.Items.ToList());
        }
        _logger.LogDebug("DocUtil 프로젝트 트리 캐시 miss - key={Key}", cacheKey);

        try
        {
            var tree = await _docUtilClient.GetProjectTreeAsync(ct);
            await _cachingService.SetAsync(cacheKey, new CachedProjectTreeDto { Items = tree.ToArray() }, CacheTtl);
            return Ok(tree);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 프로젝트 트리 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 프로젝트 트리를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 프로젝트 신규 생성 — DocUtil `/api/v1/projects` (POST). 성공 시 캐시 일괄 무효화.
    /// </summary>
    [HttpPost("projects")]
    public async Task<ActionResult<DocUtilProject>> CreateProject(
        [FromBody] DocUtilCreateProjectRequest request,
        CancellationToken ct = default)
    {
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 이름이 비어 있습니다."));
        }
        if (request.Name.Length > 255)
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 이름은 255자 이하여야 합니다."));
        }
        if (request.Description != null && request.Description.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 설명은 2000자 이하여야 합니다."));
        }

        try
        {
            var created = await _docUtilClient.CreateProjectAsync(request, ct);
            _logger.LogInformation("운영자 DocUtil 프로젝트 생성 성공 - ProjectId={Id}, Name={Name}", created.Id, created.Name);
            await InvalidateProjectsCacheAsync();
            return CreatedAtAction(nameof(GetProject), new { projectId = created.Id }, created);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 프로젝트 생성 실패 (name={Name})", request.Name);
            // 실패 시에도 invalidate — DocUtil 측 부분 commit 가능성(예: project row 생성 후 권한 row 실패)을
            // 캐시에 즉시 반영(10.1b ghost 처리 패턴).
            await InvalidateProjectsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "프로젝트 생성에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 프로젝트 상세 조회 — DocUtil `/api/v1/projects/{project_id}` 위임 + TTL 캐시.
    /// 404 응답은 NotFound + 한국어 ErrorResponseDto 로 정규화.
    /// </summary>
    [HttpGet("projects/{projectId}")]
    public async Task<ActionResult<DocUtilProject>> GetProject(string projectId, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 식별자가 비어 있습니다."));
        }

        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{CacheKeyPrefix}v{version}:detail:{projectId}";

        var cached = await _cachingService.GetAsync<CachedProjectDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 프로젝트 상세 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 프로젝트 상세 캐시 miss - key={Key}", cacheKey);

        try
        {
            var project = await _docUtilClient.GetProjectAsync(projectId, ct);
            if (project == null)
            {
                return NotFound(ErrorResponseDto.NotFound("프로젝트를 찾을 수 없습니다."));
            }
            await _cachingService.SetAsync(cacheKey, CachedProjectDto.From(project), CacheTtl);
            return Ok(project);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 프로젝트 상세 조회 실패 (id={Id})", projectId);
            return StatusCode(502, new ErrorResponseDto(
                "프로젝트 상세를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 프로젝트 수정 — DocUtil `/api/v1/projects/{project_id}` (PUT). 성공 시 캐시 일괄 무효화.
    /// DocUtil ProjectUpdate schema: name? + description? — allow_original_download 미존재(추정 금지).
    /// </summary>
    [HttpPut("projects/{projectId}")]
    public async Task<ActionResult<DocUtilProject>> UpdateProject(
        string projectId,
        [FromBody] DocUtilUpdateProjectRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 식별자가 비어 있습니다."));
        }
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (request.Name is null && request.Description is null)
        {
            return BadRequest(ErrorResponseDto.BadRequest(
                "변경할 필드를 하나 이상 지정해 주세요(name / description)."));
        }
        if (request.Name != null && (request.Name.Length == 0 || request.Name.Length > 255))
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 이름은 1~255자여야 합니다."));
        }
        if (request.Description != null && request.Description.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 설명은 2000자 이하여야 합니다."));
        }

        try
        {
            var updated = await _docUtilClient.UpdateProjectAsync(projectId, request, ct);
            _logger.LogInformation("운영자 DocUtil 프로젝트 수정 성공 - ProjectId={Id}", updated.Id);
            await InvalidateProjectsCacheAsync();
            return Ok(updated);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 프로젝트 수정 실패 (id={Id})", projectId);
            await InvalidateProjectsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "프로젝트 수정에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 프로젝트 삭제 — DocUtil `/api/v1/projects/{project_id}` (DELETE).
    /// <para>성공/실패 모두 invalidate(10.1b ghost 처리 패턴 — 404 로 사라진 프로젝트가 캐시에 남는 회귀 방지).</para>
    /// </summary>
    [HttpDelete("projects/{projectId}")]
    public async Task<IActionResult> DeleteProject(string projectId, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 식별자가 비어 있습니다."));
        }

        try
        {
            await _docUtilClient.DeleteProjectAsync(projectId, ct);
            _logger.LogInformation("운영자 DocUtil 프로젝트 삭제 성공 - ProjectId={Id}", projectId);
            await InvalidateProjectsCacheAsync();
            return NoContent();
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 프로젝트 삭제 실패 (id={Id})", projectId);
            await InvalidateProjectsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "프로젝트 삭제에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 프로젝트 멤버 / 부서 — GET (read-only)
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 프로젝트 멤버 조회 — DocUtil `/api/v1/projects/{project_id}/members` 위임 + TTL 캐시.
    /// </summary>
    [HttpGet("projects/{projectId}/members")]
    public async Task<ActionResult<List<DocUtilProjectMember>>> GetProjectMembers(
        string projectId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 식별자가 비어 있습니다."));
        }

        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{CacheKeyPrefix}v{version}:members:{projectId}";

        var cached = await _cachingService.GetAsync<CachedProjectMemberListDto>(cacheKey);
        if (cached?.Items != null)
        {
            _logger.LogDebug("DocUtil 프로젝트 멤버 캐시 hit - key={Key}, count={Count}", cacheKey, cached.Items.Length);
            return Ok(cached.Items.ToList());
        }
        _logger.LogDebug("DocUtil 프로젝트 멤버 캐시 miss - key={Key}", cacheKey);

        try
        {
            var members = await _docUtilClient.GetProjectMembersAsync(projectId, ct);
            await _cachingService.SetAsync(cacheKey, new CachedProjectMemberListDto { Items = members.ToArray() }, CacheTtl);
            return Ok(members);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 프로젝트 멤버 조회 실패 (id={Id})", projectId);
            return StatusCode(502, new ErrorResponseDto(
                "프로젝트 멤버 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 프로젝트 멤버 추가 — DocUtil `/api/v1/projects/{project_id}/members` (POST) 위임 (트랙 #101 F8).
    /// 성공/실패 모두 캐시 일괄 무효화(10.1b ghost 처리 패턴 — 부분 commit/409 회복 보장).
    /// </summary>
    /// <remarks>
    /// 외부 표면 body: { userId: UUID, role?: "member"|"manager" (default "member") }.
    /// DocUtil 측 검증:
    ///   - 409 — 중복 매핑 (이미 멤버)
    ///   - 404 — 프로젝트 또는 사용자 미존재
    ///   - 400 — role 화이트리스트 위반
    /// </remarks>
    [HttpPost("projects/{projectId}/members")]
    public async Task<ActionResult<DocUtilProjectMember>> AddProjectMember(
        string projectId,
        [FromBody] AddProjectMemberRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 식별자가 비어 있습니다."));
        }
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(request.UserId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("사용자 식별자가 비어 있습니다."));
        }

        // role 화이트리스트 사전 검증 — DocUtil 400 사전 차단 + 한국어 안내.
        var role = string.IsNullOrWhiteSpace(request.Role) ? "member" : request.Role.Trim().ToLowerInvariant();
        var allowedRoles = new[] { "member", "manager" };
        if (!allowedRoles.Contains(role))
        {
            return BadRequest(ErrorResponseDto.BadRequest(
                $"허용되지 않는 역할입니다. (허용: {string.Join(", ", allowedRoles)})"));
        }

        try
        {
            var docUtilRequest = new DocUtilAddProjectMemberRequest(request.UserId, role);
            var member = await _docUtilClient.AddProjectMemberAsync(projectId, docUtilRequest, ct);

            _logger.LogInformation(
                "운영자 DocUtil 프로젝트 멤버 추가 성공 - ProjectId={Pid}, UserId={Uid}, Role={Role}",
                projectId, request.UserId, role);

            await InvalidateProjectsCacheAsync();
            return StatusCode(StatusCodes.Status201Created, member);
        }
        catch (DocUtilUpstreamException upstreamEx)
        {
            // 트랙 #101 F4 fix: 4xx 그대로 전달(409 중복/404 미존재/400 잘못된 요청). 5xx 만 502.
            _logger.LogWarning(upstreamEx,
                "DocUtil 프로젝트 멤버 추가 upstream {Status} (projectId={Pid}, userId={Uid})",
                (int)upstreamEx.StatusCode, projectId, request.UserId);
            await InvalidateProjectsCacheAsync();

            // 409 Conflict — 이미 멤버. UI 친화 메시지로 명시 대체.
            if (upstreamEx.StatusCode == HttpStatusCode.Conflict)
            {
                return Conflict(new ErrorResponseDto(
                    "이미 프로젝트에 등록된 사용자입니다.",
                    upstreamEx.ErrorCode,
                    new { upstream = upstreamEx.Message, path = upstreamEx.Path }));
            }
            // 404 Not Found — 프로젝트 또는 사용자 미존재.
            if (upstreamEx.StatusCode == HttpStatusCode.NotFound)
            {
                return NotFound(new ErrorResponseDto(
                    "프로젝트 또는 사용자를 찾을 수 없습니다.",
                    upstreamEx.ErrorCode,
                    new { upstream = upstreamEx.Message, path = upstreamEx.Path }));
            }
            return MapDocUtilUpstreamError(upstreamEx, "프로젝트 멤버 추가에 실패했습니다.");
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex,
                "DocUtil 프로젝트 멤버 추가 실패 (projectId={Pid}, userId={Uid})",
                projectId, request.UserId);
            await InvalidateProjectsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "프로젝트 멤버 추가에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 프로젝트 멤버 제거 — DocUtil `/api/v1/projects/{project_id}/members/{user_id}` (DELETE) 위임 (트랙 #101 F8).
    /// 성공/실패 모두 캐시 일괄 무효화(ghost 회복 보장).
    /// </summary>
    [HttpDelete("projects/{projectId}/members/{userId}")]
    public async Task<IActionResult> RemoveProjectMember(
        string projectId,
        string userId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 식별자가 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(userId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("사용자 식별자가 비어 있습니다."));
        }

        try
        {
            await _docUtilClient.RemoveProjectMemberAsync(projectId, userId, ct);

            _logger.LogInformation(
                "운영자 DocUtil 프로젝트 멤버 제거 성공 - ProjectId={Pid}, UserId={Uid}",
                projectId, userId);

            await InvalidateProjectsCacheAsync();
            return NoContent();
        }
        catch (DocUtilUpstreamException upstreamEx)
        {
            // 트랙 #101 F4 fix: 4xx 그대로 전달(404 미존재 등). 5xx 만 502.
            _logger.LogWarning(upstreamEx,
                "DocUtil 프로젝트 멤버 제거 upstream {Status} (projectId={Pid}, userId={Uid})",
                (int)upstreamEx.StatusCode, projectId, userId);
            await InvalidateProjectsCacheAsync();
            return MapDocUtilUpstreamError(upstreamEx, "프로젝트 멤버 제거에 실패했습니다.");
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex,
                "DocUtil 프로젝트 멤버 제거 실패 (projectId={Pid}, userId={Uid})",
                projectId, userId);
            await InvalidateProjectsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "프로젝트 멤버 제거에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 프로젝트 참여 부서 조회 — DocUtil `/api/v1/projects/{project_id}/departments` 위임 + TTL 캐시.
    /// </summary>
    [HttpGet("projects/{projectId}/departments")]
    public async Task<ActionResult<List<DocUtilProjectDepartment>>> GetProjectDepartments(
        string projectId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 식별자가 비어 있습니다."));
        }

        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{CacheKeyPrefix}v{version}:departments:{projectId}";

        var cached = await _cachingService.GetAsync<CachedProjectDepartmentListDto>(cacheKey);
        if (cached?.Items != null)
        {
            _logger.LogDebug("DocUtil 프로젝트 부서 캐시 hit - key={Key}, count={Count}", cacheKey, cached.Items.Length);
            return Ok(cached.Items.ToList());
        }
        _logger.LogDebug("DocUtil 프로젝트 부서 캐시 miss - key={Key}", cacheKey);

        try
        {
            var depts = await _docUtilClient.GetProjectDepartmentsAsync(projectId, ct);
            await _cachingService.SetAsync(cacheKey, new CachedProjectDepartmentListDto { Items = depts.ToArray() }, CacheTtl);
            return Ok(depts);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 프로젝트 부서 조회 실패 (id={Id})", projectId);
            return StatusCode(502, new ErrorResponseDto(
                "프로젝트 부서 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 보드 — GET 목록 / POST / GET 상세 / PUT / DELETE
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 프로젝트 내 보드 목록 — DocUtil `/api/v1/projects/{project_id}/boards` 위임 + TTL 캐시.
    /// </summary>
    [HttpGet("projects/{projectId}/boards")]
    public async Task<ActionResult<DocUtilBoardList>> ListProjectBoards(
        string projectId,
        [FromQuery] int page = 1,
        [FromQuery] int size = 50,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 식별자가 비어 있습니다."));
        }

        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{CacheKeyPrefix}v{version}:boards:{projectId}|{page}|{size}";

        var cached = await _cachingService.GetAsync<CachedBoardListDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 보드 목록 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 보드 목록 캐시 miss - key={Key}", cacheKey);

        try
        {
            var list = await _docUtilClient.ListProjectBoardsAsync(projectId, page, size, ct);
            await _cachingService.SetAsync(cacheKey, CachedBoardListDto.From(list), CacheTtl);
            return Ok(list);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보드 목록 조회 실패 (projectId={Id})", projectId);
            return StatusCode(502, new ErrorResponseDto(
                "보드 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 보드 신규 생성 — DocUtil `/api/v1/projects/{project_id}/boards` (POST). 성공 시 캐시 일괄 무효화.
    /// </summary>
    [HttpPost("projects/{projectId}/boards")]
    public async Task<ActionResult<DocUtilBoard>> CreateProjectBoard(
        string projectId,
        [FromBody] DocUtilCreateBoardRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 식별자가 비어 있습니다."));
        }
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            return BadRequest(ErrorResponseDto.BadRequest("보드 이름이 비어 있습니다."));
        }
        if (request.Name.Length > 255)
        {
            return BadRequest(ErrorResponseDto.BadRequest("보드 이름은 255자 이하여야 합니다."));
        }
        if (request.Description != null && request.Description.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("보드 설명은 2000자 이하여야 합니다."));
        }

        try
        {
            var created = await _docUtilClient.CreateProjectBoardAsync(projectId, request, ct);
            _logger.LogInformation(
                "운영자 DocUtil 보드 생성 성공 - ProjectId={Pid}, BoardId={Id}, Name={Name}",
                projectId, created.Id, created.Name);
            await InvalidateProjectsCacheAsync();
            return CreatedAtAction(nameof(GetProjectBoard),
                new { projectId, boardId = created.Id }, created);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보드 생성 실패 (projectId={Pid}, name={Name})", projectId, request.Name);
            await InvalidateProjectsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "보드 생성에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 보드 상세 조회 — DocUtil `/api/v1/projects/{project_id}/boards/{board_id}` 위임 + TTL 캐시.
    /// 404 응답은 NotFound + 한국어 ErrorResponseDto 로 정규화.
    /// </summary>
    [HttpGet("projects/{projectId}/boards/{boardId}")]
    public async Task<ActionResult<DocUtilBoard>> GetProjectBoard(
        string projectId,
        string boardId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 식별자가 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(boardId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("보드 식별자가 비어 있습니다."));
        }

        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{CacheKeyPrefix}v{version}:board:{projectId}:{boardId}";

        var cached = await _cachingService.GetAsync<CachedBoardDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 보드 상세 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 보드 상세 캐시 miss - key={Key}", cacheKey);

        try
        {
            var board = await _docUtilClient.GetProjectBoardAsync(projectId, boardId, ct);
            if (board == null)
            {
                return NotFound(ErrorResponseDto.NotFound("보드를 찾을 수 없습니다."));
            }
            await _cachingService.SetAsync(cacheKey, CachedBoardDto.From(board), CacheTtl);
            return Ok(board);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보드 상세 조회 실패 (projectId={Pid}, boardId={Bid})", projectId, boardId);
            return StatusCode(502, new ErrorResponseDto(
                "보드 상세를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 보드 수정 — DocUtil `/api/v1/projects/{project_id}/boards/{board_id}` (PUT). 성공 시 캐시 일괄 무효화.
    /// </summary>
    [HttpPut("projects/{projectId}/boards/{boardId}")]
    public async Task<ActionResult<DocUtilBoard>> UpdateProjectBoard(
        string projectId,
        string boardId,
        [FromBody] DocUtilUpdateBoardRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 식별자가 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(boardId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("보드 식별자가 비어 있습니다."));
        }
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (request.Name is null && request.Description is null)
        {
            return BadRequest(ErrorResponseDto.BadRequest(
                "변경할 필드를 하나 이상 지정해 주세요(name / description)."));
        }
        if (request.Name != null && (request.Name.Length == 0 || request.Name.Length > 255))
        {
            return BadRequest(ErrorResponseDto.BadRequest("보드 이름은 1~255자여야 합니다."));
        }
        if (request.Description != null && request.Description.Length > 2000)
        {
            return BadRequest(ErrorResponseDto.BadRequest("보드 설명은 2000자 이하여야 합니다."));
        }

        try
        {
            var updated = await _docUtilClient.UpdateProjectBoardAsync(projectId, boardId, request, ct);
            _logger.LogInformation(
                "운영자 DocUtil 보드 수정 성공 - ProjectId={Pid}, BoardId={Id}",
                projectId, updated.Id);
            await InvalidateProjectsCacheAsync();
            return Ok(updated);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보드 수정 실패 (projectId={Pid}, boardId={Bid})", projectId, boardId);
            await InvalidateProjectsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "보드 수정에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 보드 삭제 — DocUtil `/api/v1/projects/{project_id}/boards/{board_id}` (DELETE).
    /// <para>성공/실패 모두 invalidate(10.1b ghost 처리 패턴).</para>
    /// </summary>
    [HttpDelete("projects/{projectId}/boards/{boardId}")]
    public async Task<IActionResult> DeleteProjectBoard(
        string projectId,
        string boardId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("프로젝트 식별자가 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(boardId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("보드 식별자가 비어 있습니다."));
        }

        try
        {
            await _docUtilClient.DeleteProjectBoardAsync(projectId, boardId, ct);
            _logger.LogInformation(
                "운영자 DocUtil 보드 삭제 성공 - ProjectId={Pid}, BoardId={Id}",
                projectId, boardId);
            await InvalidateProjectsCacheAsync();
            return NoContent();
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보드 삭제 실패 (projectId={Pid}, boardId={Bid})", projectId, boardId);
            await InvalidateProjectsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "보드 삭제에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ── 캐시 wrapper (record 직렬화 안정성을 위한 명시적 클래스) ───────────
    // record 도 직렬화 가능하나, IDistributedCache 의 generic 직렬화는 폴리모피즘에서
    // 깨지는 사례가 있어 명시적 class wrapper 권장(10.1b 와 동일 패턴).

    private sealed class CachedProjectDto
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string? Description { get; set; }
        public bool AllowOriginalDownload { get; set; }
        public string OrganizationId { get; set; } = string.Empty;
        public string CreatedBy { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }

        public static CachedProjectDto From(DocUtilProject p) => new()
        {
            Id = p.Id,
            Name = p.Name,
            Description = p.Description,
            AllowOriginalDownload = p.AllowOriginalDownload,
            OrganizationId = p.OrganizationId,
            CreatedBy = p.CreatedBy,
            CreatedAt = p.CreatedAt,
            UpdatedAt = p.UpdatedAt,
        };

        public DocUtilProject ToRecord() => new(
            Id, Name, Description, AllowOriginalDownload, OrganizationId, CreatedBy, CreatedAt, UpdatedAt);
    }

    private sealed class CachedProjectListDto
    {
        public CachedProjectDto[] Items { get; set; } = Array.Empty<CachedProjectDto>();
        public long Total { get; set; }
        public int Page { get; set; }
        public int Size { get; set; }

        public static CachedProjectListDto From(DocUtilProjectList l) => new()
        {
            Items = l.Items.Select(CachedProjectDto.From).ToArray(),
            Total = l.Total,
            Page = l.Page,
            Size = l.Size,
        };

        public DocUtilProjectList ToRecord() => new(
            Items.Select(c => c.ToRecord()).ToArray(),
            Total,
            Page,
            Size);
    }

    private sealed class CachedProjectTreeDto
    {
        public DocUtilProjectTreeNode[]? Items { get; set; }
    }

    private sealed class CachedProjectMemberListDto
    {
        public DocUtilProjectMember[]? Items { get; set; }
    }

    private sealed class CachedProjectDepartmentListDto
    {
        public DocUtilProjectDepartment[]? Items { get; set; }
    }

    private sealed class CachedBoardDto
    {
        public string Id { get; set; } = string.Empty;
        public string ProjectId { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string? Description { get; set; }
        public string CreatedBy { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }

        public static CachedBoardDto From(DocUtilBoard b) => new()
        {
            Id = b.Id,
            ProjectId = b.ProjectId,
            Name = b.Name,
            Description = b.Description,
            CreatedBy = b.CreatedBy,
            CreatedAt = b.CreatedAt,
            UpdatedAt = b.UpdatedAt,
        };

        public DocUtilBoard ToRecord() => new(
            Id, ProjectId, Name, Description, CreatedBy, CreatedAt, UpdatedAt);
    }

    private sealed class CachedBoardListDto
    {
        public CachedBoardDto[] Items { get; set; } = Array.Empty<CachedBoardDto>();
        public long Total { get; set; }
        public int Page { get; set; }
        public int Size { get; set; }

        public static CachedBoardListDto From(DocUtilBoardList l) => new()
        {
            Items = l.Items.Select(CachedBoardDto.From).ToArray(),
            Total = l.Total,
            Page = l.Page,
            Size = l.Size,
        };

        public DocUtilBoardList ToRecord() => new(
            Items.Select(c => c.ToRecord()).ToArray(),
            Total,
            Page,
            Size);
    }
}

/// <summary>
/// 프로젝트 멤버 추가 요청 DTO (트랙 #101 F8).
/// 외부 표면(camelCase): { userId: UUID, role?: "member"|"manager" }.
/// </summary>
public sealed class AddProjectMemberRequest
{
    /// <summary>추가할 사용자 UUID.</summary>
    public string UserId { get; set; } = string.Empty;

    /// <summary>역할 — "member" 또는 "manager" (기본 "member").</summary>
    public string? Role { get; set; }
}
