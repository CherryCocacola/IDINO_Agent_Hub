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
    private readonly IApiKeyPoolService _apiKeyPool;
    private readonly IConfiguration _configuration;

    public ApiServicesController(
        AIAgentManagementDbContext context,
        ILogger<ApiServicesController> logger,
        IAiProxyService aiProxyService,
        IApiKeyPoolService apiKeyPool,
        IConfiguration configuration)
    {
        _context = context;
        _logger = logger;
        _aiProxyService = aiProxyService;
        _apiKeyPool = apiKeyPool;
        _configuration = configuration;
    }

    // ─── 트랙 #97-post4 (2026-05-18): ServiceCode → ApiKeyPool key 매핑 ───
    // AiProxyService 의 switch 와 동일 — "chatgpt"/"openai" 는 같은 풀.
    private static string MapPoolKey(string serviceCode) => serviceCode.ToLowerInvariant() switch
    {
        "chatgpt" or "openai" => "openai",
        "azureopenai" => "azureopenai",
        "claude" => "claude",
        "gemini" or "google" => "gemini",
        "perplexity" => "perplexity",
        "mistral" => "mistral",
        "copilot" => "copilot",
        _ => serviceCode.ToLowerInvariant()
    };

    // ─── 트랙 #97-post4: ServiceCode → appsettings.json 섹션명 (환경변수 fallback) ───
    private static readonly Dictionary<string, string> ConfigSectionMap = new(StringComparer.OrdinalIgnoreCase)
    {
        ["openai"] = "OpenAI", ["chatgpt"] = "OpenAI",
        ["azureopenai"] = "AzureOpenAI",
        ["claude"] = "Claude",
        ["gemini"] = "Gemini", ["google"] = "Gemini",
        ["perplexity"] = "Perplexity",
        ["mistral"] = "Mistral",
        ["copilot"] = "Copilot",
        ["tavily"] = "Tavily",
    };

    /// <summary>
    /// 트랙 #97-post4: ServiceCode 별 외부/내부 분류 + 활성 키 보유 여부 판정.
    /// - Nexus → "internal", Nexus.BaseUrl 설정 시 활성
    /// - 외부 LLM → "external", ApiKeyPool 카운트(>0) 또는 환경변수 키 보유 시 활성
    /// 이미지 생성 등 매핑 없는 ServiceCode 는 매핑/카운트 모두 없으면 false (사용자 결정 — 키 없는 모델 우선 숨김).
    /// </summary>
    private (string category, bool hasKey) ClassifyService(string serviceCode)
    {
        var lower = serviceCode.ToLowerInvariant();
        if (lower == "nexus")
        {
            var nexusUrl = _configuration["Nexus:BaseUrl"];
            return ("internal", !string.IsNullOrWhiteSpace(nexusUrl));
        }
        // 외부 LLM — ApiKeyPool 우선
        var poolKey = MapPoolKey(lower);
        var poolStats = _apiKeyPool.GetPoolStats();
        if (poolStats.TryGetValue(poolKey, out var count) && count > 0)
        {
            return ("external", true);
        }
        // 환경변수 fallback (ApiKeyPool 적재 전 timing 또는 카운트 0 보강)
        if (ConfigSectionMap.TryGetValue(lower, out var section))
        {
            var configKey = _configuration[$"AiApiSettings:{section}:ApiKey"];
            if (!string.IsNullOrWhiteSpace(configKey))
            {
                return ("external", true);
            }
        }
        return ("external", false);
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

            // 트랙 #97-post4 — 외부/내부 분류 + 활성 키 보유 여부 채움 (메모리 후처리, EF 쿼리 부하 없음)
            foreach (var dto in services)
            {
                var (category, hasKey) = ClassifyService(dto.ServiceCode);
                dto.ServiceCategory = category;
                dto.HasActiveKey = hasKey;
            }

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

            // 트랙 #97-post4 — 외부/내부 분류 + 활성 키
            var (category, hasKey) = ClassifyService(dto.ServiceCode);
            dto.ServiceCategory = category;
            dto.HasActiveKey = hasKey;

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
