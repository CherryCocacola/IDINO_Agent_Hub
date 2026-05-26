using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilSettingsController — DocUtil 시스템 설정 운영자 BFF (트랙 A1 Phase B)
//
// 통합 비전 (P1 Control Plane / P5 인증 / R2 단일 진입점):
//   AgentHub 운영자 콘솔이 DocUtil 의 시스템 설정(general/security/storage) — 조회 + 저장 —
//   까지 단일 진입점에서 운영. Phase 10.2c FAQ Controller 와 동일 BFF 패턴.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")] (DocUtil 측도 admin/super_admin 강제)
//   2. TTL 캐시 + version-key invalidate (5분 TTL):
//      - prefix `du:settings:`, version namespace `docutil-settings`
//      - mutation 성공/실패 모두 invalidate (10.1b ghost 처리 패턴 — 부분 적용 위험 회피)
//   3. 4xx/5xx → 502 ErrorResponseDto 한국어 매핑
//
// 캐시 namespace 격리:
//   `docutil-settings` 는 다른 도메인(FAQ/Reports/Templates)과 의도적 분리.
//   설정 저장이 다른 캐시를 cascade 무효화하지 않음(설정은 독립 도메인).
//
// 주의 (DocUtil 측 현재 상태):
//   PUT /settings/* 는 현재 stub — {status, saved} 만 반환하고 영구 저장 미구현.
//   AgentHub BFF 는 이 stub 응답을 그대로 200/204 로 전달(클라이언트는 성공 인지).
//   DocUtil 측이 영구화되면 본 Controller 무변경 — 응답만 자동 반영.
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 DocUtil 시스템 설정 관리 BFF — 트랙 A1 Phase B.
/// AgentHub Vue 콘솔의 `/admin/docutil-settings` 페이지가 호출하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/docutil/settings")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminDocUtilSettingsController : ControllerBase
{
    private const string CacheKeyPrefix = "du:settings:";
    public const string CacheVersionNamespace = "docutil-settings";
    private static readonly TimeSpan CacheTtl = TimeSpan.FromMinutes(5);

    private readonly IDocUtilClient _docUtilClient;
    private readonly CachingService _cachingService;
    private readonly ILogger<AdminDocUtilSettingsController> _logger;

    public AdminDocUtilSettingsController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        ILogger<AdminDocUtilSettingsController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _logger = logger;
    }

    /// <summary>
    /// 설정 캐시 일괄 무효화 — version-key 패턴.
    /// mutation 성공/실패 모두 호출(10.1b ghost 정합성 보장).
    /// 실패는 swallow + 경고 로그(캐시 무효화는 best-effort).
    /// </summary>
    private async Task InvalidateSettingsCacheAsync()
    {
        try
        {
            var v = await _cachingService.IncrementVersionAsync(CacheVersionNamespace);
            _logger.LogInformation("DocUtil 시스템 설정 캐시 invalidate - newVersion={V}", v);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "DocUtil 시스템 설정 캐시 invalidate 실패(무시)");
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 설정 조회/저장
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 시스템 설정 전체 조회 — DocUtil `/api/v1/settings` 위임 + 5분 캐시.
    /// </summary>
    [HttpGet("")]
    public async Task<ActionResult<DocUtilSettings>> GetSettings(CancellationToken ct = default)
    {
        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{CacheKeyPrefix}v{version}:all";

        var cached = await _cachingService.GetAsync<CachedSettingsDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 시스템 설정 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 시스템 설정 캐시 miss - key={Key}", cacheKey);

        try
        {
            var data = await _docUtilClient.GetSettingsAsync(ct);
            await _cachingService.SetAsync(cacheKey, CachedSettingsDto.From(data), CacheTtl);
            return Ok(data);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 시스템 설정 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "시스템 설정을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 일반 설정 저장 — DocUtil `/api/v1/settings/general` (PUT, stub).
    /// 성공/실패 모두 캐시 일괄 무효화.
    /// </summary>
    [HttpPut("general")]
    public async Task<IActionResult> UpdateGeneral(
        [FromBody] DocUtilGeneralSettings payload,
        CancellationToken ct = default)
    {
        if (payload == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(payload.DefaultLanguage))
        {
            return BadRequest(ErrorResponseDto.BadRequest("기본 언어 코드가 비어 있습니다."));
        }
        if (payload.DefaultLanguage.Length > 16)
        {
            return BadRequest(ErrorResponseDto.BadRequest("기본 언어 코드는 16자 이하여야 합니다."));
        }

        try
        {
            await _docUtilClient.UpdateSettingsGeneralAsync(payload, ct);
            _logger.LogInformation("운영자 DocUtil 일반 설정 저장 성공");
            await InvalidateSettingsCacheAsync();
            return NoContent();
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 일반 설정 저장 실패");
            await InvalidateSettingsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "일반 설정 저장에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 보안 설정 저장 — DocUtil `/api/v1/settings/security` (PUT, stub).
    /// </summary>
    [HttpPut("security")]
    public async Task<IActionResult> UpdateSecurity(
        [FromBody] DocUtilSecuritySettings payload,
        CancellationToken ct = default)
    {
        if (payload == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (payload.PasswordMinLength < 4 || payload.PasswordMinLength > 128)
        {
            return BadRequest(ErrorResponseDto.BadRequest("비밀번호 최소 길이는 4~128 사이여야 합니다."));
        }
        if (payload.SessionTimeoutMinutes < 5 || payload.SessionTimeoutMinutes > 1440)
        {
            return BadRequest(ErrorResponseDto.BadRequest("세션 만료(분)는 5~1440 사이여야 합니다."));
        }

        try
        {
            await _docUtilClient.UpdateSettingsSecurityAsync(payload, ct);
            _logger.LogInformation("운영자 DocUtil 보안 설정 저장 성공");
            await InvalidateSettingsCacheAsync();
            return NoContent();
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 보안 설정 저장 실패");
            await InvalidateSettingsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "보안 설정 저장에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 스토리지 설정 저장 — DocUtil `/api/v1/settings/storage` (PUT, stub).
    /// 주의: DocUtil 측은 MinIO 연결 상태/엔드포인트/총·사용량을 자동 측정 — 본 PUT 은 운영자가
    /// 메타값을 임시 덮어쓸 때만 사용. 현재 stub 이므로 영구화는 DocUtil 차기 트랙 의존.
    /// </summary>
    [HttpPut("storage")]
    public async Task<IActionResult> UpdateStorage(
        [FromBody] DocUtilStorageSettings payload,
        CancellationToken ct = default)
    {
        if (payload == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (payload.TotalStorageBytes < 0 || payload.UsedStorageBytes < 0)
        {
            return BadRequest(ErrorResponseDto.BadRequest("저장 용량은 0 이상이어야 합니다."));
        }

        try
        {
            await _docUtilClient.UpdateSettingsStorageAsync(payload, ct);
            _logger.LogInformation("운영자 DocUtil 스토리지 설정 저장 성공");
            await InvalidateSettingsCacheAsync();
            return NoContent();
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 스토리지 설정 저장 실패");
            await InvalidateSettingsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "스토리지 설정 저장에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 캐시 wrapper DTO (record 가 아닌 클래스 — System.Text.Json 캐시 역직렬화 안정성)
    // ──────────────────────────────────────────────────────────────────────

    private sealed class CachedGeneralDto
    {
        public string DefaultLanguage { get; set; } = "ko";
        public bool MaintenanceMode { get; set; }
    }

    private sealed class CachedSecurityDto
    {
        public int PasswordMinLength { get; set; } = 8;
        public bool PasswordRequireUppercase { get; set; } = true;
        public bool PasswordRequireNumber { get; set; } = true;
        public bool PasswordRequireSpecial { get; set; } = true;
        public int SessionTimeoutMinutes { get; set; } = 30;
    }

    private sealed class CachedStorageDto
    {
        public bool MinioConnected { get; set; }
        public string MinioEndpoint { get; set; } = string.Empty;
        public long TotalStorageBytes { get; set; }
        public long UsedStorageBytes { get; set; }
    }

    private sealed class CachedSettingsDto
    {
        public CachedGeneralDto General { get; set; } = new();
        public CachedSecurityDto Security { get; set; } = new();
        public CachedStorageDto Storage { get; set; } = new();

        public static CachedSettingsDto From(DocUtilSettings s) => new()
        {
            General = new CachedGeneralDto
            {
                DefaultLanguage = s.General.DefaultLanguage,
                MaintenanceMode = s.General.MaintenanceMode,
            },
            Security = new CachedSecurityDto
            {
                PasswordMinLength = s.Security.PasswordMinLength,
                PasswordRequireUppercase = s.Security.PasswordRequireUppercase,
                PasswordRequireNumber = s.Security.PasswordRequireNumber,
                PasswordRequireSpecial = s.Security.PasswordRequireSpecial,
                SessionTimeoutMinutes = s.Security.SessionTimeoutMinutes,
            },
            Storage = new CachedStorageDto
            {
                MinioConnected = s.Storage.MinioConnected,
                MinioEndpoint = s.Storage.MinioEndpoint,
                TotalStorageBytes = s.Storage.TotalStorageBytes,
                UsedStorageBytes = s.Storage.UsedStorageBytes,
            },
        };

        public DocUtilSettings ToRecord() => new(
            new DocUtilGeneralSettings(General.DefaultLanguage, General.MaintenanceMode),
            new DocUtilSecuritySettings(
                Security.PasswordMinLength,
                Security.PasswordRequireUppercase,
                Security.PasswordRequireNumber,
                Security.PasswordRequireSpecial,
                Security.SessionTimeoutMinutes),
            new DocUtilStorageSettings(
                Storage.MinioConnected,
                Storage.MinioEndpoint,
                Storage.TotalStorageBytes,
                Storage.UsedStorageBytes));
    }
}
