using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize(Roles = "Admin")]
public class SystemSettingsController : ControllerBase
{
    private readonly AIAgentManagementDbContext _context;
    private readonly IPiiDetectionService _piiDetectionService;
    private readonly ILogger<SystemSettingsController> _logger;

    public SystemSettingsController(
        AIAgentManagementDbContext context,
        IPiiDetectionService piiDetectionService,
        ILogger<SystemSettingsController> logger)
    {
        _context = context;
        _piiDetectionService = piiDetectionService;
        _logger = logger;
    }

    [HttpGet("pii-protection")]
    public async Task<ActionResult<PiiProtectionSettings>> GetPiiProtectionSettings()
    {
        try
        {
            var settings = await _piiDetectionService.GetGlobalSettingsAsync();
            return Ok(settings);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting PII protection settings");
            return StatusCode(500, ErrorResponseDto.InternalError("설정을 가져오는 중 오류가 발생했습니다."));
        }
    }

    [HttpPut("pii-protection")]
    public async Task<ActionResult> UpdatePiiProtectionSettings([FromBody] UpdatePiiProtectionSettingsRequestDto request)
    {
        try
        {
            // Enabled 설정 업데이트
            var enabledSetting = await _context.SystemSettings
                .FirstOrDefaultAsync(s => s.SettingKey == "PiiProtection.Enabled");
            
            if (enabledSetting != null)
            {
                enabledSetting.SettingValue = request.Enabled.ToString().ToLower();
                enabledSetting.UpdatedAt = DateTime.UtcNow;
            }
            else
            {
                _context.SystemSettings.Add(new Models.SystemSetting
                {
                    SettingKey = "PiiProtection.Enabled",
                    SettingValue = request.Enabled.ToString().ToLower(),
                    DataType = "Boolean",
                    Category = "Privacy",
                    Description = "개인정보 보호 활성화 여부 (전역 기본값)",
                    IsEncrypted = false,
                    CreatedAt = DateTime.UtcNow,
                    UpdatedAt = DateTime.UtcNow
                });
            }

            // Mode 설정 업데이트
            var modeSetting = await _context.SystemSettings
                .FirstOrDefaultAsync(s => s.SettingKey == "PiiProtection.Mode");
            
            if (modeSetting != null)
            {
                modeSetting.SettingValue = request.Mode;
                modeSetting.UpdatedAt = DateTime.UtcNow;
            }
            else
            {
                _context.SystemSettings.Add(new Models.SystemSetting
                {
                    SettingKey = "PiiProtection.Mode",
                    SettingValue = request.Mode,
                    DataType = "String",
                    Category = "Privacy",
                    Description = "개인정보 보호 모드: Block(차단) 또는 Mask(마스킹)",
                    IsEncrypted = false,
                    CreatedAt = DateTime.UtcNow,
                    UpdatedAt = DateTime.UtcNow
                });
            }

            // DetectionTypes 설정 업데이트
            if (request.DetectionTypes != null && request.DetectionTypes.Count > 0)
            {
                var typesJson = System.Text.Json.JsonSerializer.Serialize(request.DetectionTypes);
                var typesSetting = await _context.SystemSettings
                    .FirstOrDefaultAsync(s => s.SettingKey == "PiiProtection.DetectionTypes");
                
                if (typesSetting != null)
                {
                    typesSetting.SettingValue = typesJson;
                    typesSetting.UpdatedAt = DateTime.UtcNow;
                }
                else
                {
                    _context.SystemSettings.Add(new Models.SystemSetting
                    {
                        SettingKey = "PiiProtection.DetectionTypes",
                        SettingValue = typesJson,
                        DataType = "JSON",
                        Category = "Privacy",
                        Description = "감지할 개인정보 유형 목록 (JSON 배열)",
                        IsEncrypted = false,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    });
                }
            }

            await _context.SaveChangesAsync();

            _logger.LogInformation("PII protection settings updated by user {UserId}", 
                User.FindFirst(ClaimTypes.NameIdentifier)?.Value);

            return Ok(new { message = "설정이 저장되었습니다." });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating PII protection settings");
            return StatusCode(500, ErrorResponseDto.InternalError("설정 저장 중 오류가 발생했습니다."));
        }
    }
}
