using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilEvaluationController — DocUtil 평가 운영자 BFF (Phase 10.2b)
//
// 통합 비전(P1 Control Plane / P5 인증 / R2 단일 진입점 / P8 RAG 단일 권위):
//   AgentHub 운영자 콘솔이 DocUtil 의 RAG 품질 평가(Evaluation) — 4 가중치 설정 +
//   평가 실행 + 로그 + 트렌드 + 실행 이력 — 까지 단일 진입점에서 관리.
//   Phase 10.1/10.2a 와 동일 BFF 패턴 적용.
//
// 책임 범위:
//   1. 인증/권한 게이트 — [Authorize(Roles = "Admin,SuperAdmin")]
//   2. TTL 캐시 분리:
//      - `du:eval:cfg:` (5분 TTL) + version-key invalidate (`docutil-evaluation-config`)
//      - `du:eval:logs:` / `du:eval:runs:` (1분 TTL) — 실시간성 우선, version-key 미적용(TTL 만)
//      - `du:eval:questions:` (5분 TTL) — 카탈로그성
//      - `du:eval:trend:` (5분 TTL) — 일별 집계라 빠른 변동 없음
//      - run 트리거(POST /run) 는 캐시 미적용
//   3. 4xx/5xx → 502 ErrorResponseDto 한국어 매핑
//   4. config mutation 시 invalidate(`docutil-evaluation-config` namespace)
//   5. evaluation/run 실행은 비용/시간 영향 — 운영자 의도 명시 시에만 호출됨
//
// 캐시 namespace 분리 사유:
//   `docutil-search-scopes`(10.2b 검색범위) / `docutil-collections`(10.1c) 와 의도적으로
//   분리 — 평가 도메인은 별도 BC. config 만 version-key invalidate 적용.
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// 운영자 DocUtil 평가(RAG 품질) 관리 BFF — Phase 10.2b.
/// AgentHub Vue 콘솔의 `/admin/docutil-evaluation` 페이지가 호출하는 진입점.
/// </summary>
[ApiController]
[Route("api/admin/docutil/evaluation")]
[Authorize(Roles = "Admin,SuperAdmin")]
public class AdminDocUtilEvaluationController : ControllerBase
{
    private const string ConfigCacheKeyPrefix = "du:eval:cfg:";
    private const string LogsCacheKeyPrefix = "du:eval:logs:";
    private const string RunsCacheKeyPrefix = "du:eval:runs:";
    private const string QuestionsCacheKeyPrefix = "du:eval:questions:";
    private const string TrendCacheKeyPrefix = "du:eval:trend:";
    public const string ConfigCacheVersionNamespace = "docutil-evaluation-config";

    private static readonly TimeSpan ConfigCacheTtl = TimeSpan.FromMinutes(5);
    private static readonly TimeSpan ShortCacheTtl = TimeSpan.FromMinutes(1);
    private static readonly TimeSpan MediumCacheTtl = TimeSpan.FromMinutes(5);

    private readonly IDocUtilClient _docUtilClient;
    private readonly CachingService _cachingService;
    private readonly ILogger<AdminDocUtilEvaluationController> _logger;

    public AdminDocUtilEvaluationController(
        IDocUtilClient docUtilClient,
        CachingService cachingService,
        ILogger<AdminDocUtilEvaluationController> logger)
    {
        _docUtilClient = docUtilClient;
        _cachingService = cachingService;
        _logger = logger;
    }

    /// <summary>
    /// 평가 설정 캐시 일괄 무효화 — config mutation 시에만.
    /// 실패는 swallow + 경고 로그(캐시 무효화는 best-effort).
    /// </summary>
    private async Task InvalidateEvaluationConfigCacheAsync()
    {
        try
        {
            var v = await _cachingService.IncrementVersionAsync(ConfigCacheVersionNamespace);
            _logger.LogInformation("DocUtil 평가 설정 캐시 invalidate - newVersion={V}", v);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "DocUtil 평가 설정 캐시 invalidate 실패(무시)");
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 평가 설정 — GET / PUT
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 평가 가중치 설정 조회 — DocUtil `/api/v1/evaluation/config` 위임 + 5분 캐시.
    /// </summary>
    [HttpGet("config")]
    public async Task<ActionResult<DocUtilEvaluationConfig>> GetEvaluationConfig(CancellationToken ct = default)
    {
        var version = await _cachingService.GetVersionAsync(ConfigCacheVersionNamespace);
        var cacheKey = $"{ConfigCacheKeyPrefix}v{version}";

        var cached = await _cachingService.GetAsync<CachedEvaluationConfigDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 평가 설정 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }
        _logger.LogDebug("DocUtil 평가 설정 캐시 miss - key={Key}", cacheKey);

        try
        {
            var config = await _docUtilClient.GetEvaluationConfigAsync(ct);
            await _cachingService.SetAsync(cacheKey, CachedEvaluationConfigDto.From(config), ConfigCacheTtl);
            return Ok(config);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 평가 설정 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "DocUtil 평가 설정을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 평가 가중치 설정 수정 — DocUtil `/api/v1/evaluation/config` (PUT). 성공/실패 모두 invalidate.
    /// <para>4 weight 모두 0~1, 합=1 권장(하지만 DocUtil 측이 정규화 처리할 수도 있어 강제 검증은 X).</para>
    /// </summary>
    [HttpPut("config")]
    public async Task<ActionResult<DocUtilEvaluationConfig>> UpdateEvaluationConfig(
        [FromBody] DocUtilUpdateEvaluationConfigRequest request,
        CancellationToken ct = default)
    {
        if (request == null)
        {
            return BadRequest(ErrorResponseDto.BadRequest("요청 본문이 비어 있습니다."));
        }
        if (request.ContextRelevancyWeight < 0 || request.ContextRelevancyWeight > 1)
        {
            return BadRequest(ErrorResponseDto.BadRequest("context_relevancy_weight 는 0~1 범위여야 합니다."));
        }
        if (request.AnswerFaithfulnessWeight < 0 || request.AnswerFaithfulnessWeight > 1)
        {
            return BadRequest(ErrorResponseDto.BadRequest("answer_faithfulness_weight 는 0~1 범위여야 합니다."));
        }
        if (request.AnswerRelevancyWeight < 0 || request.AnswerRelevancyWeight > 1)
        {
            return BadRequest(ErrorResponseDto.BadRequest("answer_relevancy_weight 는 0~1 범위여야 합니다."));
        }
        if (request.HallucinationWeight < 0 || request.HallucinationWeight > 1)
        {
            return BadRequest(ErrorResponseDto.BadRequest("hallucination_weight 는 0~1 범위여야 합니다."));
        }

        try
        {
            var updated = await _docUtilClient.UpdateEvaluationConfigAsync(request, ct);
            _logger.LogInformation(
                "운영자 DocUtil 평가 설정 수정 성공 - ConfigId={Id}, Weights=ctx{Ctx}/faith{Faith}/rel{Rel}/halu{Halu}",
                updated.Id,
                updated.ContextRelevancyWeight,
                updated.AnswerFaithfulnessWeight,
                updated.AnswerRelevancyWeight,
                updated.HallucinationWeight);
            await InvalidateEvaluationConfigCacheAsync();
            return Ok(updated);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 평가 설정 수정 실패");
            await InvalidateEvaluationConfigCacheAsync();
            return StatusCode(502, new ErrorResponseDto(
                "평가 설정 수정에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 평가 로그 — GET (페이징 + 필터)
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 평가 로그 목록(페이징 + 필터) — DocUtil `/api/v1/evaluation/logs` 위임 + 1분 캐시.
    /// </summary>
    /// <param name="page">페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 20, 한도 1~100).</param>
    /// <param name="runId">특정 run 의 로그만 조회.</param>
    /// <param name="runType">run_type 정확 일치 필터.</param>
    /// <param name="hasHallucination">hallucination 여부 필터.</param>
    /// <param name="minScore">composite_score 최소값(0~1).</param>
    /// <param name="maxScore">composite_score 최대값(0~1).</param>
    [HttpGet("logs")]
    public async Task<ActionResult<DocUtilEvaluationLogList>> ListEvaluationLogs(
        [FromQuery] int page = 1,
        [FromQuery] int size = 20,
        [FromQuery] string? runId = null,
        [FromQuery] string? runType = null,
        [FromQuery] bool? hasHallucination = null,
        [FromQuery] double? minScore = null,
        [FromQuery] double? maxScore = null,
        CancellationToken ct = default)
    {
        if (minScore.HasValue && (minScore.Value < 0 || minScore.Value > 1))
        {
            return BadRequest(ErrorResponseDto.BadRequest("min_score 는 0~1 범위여야 합니다."));
        }
        if (maxScore.HasValue && (maxScore.Value < 0 || maxScore.Value > 1))
        {
            return BadRequest(ErrorResponseDto.BadRequest("max_score 는 0~1 범위여야 합니다."));
        }
        if (minScore.HasValue && maxScore.HasValue && minScore.Value > maxScore.Value)
        {
            return BadRequest(ErrorResponseDto.BadRequest("min_score 가 max_score 보다 큽니다."));
        }

        string K(string? s) => string.IsNullOrWhiteSpace(s) ? "_" : s.Trim().ToLowerInvariant();
        string D(double? d) => d?.ToString("F4", System.Globalization.CultureInfo.InvariantCulture) ?? "_";
        string B(bool? b) => b?.ToString() ?? "_";
        var cacheKey = $"{LogsCacheKeyPrefix}list:{page}|{size}|{K(runId)}|{K(runType)}|{B(hasHallucination)}|{D(minScore)}|{D(maxScore)}";

        var cached = await _cachingService.GetAsync<CachedEvaluationLogListDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 평가 로그 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }

        try
        {
            var list = await _docUtilClient.ListEvaluationLogsAsync(
                page, size, runId, runType, hasHallucination, minScore, maxScore, ct);
            await _cachingService.SetAsync(cacheKey, CachedEvaluationLogListDto.From(list), ShortCacheTtl);
            return Ok(list);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 평가 로그 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "평가 로그를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 기본 질문 카탈로그 — GET
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 기본 평가 질문 목록 — DocUtil `/api/v1/evaluation/questions` 위임 + 5분 캐시.
    /// <para>응답이 free-form dict — 그대로 운영자 콘솔에 표시.</para>
    /// </summary>
    [HttpGet("questions")]
    public async Task<ActionResult<IDictionary<string, object?>>> GetEvaluationQuestions(CancellationToken ct = default)
    {
        var cacheKey = $"{QuestionsCacheKeyPrefix}default";
        var cached = await _cachingService.GetAsync<CachedEvaluationQuestionsDto>(cacheKey);
        if (cached?.Data != null)
        {
            _logger.LogDebug("DocUtil 평가 질문 캐시 hit");
            return Ok(cached.Data);
        }

        try
        {
            var resp = await _docUtilClient.GetEvaluationQuestionsAsync(ct);
            await _cachingService.SetAsync(
                cacheKey,
                new CachedEvaluationQuestionsDto { Data = resp.Data },
                MediumCacheTtl);
            return Ok(resp.Data);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 평가 질문 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "평가 질문 카탈로그를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 평가 실행(POST) + 실행 목록(GET) + 트렌드(GET)
    // ──────────────────────────────────────────────────────────────────────

    /// <summary>
    /// 수동 평가 실행 — DocUtil `/api/v1/evaluation/run` (POST). 캐시 미적용(매번 신규 트리거).
    /// <para>
    /// 주의: 실제 LLM 호출(평가용 judge LLM)을 트리거 — 비용/시간 영향 가능.
    /// 운영자 의도 명시(POST 호출)시에만 실행됨. 응답은 202 + 비동기 task 정보(free-form).
    /// </para>
    /// </summary>
    [HttpPost("run")]
    public async Task<ActionResult<IDictionary<string, object?>>> RunEvaluation(
        [FromBody] DocUtilRunEvaluationRequest? request,
        CancellationToken ct = default)
    {
        // 본 endpoint 는 questions 가 null 이면 DocUtil default 질문 셋 사용 — body 가 비어도 정상 동작.
        var actualRequest = request ?? new DocUtilRunEvaluationRequest();

        // 입력 sanity 체크 — 너무 많은 질문은 비용 폭증 위험.
        if (actualRequest.Questions != null && actualRequest.Questions.Length > 100)
        {
            return BadRequest(ErrorResponseDto.BadRequest("한 번에 실행 가능한 질문은 최대 100개입니다."));
        }
        if (actualRequest.Questions != null)
        {
            foreach (var q in actualRequest.Questions)
            {
                if (string.IsNullOrWhiteSpace(q))
                {
                    return BadRequest(ErrorResponseDto.BadRequest("빈 질문이 포함되어 있습니다."));
                }
                if (q.Length > 2000)
                {
                    return BadRequest(ErrorResponseDto.BadRequest("질문은 2000자 이하여야 합니다."));
                }
            }
        }

        try
        {
            var resp = await _docUtilClient.RunEvaluationAsync(actualRequest, ct);
            _logger.LogInformation(
                "운영자 DocUtil 평가 실행 트리거 성공 - QuestionsCount={Count}",
                actualRequest.Questions?.Length ?? 0);
            return Accepted(resp.Data);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 평가 실행 실패");
            return StatusCode(502, new ErrorResponseDto(
                "평가 실행에 실패했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 최근 평가 실행 목록 — DocUtil `/api/v1/evaluation/runs` 위임 + 1분 캐시.
    /// </summary>
    /// <param name="limit">반환할 run 수(1~100, 기본 30).</param>
    [HttpGet("runs")]
    public async Task<ActionResult<DocUtilEvaluationRunList>> ListEvaluationRuns(
        [FromQuery] int limit = 30,
        CancellationToken ct = default)
    {
        var safeLimit = limit < 1 || limit > 100 ? 30 : limit;
        var cacheKey = $"{RunsCacheKeyPrefix}list:{safeLimit}";

        var cached = await _cachingService.GetAsync<CachedEvaluationRunListDto>(cacheKey);
        if (cached != null)
        {
            _logger.LogDebug("DocUtil 평가 실행 목록 캐시 hit - key={Key}", cacheKey);
            return Ok(cached.ToRecord());
        }

        try
        {
            var list = await _docUtilClient.ListEvaluationRunsAsync(safeLimit, ct);
            await _cachingService.SetAsync(cacheKey, CachedEvaluationRunListDto.From(list), ShortCacheTtl);
            return Ok(list);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 평가 실행 목록 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "평가 실행 목록을 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    /// <summary>
    /// 평가 점수 추이 — DocUtil `/api/v1/evaluation/trend` 위임 + 5분 캐시.
    /// </summary>
    /// <param name="days">조회 기간(일, 1~365, 기본 30).</param>
    [HttpGet("trend")]
    public async Task<ActionResult<DocUtilEvaluationTrend>> GetEvaluationTrend(
        [FromQuery] int days = 30,
        CancellationToken ct = default)
    {
        var safeDays = days < 1 || days > 365 ? 30 : days;
        var cacheKey = $"{TrendCacheKeyPrefix}days{safeDays}";

        var cached = await _cachingService.GetAsync<CachedEvaluationTrendDto>(cacheKey);
        if (cached?.Data != null)
        {
            _logger.LogDebug("DocUtil 평가 트렌드 캐시 hit - key={Key}", cacheKey);
            return Ok(new DocUtilEvaluationTrend(cached.Data));
        }

        try
        {
            var trend = await _docUtilClient.GetEvaluationTrendAsync(safeDays, ct);
            await _cachingService.SetAsync(
                cacheKey,
                new CachedEvaluationTrendDto { Data = trend.Data },
                MediumCacheTtl);
            return Ok(trend);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogError(ex, "DocUtil 평가 트렌드 조회 실패");
            return StatusCode(502, new ErrorResponseDto(
                "평가 트렌드를 불러오지 못했습니다.",
                "DOCUTIL_UPSTREAM_ERROR",
                new { upstream = ex.Message }));
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // 캐시 wrapper DTO
    // ──────────────────────────────────────────────────────────────────────

    private sealed class CachedEvaluationConfigDto
    {
        public string Id { get; set; } = string.Empty;
        public string OrganizationId { get; set; } = string.Empty;
        public double ContextRelevancyWeight { get; set; }
        public double AnswerFaithfulnessWeight { get; set; }
        public double AnswerRelevancyWeight { get; set; }
        public double HallucinationWeight { get; set; }

        public static CachedEvaluationConfigDto From(DocUtilEvaluationConfig c) => new()
        {
            Id = c.Id,
            OrganizationId = c.OrganizationId,
            ContextRelevancyWeight = c.ContextRelevancyWeight,
            AnswerFaithfulnessWeight = c.AnswerFaithfulnessWeight,
            AnswerRelevancyWeight = c.AnswerRelevancyWeight,
            HallucinationWeight = c.HallucinationWeight,
        };

        public DocUtilEvaluationConfig ToRecord() => new(
            Id, OrganizationId,
            ContextRelevancyWeight, AnswerFaithfulnessWeight,
            AnswerRelevancyWeight, HallucinationWeight);
    }

    private sealed class CachedEvaluationLogEntryDto
    {
        public string Id { get; set; } = string.Empty;
        public string OrganizationId { get; set; } = string.Empty;
        public string RunId { get; set; } = string.Empty;
        public string Question { get; set; } = string.Empty;
        public string Answer { get; set; } = string.Empty;
        public IDictionary<string, object?>? Contexts { get; set; }
        public double ContextRelevancy { get; set; }
        public double AnswerFaithfulness { get; set; }
        public double AnswerRelevancy { get; set; }
        public double HallucinationScore { get; set; }
        public bool HasHallucination { get; set; }
        public IDictionary<string, object?>? HallucinationEvidence { get; set; }
        public double CompositeScore { get; set; }
        public IDictionary<string, object?>? JudgeDetails { get; set; }
        public string RunType { get; set; } = string.Empty;
        public int QuestionIndex { get; set; }
        public DateTime CreatedAt { get; set; }

        public static CachedEvaluationLogEntryDto From(DocUtilEvaluationLogEntry e) => new()
        {
            Id = e.Id,
            OrganizationId = e.OrganizationId,
            RunId = e.RunId,
            Question = e.Question,
            Answer = e.Answer,
            Contexts = e.Contexts,
            ContextRelevancy = e.ContextRelevancy,
            AnswerFaithfulness = e.AnswerFaithfulness,
            AnswerRelevancy = e.AnswerRelevancy,
            HallucinationScore = e.HallucinationScore,
            HasHallucination = e.HasHallucination,
            HallucinationEvidence = e.HallucinationEvidence,
            CompositeScore = e.CompositeScore,
            JudgeDetails = e.JudgeDetails,
            RunType = e.RunType,
            QuestionIndex = e.QuestionIndex,
            CreatedAt = e.CreatedAt,
        };

        public DocUtilEvaluationLogEntry ToRecord() => new(
            Id, OrganizationId, RunId, Question, Answer,
            Contexts, ContextRelevancy, AnswerFaithfulness, AnswerRelevancy,
            HallucinationScore, HasHallucination, HallucinationEvidence,
            CompositeScore, JudgeDetails, RunType, QuestionIndex, CreatedAt);
    }

    private sealed class CachedEvaluationLogListDto
    {
        public CachedEvaluationLogEntryDto[] Items { get; set; } = Array.Empty<CachedEvaluationLogEntryDto>();
        public long Total { get; set; }
        public int Page { get; set; }
        public int Size { get; set; }

        public static CachedEvaluationLogListDto From(DocUtilEvaluationLogList l) => new()
        {
            Items = l.Items.Select(CachedEvaluationLogEntryDto.From).ToArray(),
            Total = l.Total,
            Page = l.Page,
            Size = l.Size,
        };

        public DocUtilEvaluationLogList ToRecord() => new(
            Items.Select(c => c.ToRecord()).ToArray(),
            Total,
            Page,
            Size);
    }

    private sealed class CachedEvaluationQuestionsDto
    {
        public IDictionary<string, object?>? Data { get; set; }
    }

    private sealed class CachedEvaluationRunSummaryDto
    {
        public string RunId { get; set; } = string.Empty;
        public string RunType { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        public int QuestionCount { get; set; }
        public double AvgContextRelevancy { get; set; }
        public double AvgAnswerFaithfulness { get; set; }
        public double AvgAnswerRelevancy { get; set; }
        public double AvgHallucinationScore { get; set; }
        public double AvgCompositeScore { get; set; }
        public int HallucinationCount { get; set; }

        public static CachedEvaluationRunSummaryDto From(DocUtilEvaluationRunSummary s) => new()
        {
            RunId = s.RunId,
            RunType = s.RunType,
            CreatedAt = s.CreatedAt,
            QuestionCount = s.QuestionCount,
            AvgContextRelevancy = s.AvgContextRelevancy,
            AvgAnswerFaithfulness = s.AvgAnswerFaithfulness,
            AvgAnswerRelevancy = s.AvgAnswerRelevancy,
            AvgHallucinationScore = s.AvgHallucinationScore,
            AvgCompositeScore = s.AvgCompositeScore,
            HallucinationCount = s.HallucinationCount,
        };

        public DocUtilEvaluationRunSummary ToRecord() => new(
            RunId, RunType, CreatedAt, QuestionCount,
            AvgContextRelevancy, AvgAnswerFaithfulness, AvgAnswerRelevancy,
            AvgHallucinationScore, AvgCompositeScore, HallucinationCount);
    }

    private sealed class CachedEvaluationRunListDto
    {
        public CachedEvaluationRunSummaryDto[] Items { get; set; } = Array.Empty<CachedEvaluationRunSummaryDto>();
        public long Total { get; set; }

        public static CachedEvaluationRunListDto From(DocUtilEvaluationRunList l) => new()
        {
            Items = l.Items.Select(CachedEvaluationRunSummaryDto.From).ToArray(),
            Total = l.Total,
        };

        public DocUtilEvaluationRunList ToRecord() => new(
            Items.Select(c => c.ToRecord()).ToArray(),
            Total);
    }

    private sealed class CachedEvaluationTrendDto
    {
        public DocUtilEvaluationTrendDataPoint[]? Data { get; set; }
    }
}
