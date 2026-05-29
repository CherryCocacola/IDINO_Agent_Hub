using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;
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
    private readonly AIAgentManagementDbContext _db;
    private readonly ILogger<AdminDocUtilDepartmentsController> _logger;

    public AdminDocUtilDepartmentsController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        AIAgentManagementDbContext db,
        ILogger<AdminDocUtilDepartmentsController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _db = db;
        _logger = logger;
    }

    // ──────────────────────────────────────────────────────────────────────
    // 트랙 #106 (2026-05-20) — 부서 GET 메서드를 AgentHub `Departments` 마스터 직접 쿼리로 전환.
    // DocUtil `tb_departments` (9건) 는 AgentHub `Departments` (32건) 와 fork 상태로
    // AgentHub `Users.DepartmentId` 와 매핑 불가 → 부서별 인원 0명 표시 결함 해소.
    // 사용자 결정: AgentHub 단일 마스터 (R&D센터, Si 1~8팀, 개발사업팀 등 32 부서).
    // mutation(POST/PUT/DELETE) 은 본 트랙 범위 외 — DocUtil 위임 유지.
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// AgentHub `Departments` 행 + 트리 정보를 DocUtil 응답 호환 `DocUtilDepartment` 로 매핑한다.
    /// Vue 화면(`AdminDocUtilDepartments.vue`) 호환성:
    ///   - `id` = `DepartmentId` 정수의 문자열(Vue 는 string key 만 사용).
    ///   - `parentId` = `ParentDepartmentId?.ToString()`.
    ///   - `depth` / `path` = 본 메서드 호출 직전 계산된 값(materialized path 패턴).
    ///   - `organizationId` = `Tenant.TenantCode` (or empty) — DocUtil 의 org UUID 와 의미 호환.
    /// </summary>
    private static DocUtilDepartment MapDepartmentToDto(
        Department d,
        int depth,
        string path,
        string organizationId)
    {
        return new DocUtilDepartment(
            Id: d.DepartmentId.ToString(),
            OrganizationId: organizationId,
            ParentId: d.ParentDepartmentId?.ToString(),
            Name: d.DepartmentName,
            Depth: depth,
            Path: path,
            CreatedAt: d.CreatedAt);
    }

    /// <summary>
    /// 평탄 부서 리스트에서 (DepartmentId → depth, path) 트리 좌표를 계산한다.
    /// path 는 "/{id}/{childId}/..." 형식의 materialized path — Vue 의 path 사전 정렬과 호환.
    /// 순환 참조는 최대 깊이 16 으로 강제 차단(application-level 검증 — 실측 발생 시 로그).
    /// </summary>
    private static Dictionary<int, (int depth, string path)> BuildTreeCoords(IReadOnlyList<Department> all)
    {
        var byId = all.ToDictionary(d => d.DepartmentId);
        var result = new Dictionary<int, (int, string)>();

        (int depth, string path) ResolveOne(int id)
        {
            if (result.TryGetValue(id, out var cached)) return cached;
            if (!byId.TryGetValue(id, out var dept))
            {
                // 부모가 비활성/누락 — 자신을 루트로 처리.
                var fallback = (0, $"/{id}/");
                result[id] = fallback;
                return fallback;
            }
            if (dept.ParentDepartmentId is null || !byId.ContainsKey(dept.ParentDepartmentId.Value))
            {
                var rootCoord = (0, $"/{id}/");
                result[id] = rootCoord;
                return rootCoord;
            }
            var parent = ResolveOne(dept.ParentDepartmentId.Value);
            if (parent.depth >= 16)
            {
                // 순환 또는 비정상 — 즉시 차단.
                var bail = (parent.depth + 1, parent.path + id + "/");
                result[id] = bail;
                return bail;
            }
            var coord = (parent.depth + 1, parent.path + id + "/");
            result[id] = coord;
            return coord;
        }

        foreach (var d in all)
        {
            ResolveOne(d.DepartmentId);
        }
        return result;
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
            // 트랙 #106 — AgentHub Tenant 마스터 직접 조회(단일 조직 가정).
            // 다중 Tenant 환경 도래 시 본 endpoint 는 별도 query 파라미터(tenantId)로 확장 필요.
            var tenant = await _db.Tenants
                .AsNoTracking()
                .Where(t => t.IsActive)
                .OrderBy(t => t.TenantId)
                .FirstOrDefaultAsync(ct);
            if (tenant == null)
            {
                return NotFound(ErrorResponseDto.NotFound("조직 정보를 찾을 수 없습니다."));
            }

            var org = new DocUtilOrganization(
                Id: tenant.TenantCode,
                Name: tenant.TenantName,
                Slug: tenant.TenantCode,
                Description: tenant.Description,
                Settings: null,
                CreatedAt: tenant.CreatedAt);

            await _cachingService.SetAsync(cacheKey, CachedOrganizationDto.From(org), CacheTtl);
            return Ok(org);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "AgentHub 조직 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "조직 정보를 불러오지 못했습니다.",
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
            // 트랙 #106 — AgentHub Departments 마스터 직접 쿼리. 32 부서 전체 + 트리 매핑.
            var raw = await _db.Departments
                .AsNoTracking()
                .Where(d => d.IsActive)
                .OrderBy(d => d.DepartmentId)
                .ToListAsync(ct);

            var coords = BuildTreeCoords(raw);

            // organizationId 는 첫 번째 부서의 Tenant code 로 통일(단일 조직 가정 — 트랙 #106 범위).
            // 다중 Tenant 시 별도 트랙에서 분기 필요.
            string orgId = string.Empty;
            if (raw.Count > 0)
            {
                var firstTenantId = raw[0].TenantId;
                var tenant = await _db.Tenants
                    .AsNoTracking()
                    .FirstOrDefaultAsync(t => t.TenantId == firstTenantId, ct);
                orgId = tenant?.TenantCode ?? firstTenantId.ToString();
            }

            var depts = raw
                .Select(d =>
                {
                    var (depth, path) = coords.GetValueOrDefault(d.DepartmentId, (0, $"/{d.DepartmentId}/"));
                    return MapDepartmentToDto(d, depth, path, orgId);
                })
                .OrderBy(d => d.Path, StringComparer.Ordinal)
                .ToList();

            await _cachingService.SetAsync(cacheKey, new CachedDepartmentListDto { Items = depts.ToArray() }, CacheTtl);

            _logger.LogInformation(
                "AgentHub Departments 직접 쿼리 - count={Count}, orgId={OrgId}",
                depts.Count, orgId);

            return Ok(depts);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "AgentHub 부서 목록 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "부서 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 부서 생성 — AgentHub `Departments` 직접 INSERT (트랙 #125, 2026-05-27).
    /// <para>
    /// 트랙 A1 Phase D 에서 DocUtil `departments/router.py` 자체가 폐지됨 →
    /// 이전 DocUtil 위임 호출이 upstream 404 → 502. 트랙 #122 (UpdateUser) 와 동일
    /// 패턴으로 AgentHub 단일 SOT 직접 INSERT 전환.
    /// </para>
    /// <para>
    /// 매핑: request.Name → DepartmentName, request.ParentId (UUID/int 둘 다 수용) →
    /// ParentDepartmentId. TenantId 는 첫 활성 Tenant (단일 조직 가정 — ListDepartments
    /// 와 동일). DepartmentCode 는 name slug + 6자리 GUID 접미사로 자동 생성 (DB UNIQUE).
    /// OriginalDocutilUuid 는 NewGuid() 부여 (DocUtil ORM 호환 유지 — tb_departments VIEW
    /// 가 이 컬럼을 id 로 alias).
    /// </para>
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
            // parentId 정규화 — UUID 면 OriginalDocutilUuid 조회 → DepartmentId 변환.
            // int 면 직접 DepartmentId. 빈 문자열/null 이면 최상위 부서(parent 없음).
            int? parentDeptId = null;
            if (!string.IsNullOrWhiteSpace(request.ParentId))
            {
                if (Guid.TryParse(request.ParentId, out var parentUuid))
                {
                    var parent = await _db.Departments
                        .FirstOrDefaultAsync(d => d.OriginalDocutilUuid == parentUuid && d.IsActive, ct);
                    if (parent == null)
                    {
                        return BadRequest(ErrorResponseDto.BadRequest(
                            $"상위 부서를 찾을 수 없습니다(parentId={request.ParentId})."));
                    }
                    parentDeptId = parent.DepartmentId;
                }
                else if (int.TryParse(request.ParentId, out var parentIdInt))
                {
                    var exists = await _db.Departments
                        .AnyAsync(d => d.DepartmentId == parentIdInt && d.IsActive, ct);
                    if (!exists)
                    {
                        return BadRequest(ErrorResponseDto.BadRequest(
                            $"상위 부서를 찾을 수 없습니다(parentId={request.ParentId})."));
                    }
                    parentDeptId = parentIdInt;
                }
                else
                {
                    return BadRequest(ErrorResponseDto.BadRequest(
                        $"상위 부서 식별자 형식이 올바르지 않습니다(parentId={request.ParentId})."));
                }
            }

            // 첫 활성 Tenant — ListDepartments 와 동일 단일 조직 가정.
            var tenant = await _db.Tenants
                .AsNoTracking()
                .Where(t => t.IsActive)
                .OrderBy(t => t.TenantId)
                .FirstOrDefaultAsync(ct);
            if (tenant == null)
            {
                return StatusCode(500, new ErrorResponseDto(
                    "활성 조직(Tenant)이 없습니다.", "TENANT_MISSING", null));
            }

            // DepartmentCode 자동 생성 — name 기반 slug 가 UNIQUE 보장 어려워 GUID 접미사 부여.
            // 형식: "dept-{6자리}" — 운영 가독성 무관(외부 노출용 식별자, name 으로 표시됨).
            var codeSuffix = Guid.NewGuid().ToString("N").Substring(0, 6);
            var deptCode = $"dept-{codeSuffix}";

            var newDept = new Department
            {
                DepartmentCode = deptCode,
                DepartmentName = request.Name.Trim(),
                TenantId = tenant.TenantId,
                ParentDepartmentId = parentDeptId,
                IsActive = true,
                OriginalDocutilUuid = Guid.NewGuid(),
                CreatedAt = DateTime.UtcNow,
            };
            _db.Departments.Add(newDept);
            await _db.SaveChangesAsync(ct);

            _logger.LogInformation(
                "AgentHub 부서 생성 성공 - DeptId={Id}, Name={Name}, ParentId={Parent}",
                newDept.DepartmentId, newDept.DepartmentName, parentDeptId);
            await InvalidateDepartmentsCacheAsync();

            // 응답 — DocUtilDepartment 호환(Vue 화면 spec). depth/path 는 신규 단일 부서이므로 0/$"/id/".
            var depth = parentDeptId.HasValue ? 1 : 0;
            var path = parentDeptId.HasValue
                ? $"/{parentDeptId.Value}/{newDept.DepartmentId}/"
                : $"/{newDept.DepartmentId}/";
            var created = MapDepartmentToDto(newDept, depth, path, tenant.TenantCode);
            return CreatedAtAction(nameof(ListDepartments), new { }, created);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "AgentHub 부서 생성 실패 (name={Name})", request.Name);
            await InvalidateDepartmentsCacheAsync();
            return StatusCode(500, new ErrorResponseDto(
                "부서 생성에 실패했습니다.",
                "DEPARTMENT_CREATE_ERROR",
                new { error = ex.Message }));
        }
    }

    /// <summary>
    /// 부서 수정 — AgentHub `Departments` 직접 UPDATE (트랙 #125, 2026-05-27).
    /// CreateDepartment 와 동일 사유 — DocUtil 위임 폐지. partial update (name/parentId).
    /// deptId: UUID (OriginalDocutilUuid) / int (DepartmentId) 모두 수용.
    /// parentId: "" / null (해제) / int / UUID 모두 수용.
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
            Department? dept = null;
            if (Guid.TryParse(deptId, out var deptUuid))
            {
                dept = await _db.Departments
                    .FirstOrDefaultAsync(d => d.OriginalDocutilUuid == deptUuid && d.IsActive, ct);
            }
            else if (int.TryParse(deptId, out var deptIdInt))
            {
                dept = await _db.Departments
                    .FirstOrDefaultAsync(d => d.DepartmentId == deptIdInt && d.IsActive, ct);
            }
            if (dept == null)
            {
                return NotFound(ErrorResponseDto.NotFound($"부서를 찾을 수 없습니다(id={deptId})."));
            }

            if (request.Name is not null)
            {
                var trimmed = request.Name.Trim();
                if (string.IsNullOrWhiteSpace(trimmed))
                {
                    return BadRequest(ErrorResponseDto.BadRequest("부서 이름이 비어 있습니다."));
                }
                dept.DepartmentName = trimmed;
            }

            if (request.ParentId is not null)
            {
                // 빈 문자열 = parent 해제(최상위로 이동).
                if (string.IsNullOrWhiteSpace(request.ParentId))
                {
                    dept.ParentDepartmentId = null;
                }
                else
                {
                    int? parentDeptId;
                    if (Guid.TryParse(request.ParentId, out var parentUuid))
                    {
                        var parent = await _db.Departments
                            .FirstOrDefaultAsync(d => d.OriginalDocutilUuid == parentUuid && d.IsActive, ct);
                        if (parent == null)
                        {
                            return BadRequest(ErrorResponseDto.BadRequest(
                                $"상위 부서를 찾을 수 없습니다(parentId={request.ParentId})."));
                        }
                        parentDeptId = parent.DepartmentId;
                    }
                    else if (int.TryParse(request.ParentId, out var parentIdInt))
                    {
                        var exists = await _db.Departments
                            .AnyAsync(d => d.DepartmentId == parentIdInt && d.IsActive, ct);
                        if (!exists)
                        {
                            return BadRequest(ErrorResponseDto.BadRequest(
                                $"상위 부서를 찾을 수 없습니다(parentId={request.ParentId})."));
                        }
                        parentDeptId = parentIdInt;
                    }
                    else
                    {
                        return BadRequest(ErrorResponseDto.BadRequest(
                            $"상위 부서 식별자 형식이 올바르지 않습니다(parentId={request.ParentId})."));
                    }
                    // 자기 자신을 parent 로 지정 차단.
                    if (parentDeptId == dept.DepartmentId)
                    {
                        return BadRequest(ErrorResponseDto.BadRequest(
                            "자기 자신을 상위 부서로 지정할 수 없습니다."));
                    }
                    dept.ParentDepartmentId = parentDeptId;
                }
            }

            dept.UpdatedAt = DateTime.UtcNow;
            await _db.SaveChangesAsync(ct);

            _logger.LogInformation(
                "AgentHub 부서 수정 성공 - DeptId={Id}, Name={Name}, ParentId={Parent}",
                dept.DepartmentId, dept.DepartmentName, dept.ParentDepartmentId);
            await InvalidateDepartmentsCacheAsync();

            // 응답 — depth/path 재계산 (수정된 트리 좌표 반영).
            var allActive = await _db.Departments.AsNoTracking()
                .Where(d => d.IsActive).ToListAsync(ct);
            var coords = BuildTreeCoords(allActive);
            var (depth, path) = coords.GetValueOrDefault(dept.DepartmentId, (0, $"/{dept.DepartmentId}/"));
            var tenantCode = (await _db.Tenants.AsNoTracking()
                .FirstOrDefaultAsync(t => t.TenantId == dept.TenantId, ct))?.TenantCode ?? string.Empty;
            return Ok(MapDepartmentToDto(dept, depth, path, tenantCode));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "AgentHub 부서 수정 실패 (id={Id})", deptId);
            await InvalidateDepartmentsCacheAsync();
            return StatusCode(500, new ErrorResponseDto(
                "부서 수정에 실패했습니다.",
                "DEPARTMENT_UPDATE_ERROR",
                new { error = ex.Message }));
        }
    }

    /// <summary>
    /// 부서 삭제 — AgentHub `Departments` soft-delete (트랙 #125, 2026-05-27).
    /// CreateDepartment/UpdateDepartment 와 동일 사유 — DocUtil 위임 폐지.
    /// soft-delete (IsActive = false) — User.DepartmentId FK 보존, 자식 부서 존재 시 409.
    /// deptId: UUID / int 모두 수용.
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
            Department? dept = null;
            if (Guid.TryParse(deptId, out var deptUuid))
            {
                dept = await _db.Departments
                    .FirstOrDefaultAsync(d => d.OriginalDocutilUuid == deptUuid && d.IsActive, ct);
            }
            else if (int.TryParse(deptId, out var deptIdInt))
            {
                dept = await _db.Departments
                    .FirstOrDefaultAsync(d => d.DepartmentId == deptIdInt && d.IsActive, ct);
            }
            if (dept == null)
            {
                return NotFound(ErrorResponseDto.NotFound($"부서를 찾을 수 없습니다(id={deptId})."));
            }

            // 자식 부서 존재 시 차단.
            var hasChildren = await _db.Departments
                .AnyAsync(d => d.ParentDepartmentId == dept.DepartmentId && d.IsActive, ct);
            if (hasChildren)
            {
                return Conflict(new ErrorResponseDto(
                    "하위 부서가 존재하여 삭제할 수 없습니다. 하위 부서를 먼저 정리하세요.",
                    "DEPARTMENT_HAS_CHILDREN",
                    new { departmentId = dept.DepartmentId }));
            }

            // 소속 사용자 존재 시 차단(운영자에게 명시적 정리 요구).
            var hasUsers = await _db.Users
                .AnyAsync(u => u.DepartmentId == dept.DepartmentId && !u.IsDeleted, ct);
            if (hasUsers)
            {
                return Conflict(new ErrorResponseDto(
                    "소속 사용자가 존재하여 삭제할 수 없습니다. 멤버를 먼저 다른 부서로 이동하세요.",
                    "DEPARTMENT_HAS_MEMBERS",
                    new { departmentId = dept.DepartmentId }));
            }

            dept.IsActive = false;
            dept.UpdatedAt = DateTime.UtcNow;
            await _db.SaveChangesAsync(ct);

            _logger.LogInformation("AgentHub 부서 삭제(soft) 성공 - DeptId={Id}", dept.DepartmentId);
            await InvalidateDepartmentsCacheAsync();
            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "AgentHub 부서 삭제 실패 (id={Id})", deptId);
            await InvalidateDepartmentsCacheAsync();
            return StatusCode(500, new ErrorResponseDto(
                "부서 삭제에 실패했습니다.",
                "DEPARTMENT_DELETE_ERROR",
                new { error = ex.Message }));
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

        // 트랙 #123 (2026-05-27): 부서 멤버 list cache 제거 — mutation→GET 정합성 보장.
        // 원인: 사용자가 멤버 제거 (UpdateUser DepartmentId 변경) 시 AdminDocUtilUsersController
        // 가 `docutil-users` namespace 만 invalidate. 본 컨트롤러는 `docutil-departments`
        // namespace cache 사용 → cross-namespace invalidate 누락 → 멤버 list 가 stale.
        // 트랙 #113 (프로젝트 멤버) 와 정합: cache 제거 = 정합성 > 성능 trade-off 정당
        // (호출 빈도 낮음 + DB query 빠름, AgentHub Users 직접 read).
        try
        {
            // 트랙 #106 — AgentHub Users 직접 조회. deptId 는 int 문자열(Departments.DepartmentId).
            if (!int.TryParse(deptId, out var deptIdInt))
            {
                // 호환성 — 과거 호출자가 UUID 를 넘기던 경우 빈 목록 반환(에러 대신 graceful empty).
                _logger.LogWarning("부서 멤버 조회 - deptId 가 정수 형식이 아님: {DeptId} (UUID 등 deprecated 형식)", deptId);
                return Ok(new List<DocUtilDepartmentMember>());
            }

            var users = await _db.Users
                .AsNoTracking()
                .Where(u => u.DepartmentId == deptIdInt && !u.IsDeleted)
                .OrderBy(u => u.UserId)
                .ToListAsync(ct);

            var topRoles = new Dictionary<int, string?>();
            if (users.Count > 0)
            {
                var userIds = users.Select(u => u.UserId).ToList();
                var roleRows = await _db.UserRoles
                    .AsNoTracking()
                    .Where(ur => userIds.Contains(ur.UserId))
                    .Include(ur => ur.Role)
                    .ToListAsync(ct);
                topRoles = roleRows
                    .GroupBy(ur => ur.UserId)
                    .ToDictionary(
                        g => g.Key,
                        g => (string?)g.OrderBy(ur => ur.RoleId).First().Role?.RoleName);
            }

            // 트랙 #109 (2026-05-26): username 우선순위 = FullName (한글) → DocutilUsername (영문 prefix) → Email.
            // AdminDocUtilUsersController.MapUserToSummary 와 일치 — 두 화면이 동일 user 에 같은 이름 표시.
            var members = users
                .Select(u => new DocUtilDepartmentMember(
                    Id: u.OriginalDocutilUuid?.ToString() ?? u.UserId.ToString(),
                    Username: !string.IsNullOrWhiteSpace(u.FullName)
                        ? u.FullName!
                        : (!string.IsNullOrWhiteSpace(u.DocutilUsername) ? u.DocutilUsername : u.Email),
                    Email: u.Email,
                    Role: (topRoles.GetValueOrDefault(u.UserId) ?? "member").ToLowerInvariant()))
                .ToList();

            _logger.LogInformation(
                "AgentHub 부서별 멤버 직접 쿼리 (cache 미사용) - deptId={DeptId}, count={Count}",
                deptIdInt, members.Count);

            return Ok(members);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "AgentHub 부서 멤버 조회 실패 (id={Id})", deptId);
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
