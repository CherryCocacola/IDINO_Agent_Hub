using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize(Roles = "Admin")]
public class PiiDetectionLogsController : ControllerBase
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<PiiDetectionLogsController> _logger;

    public PiiDetectionLogsController(
        AIAgentManagementDbContext context,
        ILogger<PiiDetectionLogsController> logger)
    {
        _context = context;
        _logger = logger;
    }

    /// <summary>
    /// FromQuery DateTime 은 ISO 8601 Z suffix 라도 Kind=Unspecified 로 바인딩될 수 있다.
    /// PostgreSQL timestamptz 컬럼은 Kind=Utc 만 허용하므로 본 헬퍼로 정규화한다.
    /// </summary>
    private static DateTime ToUtc(DateTime value) => value.Kind switch
    {
        DateTimeKind.Utc => value,
        DateTimeKind.Local => value.ToUniversalTime(),
        _ => DateTime.SpecifyKind(value, DateTimeKind.Utc),
    };

    [HttpGet]
    public async Task<ActionResult<object>> GetLogs(
        [FromQuery] int? userId,
        [FromQuery] int? agentId,
        [FromQuery] string? detectionType,
        [FromQuery] string? actionTaken,
        [FromQuery] DateTime? startDate,
        [FromQuery] DateTime? endDate,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20)
    {
        try
        {
            var query = _context.PiiDetectionLogs.AsQueryable();

            if (userId.HasValue)
                query = query.Where(l => l.UserId == userId.Value);

            if (agentId.HasValue)
                query = query.Where(l => l.AgentId == agentId.Value);

            if (!string.IsNullOrEmpty(detectionType))
                query = query.Where(l => l.DetectionType == detectionType);

            if (!string.IsNullOrEmpty(actionTaken))
                query = query.Where(l => l.ActionTaken == actionTaken);

            if (startDate.HasValue)
            {
                // Npgsql timestamptz 호환 — FromQuery DateTime Kind 정규화
                var startUtc = ToUtc(startDate.Value);
                query = query.Where(l => l.DetectedAt >= startUtc);
            }

            if (endDate.HasValue)
            {
                var endUtc = ToUtc(endDate.Value.AddDays(1));
                query = query.Where(l => l.DetectedAt <= endUtc);
            }

            var totalCount = await query.CountAsync();

            var logs = await query
                .OrderByDescending(l => l.DetectedAt)
                .Skip((page - 1) * pageSize)
                .Take(pageSize)
                .Select(l => new PiiDetectionLogDto
                {
                    LogId = l.LogId,
                    UserId = l.UserId,
                    UserName = l.User != null ? l.User.FullName : null,
                    AgentId = l.AgentId,
                    AgentName = l.Agent != null ? l.Agent.AgentName : null,
                    ConversationId = l.ConversationId,
                    DetectionType = l.DetectionType,
                    DetectionTypeName = l.DetectionType == "PhoneNumber" ? "휴대폰 번호" :
                                       l.DetectionType == "ResidentNumber" ? "주민등록번호" :
                                       l.DetectionType == "CreditCard" ? "신용카드 번호" :
                                       l.DetectionType == "Email" ? "이메일 주소" :
                                       l.DetectionType == "AccountNumber" ? "계좌번호" :
                                       l.DetectionType == "DriverLicense" ? "운전면허번호" :
                                       l.DetectionType == "PassportNumber" ? "여권번호" :
                                       l.DetectionType == "AlienRegistrationNumber" ? "외국인등록번호" :
                                       l.DetectionType,
                    OriginalMessage = l.OriginalMessage,
                    ActionTaken = l.ActionTaken,
                    DetectedAt = l.DetectedAt,
                    IpAddress = l.IpAddress
                })
                .ToListAsync();

            return Ok(new
            {
                items = logs,
                totalCount = totalCount,
                page = page,
                pageSize = pageSize,
                totalPages = (int)Math.Ceiling(totalCount / (double)pageSize)
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting PII detection logs");
            return StatusCode(500, ErrorResponseDto.InternalError("로그 조회 중 오류가 발생했습니다."));
        }
    }

    [HttpGet("statistics")]
    public async Task<ActionResult<PiiDetectionStatisticsDto>> GetStatistics(
        [FromQuery] DateTime? startDate,
        [FromQuery] DateTime? endDate)
    {
        try
        {
            var query = _context.PiiDetectionLogs.AsQueryable();

            if (startDate.HasValue)
            {
                // Npgsql timestamptz 호환 — FromQuery DateTime Kind 정규화
                var startUtc = ToUtc(startDate.Value);
                query = query.Where(l => l.DetectedAt >= startUtc);
            }

            if (endDate.HasValue)
            {
                var endUtc = ToUtc(endDate.Value.AddDays(1));
                query = query.Where(l => l.DetectedAt <= endUtc);
            }

            var totalDetections = await query.CountAsync();
            var blockedCount = await query.CountAsync(l => l.ActionTaken == "Block");
            var maskedCount = await query.CountAsync(l => l.ActionTaken == "Mask");

            var detectionTypeCounts = await query
                .GroupBy(l => l.DetectionType)
                .Select(g => new { Type = g.Key, Count = g.Count() })
                .ToDictionaryAsync(x => x.Type, x => x.Count);

            // dailyCounts: Date 부분만 DB에서 집계 후 ToString() 은 메모리에서 처리
            var dailyCountsList = await query
                .GroupBy(l => l.DetectedAt.Date)
                .Select(g => new { Date = g.Key, Count = g.Count() })
                .OrderBy(x => x.Date)
                .ToListAsync();
            var dailyCounts = dailyCountsList
                .ToDictionary(x => x.Date.ToString("yyyy-MM-dd"), x => x.Count);

            // agentCounts: GroupBy 후 Join 은 EF Core 에서 변환 실패 가능 → 별도 쿼리 후 메모리 Join
            var agentIdCounts = await query
                .Where(l => l.AgentId.HasValue)
                .GroupBy(l => l.AgentId!.Value)
                .Select(g => new { AgentId = g.Key, Count = g.Count() })
                .ToListAsync();
            Dictionary<string, int> agentCounts;
            if (agentIdCounts.Count > 0)
            {
                var agentIds = agentIdCounts.Select(x => x.AgentId).ToList();
                var agentNameList = await _context.Agents
                    .Where(a => agentIds.Contains(a.AgentId))
                    .Select(a => new { a.AgentId, a.AgentName })
                    .ToListAsync();
                var agentNameMap = agentNameList.ToDictionary(a => a.AgentId, a => a.AgentName ?? "Unknown");
                agentCounts = agentIdCounts
                    .GroupBy(x => agentNameMap.GetValueOrDefault(x.AgentId, "Unknown"))
                    .ToDictionary(g => g.Key, g => g.Sum(x => x.Count));
            }
            else
            {
                agentCounts = new Dictionary<string, int>();
            }

            // userCounts: 동일하게 별도 쿼리 후 메모리 Join
            var userIdCounts = await query
                .Where(l => l.UserId.HasValue)
                .GroupBy(l => l.UserId!.Value)
                .Select(g => new { UserId = g.Key, Count = g.Count() })
                .ToListAsync();
            Dictionary<string, int> userCounts;
            if (userIdCounts.Count > 0)
            {
                var userIds = userIdCounts.Select(x => x.UserId).ToList();
                var userNameList = await _context.Users
                    .Where(u => userIds.Contains(u.UserId))
                    .Select(u => new { u.UserId, u.FullName })
                    .ToListAsync();
                var userNameMap = userNameList.ToDictionary(u => u.UserId, u => u.FullName ?? "Unknown");
                userCounts = userIdCounts
                    .GroupBy(x => userNameMap.GetValueOrDefault(x.UserId, "Unknown"))
                    .ToDictionary(g => g.Key, g => g.Sum(x => x.Count));
            }
            else
            {
                userCounts = new Dictionary<string, int>();
            }

            var statistics = new PiiDetectionStatisticsDto
            {
                TotalDetections = totalDetections,
                BlockedCount = blockedCount,
                MaskedCount = maskedCount,
                DetectionTypeCounts = detectionTypeCounts,
                DailyCounts = dailyCounts,
                AgentCounts = agentCounts,
                UserCounts = userCounts
            };

            return Ok(statistics);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting PII detection statistics");
            return StatusCode(500, ErrorResponseDto.InternalError("통계 조회 중 오류가 발생했습니다."));
        }
    }
}
