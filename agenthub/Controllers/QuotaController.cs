using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class QuotaController : ControllerBase
{
    private readonly IQuotaService _quotaService;
    private readonly ILogger<QuotaController> _logger;

    public QuotaController(IQuotaService quotaService, ILogger<QuotaController> logger)
    {
        _quotaService = quotaService;
        _logger = logger;
    }

    [HttpGet]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<List<QuotaDto>>> GetQuotas([FromQuery] int? userId, [FromQuery] int? serviceId)
    {
        try
        {
            var quotas = await _quotaService.GetQuotasAsync(userId, serviceId);
            return Ok(quotas);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting quotas");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("user/{userId}/service/{serviceId}")]
    public async Task<ActionResult<QuotaDto>> GetQuota(int userId, int serviceId)
    {
        try
        {
            var currentUserIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(currentUserIdClaim) || !int.TryParse(currentUserIdClaim, out var currentUserId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            // Users can only see their own quota unless admin
            if (userId != currentUserId && !User.IsInRole("Admin"))
            {
                return Forbid();
            }

            var quota = await _quotaService.GetQuotaAsync(userId, serviceId);
            if (quota == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(quota);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting quota");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost("user/{userId}/service/{serviceId}")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<QuotaDto>> SetQuota(int userId, int serviceId, [FromBody] SetQuotaRequestDto request)
    {
        try
        {
            var quota = await _quotaService.SetQuotaAsync(userId, serviceId, request);
            return Ok(quota);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error setting quota");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("my-quotas")]
    public async Task<ActionResult<List<QuotaDto>>> GetMyQuotas()
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var quotas = await _quotaService.GetQuotasAsync(userId);
            return Ok(quotas);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting my quotas");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("my/{serviceId}")]
    public async Task<ActionResult<object>> GetMyQuota(int serviceId)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var quota = await _quotaService.GetQuotaAsync(userId, serviceId);
            
            // 일일 사용량 계산
            var today = DateTime.UtcNow.Date;
            var todayUsage = await _quotaService.GetTodayUsageAsync(userId, serviceId);

            if (quota == null)
            {
                // 할당량이 없으면 기본값으로 반환
                return Ok(new
                {
                    UserId = userId,
                    ServiceId = serviceId,
                    DailyLimit = 100,
                    MonthlyLimit = 1000,
                    CurrentUsage = 0,
                    TodayUsage = todayUsage,
                    RemainingQuota = 1000
                });
            }

            return Ok(new
            {
                quota.QuotaId,
                quota.UserId,
                quota.UserEmail,
                quota.ServiceId,
                quota.ServiceName,
                quota.MonthlyLimit,
                quota.DailyLimit,
                quota.CostLimit,
                CurrentUsage = quota.CurrentUsage, // 월간 사용량
                TodayUsage = todayUsage, // 일일 사용량
                quota.CurrentCost,
                quota.AlertThreshold,
                quota.IsAlertEnabled,
                quota.LastResetAt,
                quota.CreatedAt,
                quota.UpdatedAt
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting my quota");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }
}
