using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Security.Claims;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class AnalyticsController : ControllerBase
{
    private readonly IAnalyticsService _analyticsService;
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<AnalyticsController> _logger;

    public AnalyticsController(IAnalyticsService analyticsService, AIAgentManagementDbContext context, ILogger<AnalyticsController> logger)
    {
        _analyticsService = analyticsService;
        _context = context;
        _logger = logger;
    }

    [HttpGet("dashboard")]
    public async Task<ActionResult<DashboardStatsDto>> GetDashboardStats()
    {
        try
        {
            var stats = await _analyticsService.GetDashboardStatsAsync();
            return Ok(stats);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting dashboard stats");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("usage")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<List<UsageStatsDto>>> GetUsageStats(
        [FromQuery] DateTime? startDate,
        [FromQuery] DateTime? endDate,
        [FromQuery] int? userId)
    {
        try
        {
            var stats = await _analyticsService.GetUsageStatsAsync(startDate, endDate, userId);
            return Ok(stats);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting usage stats");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("cost")]
    public async Task<ActionResult<CostAnalysisDto>> GetCostAnalysis(
        [FromQuery] DateTime? startDate,
        [FromQuery] DateTime? endDate)
    {
        try
        {
            var analysis = await _analyticsService.GetCostAnalysisAsync(startDate, endDate);
            return Ok(analysis);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting cost analysis");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("top-users")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<List<UserUsageDto>>> GetTopUsers([FromQuery] int top = 10)
    {
        try
        {
            var users = await _analyticsService.GetTopUsersAsync(top);
            return Ok(users);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting top users");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("team-stats")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<TeamStatsDto>> GetTeamStats()
    {
        try
        {
            var stats = await _analyticsService.GetTeamStatsAsync();
            return Ok(stats);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting team stats");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("user-usage/{userId}")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<UserUsageDto>> GetUserUsage(int userId, [FromQuery] DateTime? startDate, [FromQuery] DateTime? endDate)
    {
        try
        {
            var usage = await _analyticsService.GetUserUsageAsync(userId, startDate, endDate);
            return Ok(usage);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting user usage");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    /// <summary>
    /// 사용 내역 KPI 집계 — SQL aggregate(단일 쿼리)이므로 수만 건도 빠름
    /// </summary>
    [HttpGet("usage-summary")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<UsageHistorySummaryDto>> GetUsageHistorySummary(
        [FromQuery] DateTime? startDate,
        [FromQuery] DateTime? endDate,
        [FromQuery] int? userId,
        [FromQuery] int? serviceId,
        [FromQuery] int? statusCode)
    {
        try
        {
            var summary = await _analyticsService.GetUsageHistorySummaryAsync(startDate, endDate, userId, serviceId, statusCode);
            return Ok(summary);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting usage summary");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 에이전트별 대화 통계
    // ──────────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 에이전트별 일/주/월 통계 요약 반환.
    /// 에이전트 소유자(CreatedBy)이거나 Admin 권한이어야 합니다.
    /// </summary>
    [HttpGet("agents/{agentId}/stats")]
    public async Task<ActionResult<object>> GetAgentStats(int agentId, [FromQuery] string period = "month")
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (!int.TryParse(userIdClaim, out var userId))
                return Unauthorized(ErrorResponseDto.Unauthorized());

            var agent = await _context.Agents.AsNoTracking().FirstOrDefaultAsync(a => a.AgentId == agentId);
            if (agent == null)
                return NotFound(ErrorResponseDto.NotFound("Agent not found"));

            var isAdmin = User.IsInRole("Admin");
            if (!isAdmin && agent.CreatedBy != userId)
                return Forbid();

            var now = DateTime.UtcNow;
            // `.Date` / `new DateTime(...)` 모두 Kind=Unspecified 반환 — Npgsql 의 timestamptz 컬럼은
            // Kind=Utc 만 허용하므로 SpecifyKind 로 명시한다. (Phase 3.x PG 전환 후 회귀 차단)
            DateTime from = period switch
            {
                "day"   => DateTime.SpecifyKind(now.Date, DateTimeKind.Utc),
                "week"  => DateTime.SpecifyKind(now.Date.AddDays(-(int)now.DayOfWeek), DateTimeKind.Utc),
                "month" => DateTime.SpecifyKind(new DateTime(now.Year, now.Month, 1), DateTimeKind.Utc),
                "year"  => DateTime.SpecifyKind(new DateTime(now.Year, 1, 1), DateTimeKind.Utc),
                _       => DateTime.SpecifyKind(new DateTime(now.Year, now.Month, 1), DateTimeKind.Utc)
            };

            var usageQuery = _context.ApiUsages
                .Where(u => u.ConversationId != null)
                .Join(_context.ChatConversations,
                    u => u.ConversationId,
                    c => c.ConversationId,
                    (u, c) => new { Usage = u, Conv = c })
                .Where(x => x.Conv.AgentId == agentId && x.Usage.CreatedAt >= from);

            var stats = await usageQuery
                .GroupBy(_ => 1)
                .Select(g => new
                {
                    TotalRequests    = g.Count(),
                    TotalTokens      = g.Sum(x => (long?)x.Usage.TokensUsed) ?? 0,
                    TotalCost        = g.Sum(x => x.Usage.RequestCost),
                    AvgResponseTime  = g.Average(x => (double?)x.Usage.ResponseTime) ?? 0,
                    SuccessCount     = g.Count(x => x.Usage.StatusCode == 200),
                    ErrorCount       = g.Count(x => x.Usage.StatusCode != 200)
                })
                .FirstOrDefaultAsync();

            var convCount = await _context.ChatConversations
                .Where(c => c.AgentId == agentId && c.CreatedAt >= from)
                .CountAsync();

            return Ok(new
            {
                AgentId         = agentId,
                Period          = period,
                From            = from,
                To              = now,
                Conversations   = convCount,
                TotalRequests   = stats?.TotalRequests ?? 0,
                TotalTokens     = stats?.TotalTokens ?? 0,
                TotalCost       = stats?.TotalCost ?? 0,
                AvgResponseTime = Math.Round(stats?.AvgResponseTime ?? 0, 1),
                SuccessCount    = stats?.SuccessCount ?? 0,
                ErrorCount      = stats?.ErrorCount ?? 0,
                SuccessRate     = stats?.TotalRequests > 0
                    ? Math.Round((double)(stats.SuccessCount) / stats.TotalRequests * 100, 1)
                    : 100.0
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting agent stats for AgentId {AgentId}", agentId);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    /// <summary>
    /// 에이전트의 일별 요청 수 시계열 (최근 N일).
    /// </summary>
    [HttpGet("agents/{agentId}/daily")]
    public async Task<ActionResult<object>> GetAgentDailyStats(int agentId, [FromQuery] int days = 30)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (!int.TryParse(userIdClaim, out var userId))
                return Unauthorized(ErrorResponseDto.Unauthorized());

            var agent = await _context.Agents.AsNoTracking().FirstOrDefaultAsync(a => a.AgentId == agentId);
            if (agent == null)
                return NotFound(ErrorResponseDto.NotFound("Agent not found"));

            var isAdmin = User.IsInRole("Admin");
            if (!isAdmin && agent.CreatedBy != userId)
                return Forbid();

            days = Math.Clamp(days, 1, 365);
            // `.Date` 는 Kind=Unspecified 반환 → Npgsql timestamptz 호환을 위해 Utc 로 명시
            var from = DateTime.SpecifyKind(DateTime.UtcNow.Date.AddDays(-days + 1), DateTimeKind.Utc);

            var daily = await _context.ApiUsages
                .Join(_context.ChatConversations,
                    u => u.ConversationId,
                    c => c.ConversationId,
                    (u, c) => new { Usage = u, Conv = c })
                .Where(x => x.Conv.AgentId == agentId && x.Usage.CreatedAt >= from)
                .GroupBy(x => x.Usage.CreatedAt.Date)
                .Select(g => new
                {
                    Date     = g.Key,
                    Requests = g.Count(),
                    Tokens   = g.Sum(x => (long?)x.Usage.TokensUsed) ?? 0,
                    Cost     = g.Sum(x => x.Usage.RequestCost)
                })
                .OrderBy(d => d.Date)
                .ToListAsync();

            return Ok(new { AgentId = agentId, Days = days, From = from, Data = daily });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting agent daily stats for AgentId {AgentId}", agentId);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("usage-history")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<object>> GetUsageHistory(
        [FromQuery] DateTime? startDate,
        [FromQuery] DateTime? endDate,
        [FromQuery] int? userId,
        [FromQuery] int? serviceId,
        [FromQuery] int? statusCode,
        [FromQuery] string? search,
        [FromQuery] int skip = 0,
        [FromQuery] int take = 100)
    {
        try
        {
            var (items, totalCount) = await _analyticsService.GetUsageHistoryAsync(startDate, endDate, userId, serviceId, statusCode, search, skip, take);
            return Ok(new { items, totalCount });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting usage history");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }
}
