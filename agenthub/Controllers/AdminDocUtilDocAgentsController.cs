using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilDocAgentsController — DocUtil 자체 에이전트 운영자 BFF (Phase 10.2e)
//
// 통합 비전(P1 Control Plane / P5 인증 / R2 단일 진입점):
//   AgentHub 운영자 콘솔이 DocUtil 의 자체 에이전트(챗봇 / 보고서 / 제안서 / 회의록용
//   페르소나) CRUD 까지 단일 진입점에서 운영. Phase 10.1/10.2a~10.2d 와 동일 BFF 패턴.
//
// ⚠ 도메인 구분(중요):
//   - DocUtil 의 "Agent" = DocUtil 챗봇용 system_prompt / temperature / max_tokens 페르소나.
//   - AgentHub 의 "Agent" = LLM 라우팅 / RAG / 워크플로우 호스트(별개 엔티티).
//   두 도메인은 별도로 관리되며 UI 에 "DocUtil 에이전트(챗봇용 페르소나)" 라고 명확히 표기한다.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//   2. TTL 캐시(목록/상세 10분, version-key invalidate) — 카탈로그성, 보고서 템플릿과 동일 정책
//      prefix `du:docagent:list:` / `du:docagent:detail:` + namespace `docutil-doc-agents`
//   3. 4xx/5xx → 502 ErrorResponseDto 한국어 매핑
//   4. mutation(POST/PUT/DELETE) 성공/실패 모두 invalidate (10.1b ghost 처리 패턴)
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 DocUtil 에이전트(챗봇용 페르소나) 관리 BFF — Phase 10.2e.
/// AgentHub Vue 콘솔의 `/admin/docutil-doc-agents` 페이지가 호출하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/docutil/agents")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminDocUtilDocAgentsController : ControllerBase
{
    private const string ListCachePrefix = "du:docagent:list:";
    private const string DetailCachePrefix = "du:docagent:detail:";
    public const string CacheVersionNamespace = "docutil-doc-agents";

    private static readonly TimeSpan ListCacheTtl = TimeSpan.FromMinutes(10);
    private static readonly TimeSpan DetailCacheTtl = TimeSpan.FromMinutes(10);

    private readonly IDocUtilClient _docUtilClient;
    private readonly CachingService _cachingService;
    private readonly ILogger<AdminDocUtilDocAgentsController> _logger;

    public AdminDocUtilDocAgentsController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        ILogger<AdminDocUtilDocAgentsController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _logger = logger;
    }

    /// <summary>
    /// DocUtil 에이전트 캐시 일괄 무효화 — mutation 성공/실패 모두 호출(ghost 정합성 보장).
    /// </summary>
    private async Task InvalidateDocAgentsCacheAsync()
    {
        try
        {
            var v = await _cachingService.IncrementVersionAsync(CacheVersionNamespace);
            _logger.LogInformation("DocUtil 에이전트 캐시 invalidate - newVersion={V}", v);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "DocUtil 에이전트 캐시 invalidate 실패(무시)");
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // GET /api/admin/docutil/agents — 목록(페이징 + agent_type 필터)
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// DocUtil 에이전트 목록 — DocUtil `/api/v1/agents` 위임 + 10분 캐시.
    /// </summary>
    /// <param name="page">페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 20, 1~100).</param>
    /// <param name="agentType">에이전트 유형 필터(chatbot / report / proposal / minutes 등). 선택.</param>
    [HttpGet("")]
    public async Task<ActionResult<DocUtilDocAgentList>> ListDocAgents(
        [FromQuery] int page = 1,
        [FromQuery] int size = 20,
        [FromQuery] string? agentType = null,
        CancellationToken ct = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 100) size = 20;

        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        string Normalize(string? s) => string.IsNullOrWhiteSpace(s) ? "_" : s.Trim().ToLowerInvariant();
        var cacheKey = $"{ListCachePrefix}v{version}:{page}|{size}|{Normalize(agentType)}";

        var cached = await _cachingService.GetAsync<CachedDocAgentListDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 에이전트 목록 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 에이전트 목록 캐시 miss - key={Key}", cacheKey);

        try
        {
            var list = await _docUtilClient.ListDocAgentsAsync(agentType, page, size, ct);
            await _cachingService.SetAsync(cacheKey, CachedDocAgentListDto.From(list), ListCacheTtl);
            return Ok(list);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 에이전트 목록 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 에이전트 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // GET /api/admin/docutil/agents/{agentId} — 단건
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// DocUtil 에이전트 단건 — DocUtil `/api/v1/agents/{agent_id}` 위임 + 10분 캐시.
    /// 404 응답은 한국어 ErrorResponseDto 로 정규화.
    /// </summary>
    [HttpGet("{agentId}")]
    public async Task<ActionResult<DocUtilDocAgentDetail>> GetDocAgent(
        string agentId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(agentId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("에이전트 식별자가 비어 있습니다."));
        }

        var version = await _cachingService.GetVersionAsync(CacheVersionNamespace);
        var cacheKey = $"{DetailCachePrefix}v{version}:{agentId}";

        var cached = await _cachingService.GetAsync<CachedDocAgentDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 에이전트 상세 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 에이전트 상세 캐시 miss - key={Key}", cacheKey);

        try
        {
            var detail = await _docUtilClient.GetDocAgentAsync(agentId, ct);
            if (detail == null)
            {
                return NotFound(ErrorResponseDto.NotFound("DocUtil 에이전트를 찾을 수 없습니다."));
            }
            await _cachingService.SetAsync(cacheKey, CachedDocAgentDto.From(detail), DetailCacheTtl);
            return Ok(detail);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 에이전트 상세 조회 실패 (id={Id})", agentId);
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 에이전트 상세를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // POST /api/admin/docutil/agents — 생성
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// DocUtil 에이전트 생성 — DocUtil `/api/v1/agents` (POST, AgentCreate).
    /// 성공/실패 모두 캐시 일괄 무효화.
    /// </summary>
    [HttpPost("")]
    public async Task<ActionResult<DocUtilDocAgentDetail>> CreateDocAgent(
        [FromBody] DocUtilCreateDocAgentRequest request,
        CancellationToken ct = default)
    {
        var err = ValidateCreate(request);
        if (err != null) return BadRequest(ErrorResponseDto.BadRequest(err));

        try
        {
            var created = await _docUtilClient.CreateDocAgentAsync(request, ct);
            _logger.LogInformation(
                "운영자 DocUtil 에이전트 생성 성공 - AgentId={Id}, Name={Name}, Type={Type}",
                created.Id, created.Name, created.AgentType);
            await InvalidateDocAgentsCacheAsync();
            return CreatedAtAction(nameof(GetDocAgent), new { agentId = created.Id }, created);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 에이전트 생성 실패 (Name={Name})", request?.Name);
            await InvalidateDocAgentsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 에이전트 생성에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // PUT /api/admin/docutil/agents/{agentId} — 부분 수정
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// DocUtil 에이전트 부분 수정 — DocUtil `/api/v1/agents/{agent_id}` (PUT, AgentUpdate).
    /// null 필드는 직렬화 제외 — 보낸 필드만 갱신된다.
    /// 성공/실패 모두 캐시 일괄 무효화.
    /// </summary>
    [HttpPut("{agentId}")]
    public async Task<ActionResult<DocUtilDocAgentDetail>> UpdateDocAgent(
        string agentId,
        [FromBody] DocUtilUpdateDocAgentRequest request,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(agentId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("에이전트 식별자가 비어 있습니다."));
        }
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        var err = ValidateUpdate(request);
        if (err != null) return BadRequest(ErrorResponseDto.BadRequest(err));

        try
        {
            var updated = await _docUtilClient.UpdateDocAgentAsync(agentId, request, ct);
            _logger.LogInformation(
                "운영자 DocUtil 에이전트 수정 성공 - AgentId={Id}, Name={Name}",
                updated.Id, updated.Name);
            await InvalidateDocAgentsCacheAsync();
            return Ok(updated);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 에이전트 수정 실패 (id={Id})", agentId);
            await InvalidateDocAgentsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 에이전트 수정에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // DELETE /api/admin/docutil/agents/{agentId} — 삭제
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// DocUtil 에이전트 삭제 — DocUtil `/api/v1/agents/{agent_id}` (DELETE 204).
    /// 성공/실패 모두 캐시 일괄 무효화.
    /// </summary>
    [HttpDelete("{agentId}")]
    public async Task<IActionResult> DeleteDocAgent(
        string agentId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(agentId))
        {
            return BadRequest(ErrorResponseDto.BadRequest("에이전트 식별자가 비어 있습니다."));
        }

        try
        {
            await _docUtilClient.DeleteDocAgentAsync(agentId, ct);
            _logger.LogInformation("운영자 DocUtil 에이전트 삭제 성공 - AgentId={Id}", agentId);
            await InvalidateDocAgentsCacheAsync();
            return NoContent();
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 에이전트 삭제 실패 (id={Id})", agentId);
            await InvalidateDocAgentsCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 에이전트 삭제에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // 검증 헬퍼 — DocUtil schemas.py 의 Field 제약과 1:1 매핑
    // ══════════════════════════════════════════════════════════════════════

    private static string? ValidateCreate(DocUtilCreateDocAgentRequest? r)
    {
        if (r == null) return "요청 본문이 비어 있습니다.";
        if (string.IsNullOrWhiteSpace(r.Name)) return "에이전트 이름이 비어 있습니다.";
        if (r.Name.Length > 255) return "에이전트 이름은 255자 이하여야 합니다.";
        if (r.Description != null && r.Description.Length > 2000) return "에이전트 설명은 2000자 이하여야 합니다.";
        if (string.IsNullOrWhiteSpace(r.AgentType)) return "에이전트 유형이 비어 있습니다.";
        if (r.AgentType.Length > 20) return "에이전트 유형은 20자 이하여야 합니다.";
        if (string.IsNullOrWhiteSpace(r.SystemPrompt)) return "시스템 프롬프트가 비어 있습니다.";
        if (r.LlmProvider != null && r.LlmProvider.Length > 50) return "LLM 프로바이더는 50자 이하여야 합니다.";
        if (r.LlmModel != null && r.LlmModel.Length > 255) return "LLM 모델은 255자 이하여야 합니다.";
        if (r.Temperature < 0.0 || r.Temperature > 2.0) return "temperature 는 0.0 ~ 2.0 범위여야 합니다.";
        if (r.MaxTokens < 1 || r.MaxTokens > 128000) return "max_tokens 는 1 ~ 128000 범위여야 합니다.";
        return null;
    }

    private static string? ValidateUpdate(DocUtilUpdateDocAgentRequest r)
    {
        if (r.Name != null)
        {
            if (string.IsNullOrWhiteSpace(r.Name)) return "에이전트 이름이 비어 있습니다.";
            if (r.Name.Length > 255) return "에이전트 이름은 255자 이하여야 합니다.";
        }
        if (r.Description != null && r.Description.Length > 2000) return "에이전트 설명은 2000자 이하여야 합니다.";
        if (r.AgentType != null && r.AgentType.Length > 20) return "에이전트 유형은 20자 이하여야 합니다.";
        if (r.SystemPrompt != null && string.IsNullOrWhiteSpace(r.SystemPrompt)) return "시스템 프롬프트가 비어 있습니다.";
        if (r.LlmProvider != null && r.LlmProvider.Length > 50) return "LLM 프로바이더는 50자 이하여야 합니다.";
        if (r.LlmModel != null && r.LlmModel.Length > 255) return "LLM 모델은 255자 이하여야 합니다.";
        if (r.Temperature.HasValue && (r.Temperature < 0.0 || r.Temperature > 2.0))
            return "temperature 는 0.0 ~ 2.0 범위여야 합니다.";
        if (r.MaxTokens.HasValue && (r.MaxTokens < 1 || r.MaxTokens > 128000))
            return "max_tokens 는 1 ~ 128000 범위여야 합니다.";
        return null;
    }

    // ══════════════════════════════════════════════════════════════════════
    // 캐시 직렬화용 DTO
    // ══════════════════════════════════════════════════════════════════════

    public sealed class CachedDocAgentDto
    {
        public string Id { get; set; } = string.Empty;
        public string OrganizationId { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string? Description { get; set; }
        public string AgentType { get; set; } = string.Empty;
        public string SystemPrompt { get; set; } = string.Empty;
        public string? LlmProvider { get; set; }
        public string LlmModel { get; set; } = "gpt-4o";
        public double Temperature { get; set; }
        public int MaxTokens { get; set; }
        public bool IsActive { get; set; }
        public string CreatedBy { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }

        public static CachedDocAgentDto From(DocUtilDocAgentDetail r) => new()
        {
            Id = r.Id,
            OrganizationId = r.OrganizationId,
            Name = r.Name,
            Description = r.Description,
            AgentType = r.AgentType,
            SystemPrompt = r.SystemPrompt,
            LlmProvider = r.LlmProvider,
            LlmModel = r.LlmModel,
            Temperature = r.Temperature,
            MaxTokens = r.MaxTokens,
            IsActive = r.IsActive,
            CreatedBy = r.CreatedBy,
            CreatedAt = r.CreatedAt,
            UpdatedAt = r.UpdatedAt,
        };

        public DocUtilDocAgentDetail ToRecord() => new(
            Id, OrganizationId, Name, Description, AgentType, SystemPrompt,
            LlmProvider, LlmModel, Temperature, MaxTokens, IsActive, CreatedBy, CreatedAt, UpdatedAt);
    }

    public sealed class CachedDocAgentListDto
    {
        public CachedDocAgentDto[] Items { get; set; } = Array.Empty<CachedDocAgentDto>();
        public long Total { get; set; }
        public int Page { get; set; }
        public int Size { get; set; }

        public static CachedDocAgentListDto From(DocUtilDocAgentList l) => new()
        {
            Items = l.Items.Select(CachedDocAgentDto.From).ToArray(),
            Total = l.Total,
            Page = l.Page,
            Size = l.Size,
        };

        public DocUtilDocAgentList ToRecord() => new(
            Items.Select(i => i.ToRecord()).ToArray(),
            Total, Page, Size);
    }
}
