using System.Diagnostics;
using System.Net;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace AIAgentManagement.Services;

// ════════════════════════════════════════════════════════════════════════════
// DocUtilClient — IDocUtilClient 구현체 (Phase 6.1, ADR-2)
//
// 책임 범위:
//   1. Named HttpClient "docutil" 사용(연결 풀/타임아웃은 Program.cs 에서 관리)
//   2. DocUtil 측 운영자 JWT 또는 ApiKey 를 IConfiguration 에서 로드 후
//      Authorization: Bearer {token} 헤더로 부착
//   3. 6 개 엔드포인트 호출 및 snake_case <-> PascalCase 매핑(JSON)
//   4. HTTP 상태 코드별 한국어 예외 매핑 — InvalidOperationException 으로 통일
//      → AgentHub Controller / GlobalExceptionHandlerMiddleware 가 502/503 응답 합성
//
// 책임 범위 밖:
//   - RAG 결과 캐싱(RagService 가 처리)
//   - Agent 권한 검증(IAgentService / Controller 레이어)
//   - DTO 매핑(외부 RagSearchResultDto 변환은 RagService 에서)
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// DocUtil FastAPI 클라이언트 구현. AgentHub 가 운영자 콘솔 BFF + RAG 라우팅 분기에서 합성한다.
/// </summary>
public class DocUtilClient : IDocUtilClient
{
    private const string HttpClientName = "docutil";

    // ── Phase 4: SearchAsync 응답 캐시 ─────────────────────────────────────
    // 캐시 네임스페이스 prefix — RagService 의 결과 캐시(`rag:`) 와 분리하여
    // 후속 트랙: 운영자 KB 수정 시 version-key 패턴으로 일괄 무효화.
    //
    // 캐시 키 패턴: `du:s:v{N}:{hash}` — N 은 CachingService.GetVersionAsync("docutil-search")
    //   에서 받아온 단조 증가 정수. 운영자가 KB 문서 업로드/삭제 시 IncrementVersionAsync
    //   호출 → N+1 → 이전 버전 키 일괄 stale (TTL 5분 자연 expire / LRU eviction).
    //
    // SearchCacheVersionNamespace 는 CachingService 의 version key 격리 단위.
    private const string SearchCacheKeyPrefix = "du:s:";
    public const string SearchCacheVersionNamespace = "docutil-search";
    // RagService 결과 캐시(10분) 보다 짧게 — sub-query 단계라 KB 수정의 빠른 반영 우선.
    private static readonly TimeSpan SearchCacheTtl = TimeSpan.FromMinutes(5);

    // ── 후속 트랙 2026-05-08 + Phase 10.1c 통합: ListCollectionsAsync 응답 캐시 ─
    // 캐시 네임스페이스 prefix `du:c:` — Search 캐시(`du:s:`) 와 격리.
    // 캐시 키 패턴: `du:c:v{N}:{page}|{size}` — page/size 조합당 단일 키 + version prefix.
    //
    // 캐시 무효화 전략 (Phase 10.1c 부터):
    //   AdminDocUtilProjectsController 가 프로젝트/보드 mutation 성공 시
    //   IncrementVersionAsync(CollectionCacheVersionNamespace = "docutil-collections")
    //   호출 → N+1 → 이전 버전 키 일괄 stale → AgentBuilder 의 dropdown 도
    //   즉시 신규 프로젝트 노출(통합 namespace 효과).
    //
    // Phase 10.1c 이전(after 2026-05-08, before 2026-05-10): 단순 TTL 10분 자연 expire 만 의존.
    //   본 변경은 시그니처 미변경 — 외부 호출자 무영향(단지 캐시 일관성 향상).
    public const string CollectionCacheVersionNamespace = "docutil-collections";
    private const string CollectionCacheKeyPrefix = "du:c:";
    private static readonly TimeSpan CollectionCacheTtl = TimeSpan.FromMinutes(10);

    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IConfiguration _configuration;
    private readonly IDocUtilTokenProvider _tokenProvider;
    private readonly CachingService _cachingService;
    private readonly IRagMetrics _ragMetrics;
    private readonly ILogger<DocUtilClient> _logger;

    // DocUtil FastAPI 는 snake_case(SQLAlchemy 2 / Pydantic) — JsonNamingPolicy.SnakeCaseLower 일관 적용.
    // PropertyNameCaseInsensitive 는 폴백용(서버 측 일부 alias 가 PascalCase 인 경우 보호).
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        PropertyNameCaseInsensitive = true,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    public DocUtilClient(
        IHttpClientFactory httpClientFactory,
        IConfiguration configuration,
        IDocUtilTokenProvider tokenProvider,
        CachingService cachingService,
        IRagMetrics ragMetrics,
        ILogger<DocUtilClient> logger)
    {
        _httpClientFactory = httpClientFactory;
        _configuration = configuration;
        _tokenProvider = tokenProvider;
        _cachingService = cachingService;
        _ragMetrics = ragMetrics;
        _logger = logger;
    }

    // ══════════════════════════════════════════════════════════════════════
    // 1. SearchAsync — POST /api/v1/search (RAG 라우팅 분기 핵심)
    // ══════════════════════════════════════════════════════════════════════
    public async Task<DocUtilSearchResult> SearchAsync(
        string query,
        string? collectionRef,
        int maxResults = 10,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(query))
        {
            // 빈 쿼리는 빈 결과 — DocUtil 호출 비용 절감 + 422 회피.
            // 캐시/메트릭 기록 없이 단순 폴백(상위 분기에서 이미 처리되어야 정상).
            return new DocUtilSearchResult(Array.Empty<DocUtilSearchHit>(), 0d, null);
        }

        // ── Phase 4 + 후속 트랙: SearchAsync 응답 캐시 ─────────────────────
        // 캐시 키: `du:s:v{N}:{SHA256(query|collectionRef|maxResults)[..16]}`
        //   - N: CachingService 의 version-key namespace `docutil-search` 현재 값.
        //   - 운영자가 KB upload/delete 시 IncrementVersionAsync 호출 → N+1 →
        //     이전 버전 키 일괄 stale (TTL 5분 자연 expire 또는 LRU eviction).
        //   - hash: query+collectionRef+maxResults 의 SHA256 short hex.
        // 다른 Agent 가 동일 KB 컬렉션으로 동일 sub-query 호출 시 hit.
        // 빈 결과(Hits=0)도 캐싱 — 부하 절감 우선(KB 수정 시 5분 또는 invalidate 시점에 반영).
        //
        // 버전 fetch 실패 시 0 으로 graceful 폴백 — 본 호출 흐름은 차단되지 않음.
        var version = await _cachingService.GetVersionAsync(SearchCacheVersionNamespace);
        var cacheKey = BuildSearchCacheKey(version, query, collectionRef, maxResults);

        var cached = await _cachingService.GetAsync<CachedSearchResultDto>(cacheKey);
        if (cached != null)
        {
            _ragMetrics.IncrementDocUtilSearchCacheHit();
            _logger.LogDebug(
                "DocUtil 검색 캐시 hit - key={Key}, version={Version}, query={QueryPreview}, hits={HitCount}",
                cacheKey,
                version,
                query.Length > 40 ? query[..40] + "..." : query,
                cached.Hits?.Length ?? 0);
            return new DocUtilSearchResult(
                cached.Hits ?? Array.Empty<DocUtilSearchHit>(),
                cached.TotalTime,
                cached.Metadata);
        }
        _ragMetrics.IncrementDocUtilSearchCacheMiss();
        _logger.LogDebug(
            "DocUtil 검색 캐시 miss - key={Key}, version={Version}, query={QueryPreview}",
            cacheKey,
            version,
            query.Length > 40 ? query[..40] + "..." : query);

        var client = _httpClientFactory.CreateClient(HttpClientName);

        // DocUtil SearchRequest schema:
        //   { "query": string, "scope_id"?: string, "doc_ids"?: string[],
        //     "agentic"?: bool, "max_results"?: int }
        // collectionRef 가 비어있으면 글로벌 검색(DocUtil 측이 전체 corpus 대상으로 처리).
        var requestBody = new Dictionary<string, object?>
        {
            ["query"] = query,
            ["max_results"] = maxResults,
        };
        if (!string.IsNullOrWhiteSpace(collectionRef))
        {
            requestBody["scope_id"] = collectionRef;
        }

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, "/api/v1/search", requestBody, cancellationToken);

        _logger.LogDebug(
            "DocUtil 하이브리드 검색 호출 - CollectionRef={CollectionRef}, MaxResults={MaxResults}, QueryLen={QueryLen}",
            collectionRef ?? "(global)", maxResults, query.Length);

        // ── HTTP 호출 latency 측정 + 메트릭 기록 (try-finally 로 보장) ──
        _ragMetrics.IncrementDocUtilSearchCall();
        var stopwatch = Stopwatch.StartNew();
        DocUtilSearchResult resultToReturn;
        try
        {
            using var response = await client.SendAsync(
                httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

            await EnsureSuccessOrThrowKoreanAsync(response, "/api/v1/search", cancellationToken);

            await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
            var dto = await JsonSerializer.DeserializeAsync<SearchResponseDto>(stream, JsonOptions, cancellationToken);

            if (dto is null)
            {
                throw new InvalidOperationException("DocUtil 검색 응답을 디시리얼라이즈하지 못했습니다.");
            }

            var hits = (dto.Results ?? Array.Empty<SearchHitDto>())
                .Select(r => new DocUtilSearchHit(
                    r.Id ?? string.Empty,
                    r.Content ?? string.Empty,
                    r.Score,
                    r.Metadata))
                .ToArray();

            _logger.LogDebug(
                "DocUtil 검색 응답 - Hits={HitCount}, TotalTime={TotalTime}s, Latency={LatencyMs}ms",
                hits.Length, dto.TotalTime, stopwatch.ElapsedMilliseconds);

            resultToReturn = new DocUtilSearchResult(hits, dto.TotalTime, dto.Metadata);
        }
        catch (Exception)
        {
            // 실패 메트릭 — EnsureSuccessOrThrow / DeserializeAsync / Send 모든 실패 경로 포괄.
            _ragMetrics.IncrementDocUtilSearchFailure();
            throw;
        }
        finally
        {
            stopwatch.Stop();
            _ragMetrics.RecordDocUtilSearchLatency(stopwatch.ElapsedMilliseconds);
        }

        // ── 캐시 적재(성공 응답만) ─────────────────────────────────────────
        // CachedSearchResultDto 는 DocUtilSearchResult 의 record 가 직렬화에 약하므로
        // 클래스 wrapper 사용. metadata 는 object? 로 그대로 직렬화/역직렬화.
        var cacheValue = new CachedSearchResultDto
        {
            Hits = resultToReturn.Results,
            TotalTime = resultToReturn.TotalTime,
            Metadata = resultToReturn.Metadata,
        };
        await _cachingService.SetAsync(cacheKey, cacheValue, SearchCacheTtl);

        return resultToReturn;
    }

    /// <summary>
    /// SearchAsync 캐시 키 생성기 — version + query + collectionRef + maxResults 의
    /// SHA256 short hash. query 는 trim + lower 정규화하여 다른 공백/대소문자 표기를
    /// 동일 키로 융합.
    /// </summary>
    /// <param name="version">현재 캐시 버전(CachingService.GetVersionAsync). KB 수정 시
    /// IncrementVersionAsync 로 +1 → 이전 버전 키 일괄 stale.</param>
    private static string BuildSearchCacheKey(long version, string query, string? collectionRef, int maxResults)
    {
        var input = $"{query.Trim().ToLowerInvariant()}|{collectionRef ?? string.Empty}|{maxResults}";
        var hash = SHA256.HashData(Encoding.UTF8.GetBytes(input));
        return $"{SearchCacheKeyPrefix}v{version}:{Convert.ToHexString(hash, 0, 8)}";
    }

    // ══════════════════════════════════════════════════════════════════════
    // 2. ListDocumentsAsync — GET /api/v1/documents
    // ══════════════════════════════════════════════════════════════════════
    public async Task<DocUtilDocumentList> ListDocumentsAsync(
        string? collectionRef,
        int page = 1,
        int size = 20,
        CancellationToken cancellationToken = default)
    {
        var client = _httpClientFactory.CreateClient(HttpClientName);

        var query = new List<string>
        {
            $"page={page}",
            $"size={size}",
        };
        if (!string.IsNullOrWhiteSpace(collectionRef))
        {
            query.Add($"folder_id={Uri.EscapeDataString(collectionRef)}");
        }
        var path = $"/api/v1/documents?{string.Join("&", query)}";

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentListDto>(stream, JsonOptions, cancellationToken);

        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 문서 목록 응답을 디시리얼라이즈하지 못했습니다.");
        }

        var items = (dto.Items ?? Array.Empty<DocumentSummaryDto>())
            .Select(d => new DocUtilDocumentSummary(
                d.Id ?? string.Empty,
                d.Name ?? string.Empty,
                d.Status ?? "unknown",
                d.CreatedAt))
            .ToArray();

        return new DocUtilDocumentList(items, dto.Total, dto.Page, dto.Size);
    }

    // ══════════════════════════════════════════════════════════════════════
    // 3. GetDocumentAsync — GET /api/v1/documents/{id} (404 → null)
    // ══════════════════════════════════════════════════════════════════════
    public async Task<DocUtilDocumentDetail?> GetDocumentAsync(
        string documentId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(documentId))
        {
            throw new ArgumentException("documentId 가 비어있습니다.", nameof(documentId));
        }

        var client = _httpClientFactory.CreateClient(HttpClientName);
        var path = $"/api/v1/documents/{Uri.EscapeDataString(documentId)}";

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        // 404 정규화 — 운영자 콘솔에서 호출 시 NotFound 분기를 단순화.
        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            _logger.LogDebug("DocUtil 문서 미존재 - DocumentId={DocumentId}", documentId);
            return null;
        }

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentDetailDto>(stream, JsonOptions, cancellationToken);

        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 문서 상세 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return new DocUtilDocumentDetail(
            dto.Id ?? string.Empty,
            dto.Name ?? string.Empty,
            dto.Status ?? "unknown",
            dto.CreatedAt,
            dto.UploaderName,
            dto.VisibilityTargets);
    }

    // ══════════════════════════════════════════════════════════════════════
    // 4. UploadDocumentAsync — POST /api/v1/documents/upload (multipart)
    //
    // multipart/form-data 구성:
    //   - file: StreamContent (필수)
    //   - folder_id: collectionRef (선택)
    //   - visibility: "public" | "private" | ... (선택)
    //
    // fileStream 은 호출자(컨트롤러) 가 소유 — 본 메서드는 Read 만 하고 Dispose 하지 않는다.
    // multipart boundary 는 .NET MultipartFormDataContent 가 자동 생성.
    // ══════════════════════════════════════════════════════════════════════
    public async Task<DocUtilUploadResult> UploadDocumentAsync(
        Stream fileStream,
        string fileName,
        string? collectionRef,
        string? visibility = null,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(fileStream);
        if (string.IsNullOrWhiteSpace(fileName))
        {
            throw new ArgumentException("fileName 이 비어있습니다.", nameof(fileName));
        }

        var client = _httpClientFactory.CreateClient(HttpClientName);

        using var multipart = new MultipartFormDataContent();

        // 파일 본문 — 호출자 stream 을 그대로 전달(메모리 복사 없음).
        var streamContent = new StreamContent(fileStream);
        streamContent.Headers.ContentType = new MediaTypeHeaderValue("application/octet-stream");
        multipart.Add(streamContent, "file", fileName);

        if (!string.IsNullOrWhiteSpace(collectionRef))
        {
            multipart.Add(new StringContent(collectionRef, Encoding.UTF8), "folder_id");
        }
        if (!string.IsNullOrWhiteSpace(visibility))
        {
            multipart.Add(new StringContent(visibility, Encoding.UTF8), "visibility");
        }

        using var httpRequest = new HttpRequestMessage(HttpMethod.Post, "/api/v1/documents/upload")
        {
            Content = multipart,
        };
        var uploadToken = await _tokenProvider.GetTokenAsync(cancellationToken);
        if (!string.IsNullOrWhiteSpace(uploadToken))
        {
            httpRequest.Headers.Authorization = new AuthenticationHeaderValue("Bearer", uploadToken);
        }
        else
        {
            _logger.LogWarning(
                "DocUtil 토큰 미설정 — multipart upload 호출이 401 로 실패할 수 있음.");
        }

        _logger.LogDebug(
            "DocUtil 문서 업로드 호출 - FileName={FileName}, CollectionRef={CollectionRef}, Visibility={Visibility}",
            fileName, collectionRef ?? "(none)", visibility ?? "(default)");

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, "/api/v1/documents/upload", cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<UploadResponseDto>(stream, JsonOptions, cancellationToken);

        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 업로드 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return new DocUtilUploadResult(
            dto.Id ?? string.Empty,
            dto.Name ?? fileName,
            dto.Status ?? "pending",
            dto.JobId);
    }

    // ══════════════════════════════════════════════════════════════════════
    // 5. DeleteDocumentAsync — DELETE /api/v1/documents/{id}
    // ══════════════════════════════════════════════════════════════════════
    public async Task DeleteDocumentAsync(
        string documentId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(documentId))
        {
            throw new ArgumentException("documentId 가 비어있습니다.", nameof(documentId));
        }

        var client = _httpClientFactory.CreateClient(HttpClientName);
        var path = $"/api/v1/documents/{Uri.EscapeDataString(documentId)}";

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Delete, path, body: null, cancellationToken);

        _logger.LogDebug("DocUtil 문서 삭제 호출 - DocumentId={DocumentId}", documentId);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        // 204 NoContent / 200 OK 모두 성공으로 인정. 그 외는 한국어 예외.
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
    }

    // ══════════════════════════════════════════════════════════════════════
    // 6. GetChunksAsync — GET /api/v1/documents/{id}/chunks
    // ══════════════════════════════════════════════════════════════════════
    public async Task<List<DocUtilChunk>> GetChunksAsync(
        string documentId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(documentId))
        {
            throw new ArgumentException("documentId 가 비어있습니다.", nameof(documentId));
        }

        var client = _httpClientFactory.CreateClient(HttpClientName);
        var path = $"/api/v1/documents/{Uri.EscapeDataString(documentId)}/chunks";

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dtos = await JsonSerializer.DeserializeAsync<List<ChunkResponseDto>>(stream, JsonOptions, cancellationToken);

        if (dtos is null)
        {
            return new List<DocUtilChunk>();
        }

        return dtos
            .Select(c => new DocUtilChunk(
                c.ChunkId ?? string.Empty,
                c.Content ?? string.Empty,
                c.ChunkIndex,
                c.Metadata))
            .ToList();
    }

    // ══════════════════════════════════════════════════════════════════════
    // 7. ListCollectionsAsync — GET /api/v1/projects (운영자 dropdown UX)
    //
    // DocUtil schema 매핑(2026-05-08 운영 확인):
    //   GET /api/v1/projects?page={page}&size={size}
    //   응답: { items: [{ id, name, description, allow_original_download,
    //                     organization_id, created_by, created_at, updated_at }],
    //          total, page, size }
    //
    // BFF 표면 단순화: id/name/description 3 필드만 노출. 나머지(organization_id /
    // created_by / timestamps / allow_original_download) 는 dropdown UX 에 불필요하고
    // DocUtil 내부 schema 변경 시 영향 면적을 늘리므로 비노출.
    //
    // 캐시 전략(후속 트랙 2026-05-08):
    //   prefix `du:c:`, TTL 10분. version-key 패턴 미적용 — collection 생성/삭제는
    //   DocUtil 콘솔에서 직접 발생(AgentHub BFF 비경유) 이므로 explicit invalidate
    //   트리거 불가. 단순 TTL 자연 expire 로 운영자 워크플로(Agent 생성/편집 시
    //   매번 dropdown 호출) 의 DocUtil 부하를 감소시킨다.
    //   빈 결과(0건) 도 캐싱 — 빈 응답을 반복 호출하는 부하도 줄임.
    // ══════════════════════════════════════════════════════════════════════
    public async Task<List<DocUtilCollection>> ListCollectionsAsync(
        int page = 1,
        int size = 50,
        CancellationToken cancellationToken = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 200) size = 50;

        // ── 캐시 조회 (Phase 10.1c: version-key 통합) ──────────────────────
        // 키: du:c:v{N}:{page}|{size} — version prefix 로 운영자 mutation 시 일괄 stale.
        // version fetch 실패 시 0 폴백(서비스는 차단되지 않음).
        var version = await _cachingService.GetVersionAsync(CollectionCacheVersionNamespace);
        var cacheKey = $"{CollectionCacheKeyPrefix}v{version}:{page}|{size}";
        var cached = await _cachingService.GetAsync<CachedCollectionListDto>(cacheKey);
        if (cached?.Items != null)
        {
            _ragMetrics.IncrementDocUtilCollectionCacheHit();
            _logger.LogDebug(
                "DocUtil 컬렉션 캐시 hit - key={Key}, count={Count}",
                cacheKey, cached.Items.Length);
            return cached.Items.ToList();
        }
        _ragMetrics.IncrementDocUtilCollectionCacheMiss();
        _logger.LogDebug(
            "DocUtil 컬렉션 캐시 miss - key={Key}", cacheKey);

        var client = _httpClientFactory.CreateClient(HttpClientName);
        var path = $"/api/v1/projects?page={page}&size={size}";

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        _logger.LogDebug(
            "DocUtil 컬렉션(projects) 목록 호출 - Page={Page}, Size={Size}", page, size);

        // ── HTTP 호출 latency 측정 + 메트릭 기록 (try-finally 로 보장) ──
        _ragMetrics.IncrementDocUtilCollectionCall();
        var stopwatch = Stopwatch.StartNew();
        List<DocUtilCollection> items;
        try
        {
            using var response = await client.SendAsync(
                httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

            await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

            await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
            var dto = await JsonSerializer.DeserializeAsync<ProjectListDto>(stream, JsonOptions, cancellationToken);

            if (dto is null)
            {
                throw new InvalidOperationException("DocUtil 컬렉션(projects) 목록 응답을 디시리얼라이즈하지 못했습니다.");
            }

            items = (dto.Items ?? Array.Empty<ProjectSummaryDto>())
                .Select(p => new DocUtilCollection(
                    p.Id ?? string.Empty,
                    p.Name ?? string.Empty,
                    p.Description))
                .Where(c => !string.IsNullOrWhiteSpace(c.Id))
                .ToList();

            _logger.LogDebug(
                "DocUtil 컬렉션 응답 - Count={Count}, Total={Total}, Latency={LatencyMs}ms",
                items.Count, dto.Total, stopwatch.ElapsedMilliseconds);
        }
        catch (Exception)
        {
            // 실패 메트릭 — EnsureSuccessOrThrow / DeserializeAsync / Send 모든 실패 경로 포괄.
            _ragMetrics.IncrementDocUtilCollectionFailure();
            throw;
        }
        finally
        {
            stopwatch.Stop();
        }

        // ── 캐시 적재(성공 응답만, 빈 결과 포함) ─────────────────────────
        // record DocUtilCollection 직렬화 안정성을 위해 클래스 wrapper 사용 — Search 와 동일 패턴.
        var cacheValue = new CachedCollectionListDto
        {
            Items = items.ToArray(),
        };
        await _cachingService.SetAsync(cacheKey, cacheValue, CollectionCacheTtl);

        return items;
    }

    // ══════════════════════════════════════════════════════════════════════
    // 8. ListUsersAsync — GET /api/v1/users (Phase 10.1a, 2026-05-10)
    //
    // org_id 자동 부착:
    //   IDocUtilTokenProvider.GetOrganizationIdAsync 가 운영자 토큰의 `org` claim
    //   을 추출하여 반환. 추출 실패(ApiKey 모드 / decode 실패) 시 502 매핑(InvalidOperationException).
    //
    // 추가 query 파라미터(role/status/search) 는 호출자(Controller) 가 외부에서 받아 전달.
    // ══════════════════════════════════════════════════════════════════════
    public async Task<DocUtilUserList> ListUsersAsync(
        int page = 1,
        int size = 20,
        string? role = null,
        string? status = null,
        string? search = null,
        CancellationToken cancellationToken = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 100) size = 20;

        var orgId = await _tokenProvider.GetOrganizationIdAsync(cancellationToken);
        if (string.IsNullOrWhiteSpace(orgId))
        {
            // 운영자 자격이 JWT 가 아닌 영구 ApiKey 만 등록된 경우 또는 토큰 디코드 실패.
            // 한국어 메시지 — Controller 가 502 ErrorResponseDto 로 매핑.
            throw new InvalidOperationException(
                "DocUtil 운영자 토큰에서 organization_id 를 추출할 수 없습니다. " +
                "ServiceUsername/ServicePassword 또는 JwtToken 설정을 확인하세요.");
        }

        var queryParts = new List<string>
        {
            $"org_id={Uri.EscapeDataString(orgId)}",
            $"page={page}",
            $"size={size}",
        };
        if (!string.IsNullOrWhiteSpace(role))
        {
            queryParts.Add($"role={Uri.EscapeDataString(role)}");
        }
        if (!string.IsNullOrWhiteSpace(status))
        {
            queryParts.Add($"status={Uri.EscapeDataString(status)}");
        }
        if (!string.IsNullOrWhiteSpace(search))
        {
            queryParts.Add($"search={Uri.EscapeDataString(search)}");
        }
        var path = $"/api/v1/users?{string.Join("&", queryParts)}";

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        _logger.LogDebug(
            "DocUtil 사용자 목록 호출 - OrgId={OrgId}, Page={Page}, Size={Size}, Role={Role}, Status={Status}, SearchLen={SearchLen}",
            orgId, page, size, role ?? "(none)", status ?? "(none)", search?.Length ?? 0);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<UserListResponseDto>(stream, JsonOptions, cancellationToken);

        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 사용자 목록 응답을 디시리얼라이즈하지 못했습니다.");
        }

        var items = (dto.Items ?? Array.Empty<UserResponseDto>())
            .Select(MapUserSummary)
            .ToArray();

        return new DocUtilUserList(items, dto.Total, dto.Page, dto.Size);
    }

    // ══════════════════════════════════════════════════════════════════════
    // 9. GetUserAsync — GET /api/v1/users/{user_id} (404 → null)
    // ══════════════════════════════════════════════════════════════════════
    public async Task<DocUtilUserDetail?> GetUserAsync(
        string userId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(userId))
        {
            throw new ArgumentException("userId 가 비어있습니다.", nameof(userId));
        }

        var client = _httpClientFactory.CreateClient(HttpClientName);
        var path = $"/api/v1/users/{Uri.EscapeDataString(userId)}";

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            _logger.LogDebug("DocUtil 사용자 미존재 - UserId={UserId}", userId);
            return null;
        }

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<UserResponseDto>(stream, JsonOptions, cancellationToken);

        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 사용자 상세 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return MapUserDetail(dto);
    }

    // ══════════════════════════════════════════════════════════════════════
    // 10. UpdateUserStatusAsync — PUT /api/v1/users/{user_id}/status
    //
    // body: { "status": "active" | "inactive" | "locked" }
    // 응답: 변경된 UserResponse — 호출자가 UI 즉시 반영.
    // ══════════════════════════════════════════════════════════════════════
    public async Task<DocUtilUserDetail> UpdateUserStatusAsync(
        string userId,
        string status,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(userId))
        {
            throw new ArgumentException("userId 가 비어있습니다.", nameof(userId));
        }
        if (string.IsNullOrWhiteSpace(status))
        {
            throw new ArgumentException("status 가 비어있습니다.", nameof(status));
        }

        var client = _httpClientFactory.CreateClient(HttpClientName);
        var path = $"/api/v1/users/{Uri.EscapeDataString(userId)}/status";

        var body = new Dictionary<string, object?>
        {
            ["status"] = status,
        };

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Put, path, body, cancellationToken);

        _logger.LogInformation(
            "DocUtil 사용자 상태 변경 호출 - UserId={UserId}, Status={Status}", userId, status);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<UserResponseDto>(stream, JsonOptions, cancellationToken);

        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 사용자 상태 변경 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return MapUserDetail(dto);
    }

    // ══════════════════════════════════════════════════════════════════════
    // 11. DeleteUserAsync — DELETE /api/v1/users/{user_id}
    // ══════════════════════════════════════════════════════════════════════
    public async Task DeleteUserAsync(
        string userId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(userId))
        {
            throw new ArgumentException("userId 가 비어있습니다.", nameof(userId));
        }

        var client = _httpClientFactory.CreateClient(HttpClientName);
        var path = $"/api/v1/users/{Uri.EscapeDataString(userId)}";

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Delete, path, body: null, cancellationToken);

        _logger.LogInformation("DocUtil 사용자 삭제 호출 - UserId={UserId}", userId);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        // 204 NoContent / 200 OK 모두 성공으로 인정. 그 외는 한국어 예외.
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
    }

    // ══════════════════════════════════════════════════════════════════════
    // Phase 10.1b (2026-05-10): DocUtil 조직/부서/할당량 운영자 BFF — 9 메서드
    //
    // org_id 자동 부착:
    //   IDocUtilTokenProvider.GetOrganizationIdAsync 가 운영자 토큰의 `org` claim
    //   을 추출. 추출 실패 시 InvalidOperationException(한국어) → Controller 가 502 매핑.
    //
    // 캐시 전략:
    //   본 클라이언트는 캐시 미적용 — Controller 레이어(AdminDocUtilDepartmentsController)
    //   가 version-key + TTL 패턴으로 처리하여 mutation invalidate 를 정확히 트리거.
    // ══════════════════════════════════════════════════════════════════════

    // 1) GetOrganizationAsync — GET /api/v1/organizations/{org_id}
    public async Task<DocUtilOrganization?> GetOrganizationAsync(
        CancellationToken cancellationToken = default)
    {
        var orgId = await ResolveOrganizationIdAsync(cancellationToken);
        var path = $"/api/v1/organizations/{Uri.EscapeDataString(orgId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            _logger.LogWarning("DocUtil 조직 미존재 - OrgId={OrgId}", orgId);
            return null;
        }

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<OrganizationResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 조직 조회 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return MapOrganization(dto);
    }

    // 2) UpdateOrganizationAsync — PUT /api/v1/organizations/{org_id}
    public async Task<DocUtilOrganization> UpdateOrganizationAsync(
        DocUtilUpdateOrganizationRequest request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);

        var orgId = await ResolveOrganizationIdAsync(cancellationToken);
        var path = $"/api/v1/organizations/{Uri.EscapeDataString(orgId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);

        // partial update — null 필드는 직렬화 제외(JsonOptions.DefaultIgnoreCondition.WhenWritingNull).
        var body = new Dictionary<string, object?>();
        if (request.Name is not null) body["name"] = request.Name;
        if (request.Description is not null) body["description"] = request.Description;
        if (request.Settings is not null) body["settings"] = request.Settings;

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Put, path, body, cancellationToken);

        _logger.LogInformation(
            "DocUtil 조직 수정 호출 - OrgId={OrgId}, FieldCount={FieldCount}", orgId, body.Count);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<OrganizationResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 조직 수정 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return MapOrganization(dto);
    }

    // 3) ListDepartmentsAsync — GET /api/v1/organizations/{org_id}/departments
    public async Task<List<DocUtilDepartment>> ListDepartmentsAsync(
        CancellationToken cancellationToken = default)
    {
        var orgId = await ResolveOrganizationIdAsync(cancellationToken);
        var path = $"/api/v1/organizations/{Uri.EscapeDataString(orgId)}/departments";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dtos = await JsonSerializer.DeserializeAsync<List<DepartmentResponseDto>>(stream, JsonOptions, cancellationToken);
        if (dtos is null)
        {
            return new List<DocUtilDepartment>();
        }

        return dtos.Select(MapDepartment).ToList();
    }

    // 4) CreateDepartmentAsync — POST /api/v1/organizations/{org_id}/departments
    public async Task<DocUtilDepartment> CreateDepartmentAsync(
        DocUtilCreateDepartmentRequest request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            throw new ArgumentException("부서 이름이 비어있습니다.", nameof(request));
        }

        var orgId = await ResolveOrganizationIdAsync(cancellationToken);
        var path = $"/api/v1/organizations/{Uri.EscapeDataString(orgId)}/departments";
        var client = _httpClientFactory.CreateClient(HttpClientName);

        var body = new Dictionary<string, object?>
        {
            ["name"] = request.Name,
        };
        if (!string.IsNullOrWhiteSpace(request.ParentId))
        {
            body["parent_id"] = request.ParentId;
        }

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body, cancellationToken);

        _logger.LogInformation(
            "DocUtil 부서 생성 호출 - OrgId={OrgId}, Name={Name}, ParentId={ParentId}",
            orgId, request.Name, request.ParentId ?? "(root)");

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DepartmentResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 부서 생성 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return MapDepartment(dto);
    }

    // 5) UpdateDepartmentAsync — PUT /api/v1/organizations/{org_id}/departments/{dept_id}
    public async Task<DocUtilDepartment> UpdateDepartmentAsync(
        string departmentId,
        DocUtilUpdateDepartmentRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(departmentId))
        {
            throw new ArgumentException("departmentId 가 비어있습니다.", nameof(departmentId));
        }
        ArgumentNullException.ThrowIfNull(request);

        var orgId = await ResolveOrganizationIdAsync(cancellationToken);
        var path = $"/api/v1/organizations/{Uri.EscapeDataString(orgId)}/departments/{Uri.EscapeDataString(departmentId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);

        var body = new Dictionary<string, object?>();
        if (request.Name is not null) body["name"] = request.Name;
        if (request.ParentId is not null) body["parent_id"] = request.ParentId;

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Put, path, body, cancellationToken);

        _logger.LogInformation(
            "DocUtil 부서 수정 호출 - OrgId={OrgId}, DeptId={DeptId}, FieldCount={FieldCount}",
            orgId, departmentId, body.Count);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DepartmentResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 부서 수정 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return MapDepartment(dto);
    }

    // 6) DeleteDepartmentAsync — DELETE /api/v1/organizations/{org_id}/departments/{dept_id}
    public async Task DeleteDepartmentAsync(
        string departmentId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(departmentId))
        {
            throw new ArgumentException("departmentId 가 비어있습니다.", nameof(departmentId));
        }

        var orgId = await ResolveOrganizationIdAsync(cancellationToken);
        var path = $"/api/v1/organizations/{Uri.EscapeDataString(orgId)}/departments/{Uri.EscapeDataString(departmentId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Delete, path, body: null, cancellationToken);

        _logger.LogInformation("DocUtil 부서 삭제 호출 - OrgId={OrgId}, DeptId={DeptId}", orgId, departmentId);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
    }

    // 7) GetDepartmentMembersAsync — GET /api/v1/organizations/{org_id}/departments/{dept_id}/members
    public async Task<List<DocUtilDepartmentMember>> GetDepartmentMembersAsync(
        string departmentId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(departmentId))
        {
            throw new ArgumentException("departmentId 가 비어있습니다.", nameof(departmentId));
        }

        var orgId = await ResolveOrganizationIdAsync(cancellationToken);
        var path = $"/api/v1/organizations/{Uri.EscapeDataString(orgId)}/departments/{Uri.EscapeDataString(departmentId)}/members";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dtos = await JsonSerializer.DeserializeAsync<List<DepartmentMemberResponseDto>>(stream, JsonOptions, cancellationToken);
        if (dtos is null)
        {
            return new List<DocUtilDepartmentMember>();
        }

        return dtos
            .Select(m => new DocUtilDepartmentMember(
                m.Id ?? string.Empty,
                m.Username ?? string.Empty,
                m.Email ?? string.Empty,
                m.Role ?? string.Empty))
            .ToList();
    }

    // 8) GetOrganizationQuotaAsync — GET /api/v1/organizations/{org_id}/quotas/current
    public async Task<DocUtilOrganizationQuotaCurrent> GetOrganizationQuotaAsync(
        CancellationToken cancellationToken = default)
    {
        var orgId = await ResolveOrganizationIdAsync(cancellationToken);
        var path = $"/api/v1/organizations/{Uri.EscapeDataString(orgId)}/quotas/current";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<OrganizationQuotasCurrentResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 조직 할당량 응답을 디시리얼라이즈하지 못했습니다.");
        }

        // quotas map → 평탄 List 로 변환(quota_type 별 1행, key 정렬 — 운영자 UI 의 결정성 보장).
        var quotaList = (dto.Quotas ?? new Dictionary<string, QuotaStatusResponseDto>())
            .OrderBy(kv => kv.Key, StringComparer.Ordinal)
            .Select(kv => new DocUtilOrganizationQuotaStatus(
                kv.Value?.QuotaType ?? kv.Key,
                kv.Value?.MonthlyLimit ?? 0,
                kv.Value?.UsedCount ?? 0,
                kv.Value?.Remaining ?? 0,
                kv.Value?.YearMonth ?? dto.YearMonth ?? string.Empty))
            .ToArray();

        return new DocUtilOrganizationQuotaCurrent(
            dto.OrganizationId ?? orgId,
            dto.YearMonth ?? string.Empty,
            quotaList);
    }

    // ══════════════════════════════════════════════════════════════════════
    // Phase 10.1c (2026-05-10): DocUtil 프로젝트/보드 운영자 BFF — 13 메서드
    //
    // 기존 ListCollectionsAsync 보존(294e8a6, AgentBuilder dropdown 의존):
    //   - 시그니처/캐시 prefix `du:c:`/응답 형태(BFF 단순화 3 필드) 모두 동일.
    //   - 본 트랙의 새 메서드들은 별도 이름 — `ListProjectsAsync` / `GetProjectAsync` 등.
    //
    // 캐시 전략:
    //   본 클라이언트는 캐시 미적용 — Controller(AdminDocUtilProjectsController)가
    //   version-key + TTL 패턴으로 처리. mutation invalidate 는 ListCollectionsAsync 와 동일
    //   namespace `docutil-collections` 사용 → 운영자가 본 화면에서 프로젝트 mutation 시
    //   AgentBuilder 의 dropdown 도 즉시 새 데이터로 갱신(통합 namespace 효과).
    //
    // org_id 자동 부착:
    //   DocUtil 의 /projects 는 org-scoped (운영자 토큰의 org claim 으로 자동 필터). 본
    //   클라이언트는 path 에 orgId 를 명시하지 않지만 DocUtil 측에서 token 의 org 으로
    //   응답을 제한. 명시 호출 외 추가 검증 불필요.
    // ══════════════════════════════════════════════════════════════════════

    // 1) ListProjectsAsync — GET /api/v1/projects
    public async Task<DocUtilProjectList> ListProjectsAsync(
        int page = 1,
        int size = 20,
        string? search = null,
        CancellationToken cancellationToken = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 200) size = 20;

        var queryParts = new List<string>
        {
            $"page={page}",
            $"size={size}",
        };
        if (!string.IsNullOrWhiteSpace(search))
        {
            queryParts.Add($"search={Uri.EscapeDataString(search)}");
        }
        var path = $"/api/v1/projects?{string.Join("&", queryParts)}";

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        _logger.LogDebug(
            "DocUtil 프로젝트 목록 호출 - Page={Page}, Size={Size}, SearchLen={SearchLen}",
            page, size, search?.Length ?? 0);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<ProjectListResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 프로젝트 목록 응답을 디시리얼라이즈하지 못했습니다.");
        }

        var items = (dto.Items ?? Array.Empty<ProjectResponseDto>())
            .Select(MapProject)
            .ToArray();
        return new DocUtilProjectList(items, dto.Total, dto.Page, dto.Size);
    }

    // 2) GetProjectTreeAsync — GET /api/v1/projects/tree
    public async Task<List<DocUtilProjectTreeNode>> GetProjectTreeAsync(
        CancellationToken cancellationToken = default)
    {
        const string path = "/api/v1/projects/tree";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dtos = await JsonSerializer.DeserializeAsync<List<ProjectTreeNodeDto>>(stream, JsonOptions, cancellationToken);
        if (dtos is null)
        {
            return new List<DocUtilProjectTreeNode>();
        }

        return dtos
            .Select(n => new DocUtilProjectTreeNode(
                n.Id ?? string.Empty,
                n.Name ?? string.Empty,
                (n.Boards ?? Array.Empty<BoardResponseDto>())
                    .Select(MapBoard)
                    .ToArray()))
            .ToList();
    }

    // 3) GetProjectAsync — GET /api/v1/projects/{project_id} (404 → null)
    public async Task<DocUtilProject?> GetProjectAsync(
        string projectId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            throw new ArgumentException("projectId 가 비어있습니다.", nameof(projectId));
        }

        var path = $"/api/v1/projects/{Uri.EscapeDataString(projectId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            _logger.LogDebug("DocUtil 프로젝트 미존재 - ProjectId={ProjectId}", projectId);
            return null;
        }

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<ProjectResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 프로젝트 상세 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return MapProject(dto);
    }

    // 4) CreateProjectAsync — POST /api/v1/projects
    public async Task<DocUtilProject> CreateProjectAsync(
        DocUtilCreateProjectRequest request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            throw new ArgumentException("프로젝트 이름이 비어있습니다.", nameof(request));
        }

        const string path = "/api/v1/projects";
        var client = _httpClientFactory.CreateClient(HttpClientName);

        // DocUtil ProjectCreate: name + description? + allow_original_download? (default true)
        var body = new Dictionary<string, object?>
        {
            ["name"] = request.Name,
        };
        if (request.Description is not null) body["description"] = request.Description;
        if (request.AllowOriginalDownload is not null) body["allow_original_download"] = request.AllowOriginalDownload;

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body, cancellationToken);

        _logger.LogInformation(
            "DocUtil 프로젝트 생성 호출 - Name={Name}, AllowOriginalDownload={Allow}",
            request.Name, request.AllowOriginalDownload?.ToString() ?? "(default)");

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<ProjectResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 프로젝트 생성 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return MapProject(dto);
    }

    // 5) UpdateProjectAsync — PUT /api/v1/projects/{project_id}
    public async Task<DocUtilProject> UpdateProjectAsync(
        string projectId,
        DocUtilUpdateProjectRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            throw new ArgumentException("projectId 가 비어있습니다.", nameof(projectId));
        }
        ArgumentNullException.ThrowIfNull(request);

        var path = $"/api/v1/projects/{Uri.EscapeDataString(projectId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);

        // DocUtil ProjectUpdate: name? + description? — allow_original_download 미존재(추정 금지).
        var body = new Dictionary<string, object?>();
        if (request.Name is not null) body["name"] = request.Name;
        if (request.Description is not null) body["description"] = request.Description;

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Put, path, body, cancellationToken);

        _logger.LogInformation(
            "DocUtil 프로젝트 수정 호출 - ProjectId={ProjectId}, FieldCount={FieldCount}",
            projectId, body.Count);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<ProjectResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 프로젝트 수정 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return MapProject(dto);
    }

    // 6) DeleteProjectAsync — DELETE /api/v1/projects/{project_id}
    public async Task DeleteProjectAsync(
        string projectId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            throw new ArgumentException("projectId 가 비어있습니다.", nameof(projectId));
        }

        var path = $"/api/v1/projects/{Uri.EscapeDataString(projectId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Delete, path, body: null, cancellationToken);

        _logger.LogInformation("DocUtil 프로젝트 삭제 호출 - ProjectId={ProjectId}", projectId);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
    }

    // 7) GetProjectMembersAsync — GET /api/v1/projects/{project_id}/members
    public async Task<List<DocUtilProjectMember>> GetProjectMembersAsync(
        string projectId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            throw new ArgumentException("projectId 가 비어있습니다.", nameof(projectId));
        }

        var path = $"/api/v1/projects/{Uri.EscapeDataString(projectId)}/members";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dtos = await JsonSerializer.DeserializeAsync<List<ProjectMemberResponseDto>>(stream, JsonOptions, cancellationToken);
        if (dtos is null) return new List<DocUtilProjectMember>();

        return dtos
            .Select(m => new DocUtilProjectMember(
                m.Id ?? string.Empty,
                m.Username ?? string.Empty,
                m.Email ?? string.Empty,
                m.Role ?? string.Empty))
            .ToList();
    }

    // 8) GetProjectDepartmentsAsync — GET /api/v1/projects/{project_id}/departments
    public async Task<List<DocUtilProjectDepartment>> GetProjectDepartmentsAsync(
        string projectId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            throw new ArgumentException("projectId 가 비어있습니다.", nameof(projectId));
        }

        var path = $"/api/v1/projects/{Uri.EscapeDataString(projectId)}/departments";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dtos = await JsonSerializer.DeserializeAsync<List<ProjectDepartmentResponseDto>>(stream, JsonOptions, cancellationToken);
        if (dtos is null) return new List<DocUtilProjectDepartment>();

        return dtos
            .Select(d => new DocUtilProjectDepartment(
                d.Id ?? string.Empty,
                d.Name ?? string.Empty,
                d.Path ?? string.Empty,
                d.Depth))
            .ToList();
    }

    // 9) ListProjectBoardsAsync — GET /api/v1/projects/{project_id}/boards
    public async Task<DocUtilBoardList> ListProjectBoardsAsync(
        string projectId,
        int page = 1,
        int size = 50,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            throw new ArgumentException("projectId 가 비어있습니다.", nameof(projectId));
        }
        if (page < 1) page = 1;
        if (size < 1 || size > 200) size = 50;

        var path = $"/api/v1/projects/{Uri.EscapeDataString(projectId)}/boards?page={page}&size={size}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<BoardListResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 보드 목록 응답을 디시리얼라이즈하지 못했습니다.");
        }

        var items = (dto.Items ?? Array.Empty<BoardResponseDto>())
            .Select(MapBoard)
            .ToArray();
        return new DocUtilBoardList(items, dto.Total, dto.Page, dto.Size);
    }

    // 10) CreateProjectBoardAsync — POST /api/v1/projects/{project_id}/boards
    public async Task<DocUtilBoard> CreateProjectBoardAsync(
        string projectId,
        DocUtilCreateBoardRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            throw new ArgumentException("projectId 가 비어있습니다.", nameof(projectId));
        }
        ArgumentNullException.ThrowIfNull(request);
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            throw new ArgumentException("보드 이름이 비어있습니다.", nameof(request));
        }

        var path = $"/api/v1/projects/{Uri.EscapeDataString(projectId)}/boards";
        var client = _httpClientFactory.CreateClient(HttpClientName);

        // DocUtil BoardCreate: name + description? — folder_id 미존재(추정 금지).
        var body = new Dictionary<string, object?>
        {
            ["name"] = request.Name,
        };
        if (request.Description is not null) body["description"] = request.Description;

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body, cancellationToken);

        _logger.LogInformation(
            "DocUtil 보드 생성 호출 - ProjectId={ProjectId}, Name={Name}",
            projectId, request.Name);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<BoardResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 보드 생성 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return MapBoard(dto);
    }

    // 11) GetProjectBoardAsync — GET /api/v1/projects/{project_id}/boards/{board_id} (404 → null)
    public async Task<DocUtilBoard?> GetProjectBoardAsync(
        string projectId,
        string boardId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            throw new ArgumentException("projectId 가 비어있습니다.", nameof(projectId));
        }
        if (string.IsNullOrWhiteSpace(boardId))
        {
            throw new ArgumentException("boardId 가 비어있습니다.", nameof(boardId));
        }

        var path = $"/api/v1/projects/{Uri.EscapeDataString(projectId)}/boards/{Uri.EscapeDataString(boardId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            _logger.LogDebug("DocUtil 보드 미존재 - ProjectId={ProjectId}, BoardId={BoardId}", projectId, boardId);
            return null;
        }

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<BoardResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 보드 상세 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return MapBoard(dto);
    }

    // 12) UpdateProjectBoardAsync — PUT /api/v1/projects/{project_id}/boards/{board_id}
    public async Task<DocUtilBoard> UpdateProjectBoardAsync(
        string projectId,
        string boardId,
        DocUtilUpdateBoardRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            throw new ArgumentException("projectId 가 비어있습니다.", nameof(projectId));
        }
        if (string.IsNullOrWhiteSpace(boardId))
        {
            throw new ArgumentException("boardId 가 비어있습니다.", nameof(boardId));
        }
        ArgumentNullException.ThrowIfNull(request);

        var path = $"/api/v1/projects/{Uri.EscapeDataString(projectId)}/boards/{Uri.EscapeDataString(boardId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);

        var body = new Dictionary<string, object?>();
        if (request.Name is not null) body["name"] = request.Name;
        if (request.Description is not null) body["description"] = request.Description;

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Put, path, body, cancellationToken);

        _logger.LogInformation(
            "DocUtil 보드 수정 호출 - ProjectId={ProjectId}, BoardId={BoardId}, FieldCount={FieldCount}",
            projectId, boardId, body.Count);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<BoardResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 보드 수정 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return MapBoard(dto);
    }

    // 13) DeleteProjectBoardAsync — DELETE /api/v1/projects/{project_id}/boards/{board_id}
    public async Task DeleteProjectBoardAsync(
        string projectId,
        string boardId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(projectId))
        {
            throw new ArgumentException("projectId 가 비어있습니다.", nameof(projectId));
        }
        if (string.IsNullOrWhiteSpace(boardId))
        {
            throw new ArgumentException("boardId 가 비어있습니다.", nameof(boardId));
        }

        var path = $"/api/v1/projects/{Uri.EscapeDataString(projectId)}/boards/{Uri.EscapeDataString(boardId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Delete, path, body: null, cancellationToken);

        _logger.LogInformation(
            "DocUtil 보드 삭제 호출 - ProjectId={ProjectId}, BoardId={BoardId}",
            projectId, boardId);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
    }

    // ── Phase 10.1c 매핑 헬퍼 ──────────────────────────────────────────────
    private static DocUtilProject MapProject(ProjectResponseDto dto)
        => new(
            dto.Id ?? string.Empty,
            dto.Name ?? string.Empty,
            dto.Description,
            dto.AllowOriginalDownload,
            dto.OrganizationId ?? string.Empty,
            dto.CreatedBy ?? string.Empty,
            dto.CreatedAt,
            dto.UpdatedAt);

    private static DocUtilBoard MapBoard(BoardResponseDto dto)
        => new(
            dto.Id ?? string.Empty,
            dto.ProjectId ?? string.Empty,
            dto.Name ?? string.Empty,
            dto.Description,
            dto.CreatedBy ?? string.Empty,
            dto.CreatedAt,
            dto.UpdatedAt);

    // ══════════════════════════════════════════════════════════════════════
    // (Phase 10.1b 잔여 — UpdateOrganizationQuotaAsync 는 본 위치에 유지)
    // 9) UpdateOrganizationQuotaAsync — PUT /api/v1/organizations/{org_id}/quotas/{quota_type}
    public async Task<DocUtilOrganizationQuotaStatus> UpdateOrganizationQuotaAsync(
        string quotaType,
        DocUtilUpdateQuotaRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(quotaType))
        {
            throw new ArgumentException("quotaType 이 비어있습니다.", nameof(quotaType));
        }
        ArgumentNullException.ThrowIfNull(request);

        var orgId = await ResolveOrganizationIdAsync(cancellationToken);
        var path = $"/api/v1/organizations/{Uri.EscapeDataString(orgId)}/quotas/{Uri.EscapeDataString(quotaType)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);

        var body = new Dictionary<string, object?>
        {
            ["monthly_limit"] = request.MonthlyLimit,
        };

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Put, path, body, cancellationToken);

        _logger.LogInformation(
            "DocUtil 조직 할당량 수정 호출 - OrgId={OrgId}, QuotaType={QuotaType}, MonthlyLimit={Limit}",
            orgId, quotaType, request.MonthlyLimit);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<QuotaStatusResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 조직 할당량 수정 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return new DocUtilOrganizationQuotaStatus(
            dto.QuotaType ?? quotaType,
            dto.MonthlyLimit,
            dto.UsedCount,
            dto.Remaining,
            dto.YearMonth ?? string.Empty);
    }

    // ── Phase 10.1b 매핑 헬퍼 ──────────────────────────────────────────────
    private static DocUtilOrganization MapOrganization(OrganizationResponseDto dto)
        => new(
            dto.Id ?? string.Empty,
            dto.Name ?? string.Empty,
            dto.Slug ?? string.Empty,
            dto.Description,
            dto.Settings,
            dto.CreatedAt);

    private static DocUtilDepartment MapDepartment(DepartmentResponseDto dto)
        => new(
            dto.Id ?? string.Empty,
            dto.OrganizationId ?? string.Empty,
            dto.ParentId,
            dto.Name ?? string.Empty,
            dto.Depth,
            dto.Path ?? string.Empty,
            dto.CreatedAt);

    /// <summary>
    /// IDocUtilTokenProvider 의 GetOrganizationIdAsync 결과를 검증하고 반환.
    /// 실패 시 한국어 InvalidOperationException — Controller 가 502 매핑.
    /// </summary>
    private async Task<string> ResolveOrganizationIdAsync(CancellationToken cancellationToken)
    {
        var orgId = await _tokenProvider.GetOrganizationIdAsync(cancellationToken);
        if (string.IsNullOrWhiteSpace(orgId))
        {
            throw new InvalidOperationException(
                "DocUtil 운영자 토큰에서 organization_id 를 추출할 수 없습니다. " +
                "ServiceUsername/ServicePassword 또는 JwtToken 설정을 확인하세요.");
        }
        return orgId;
    }

    // ── Phase 10.1a UserResponse → record 매핑 헬퍼 ────────────────────────
    private static DocUtilUserSummary MapUserSummary(UserResponseDto dto)
        => new(
            dto.Id ?? string.Empty,
            dto.Username ?? string.Empty,
            dto.Email ?? string.Empty,
            dto.Role ?? string.Empty,
            dto.Status ?? string.Empty,
            dto.OrganizationId ?? string.Empty,
            dto.DepartmentId,
            dto.Language,
            dto.LastLoginAt,
            dto.CreatedAt);

    private static DocUtilUserDetail MapUserDetail(UserResponseDto dto)
        => new(
            dto.Id ?? string.Empty,
            dto.Username ?? string.Empty,
            dto.Email ?? string.Empty,
            dto.Role ?? string.Empty,
            dto.Status ?? string.Empty,
            dto.OrganizationId ?? string.Empty,
            dto.DepartmentId,
            dto.Language,
            dto.LastLoginAt,
            dto.CreatedAt);

    // ══════════════════════════════════════════════════════════════════════
    // 헬퍼
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// JSON 요청 빌더 — IDocUtilTokenProvider 에서 받은 Bearer 토큰 + (선택) JSON body 부착.
    /// 토큰은 만료 5분 전부터 자동 refresh / re-login 되며 매 호출 fast cache hit.
    /// </summary>
    private async Task<HttpRequestMessage> BuildJsonRequestAsync(
        HttpMethod method, string relativePath, object? body, CancellationToken cancellationToken)
    {
        var httpRequest = new HttpRequestMessage(method, relativePath);

        var token = await _tokenProvider.GetTokenAsync(cancellationToken);
        if (!string.IsNullOrWhiteSpace(token))
        {
            httpRequest.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        }
        else
        {
            // 토큰 미설정 — 401 이 나면 EnsureSuccessOrThrowKoreanAsync 가 한국어 메시지로 안내한다.
            _logger.LogWarning(
                "DocUtil 토큰 미설정 — JwtToken / ServiceAccount(Username/Password) / ApiKey 중 하나 필수.");
        }

        if (body is not null)
        {
            var jsonBody = JsonSerializer.Serialize(body, JsonOptions);
            httpRequest.Content = new StringContent(jsonBody, Encoding.UTF8, "application/json");
        }

        return httpRequest;
    }

    /// <summary>
    /// DocUtil 응답 상태 코드를 검사하고, 실패 시 한국어 InvalidOperationException 으로 변환.
    /// AgentHub GlobalExceptionHandlerMiddleware 가 502/503 으로 응답 합성한다.
    /// </summary>
    private async Task EnsureSuccessOrThrowKoreanAsync(
        HttpResponseMessage response,
        string path,
        CancellationToken cancellationToken)
    {
        if (response.IsSuccessStatusCode) return;

        var status = (int)response.StatusCode;
        var body = await SafeReadErrorBodyAsync(response, cancellationToken);

        // 인증 실패 — 운영자 토큰 누락/만료가 가장 흔한 시나리오.
        if (response.StatusCode == HttpStatusCode.Unauthorized
            || response.StatusCode == HttpStatusCode.Forbidden)
        {
            _logger.LogError(
                "DocUtil 인증 실패 - Path={Path}, Status={Status}, Body={Body}",
                path, status, body);
            throw new InvalidOperationException(
                "DocUtil 인증 실패. JwtToken 또는 ApiKey 설정을 확인하세요.");
        }

        // 5xx — DocUtil 서비스 장애.
        if (status >= 500)
        {
            _logger.LogError(
                "DocUtil 서비스 오류 - Path={Path}, Status={Status}, Body={Body}",
                path, status, body);
            throw new InvalidOperationException(
                $"DocUtil 응답 실패. 네트워크 또는 서비스 상태를 확인하세요. (HTTP {status})");
        }

        // 그 외 4xx — 호출자 책임.
        _logger.LogWarning(
            "DocUtil 호출 실패 - Path={Path}, Status={Status}, Body={Body}",
            path, status, body);
        throw new InvalidOperationException(
            $"DocUtil 호출이 실패했습니다 (HTTP {status}): {Truncate(body, 200)}");
    }

    private static async Task<string> SafeReadErrorBodyAsync(
        HttpResponseMessage response,
        CancellationToken cancellationToken)
    {
        try
        {
            return await response.Content.ReadAsStringAsync(cancellationToken);
        }
        catch
        {
            return string.Empty;
        }
    }

    private static string Truncate(string s, int max)
        => string.IsNullOrEmpty(s) ? string.Empty : (s.Length <= max ? s : s[..max] + "...");

    // ── DocUtil FastAPI 응답 매핑 DTO (private — 외부 노출 X) ─────────────

    private sealed class SearchResponseDto
    {
        [JsonPropertyName("results")] public SearchHitDto[]? Results { get; set; }
        [JsonPropertyName("total_time")] public double TotalTime { get; set; }
        [JsonPropertyName("metadata")] public object? Metadata { get; set; }
    }

    private sealed class SearchHitDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("content")] public string? Content { get; set; }
        [JsonPropertyName("score")] public double Score { get; set; }
        [JsonPropertyName("metadata")] public object? Metadata { get; set; }
    }

    private sealed class DocumentListDto
    {
        [JsonPropertyName("items")] public DocumentSummaryDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
        [JsonPropertyName("page")] public int Page { get; set; }
        [JsonPropertyName("size")] public int Size { get; set; }
    }

    private sealed class DocumentSummaryDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("status")] public string? Status { get; set; }
        [JsonPropertyName("created_at")] public DateTime? CreatedAt { get; set; }
    }

    private sealed class DocumentDetailDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("status")] public string? Status { get; set; }
        [JsonPropertyName("created_at")] public DateTime? CreatedAt { get; set; }
        [JsonPropertyName("uploader_name")] public string? UploaderName { get; set; }
        [JsonPropertyName("visibility_targets")] public object? VisibilityTargets { get; set; }
    }

    private sealed class UploadResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("status")] public string? Status { get; set; }
        [JsonPropertyName("job_id")] public string? JobId { get; set; }
    }

    private sealed class ChunkResponseDto
    {
        [JsonPropertyName("chunk_id")] public string? ChunkId { get; set; }
        [JsonPropertyName("content")] public string? Content { get; set; }
        [JsonPropertyName("chunk_index")] public int ChunkIndex { get; set; }
        [JsonPropertyName("metadata")] public object? Metadata { get; set; }
    }

    // DocUtil GET /api/v1/projects 응답 매핑 — 후속 트랙 KB collection dropdown(2026-05-08).
    // BFF 표면 단순화 원칙: items[].id/name/description 3 필드만 사용. 그 외 필드(organization_id,
    // created_by, created_at, updated_at, allow_original_download) 는 deserialize 비대상.
    private sealed class ProjectListDto
    {
        [JsonPropertyName("items")] public ProjectSummaryDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
        [JsonPropertyName("page")] public int Page { get; set; }
        [JsonPropertyName("size")] public int Size { get; set; }
    }

    private sealed class ProjectSummaryDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
    }

    // ── Phase 4: SearchAsync 캐시용 wrapper(record 가 직렬화 시 비결정성 방지) ──
    // CachingService 는 generic GetAsync<T>/SetAsync<T> 시 `where T : class` 제약이므로
    // record 는 사용 가능하지만 명시적 클래스 wrapper 가 직렬화/역직렬화 안정성 우수.
    public sealed class CachedSearchResultDto
    {
        public DocUtilSearchHit[]? Hits { get; set; }
        public double TotalTime { get; set; }
        public object? Metadata { get; set; }
    }

    // ── 후속 트랙 2026-05-08: ListCollectionsAsync 캐시용 wrapper ──────────
    // record DocUtilCollection 직렬화 안정성을 위해 클래스 wrapper 사용 — Search 와 동일 패턴.
    // Items 는 array 로 직렬화(List 보다 JsonSerializer 의 polymorphic round-trip 안정).
    public sealed class CachedCollectionListDto
    {
        public DocUtilCollection[]? Items { get; set; }
    }

    // ── Phase 10.1a (2026-05-10): DocUtil Users API 응답 매핑 DTO ───────────
    // OpenAPI 캡처 결과 UserResponse / UserListResponse schema 에 1:1 매핑.
    // ins_dt → created_at alias 는 DocUtil 측이 처리(2026-05-10 schema 검증 완료).

    private sealed class UserListResponseDto
    {
        [JsonPropertyName("items")] public UserResponseDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
        [JsonPropertyName("page")] public int Page { get; set; }
        [JsonPropertyName("size")] public int Size { get; set; }
    }

    private sealed class UserResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("username")] public string? Username { get; set; }
        [JsonPropertyName("email")] public string? Email { get; set; }
        [JsonPropertyName("role")] public string? Role { get; set; }
        [JsonPropertyName("status")] public string? Status { get; set; }
        [JsonPropertyName("organization_id")] public string? OrganizationId { get; set; }
        [JsonPropertyName("department_id")] public string? DepartmentId { get; set; }
        [JsonPropertyName("language")] public string? Language { get; set; }
        [JsonPropertyName("last_login_at")] public DateTime? LastLoginAt { get; set; }
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
    }

    // ── Phase 10.1b (2026-05-10): DocUtil 조직/부서/할당량 응답 매핑 DTO ──
    // OpenAPI 캡처(2026-05-10) 결과 OrganizationResponse / DepartmentResponse /
    // OrganizationQuotasCurrentResponse / QuotaStatusResponse schema 에 1:1 매핑.
    // 부서 멤버는 free-form 응답으로, 실제 캡처 응답에서 4 필드(id/username/email/role) 확인.

    private sealed class OrganizationResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("slug")] public string? Slug { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
        [JsonPropertyName("settings")] public object? Settings { get; set; }
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
    }

    private sealed class DepartmentResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("organization_id")] public string? OrganizationId { get; set; }
        [JsonPropertyName("parent_id")] public string? ParentId { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("depth")] public int Depth { get; set; }
        [JsonPropertyName("path")] public string? Path { get; set; }
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
    }

    private sealed class DepartmentMemberResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("username")] public string? Username { get; set; }
        [JsonPropertyName("email")] public string? Email { get; set; }
        [JsonPropertyName("role")] public string? Role { get; set; }
    }

    private sealed class OrganizationQuotasCurrentResponseDto
    {
        [JsonPropertyName("organization_id")] public string? OrganizationId { get; set; }
        [JsonPropertyName("year_month")] public string? YearMonth { get; set; }
        [JsonPropertyName("quotas")] public Dictionary<string, QuotaStatusResponseDto>? Quotas { get; set; }
    }

    private sealed class QuotaStatusResponseDto
    {
        [JsonPropertyName("quota_type")] public string? QuotaType { get; set; }
        [JsonPropertyName("monthly_limit")] public int MonthlyLimit { get; set; }
        [JsonPropertyName("used_count")] public int UsedCount { get; set; }
        [JsonPropertyName("remaining")] public int Remaining { get; set; }
        [JsonPropertyName("year_month")] public string? YearMonth { get; set; }
    }

    // ── Phase 10.1c (2026-05-10): DocUtil Projects/Boards API 응답 매핑 DTO ─
    // OpenAPI 캡처(2026-05-10) ProjectResponse / ProjectListResponse / BoardResponse /
    // BoardListResponse 에 1:1 매핑. members/departments/tree 응답은 free-form (typed schema 없음).

    private sealed class ProjectResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
        [JsonPropertyName("allow_original_download")] public bool AllowOriginalDownload { get; set; }
        [JsonPropertyName("organization_id")] public string? OrganizationId { get; set; }
        [JsonPropertyName("created_by")] public string? CreatedBy { get; set; }
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
        [JsonPropertyName("updated_at")] public DateTime UpdatedAt { get; set; }
    }

    private sealed class ProjectListResponseDto
    {
        [JsonPropertyName("items")] public ProjectResponseDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
        [JsonPropertyName("page")] public int Page { get; set; }
        [JsonPropertyName("size")] public int Size { get; set; }
    }

    private sealed class ProjectTreeNodeDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("boards")] public BoardResponseDto[]? Boards { get; set; }
    }

    private sealed class ProjectMemberResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("username")] public string? Username { get; set; }
        [JsonPropertyName("email")] public string? Email { get; set; }
        [JsonPropertyName("role")] public string? Role { get; set; }
    }

    private sealed class ProjectDepartmentResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("path")] public string? Path { get; set; }
        [JsonPropertyName("depth")] public int Depth { get; set; }
    }

    private sealed class BoardResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("project_id")] public string? ProjectId { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
        [JsonPropertyName("created_by")] public string? CreatedBy { get; set; }
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
        [JsonPropertyName("updated_at")] public DateTime UpdatedAt { get; set; }
    }

    private sealed class BoardListResponseDto
    {
        [JsonPropertyName("items")] public BoardResponseDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
        [JsonPropertyName("page")] public int Page { get; set; }
        [JsonPropertyName("size")] public int Size { get; set; }
    }
}
