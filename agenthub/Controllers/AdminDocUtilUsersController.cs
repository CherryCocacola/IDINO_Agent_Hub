using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
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
    private readonly ILogger<AdminDocUtilUsersController> _logger;

    public AdminDocUtilUsersController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        ILogger<AdminDocUtilUsersController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _logger = logger;
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
            var result = await _docUtilClient.ListUsersAsync(page, size, role, status, search, ct);

            // ── 캐시 적재(성공 응답만) ─────────────────────────────────
            await _cachingService.SetAsync(cacheKey, new CachedUserListDto
            {
                Items = result.Items,
                Total = result.Total,
                Page = result.Page,
                Size = result.Size,
            }, CacheTtl);

            return Ok(result);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 사용자 목록 조회 실패 (page={Page}, size={Size}, role={Role}, status={Status})",
                page, size, role, status);
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 사용자 목록을 불러오지 못했습니다. DocUtil 서비스 상태를 확인하세요.",
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
            var detail = await _docUtilClient.GetUserAsync(id, ct);
            if (detail == null)
            {
                return NotFound(ErrorResponseDto.NotFound("해당 사용자를 찾을 수 없습니다."));
            }
            return Ok(detail);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 사용자 상세 조회 실패 (id={Id})", id);
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 사용자 상세를 불러오지 못했습니다.",
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
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 사용자 상태 변경 실패 (id={Id}, status={Status})", id, request.Status);
            // 실패 시에도 invalidate — DocUtil 측 상태가 부분 변경되었을 수 있어(예: 5xx 중간 단절),
            // ghost 데이터가 GET 응답에 남는 일이 없도록 안전을 위해 캐시 무효화.
            // (10.1c+ DeleteDepartment 의 동일 패턴 일관 적용)
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
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 사용자 삭제 실패 (id={Id})", id);
            // 실패 시에도 invalidate — 404(이미 DocUtil 측 삭제됨) / 5xx(부분 단절) 상황에서
            // ghost 사용자가 GET 응답에 남는 일이 없도록 안전 차원에서 캐시 무효화.
            // (DeleteDepartment 와 동일 패턴 일관 적용)
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
