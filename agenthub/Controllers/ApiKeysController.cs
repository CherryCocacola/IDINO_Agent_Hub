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
            return BadRequest("KeyName, ServiceCode, and ApiKey are required");

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

    private int? GetCurrentUserId()
    {
        var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier);
        if (userIdClaim == null || !int.TryParse(userIdClaim.Value, out var userId))
            return null;

        return userId;
    }
}
