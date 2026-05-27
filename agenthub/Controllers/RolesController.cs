using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using AIAgentManagement.Data;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// RolesController — 사용자 권한 카탈로그 (트랙 #121, 2026-05-27)
//
// 신설 사유:
//   Users.vue 의 신규/수정 사용자 modal 에서 role multi-select UI 가 부재.
//   backend (UpdateUserRequestDto.RoleIds + UserService.UpdateUserAsync) 는 이미
//   RoleIds 처리 지원 — frontend 가 role list 를 동적으로 fetch 해서 표시하기 위함.
//
// 응답:
//   GET /api/roles → [{ roleId: int, roleName: string, description?: string }, ...]
//   현재 시드 = Admin(1), Developer(2), User(3)
// ════════════════════════════════════════════════════════════════════════════

[ApiController]
[Route("api/[controller]")]
[Authorize(Roles = "Admin")]
public class RolesController : ControllerBase
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<RolesController> _logger;

    public RolesController(AIAgentManagementDbContext context, ILogger<RolesController> logger)
    {
        _context = context;
        _logger = logger;
    }

    /// <summary>
    /// 권한 카탈로그 조회 — Users.vue 의 신규/수정 modal 의 role select 옵션 source.
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<IEnumerable<object>>> GetRoles(CancellationToken ct = default)
    {
        try
        {
            var roles = await _context.Roles
                .AsNoTracking()
                .OrderBy(r => r.RoleId)
                .Select(r => new
                {
                    roleId = r.RoleId,
                    roleName = r.RoleName,
                    description = r.Description,
                })
                .ToListAsync(ct);
            return Ok(roles);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting roles");
            return StatusCode(500, new { message = "권한 카탈로그를 불러오지 못했습니다." });
        }
    }
}
