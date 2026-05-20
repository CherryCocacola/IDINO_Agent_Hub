using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Exceptions;
using AIAgentManagement.Models;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilUsersController — DocUtil 사용자 운영자 BFF (Phase 10.1a, 2026-05-10)
//
// 통합 비전(P1 Control Plane / P5 인증 / R2 단일 진입점):
//   AgentHub 운영자 콘솔이 DocUtil 사용자 카탈로그를 관리하는 단일 진입점이다.
//   IDocUtilClient.{ListUsers,GetUser,UpdateUserStatus,DeleteUser}Async 4 메서드를
//   운영자(`Admin` / `SuperAdmin`) 권한 게이트와 함께 외부 표면에 노출하는
//   forwarding + TTL 캐시 + version-key invalidate 레이어다.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//   2. TTL 캐시(`du:users:` prefix, 5분) + version-key invalidate (`docutil-users` namespace)
//   3. DocUtil DTO → JSON camelCase 직렬화(Program.cs JsonNamingPolicy 적용)
//   4. 4xx/5xx → 502 ErrorResponseDto 한국어 매핑(InvalidOperationException 변환)
//
// 책임 범위 밖:
//   - org_id 추출(IDocUtilTokenProvider 가 처리)
//   - DocUtil 인증 토큰 부착(DocUtilClient 가 처리)
//   - 한국어 에러 매핑 1차 변환(DocUtilClient 가 InvalidOperationException 으로 통일)
//
// 캐시 전략:
//   - 키 패턴: `du:users:v{N}:{page}|{size}|{role}|{status}|{searchHash}`
//   - 5분 TTL (운영자 콘솔 워크플로 — 검색/페이지 이동이 잦지 않으므로 적정)
//   - mutation 성공(상태 변경/삭제) 후 IncrementVersionAsync("docutil-users") 호출 →
//     이전 버전 prefix 의 모든 키가 자동으로 stale 처리됨
//
// 향후 트랙(10.1b/10.1c):
//   - 10.1b: AdminDocUtilDepartmentsController — 부서 카탈로그 + dropdown 필터 합성
//   - 10.1c: AdminDocUtilProjectsController — 프로젝트 멤버십 / RAG collection 권한
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 DocUtil 사용자 관리 BFF — Phase 10.1a.
/// AgentHub Vue 콘솔의 `/admin/docutil-users` 페이지가 호출하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/docutil")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminDocUtilUsersController : ControllerBase
{
    private const string CacheKeyPrefix = "du:users:";
    public const string CacheVersionNamespace = "docutil-users";
    private static readonly TimeSpan CacheTtl = TimeSpan.FromMinutes(5);

    private readonly IDocUtilClient _docUtilClient;
    private readonly CachingService _cachingService;
    private readonly AIAgentManagementDbContext _db;
    private readonly ILogger<AdminDocUtilUsersController> _logger;

    public AdminDocUtilUsersController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        AIAgentManagementDbContext db,
        ILogger<AdminDocUtilUsersController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _db = db;
        _logger = logger;
    }

    // ──────────────────────────────────────────────────────────────────────
    // 트랙 #106 (2026-05-20) — GET 메서드를 AgentHub `Users` 마스터 직접 쿼리로 전환.
    // DocUtil 위임 시 부서/조직 매핑이 깨지는 문제 해결:
    //   - DocUtil `tb_users` VIEW 의 `department_id` 가 NULL::uuid 로 하드코딩되어
    //     AgentHub 32 부서 중 어디에도 매핑 불가 → 부서별 멤버 0명 표시.
    //   - 사용자 결정: `tb_users` 폐기, AgentHub `Users` + `Departments` 단일 마스터.
    // mutation(PUT/DELETE) 은 본 트랙 범위 외 — DocUtil 위임 유지(별도 트랙 처리 예정).
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// AgentHub `Users` 행을 DocUtil 응답 호환 `DocUtilUserSummary` 로 매핑한다.
    /// Vue 화면(`AdminDocUtilUsers.vue`) 호환성:
    ///   - `id` 는 DocUtil UUID 우선(`OriginalDocutilUuid`), 없으면 `userId` 문자열.
    ///   - `username` 은 `DocutilUsername` 우선(영문 short — 트랙 #99 fix), 없으면 `FullName`.
    ///   - `role` 은 `UserRoles` 의 최고 권한 RoleName 소문자(없으면 "member").
    ///   - `status` 는 Active/Inactive/Locked → 소문자 변환(DocUtil 표준 enum 호환).
    ///   - `departmentId` 는 AgentHub int FK 를 문자열로 직렬화(Vue 는 string 키만 사용).
    /// </summary>
    private static DocUtilUserSummary MapUserToSummary(User u, string? roleName)
    {
        var statusLower = string.IsNullOrEmpty(u.Status)
            ? "active"
            : u.Status.ToLowerInvariant();
        return new DocUtilUserSummary(
            Id: u.OriginalDocutilUuid?.ToString() ?? u.UserId.ToString(),
            Username: !string.IsNullOrWhiteSpace(u.DocutilUsername)
                ? u.DocutilUsername!
                : (!string.IsNullOrWhiteSpace(u.FullName) ? u.FullName : u.Email),
            Email: u.Email,
            Role: string.IsNullOrWhiteSpace(roleName) ? "member" : roleName.ToLowerInvariant(),
            Status: statusLower,
            OrganizationId: u.OrganizationId?.ToString() ?? string.Empty,
            DepartmentId: u.DepartmentId?.ToString(),
            Language: u.Language,
            LastLoginAt: u.LastLoginAt,
            CreatedAt: u.CreatedAt);
    }

    private static DocUtilUserDetail MapUserToDetail(User u, string? roleName)
    {
        var s = MapUserToSummary(u, roleName);
        return new DocUtilUserDetail(
            s.Id, s.Username, s.Email, s.Role, s.Status,
            s.OrganizationId, s.DepartmentId, s.Language, s.LastLoginAt, s.CreatedAt);
    }

    /// <summary>
    /// 다중 사용자에 대한 최상위 RoleName 을 한 번의 LEFT JOIN 쿼리로 dict 화한다.
    /// N+1 회피 — 페이지당 1 쿼리.
    /// </summary>
    private async Task<Dictionary<int, string?>> LoadTopRolesAsync(
        IReadOnlyCollection<int> userIds,
        CancellationToken ct)
    {
        if (userIds.Count == 0) return new();
        // RoleId 가 낮을수록 상위 권한이라고 가정(시드 순서 — SuperAdmin=1, Admin=2 등).
        // 동일 사용자 다중 Role 시 RoleId 최소값의 RoleName 채택.
        var grouped = await _db.UserRoles
            .AsNoTracking()
            .Where(ur => userIds.Contains(ur.UserId))
            .Include(ur => ur.Role)
            .ToListAsync(ct);
        return grouped
            .GroupBy(ur => ur.UserId)
            .ToDictionary(
                g => g.Key,
                g => (string?)g.OrderBy(ur => ur.RoleId).First().Role?.RoleName);
    }

    /// <summary>
    /// DocUtil 사용자 캐시 일괄 무효화 — version-key 패턴.
    /// mutation(상태 변경 / 삭제) 성공 후 호출. 실패는 swallow + 경고 로그
    /// (캐시 무효화는 best-effort, 본 mutation 자체를 죽이지 않음).
    /// </summary>
    private async Task InvalidateUsersCacheAsync()
    {
        try
        {
            var v = await _cachingService.IncrementVersionAsync(CacheVersionNamespace);
            _logger.LogInformation("DocUtil 사용자 캐시 invalidate - newVersion={V}", v);
        }
        catch (Exception ex)
        {
            // best-effort — mutation 응답을 막지 않는다.
            _logger.LogWarning(ex, "DocUtil 사용자 캐시 invalidate 실패(무시)");
        }
    }

    /// <summary>
    /// 사용자 목록 캐시 키 — version + page/size/role/status/searchHash 조합.
    /// search 는 SHA256 short hex 로 정규화하여 키 길이 제한 + 한글 안전.
    /// </summary>
    private static string BuildListCacheKey(long version, int page, int size, string? role, string? status, string? search)
    {
        var searchToken = string.IsNullOrWhiteSpace(search) ? string.Empty : ShortHash(search);
        var roleToken = role ?? string.Empty;
        var statusToken = status ?? string.Empty;
        return $"{CacheKeyPrefix}v{version}:{page}|{size}|{roleToken}|{statusToken}|{searchToken}";
    }

    private static string ShortHash(string s)
    {
        var bytes = System.Text.Encoding.UTF8.GetBytes(s.Trim().ToLowerInvariant());
        var hash = System.Security.Cryptography.SHA256.HashData(bytes);
        return Convert.ToHexString(hash, 0, 8);
    }

    /// <summary>
    /// 사용자 목록 조회 — DocUtil `/api/v1/users` 위임 + TTL 캐시.
    /// </summary>
    /// <remarks>
    /// 권한: Admin / SuperAdmin (컨트롤러 레벨 [Authorize] 상속). Bearer JWT 미부착 시 401.
    /// 502: DocUtil 접근 실패 — 한국어 ErrorResponseDto 응답.
    /// </remarks>
    [HttpGet("users")]
    public async Task<ActionResult<DocUtilUserList>> ListUsers(
        [FromQuery] int page = 1,
        [FromQuery] int size = 20,
        [FromQuery] string? role = null,
        [FromQuery] string? status = null,
        [FromQuery] string? search = null,
        CancellationToken ct = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 100) size = 20;

        // ── 캐시 조회 ─────────────────────────────────────────────────────
        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = BuildListCacheKey(version, page, size, role, status, search);

        var cached = await _cachingService.GetAsync<CachedUserListDto>(cacheKey);
        if (cached?.Items != null)
        {
            _logger.LogDebug(
                "DocUtil 사용자 캐시 hit - key={Key}, count={Count}",
                cacheKey, cached.Items.Length);
            return Ok(new DocUtilUserList(cached.Items, cached.Total, cached.Page, cached.Size));
        }
        _logger.LogDebug("DocUtil 사용자 캐시 miss - key={Key}", cacheKey);

        try
        {
            // 트랙 #106 — AgentHub Users 마스터 직접 쿼리. DocUtil VIEW 미사용.
            var query = _db.Users.AsNoTracking().Where(u => !u.IsDeleted);

            // status 필터 (active/inactive/locked) — AgentHub `Users.Status` 비교는 대소문자 무시.
            if (!string.IsNullOrWhiteSpace(status))
            {
                var statusLower = status.Trim().ToLowerInvariant();
                query = query.Where(u => u.Status.ToLower() == statusLower);
            }

            // search 필터 — email / FullName / DocutilUsername ILIKE.
            if (!string.IsNullOrWhiteSpace(search))
            {
                var pattern = $"%{search.Trim()}%";
                query = query.Where(u =>
                    EF.Functions.ILike(u.Email, pattern)
                    || (u.FullName != null && EF.Functions.ILike(u.FullName, pattern))
                    || (u.DocutilUsername != null && EF.Functions.ILike(u.DocutilUsername, pattern)));
            }

            // role 필터 — UserRoles join. RoleId 최소값(상위 권한)이 query role 과 일치.
            if (!string.IsNullOrWhiteSpace(role))
            {
                var roleLower = role.Trim().ToLowerInvariant();
                query = query.Where(u => _db.UserRoles
                    .Where(ur => ur.UserId == u.UserId)
                    .Join(_db.Roles, ur => ur.RoleId, r => r.RoleId, (ur, r) => r.RoleName)
                    .Any(rn => rn.ToLower() == roleLower));
            }

            var total = await query.LongCountAsync(ct);
            var paged = await query
                .OrderBy(u => u.UserId)
                .Skip((page - 1) * size)
                .Take(size)
                .ToListAsync(ct);

            // 최상위 role 한 번에 조회 (N+1 회피).
            var topRoles = await LoadTopRolesAsync(paged.Select(u => u.UserId).ToList(), ct);

            var items = paged
                .Select(u => MapUserToSummary(u, topRoles.GetValueOrDefault(u.UserId)))
                .ToArray();

            var result = new DocUtilUserList(items, total, page, size);

            // ── 캐시 적재 ─────────────────────────────────────────────
            await _cachingService.SetAsync(cacheKey, new CachedUserListDto
            {
                Items = result.Items,
                Total = result.Total,
                Page = result.Page,
                Size = result.Size,
            }, CacheTtl);

            _logger.LogInformation(
                "AgentHub Users 직접 쿼리 - total={Total}, page={Page}/{Size}, returned={Count}",
                total, page, size, items.Length);

            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "AgentHub 사용자 목록 조회 실패 (page={Page}, size={Size}, role={Role}, status={Status})",
                page, size, role, status);
            return StatusCode(502, new ErrorResponseDto(
                "사용자 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 사용자 상세 조회 — DocUtil `/api/v1/users/{id}` 위임.
    /// </summary>
    [HttpGet("users/{id}")]
    public async Task<ActionResult<DocUtilUserDetail>> GetUser(string id, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            return BadRequest(ErrorResponseDto.BadRequest("사용자 식별자가 비어 있습니다."));
        }

        try
        {
            // 트랙 #106 — AgentHub Users 직접 조회. id 가 UUID 형식이면 OriginalDocutilUuid 매칭,
            // 정수 문자열이면 UserId 매칭 — 둘 다 시도하여 견고성 확보.
            User? user = null;
            if (Guid.TryParse(id, out var guidId))
            {
                user = await _db.Users.AsNoTracking()
                    .FirstOrDefaultAsync(u => u.OriginalDocutilUuid == guidId && !u.IsDeleted, ct);
            }
            if (user == null && int.TryParse(id, out var intId))
            {
                user = await _db.Users.AsNoTracking()
                    .FirstOrDefaultAsync(u => u.UserId == intId && !u.IsDeleted, ct);
            }
            if (user == null)
            {
                return NotFound(ErrorResponseDto.NotFound("해당 사용자를 찾을 수 없습니다."));
            }
            var topRoles = await LoadTopRolesAsync(new[] { user.UserId }, ct);
            var detail = MapUserToDetail(user, topRoles.GetValueOrDefault(user.UserId));
            return Ok(detail);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "AgentHub 사용자 상세 조회 실패 (id={Id})", id);
            return StatusCode(502, new ErrorResponseDto(
                "사용자 상세를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 사용자 일반 정보 수정 — DocUtil `/api/v1/users/{id}` (PUT) 위임 (트랙 #101 F7).
    /// 성공/실패 모두 캐시 일괄 무효화 — 부분 commit 가능성 대비(10.1b ghost 처리 패턴).
    /// </summary>
    /// <remarks>
    /// 외부 표면 body: { email?, role?, departmentId?, language?, status? } — partial update.
    /// 모든 필드 nullable. status 가 포함되면 DocUtil 측에서 active/inactive/locked 검증.
    /// </remarks>
    [HttpPut("users/{id}")]
    public async Task<ActionResult<DocUtilUserDetail>> UpdateUser(
        string id,
        [FromBody] UpdateDocUtilUserRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            return BadRequest(ErrorResponseDto.BadRequest("사용자 식별자가 비어 있습니다."));
        }
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }

        // 모든 필드 nullable 이지만 최소 한 개는 있어야 의미가 있다.
        var hasAnyField =
            request.Email is not null
            || request.Role is not null
            || request.DepartmentId is not null
            || request.Language is not null
            || request.Status is not null;
        if (!hasAnyField)
        {
            return BadRequest(ErrorResponseDto.BadRequest(
                "변경할 필드를 하나 이상 지정해 주세요(email/role/departmentId/language/status)."));
        }

        // status 가 포함되었으면 화이트리스트 사전 검증 (DocUtil 422 사전 차단).
        if (request.Status is not null)
        {
            var allowed = new[] { "active", "inactive", "locked" };
            if (!allowed.Contains(request.Status, StringComparer.OrdinalIgnoreCase))
            {
                return BadRequest(ErrorResponseDto.BadRequest(
                    $"허용되지 않는 상태값입니다. (허용: {string.Join(", ", allowed)})"));
            }
        }

        try
        {
            var docUtilRequest = new DocUtilUpdateUserRequest(
                Email: request.Email,
                Role: request.Role,
                DepartmentId: request.DepartmentId,
                Language: request.Language,
                Status: request.Status?.ToLowerInvariant());

            var result = await _docUtilClient.UpdateUserAsync(id, docUtilRequest, ct);

            _logger.LogInformation(
                "운영자 DocUtil 사용자 정보 수정 성공 - UserId={UserId}, Fields=[email={E},role={R},dept={D},lang={L},status={S}]",
                id,
                request.Email is null ? "-" : "set",
                request.Role ?? "-",
                request.DepartmentId is null ? "-" : (request.DepartmentId.Length == 0 ? "clear" : "set"),
                request.Language ?? "-",
                request.Status ?? "-");

            await InvalidateUsersCacheAsync();
            return Ok(result);
        }
        catch (DocUtilUpstreamException ex)
        {
            _logger.LogError(ex,
                "DocUtil 사용자 정보 수정 실패 - errorCode={ErrorCode}, status={Status}, id={Id}",
                ex.ErrorCode, (int)ex.StatusCode, id);
            await InvalidateUsersCacheAsync();
            return StatusCode(
                ErrorResponseDto.MapDocUtilUpstreamToStatusCode(ex),
                ErrorResponseDto.FromDocUtilUpstream(ex,
                    "사용자 정보 수정에 실패했습니다. " + ex.Message));
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 사용자 정보 수정 실패 (id={Id})", id);
            await InvalidateUsersCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "사용자 정보 수정에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 사용자 상태 변경 — DocUtil `/api/v1/users/{id}/status` 위임.
    /// 성공 시 캐시 일괄 무효화(version-key bump).
    /// </summary>
    /// <remarks>
    /// 외부 표면 body: { "status": "active" | "inactive" | "locked" }
    /// </remarks>
    [HttpPut("users/{id}/status")]
    public async Task<ActionResult<DocUtilUserDetail>> UpdateUserStatus(
        string id,
        [FromBody] UpdateUserStatusRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            return BadRequest(ErrorResponseDto.BadRequest("사용자 식별자가 비어 있습니다."));
        }
        if (request == null || string.IsNullOrWhiteSpace(request.Status))
        {
            return BadRequest(ErrorResponseDto.BadRequest("변경할 상태값이 비어 있습니다."));
        }

        // 화이트리스트 — DocUtil 측 422 를 사전 차단 + 명시적 한국어 안내.
        var allowed = new[] { "active", "inactive", "locked" };
        if (!allowed.Contains(request.Status, StringComparer.OrdinalIgnoreCase))
        {
            return BadRequest(ErrorResponseDto.BadRequest(
                $"허용되지 않는 상태값입니다. (허용: {string.Join(", ", allowed)})"));
        }

        try
        {
            var result = await _docUtilClient.UpdateUserStatusAsync(id, request.Status.ToLowerInvariant(), ct);

            _logger.LogInformation(
                "운영자 DocUtil 사용자 상태 변경 성공 - UserId={UserId}, NewStatus={Status}",
                id, request.Status);

            // 캐시 invalidate — 다음 목록 조회부터 즉시 반영.
            await InvalidateUsersCacheAsync();

            return Ok(result);
        }
        catch (DocUtilUpstreamException ex)
        {
            _logger.LogError(ex,
                "DocUtil 사용자 상태 변경 실패 - errorCode={ErrorCode}, status={Status}, id={Id}, newStatus={NewStatus}",
                ex.ErrorCode, (int)ex.StatusCode, id, request.Status);
            // 실패 시에도 invalidate — DocUtil 측 상태가 부분 변경되었을 수 있어(예: 5xx 중간 단절),
            // ghost 데이터가 GET 응답에 남는 일이 없도록 안전을 위해 캐시 무효화.
            await InvalidateUsersCacheAsync();
            return StatusCode(
                ErrorResponseDto.MapDocUtilUpstreamToStatusCode(ex),
                ErrorResponseDto.FromDocUtilUpstream(ex,
                    "사용자 상태 변경에 실패했습니다. " + ex.Message));
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 사용자 상태 변경 실패 (id={Id}, status={Status})", id, request.Status);
            await InvalidateUsersCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "사용자 상태 변경에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 사용자 삭제 — DocUtil `/api/v1/users/{id}` 위임 (DELETE).
    /// 성공 시 캐시 일괄 무효화(version-key bump).
    /// </summary>
    [HttpDelete("users/{id}")]
    public async Task<IActionResult> DeleteUser(string id, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            return BadRequest(ErrorResponseDto.BadRequest("사용자 식별자가 비어 있습니다."));
        }

        try
        {
            await _docUtilClient.DeleteUserAsync(id, ct);
            _logger.LogInformation("운영자 DocUtil 사용자 삭제 성공 - UserId={UserId}", id);

            // 캐시 invalidate — 다음 목록 조회부터 즉시 반영.
            await InvalidateUsersCacheAsync();

            return NoContent();
        }
        catch (DocUtilUpstreamException ex)
        {
            _logger.LogError(ex,
                "DocUtil 사용자 삭제 실패 - errorCode={ErrorCode}, status={Status}, id={Id}",
                ex.ErrorCode, (int)ex.StatusCode, id);
            // 실패 시에도 invalidate — 404(이미 DocUtil 측 삭제됨) / 5xx(부분 단절) 상황에서
            // ghost 사용자가 GET 응답에 남는 일이 없도록 안전 차원에서 캐시 무효화.
            await InvalidateUsersCacheAsync();
            return StatusCode(
                ErrorResponseDto.MapDocUtilUpstreamToStatusCode(ex),
                ErrorResponseDto.FromDocUtilUpstream(ex,
                    "사용자 삭제에 실패했습니다. " + ex.Message));
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 사용자 삭제 실패 (id={Id})", id);
            await InvalidateUsersCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "사용자 삭제에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ── 캐시 wrapper (record 직렬화 안정성을 위한 명시적 클래스) ───────────
    private sealed class CachedUserListDto
    {
        public DocUtilUserSummary[]? Items { get; set; }
        public long Total { get; set; }
        public int Page { get; set; }
        public int Size { get; set; }
    }
}

/// <summary>
/// 사용자 상태 변경 요청 DTO. 외부 표면(camelCase): { "status": "active|inactive|locked" }.
/// </summary>
public sealed class UpdateUserStatusRequest
{
    /// <summary>변경할 상태값. DocUtil 측이 검증("active" | "inactive" | "locked").</summary>
    public string Status { get; set; } = string.Empty;
}

/// <summary>
/// 사용자 일반 정보 수정 요청 DTO (트랙 #101 F7).
/// 외부 표면(camelCase): { email?, role?, departmentId?, language?, status? } — partial update.
/// </summary>
/// <remarks>
/// departmentId 가 빈문자열("")이면 부서 해제 의도로 해석된다(null 로 매핑).
/// status 는 "active" / "inactive" / "locked" 중 하나여야 한다(컨트롤러에서 사전 검증).
/// </remarks>
public sealed class UpdateDocUtilUserRequest
{
    /// <summary>변경할 이메일. null 이면 변경하지 않음.</summary>
    public string? Email { get; set; }

    /// <summary>변경할 역할. null 이면 변경하지 않음.</summary>
    public string? Role { get; set; }

    /// <summary>변경할 부서 UUID(string). 빈문자열은 부서 해제 의도.</summary>
    public string? DepartmentId { get; set; }

    /// <summary>변경할 선호 언어 코드(예: "ko", "en").</summary>
    public string? Language { get; set; }

    /// <summary>변경할 상태값(active/inactive/locked). null 이면 변경하지 않음.</summary>
    public string? Status { get; set; }
}
