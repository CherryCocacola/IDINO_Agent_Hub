using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilApiKeysController — DocUtil LLM API Key 운영자 BFF (Phase 10.2e)
//
// 통합 비전(P1 Control Plane / P5 인증 / R2 단일 진입점):
//   AgentHub 운영자 콘솔이 DocUtil 의 LLM API Key 카탈로그(등록/조회/회수/검증)까지 단일
//   진입점에서 운영. Phase 10.1/10.2a~10.2d 와 동일 BFF 패턴.
//
// 도메인 특징(다른 BFF 와 차이):
//   - 평문 API Key 는 POST 응답에 단 한 번도 노출되지 않는다 — 마스킹 prefix 만 반환됨.
//     (DocUtil 측 ApiKeyResponse 가 ApiKeyPrefix 만 노출 — 평문 저장 X / 즉시 폐기 정책)
//   - VerifyApiKey 는 DocUtil 측이 실제 LLM 프로바이더에 1회 호출하는 비동기 검증.
//     장시간 소요 가능성 — 본 BFF 는 cancellation 만 전달, 별도 폴링 X.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//   2. TTL 캐시 — 목록 5분 (API Key 카탈로그는 매우 민감, 짧게 유지)
//      prefix `du:apikey:list:` + namespace `docutil-api-keys`
//   3. 4xx/5xx → 502 ErrorResponseDto 한국어 매핑
//   4. mutation(POST/DELETE/verify) 성공/실패 모두 invalidate (10.1b ghost 처리 패턴)
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 DocUtil LLM API Key 관리 BFF — Phase 10.2e.
/// AgentHub Vue 콘솔의 `/admin/docutil-api-keys` 페이지가 호출하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/docutil/api-keys")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminDocUtilApiKeysController : ControllerBase
{
    private const string ListCachePrefix = "du:apikey:list:";
    public const string CacheVersionNamespace = "docutil-api-keys";

    // API Key 카탈로그는 매우 민감 — TTL 짧게(5분) 유지.
    private static readonly TimeSpan ListCacheTtl = TimeSpan.FromMinutes(5);

    private readonly IDocUtilClient _docUtilClient;
    private readonly CachingService _cachingService;
    private readonly ILogger<AdminDocUtilApiKeysController> _logger;

    public AdminDocUtilApiKeysController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        ILogger<AdminDocUtilApiKeysController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _logger = logger;
    }

    /// <summary>
    /// LLM API Key 캐시 일괄 무효화 — mutation 성공/실패 모두 호출(ghost 정합성 보장).
    /// 캐시 무효화는 best-effort — 실패는 swallow + 경고 로그.
    /// </summary>
    private async Task InvalidateApiKeysCacheAsync()
    {
        try
        {
            var v = await _cachingService.IncrementVersionAsync(CacheVersionNamespace);
            _logger.LogInformation("DocUtil API Key 캐시 invalidate - newVersion={V}", v);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "DocUtil API Key 캐시 invalidate 실패(무시)");
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // GET /api/admin/docutil/api-keys — 목록(페이징)
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// LLM API Key 목록(페이징) — DocUtil `/api/v1/api-keys` 위임 + 5분 캐시.
    /// 응답의 ``ApiKeyPrefix`` 는 마스킹된 prefix — 평문은 등록 시 단 한 번만 반환된다.
    /// </summary>
    /// <param name="page">페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 20, 1~100).</param>
    [HttpGet("")]
    public async Task<ActionResult<DocUtilApiKeyList>> ListApiKeys(
        [FromQuery] int page = 1,
        [FromQuery] int size = 20,
        CancellationToken ct = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 100) size = 20;

        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{ListCachePrefix}v{version}:{page}|{size}";

        var cached = await _cachingService.GetAsync<CachedApiKeyListDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil API Key 목록 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil API Key 목록 캐시 miss - key={Key}", cacheKey);

        try
        {
            var list = await _docUtilClient.ListApiKeysAsync(page, size, ct);
            await _cachingService.SetAsync(cacheKey, CachedApiKeyListDto.From(list), ListCacheTtl);
            return Ok(list);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil API Key 목록 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil API Key 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // POST /api/admin/docutil/api-keys — 등록
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// LLM API Key 등록 — DocUtil `/api/v1/api-keys` (POST, ApiKeyCreate).
    /// <para>
    /// 평문 ``ApiKey`` 는 요청 본문으로 한 번만 전송된다. DocUtil 측이 AES 암호화 후 즉시 폐기.
    /// 응답에는 마스킹 prefix 만 포함되며, 같은 키 값을 재조회할 수 없다.
    /// </para>
    /// 성공/실패 모두 캐시 일괄 무효화.
    /// </summary>
    [HttpPost("")]
    public async Task<ActionResult<DocUtilApiKeyDetail>> CreateApiKey(
        [FromBody] DocUtilCreateApiKeyRequest request,
        CancellationToken ct = default)
    {
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (string.IsNullOrWhiteSpace(request.LlmName))
        {
            return BadRequest(ErrorResponseDto.BadRequest("LLM 프로바이더 이름이 비어 있습니다."));
        }
        if (request.LlmName.Length > 64)
        {
            return BadRequest(ErrorResponseDto.BadRequest("LLM 프로바이더 이름은 64자 이하여야 합니다."));
        }
        if (string.IsNullOrWhiteSpace(request.ApiKey))
        {
            return BadRequest(ErrorResponseDto.BadRequest("API Key 평문이 비어 있습니다."));
        }
        // 평문 키 길이는 프로바이더별 상이 — 상한만 가볍게 차단(과도한 입력 방지).
        if (request.ApiKey.Length > 4096)
        {
            return BadRequest(ErrorResponseDto.BadRequest("API Key 평문 길이가 너무 깁니다."));
        }

        try
        {
            var created = await _docUtilClient.CreateApiKeyAsync(request, ct);
            // 평문 키는 절대 로그에 남기지 않음 — id/llm_name/prefix 만 기록.
            _logger.LogInformation(
                "운영자 DocUtil API Key 등록 성공 - KeyId={Id}, Llm={Llm}, Prefix={Prefix}",
                created.Id, created.LlmName, created.ApiKeyPrefix);
            await InvalidateApiKeysCacheAsync();
            return CreatedAtAction(nameof(ListApiKeys), new { page = 1, size = 20 }, created);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil API Key 등록 실패 (Llm={Llm})", request.LlmName);
            await InvalidateApiKeysCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil API Key 등록에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // DELETE /api/admin/docutil/api-keys/{keyId} — 회수
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// LLM API Key 회수(삭제) — DocUtil `/api/v1/api-keys/{key_id}` (DELETE 204).
    /// 성공/실패 모두 캐시 일괄 무효화.
    /// </summary>
    [HttpDelete("{keyId}")]
    public async Task<IActionResult> DeleteApiKey(
        string keyId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(keyId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("API Key 식별자가 비어 있습니다."));
        }

        try
        {
            await _docUtilClient.DeleteApiKeyAsync(keyId, ct);
            _logger.LogInformation("운영자 DocUtil API Key 삭제 성공 - KeyId={Id}", keyId);
            await InvalidateApiKeysCacheAsync();
            return NoContent();
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil API Key 삭제 실패 (id={Id})", keyId);
            await InvalidateApiKeysCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil API Key 삭제에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // POST /api/admin/docutil/api-keys/{keyId}/verify — 검증
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// LLM API Key 검증 — DocUtil `/api/v1/api-keys/{key_id}/verify` (POST).
    /// <para>
    /// DocUtil 측이 복호화된 키로 LLM 프로바이더에 1회 호출하고 ``is_valid`` + ``message`` 반환.
    /// 외부 LLM 응답 지연으로 수십 초 소요 가능 — 클라이언트 UX 에서 별도 로딩 처리 권장.
    /// </para>
    /// 검증 성공 시 DocUtil 측이 ApiKey.is_verified 를 true 로 갱신하므로 캐시 invalidate.
    /// </summary>
    [HttpPost("{keyId}/verify")]
    public async Task<ActionResult<DocUtilApiKeyVerifyResult>> VerifyApiKey(
        string keyId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(keyId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("API Key 식별자가 비어 있습니다."));
        }

        try
        {
            var result = await _docUtilClient.VerifyApiKeyAsync(keyId, ct);
            _logger.LogInformation(
                "운영자 DocUtil API Key 검증 결과 - KeyId={Id}, IsValid={Valid}, Msg={Msg}",
                keyId, result.IsValid, result.Message);
            // 검증 성공 시 IsVerified 가 갱신되므로 캐시 invalidate.
            // 실패 시에도 상태 변경 가능성 있어 동일 처리.
            await InvalidateApiKeysCacheAsync();
            return Ok(result);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil API Key 검증 실패 (id={Id})", keyId);
            await InvalidateApiKeysCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil API Key 검증에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // 캐시 직렬화용 DTO — record 가 JSON 직렬화 가능하지만 ToRecord/From 패턴 통일.
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// 캐시 직렬화용 API Key 행 DTO — record 의 positional 인수가 JSON 라운드트립 보장.
    /// </summary>
    public sealed class CachedApiKeyDto
    {
        public string Id { get; set; } = string.Empty;
        public string OrganizationId { get; set; } = string.Empty;
        public string LlmName { get; set; } = string.Empty;
        public string ApiKeyPrefix { get; set; } = string.Empty;
        public bool IsVerified { get; set; }
        public string? RegisteredBy { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }

        public static CachedApiKeyDto From(DocUtilApiKeyDetail r) => new()
        {
            Id = r.Id,
            OrganizationId = r.OrganizationId,
            LlmName = r.LlmName,
            ApiKeyPrefix = r.ApiKeyPrefix,
            IsVerified = r.IsVerified,
            RegisteredBy = r.RegisteredBy,
            CreatedAt = r.CreatedAt,
            UpdatedAt = r.UpdatedAt,
        };

        public DocUtilApiKeyDetail ToRecord() => new(
            Id, OrganizationId, LlmName, ApiKeyPrefix, IsVerified, RegisteredBy, CreatedAt, UpdatedAt);
    }

    /// <summary>캐시 직렬화용 API Key 목록 DTO.</summary>
    public sealed class CachedApiKeyListDto
    {
        public CachedApiKeyDto[] Items { get; set; } = Array.Empty<CachedApiKeyDto>();
        public long Total { get; set; }
        public int Page { get; set; }
        public int Size { get; set; }

        public static CachedApiKeyListDto From(DocUtilApiKeyList l) => new()
        {
            Items = l.Items.Select(CachedApiKeyDto.From).ToArray(),
            Total = l.Total,
            Page = l.Page,
            Size = l.Size,
        };

        public DocUtilApiKeyList ToRecord() => new(
            Items.Select(i => i.ToRecord()).ToArray(),
            Total, Page, Size);
    }
}
