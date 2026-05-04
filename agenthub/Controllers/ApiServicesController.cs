using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class ApiServicesController : ControllerBase
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<ApiServicesController> _logger;
    private readonly IAiProxyService _aiProxyService;

    public ApiServicesController(
        AIAgentManagementDbContext context, 
        ILogger<ApiServicesController> logger,
        IAiProxyService aiProxyService)
    {
        _context = context;
        _logger = logger;
        _aiProxyService = aiProxyService;
    }

    [HttpGet]
    public async Task<ActionResult<List<ApiServiceDto>>> GetServices([FromQuery] string? serviceType = null)
    {
        try
        {
            // 프로젝션을 쿼리 레벨에서 수행하여 성능 향상
            var query = _context.ApiServices
                .AsNoTracking() // 변경 추적 비활성화
                .Where(s => s.IsActive);

            if (!string.IsNullOrEmpty(serviceType))
                query = query.Where(s => s.ServiceType == serviceType);

            var services = await query
                .OrderBy(s => s.SortOrder)
                .Select(s => new ApiServiceDto
                {
                    ServiceId = s.ServiceId,
                    ServiceCode = s.ServiceCode,
                    ServiceName = s.ServiceName,
                    Description = s.Description,
                    IconClass = s.IconClass,
                    ColorCode = s.ColorCode,
                    DefaultModel = s.DefaultModel,
                    CostPerRequest = s.CostPerRequest,
                    IsActive = s.IsActive,
                    ServiceType = s.ServiceType
                })
                .ToListAsync();

            return Ok(services);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting API services");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<ApiServiceDto>> GetService(int id)
    {
        try
        {
            var service = await _context.ApiServices.FindAsync(id);
            if (service == null || !service.IsActive)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            var dto = new ApiServiceDto
            {
                ServiceId = service.ServiceId,
                ServiceCode = service.ServiceCode,
                ServiceName = service.ServiceName,
                Description = service.Description,
                IconClass = service.IconClass,
                ColorCode = service.ColorCode,
                DefaultModel = service.DefaultModel,
                CostPerRequest = service.CostPerRequest,
                IsActive = service.IsActive,
                ServiceType = service.ServiceType
            };

            return Ok(dto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting API service {ServiceId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("{id}/models")]
    public async Task<ActionResult<List<string>>> GetServiceModels(int id)
    {
        try
        {
            var service = await _context.ApiServices.FindAsync(id);
            if (service == null || !service.IsActive)
            {
                return NotFound(ErrorResponseDto.NotFound("Service not found or inactive"));
            }

            var models = await _aiProxyService.GetAvailableModelsAsync(id);
            return Ok(models);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting models for service {ServiceId}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred while fetching models"));
        }
    }

    [HttpGet("{id}/connection-status")]
    public async Task<ActionResult<object>> GetConnectionStatus(int id)
    {
        try
        {
            var service = await _context.ApiServices.FindAsync(id);
            if (service == null || !service.IsActive)
            {
                return NotFound(ErrorResponseDto.NotFound("Service not found or inactive"));
            }

            var isConnected = await _aiProxyService.TestServiceConnectionAsync(id);
            return Ok(new { connected = isConnected });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error checking connection status for service {ServiceId}", id);
            return Ok(new { connected = false });
        }
    }
}
