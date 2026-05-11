using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilDepartmentsController — DocUtil 조직/부서/할당량 운영자 BFF (Phase 10.1b)
//
// 통합 비전(P1 Control Plane / P5 인증 / R2 단일 진입점):
//   AgentHub 운영자 콘솔이 DocUtil 의 조직 메타 + 부서 트리 + 월 할당량을 관리하는
//   단일 진입점이다. 10.1a 의 사용자 트랙(AdminDocUtilUsersController)과 같은 BFF
//   패턴을 그대로 적용 — 운영자가 DocUtil 콘솔에 별도 로그인하지 않아도 됨.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//   2. TTL 캐시(`du:depts:` prefix, 10분) + version-key invalidate (`docutil-departments` namespace)
//      - 부서는 사용자보다 변경 빈도 낮음 → TTL 5분 → 10분 으로 길게.
//      - 할당량은 변동 잦으므로 캐시 미적용(매 호출 fresh).
//   3. DocUtil DTO → JSON camelCase 직렬화(Program.cs JsonNamingPolicy 적용)
//   4. 4xx/5xx → 502 ErrorResponseDto 한국어 매핑(InvalidOperationException 변환)
//
// 책임 범위 밖:
//   - org_id 추출(IDocUtilTokenProvider 가 처리, DocUtilClient 가 호출)
//   - DocUtil 인증 토큰 부착(DocUtilClient 가 처리)
//   - 한국어 에러 매핑 1차 변환(DocUtilClient 가 InvalidOperationException 으로 통일)
//
// 캐시 전략:
//   - 키 패턴(부서 목록): `du:depts:v{N}:list`
//   - 키 패턴(부서 멤버): `du:depts:v{N}:members:{deptId}`
//   - 10분 TTL (부서 변경 빈도 낮음)
//   - mutation 성공(부서 생성/수정/삭제 / 조직 정보 수정) 후 IncrementVersionAsync 호출 →
//     이전 버전 prefix 의 모든 키가 자동으로 stale 처리됨
//   - 할당량(GET/PUT) 은 캐시 미적용 — 차감 로직이 백엔드에서 잦으므로 fresh 우선.
//
// 향후 트랙(10.1c):
//   - AdminDocUtilProjectsController — 프로젝트 멤버십 / 프로젝트 보드(KB collection) 권한
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 DocUtil 조직/부서/할당량 관리 BFF — Phase 10.1b.
/// AgentHub Vue 콘솔의 `/admin/docutil-departments` 페이지가 호출하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/docutil")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminDocUtilDepartmentsController : ControllerBase
{
    private const string CacheKeyPrefix = "du:depts:";
    public const string CacheVersionNamespace = "docutil-departments";
    private static readonly TimeSpan CacheTtl = TimeSpan.FromMinutes(10);

    private readonly IDocUtilClient _docUtilClient;
    private readonly CachingService _cachingService;
    private readonly ILogger<AdminDocUtilDepartmentsController> _logger;

    public AdminDocUtilDepartmentsController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        ILogger<AdminDocUtilDepartmentsController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _logger = logger;
    }

    /// <summary>
    /// 부서 캐시 일괄 무효화 — version-key 패턴.
    /// mutation(부서 생성/수정/삭제 / 조직 정보 수정) 성공 후 호출.
    /// 실패는 swallow + 경고 로그(캐시 무효화는 best-effort, 본 mutation 자체를 죽이지 않음).
    /// </summary>
    private async Task InvalidateDepartmentsCacheAsync()
    {
        try
        {
            var v = await _cachingService.IncrementVersionAsync(CacheVersionNamespace);
            _logger.LogInformation("DocUtil 부서/조직 캐시 invalidate - newVersion={V}", v);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "DocUtil 부서/조직 캐시 invalidate 실패(무시)");
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 조직 정보 — GET / PUT
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 조직 정보 조회 — DocUtil `/api/v1/organizations/{org_id}` 위임 + TTL 캐시.
    /// </summary>
    [HttpGet("organization")]
    public async Task<ActionResult<DocUtilOrganization>> GetOrganization(CancellationToken ct = default)
    {
        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{CacheKeyPrefix}v{version}:org";

        var cached = await _cachingService.GetAsync<CachedOrganizationDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 조직 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 조직 캐시 miss - key={Key}", cacheKey);

        try
        {
            var org = await _docUtilClient.GetOrganizationAsync(ct);
            if (org == null)
            {
                return NotFound(ErrorResponseDto.NotFound("DocUtil 조직 정보를 찾을 수 없습니다."));
            }

            await _cachingService.SetAsync(cacheKey, CachedOrganizationDto.From(org), CacheTtl);
            return Ok(org);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 조직 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 조직 정보를 불러오지 못했습니다. DocUtil 서비스 상태를 확인하세요.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 조직 정보 수정 — DocUtil `/api/v1/organizations/{org_id}` (PUT).
    /// 성공 시 캐시 일괄 무효화.
    /// </summary>
    [HttpPut("organization")]
    public async Task<ActionResult<DocUtilOrganization>> UpdateOrganization(
        [FromBody] DocUtilUpdateOrganizationRequest request,
        CancellationToken ct = default)
    {
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }

        // 모든 필드 nullable — 적어도 하나는 지정해야 의미 있음.
        if (request.Name is null && request.Description is null && request.Settings is null)
        {
            return BadRequest(ErrorResponseDto.BadRequest(
                "변경할 필드를 하나 이상 지정해 주세요(name / description / settings)."));
        }

        try
        {
            var updated = await _docUtilClient.UpdateOrganizationAsync(request, ct);
            _logger.LogInformation("운영자 DocUtil 조직 수정 성공 - OrgId={Id}", updated.Id);
            await InvalidateDepartmentsCacheAsync();
            return Ok(updated);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 조직 수정 실패");
            // 실패 시에도 invalidate — 5xx 중간 단절 시 부분 변경이 발생했을 수 있어,
            // 캐시가 DocUtil 실제 상태와 어긋나지 않도록 안전 차원에서 무효화.
            // (DeleteDepartment 와 동일 일관 패턴)
            await InvalidateDepartmentsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 조직 정보 수정에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 부서 — GET / POST / PUT / DELETE / GET members
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 부서 목록 조회 — DocUtil `/api/v1/organizations/{org_id}/departments` 위임 + TTL 캐시.
    /// </summary>
    [HttpGet("departments")]
    public async Task<ActionResult<List<DocUtilDepartment>>> ListDepartments(CancellationToken ct = default)
    {
        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{CacheKeyPrefix}v{version}:list";

        var cached = await _cachingService.GetAsync<CachedDepartmentListDto>(cacheKey);
        if (cached?.Items != null)
        {
            _logger.LogDebug("DocUtil 부서 목록 캐시 hit - key={Key}, count={Count}", cacheKey, cached.Items.Length);
            return Ok(cached.Items.ToList());
        }
        _logger.LogDebug("DocUtil 부서 목록 캐시 miss - key={Key}", cacheKey);

        try
        {
            var depts = await _docUtilClient.ListDepartmentsAsync(ct);
            await _cachingService.SetAsync(cacheKey, new CachedDepartmentListDto { Items = depts.ToArray() }, CacheTtl);
            return Ok(depts);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 부서 목록 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 부서 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 부서 생성 — DocUtil `/api/v1/organizations/{org_id}/departments` (POST).
    /// 성공 시 캐시 일괄 무효화.
    /// </summary>
    [HttpPost("departments")]
    public async Task<ActionResult<DocUtilDepartment>> CreateDepartment(
        [FromBody] DocUtilCreateDepartmentRequest request,
        CancellationToken ct = default)
    {
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            return BadRequest(ErrorResponseDto.BadRequest("부서 이름이 비어 있습니다."));
        }

        try
        {
            var created = await _docUtilClient.CreateDepartmentAsync(request, ct);
            _logger.LogInformation("운영자 DocUtil 부서 생성 성공 - DeptId={Id}, Name={Name}", created.Id, created.Name);
            await InvalidateDepartmentsCacheAsync();
            return CreatedAtAction(nameof(ListDepartments), new { }, created);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 부서 생성 실패 (name={Name})", request.Name);
            // 실패 시에도 invalidate — 5xx 중간 단절 시 부분 생성된 부서가 DocUtil 측에
            // 남아있을 수 있어(예: 트랜잭션 실패 전 row 생성), 다음 GET 에서 그것이 즉시
            // 반영되도록 캐시 무효화.
            await InvalidateDepartmentsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "부서 생성에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 부서 수정 — DocUtil `/api/v1/organizations/{org_id}/departments/{dept_id}` (PUT).
    /// 성공 시 캐시 일괄 무효화.
    /// </summary>
    [HttpPut("departments/{deptId}")]
    public async Task<ActionResult<DocUtilDepartment>> UpdateDepartment(
        string deptId,
        [FromBody] DocUtilUpdateDepartmentRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(deptId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("부서 식별자가 비어 있습니다."));
        }
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (request.Name is null && request.ParentId is null)
        {
            return BadRequest(ErrorResponseDto.BadRequest(
                "변경할 필드를 하나 이상 지정해 주세요(name / parent_id)."));
        }

        try
        {
            var updated = await _docUtilClient.UpdateDepartmentAsync(deptId, request, ct);
            _logger.LogInformation("운영자 DocUtil 부서 수정 성공 - DeptId={Id}", updated.Id);
            await InvalidateDepartmentsCacheAsync();
            return Ok(updated);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 부서 수정 실패 (id={Id})", deptId);
            // 실패 시에도 invalidate — 5xx 중간 단절 시 부분 변경이 발생했을 수 있어,
            // 캐시가 DocUtil 실제 상태와 어긋나지 않도록 안전 차원에서 무효화.
            await InvalidateDepartmentsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "부서 수정에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 부서 삭제 — DocUtil `/api/v1/organizations/{org_id}/departments/{dept_id}` (DELETE).
    /// <para>
    /// 캐시 무효화는 성공/실패 모두 수행한다. 실패(예: 404 = 이미 DocUtil 측에서 삭제됨,
    /// 409 = 자식 부서 존재) 의 경우 AgentHub 캐시가 DocUtil 의 실제 상태와 어긋날 수
    /// 있으므로(DocUtil 에 없는 부서가 캐시에 남아있는 ghost), 안전을 위해 invalidate.
    /// </para>
    /// </summary>
    [HttpDelete("departments/{deptId}")]
    public async Task<IActionResult> DeleteDepartment(string deptId, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(deptId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("부서 식별자가 비어 있습니다."));
        }

        try
        {
            await _docUtilClient.DeleteDepartmentAsync(deptId, ct);
            _logger.LogInformation("운영자 DocUtil 부서 삭제 성공 - DeptId={Id}", deptId);
            await InvalidateDepartmentsCacheAsync();
            return NoContent();
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 부서 삭제 실패 (id={Id})", deptId);
            // 실패 시에도 invalidate — DocUtil 측 상태 변동 가능성(예: 404 로 사라진 부서)을
            // 캐시에 즉시 반영하여 ghost 부서가 GET 응답에 남는 일이 없도록 한다.
            await InvalidateDepartmentsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "부서 삭제에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 부서 멤버 조회 — DocUtil `/api/v1/organizations/{org_id}/departments/{dept_id}/members` 위임 + TTL 캐시.
    /// </summary>
    [HttpGet("departments/{deptId}/members")]
    public async Task<ActionResult<List<DocUtilDepartmentMember>>> GetDepartmentMembers(
        string deptId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(deptId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("부서 식별자가 비어 있습니다."));
        }

        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{CacheKeyPrefix}v{version}:members:{deptId}";

        var cached = await _cachingService.GetAsync<CachedMemberListDto>(cacheKey);
        if (cached?.Items != null)
        {
            _logger.LogDebug("DocUtil 부서 멤버 캐시 hit - key={Key}, count={Count}", cacheKey, cached.Items.Length);
            return Ok(cached.Items.ToList());
        }
        _logger.LogDebug("DocUtil 부서 멤버 캐시 miss - key={Key}", cacheKey);

        try
        {
            var members = await _docUtilClient.GetDepartmentMembersAsync(deptId, ct);
            await _cachingService.SetAsync(cacheKey, new CachedMemberListDto { Items = members.ToArray() }, CacheTtl);
            return Ok(members);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 부서 멤버 조회 실패 (id={Id})", deptId);
            return StatusCode(502, new ErrorResponseDto(
                "부서 멤버 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 할당량 — GET / PUT (캐시 미적용)
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 조직 월 할당량 현황 조회 — DocUtil `/api/v1/organizations/{org_id}/quotas/current` 위임.
    /// 캐시 미적용 — 차감 로직 잦으므로 매 호출 fresh.
    /// </summary>
    [HttpGet("organization/quota")]
    public async Task<ActionResult<DocUtilOrganizationQuotaCurrent>> GetOrganizationQuota(CancellationToken ct = default)
    {
        try
        {
            var quota = await _docUtilClient.GetOrganizationQuotaAsync(ct);
            return Ok(quota);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 조직 할당량 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 조직 할당량을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 조직 월 할당량 한도 수정 — DocUtil `/api/v1/organizations/{org_id}/quotas/{quota_type}` (PUT).
    /// 캐시 미적용 — 변경 즉시 GET 응답에 반영.
    /// </summary>
    [HttpPut("organization/quota/{quotaType}")]
    public async Task<ActionResult<DocUtilOrganizationQuotaStatus>> UpdateOrganizationQuota(
        string quotaType,
        [FromBody] DocUtilUpdateQuotaRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(quotaType))
        {
            return BadRequest(ErrorResponseDto.BadRequest("quota_type 이 비어 있습니다."));
        }
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (request.MonthlyLimit < 0)
        {
            return BadRequest(ErrorResponseDto.BadRequest(
                "monthly_limit 은 0 이상의 정수여야 합니다."));
        }

        try
        {
            var updated = await _docUtilClient.UpdateOrganizationQuotaAsync(quotaType, request, ct);
            _logger.LogInformation(
                "운영자 DocUtil 할당량 수정 성공 - QuotaType={Type}, MonthlyLimit={Limit}",
                quotaType, request.MonthlyLimit);
            return Ok(updated);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 할당량 수정 실패 (type={Type})", quotaType);
            return StatusCode(502, new ErrorResponseDto(
                "할당량 수정에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ── 캐시 wrapper (record 직렬화 안정성을 위한 명시적 클래스) ───────────
    private sealed class CachedOrganizationDto
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string Slug { get; set; } = string.Empty;
        public string? Description { get; set; }
        public object? Settings { get; set; }
        public DateTime CreatedAt { get; set; }

        public static CachedOrganizationDto From(DocUtilOrganization o) => new()
        {
            Id = o.Id,
            Name = o.Name,
            Slug = o.Slug,
            Description = o.Description,
            Settings = o.Settings,
            CreatedAt = o.CreatedAt,
        };

        public DocUtilOrganization ToRecord() => new(Id, Name, Slug, Description, Settings, CreatedAt);
    }

    private sealed class CachedDepartmentListDto
    {
        public DocUtilDepartment[]? Items { get; set; }
    }

    private sealed class CachedMemberListDto
    {
        public DocUtilDepartmentMember[]? Items { get; set; }
    }
}
