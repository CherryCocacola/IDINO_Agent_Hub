using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class ApiKeysController : ControllerBase
{
    private readonly IApiKeyService _apiKeyService;
    private readonly ILogger<ApiKeysController> _logger;

    public ApiKeysController(IApiKeyService apiKeyService, ILogger<ApiKeysController> logger)
    {
        _apiKeyService = apiKeyService;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<List<ApiKeyDto>>> GetUserApiKeys()
    {
        var userId = GetCurrentUserId();
        if (userId == null)
            return Unauthorized(ErrorResponseDto.Unauthorized());

        var apiKeys = await _apiKeyService.GetUserApiKeysAsync(userId.Value);
        return Ok(apiKeys);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<ApiKeyDto>> GetApiKey(int id)
    {
        var userId = GetCurrentUserId();
        if (userId == null)
            return Unauthorized(ErrorResponseDto.Unauthorized());

        var apiKey = await _apiKeyService.GetApiKeyByIdAsync(id, userId.Value);
        if (apiKey == null)
            return NotFound(ErrorResponseDto.NotFound());

        return Ok(apiKey);
    }

    [HttpPost]
    public async Task<ActionResult<ApiKeyDto>> CreateApiKey([FromBody] CreateApiKeyRequestDto request)
    {
        var userId = GetCurrentUserId();
        if (userId == null)
            return Unauthorized(ErrorResponseDto.Unauthorized());

        if (string.IsNullOrWhiteSpace(request.KeyName) || string.IsNullOrWhiteSpace(request.ServiceCode) || string.IsNullOrWhiteSpace(request.ApiKey))
            return BadRequest(ErrorResponseDto.BadRequest("KeyName, ServiceCode, ApiKey 는 필수 입력 항목입니다."));

        var apiKey = await _apiKeyService.CreateApiKeyAsync(request, userId.Value);
        return CreatedAtAction(nameof(GetApiKey), new { id = apiKey.ApiKeyId }, apiKey);
    }

    [HttpPut("{id}")]
    public async Task<ActionResult<ApiKeyDto>> UpdateApiKey(int id, [FromBody] UpdateApiKeyRequestDto request)
    {
        var userId = GetCurrentUserId();
        if (userId == null)
            return Unauthorized(ErrorResponseDto.Unauthorized());

        var apiKey = await _apiKeyService.UpdateApiKeyAsync(id, request, userId.Value);
        if (apiKey == null)
            return NotFound(ErrorResponseDto.NotFound());

        return Ok(apiKey);
    }

    [HttpDelete("{id}")]
    public async Task<ActionResult> DeleteApiKey(int id)
    {
        var userId = GetCurrentUserId();
        if (userId == null)
            return Unauthorized(ErrorResponseDto.Unauthorized());

        var deleted = await _apiKeyService.DeleteApiKeyAsync(id, userId.Value);
        if (!deleted)
            return NotFound(ErrorResponseDto.NotFound());

        return NoContent();
    }

    [HttpPost("{id}/reveal")]
    public async Task<ActionResult<object>> RevealApiKey(int id)
    {
        var userId = GetCurrentUserId();
        if (userId == null)
            return Unauthorized(ErrorResponseDto.Unauthorized());

        var decryptedKey = await _apiKeyService.GetDecryptedApiKeyAsync(id, userId.Value);
        if (decryptedKey == null)
            return NotFound(ErrorResponseDto.NotFound());

        return Ok(new { key = decryptedKey });
    }

    // ── 트랙 #91 — 외부 LLM 풀 키 운영 endpoint ───────────────────────────────

    /// <summary>
    /// 외부 LLM 풀 키(`KeyType="Provider"`) 등록. Admin/SuperAdmin 전용.
    /// 등록 후 즉시 `IApiKeyPoolService.RefreshAsync()` 트리거 → 다음 LLM 호출부터 신규 키 사용 가능.
    /// </summary>
    [HttpPost("provider")]
    [Authorize(Roles = "Admin,SuperAdmin")]
    public async Task<ActionResult<ApiKeyDto>> CreateProviderApiKey(
        [FromBody] CreateProviderApiKeyRequestDto request,
        CancellationToken ct)
    {
        var userId = GetCurrentUserId();
        if (userId == null)
            return Unauthorized(ErrorResponseDto.Unauthorized());

        try
        {
            var dto = await _apiKeyService.CreateProviderApiKeyAsync(request, userId.Value, ct);
            return CreatedAtAction(nameof(GetApiKey), new { id = dto.ApiKeyId }, dto);
        }
        catch (ArgumentException ex)
        {
            // ServiceCode 화이트리스트 / 키 길이 등 입력 검증 실패.
            return BadRequest(ErrorResponseDto.BadRequest(ex.Message));
        }
        catch (InvalidOperationException ex)
        {
            // KeyHash 중복 등 비즈니스 충돌.
            _logger.LogWarning("[Provider ApiKey] 등록 충돌: {Message}", ex.Message);
            return Conflict(new ErrorResponseDto(ex.Message, "API_KEY_DUPLICATE"));
        }
    }

    /// <summary>
    /// 외부 LLM 키 유효성 검증 — 제공사별 가벼운 GET endpoint 1회 호출. Admin/SuperAdmin 전용.
    /// </summary>
    [HttpPost("{id}/test")]
    [Authorize(Roles = "Admin,SuperAdmin")]
    public async Task<ActionResult<TestApiKeyResponseDto>> TestApiKey(int id, CancellationToken ct)
    {
        var userId = GetCurrentUserId();
        if (userId == null)
            return Unauthorized(ErrorResponseDto.Unauthorized());

        var result = await _apiKeyService.TestApiKeyAsync(id, userId.Value, ct);
        return Ok(result);
    }

    /// <summary>
    /// 외부 LLM 키 풀 통계 — 제공사별 (총/appsettings/DB/냉각) 카운트. Admin/SuperAdmin 전용.
    /// </summary>
    [HttpGet("pool-stats")]
    [Authorize(Roles = "Admin,SuperAdmin")]
    public ActionResult<PoolStatsResponseDto> GetPoolStats([FromServices] IApiKeyPoolService pool)
    {
        var stats = pool.GetPoolStatsWithSource();
        var response = new PoolStatsResponseDto
        {
            LastRefreshedAt = DateTime.UtcNow,
            Providers = stats
                .Select(kvp => new ProviderPoolStatDto
                {
                    ServiceCode = kvp.Key,
                    TotalCount = kvp.Value.TotalCount,
                    FromAppsettings = kvp.Value.FromAppsettings,
                    FromDb = kvp.Value.FromDb,
                    CoolingDownCount = kvp.Value.CoolingDownCount
                })
                .OrderBy(p => p.ServiceCode, StringComparer.OrdinalIgnoreCase)
                .ToList()
        };
        return Ok(response);
    }

    private int? GetCurrentUserId()
    {
        var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier);
        if (userIdClaim == null || !int.TryParse(userIdClaim.Value, out var userId))
            return null;

        return userId;
    }
}
