using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class UserPreferencesController : ControllerBase
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<UserPreferencesController> _logger;

    public UserPreferencesController(
        AIAgentManagementDbContext context,
        ILogger<UserPreferencesController> logger)
    {
        _context = context;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<List<UserPreferenceDto>>> GetUserPreferences()
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var preferences = await _context.UserPreferences
                .Where(p => p.UserId == userId)
                .Select(p => new UserPreferenceDto
                {
                    PreferenceId = p.PreferenceId,
                    UserId = p.UserId,
                    PreferenceKey = p.PreferenceKey,
                    PreferenceValue = p.PreferenceValue,
                    DataType = p.DataType,
                    Category = p.Category,
                    Description = p.Description,
                    CreatedAt = p.CreatedAt,
                    UpdatedAt = p.UpdatedAt
                })
                .ToListAsync();

            return Ok(preferences);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting user preferences");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("{key}")]
    public async Task<ActionResult<UserPreferenceDto>> GetUserPreference(string key)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var preference = await _context.UserPreferences
                .FirstOrDefaultAsync(p => p.UserId == userId && p.PreferenceKey == key);

            if (preference == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            var dto = new UserPreferenceDto
            {
                PreferenceId = preference.PreferenceId,
                UserId = preference.UserId,
                PreferenceKey = preference.PreferenceKey,
                PreferenceValue = preference.PreferenceValue,
                DataType = preference.DataType,
                Category = preference.Category,
                Description = preference.Description,
                CreatedAt = preference.CreatedAt,
                UpdatedAt = preference.UpdatedAt
            };

            return Ok(dto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting user preference {Key}", key);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost]
    public async Task<ActionResult<UserPreferenceDto>> CreateUserPreference([FromBody] CreateUserPreferenceRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            // 기존 설정 확인
            var existing = await _context.UserPreferences
                .FirstOrDefaultAsync(p => p.UserId == userId && p.PreferenceKey == request.PreferenceKey);

            if (existing != null)
            {
                // 업데이트
                existing.PreferenceValue = request.PreferenceValue;
                existing.DataType = request.DataType ?? "String";
                existing.Category = request.Category;
                existing.Description = request.Description;
                existing.UpdatedAt = DateTime.UtcNow;

                await _context.SaveChangesAsync();

                var updatedDto = new UserPreferenceDto
                {
                    PreferenceId = existing.PreferenceId,
                    UserId = existing.UserId,
                    PreferenceKey = existing.PreferenceKey,
                    PreferenceValue = existing.PreferenceValue,
                    DataType = existing.DataType,
                    Category = existing.Category,
                    Description = existing.Description,
                    CreatedAt = existing.CreatedAt,
                    UpdatedAt = existing.UpdatedAt
                };

                return Ok(updatedDto);
            }
            else
            {
                // 생성
                var preference = new UserPreference
                {
                    UserId = userId,
                    PreferenceKey = request.PreferenceKey,
                    PreferenceValue = request.PreferenceValue,
                    DataType = request.DataType ?? "String",
                    Category = request.Category,
                    Description = request.Description,
                    CreatedAt = DateTime.UtcNow,
                    UpdatedAt = DateTime.UtcNow
                };

                _context.UserPreferences.Add(preference);
                await _context.SaveChangesAsync();

                var dto = new UserPreferenceDto
                {
                    PreferenceId = preference.PreferenceId,
                    UserId = preference.UserId,
                    PreferenceKey = preference.PreferenceKey,
                    PreferenceValue = preference.PreferenceValue,
                    DataType = preference.DataType,
                    Category = preference.Category,
                    Description = preference.Description,
                    CreatedAt = preference.CreatedAt,
                    UpdatedAt = preference.UpdatedAt
                };

                return CreatedAtAction(nameof(GetUserPreference), new { key = preference.PreferenceKey }, dto);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating/updating user preference");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPut("{key}")]
    public async Task<ActionResult<UserPreferenceDto>> UpdateUserPreference(string key, [FromBody] UpdateUserPreferenceRequestDto request)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var preference = await _context.UserPreferences
                .FirstOrDefaultAsync(p => p.UserId == userId && p.PreferenceKey == key);

            if (preference == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            if (request.PreferenceValue != null)
            {
                preference.PreferenceValue = request.PreferenceValue;
            }
            if (request.DataType != null)
            {
                preference.DataType = request.DataType;
            }
            if (request.Category != null)
            {
                preference.Category = request.Category;
            }
            if (request.Description != null)
            {
                preference.Description = request.Description;
            }
            preference.UpdatedAt = DateTime.UtcNow;

            await _context.SaveChangesAsync();

            var dto = new UserPreferenceDto
            {
                PreferenceId = preference.PreferenceId,
                UserId = preference.UserId,
                PreferenceKey = preference.PreferenceKey,
                PreferenceValue = preference.PreferenceValue,
                DataType = preference.DataType,
                Category = preference.Category,
                Description = preference.Description,
                CreatedAt = preference.CreatedAt,
                UpdatedAt = preference.UpdatedAt
            };

            return Ok(dto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating user preference {Key}", key);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpDelete("{key}")]
    public async Task<IActionResult> DeleteUserPreference(string key)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var preference = await _context.UserPreferences
                .FirstOrDefaultAsync(p => p.UserId == userId && p.PreferenceKey == key);

            if (preference == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            _context.UserPreferences.Remove(preference);
            await _context.SaveChangesAsync();

            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting user preference {Key}", key);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }
}
