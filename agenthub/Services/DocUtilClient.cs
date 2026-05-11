using System.Diagnostics;
using System.Net;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using AIAgentManagement.Exceptions;

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
    // Phase 10.x — Long-running endpoint 전용 named client (5분 timeout).
    // 적용 대상:
    //   1) DownloadReportAsync               — Report 파일(zip/csv/xlsx) 다운로드
    //   2) PreviewDocumentTemplateAsync      — Jinja2 템플릿 렌더 미리보기(파일 합성)
    //   3) RequestDocumentV2ExportAsync      — 비동기 export job 요청(서버 동기 큐잉 시 지연 가능)
    //   4) DownloadDocumentV2ExportAsync     — 완료된 export 파일 다운로드(대용량 가능)
    //   5) ExportAuditLogsAsync              — 감사 로그 CSV 스트리밍(N만건 가능)
    // 표준 60s timeout 으로는 부족 — 사용자 체감 한계(5분)까지 허용하되 그 이상은 504 전파.
    private const string LongRunningHttpClientName = "docutil-longrunning";

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

    // ══════════════════════════════════════════════════════════════════════
    // Phase 10.2a (2026-05-10) — DocUtil Dashboard + Audit BFF 7 메서드
    //
    // org_id 자동 부착:
    //   DocUtil 의 dashboard / audit-logs 는 token 의 org claim 으로 자동 scope.
    //   본 클라이언트는 path 에 orgId 를 명시하지 않는다(추정 금지 — OpenAPI 검증 결과).
    //
    // 한국어 502 매핑:
    //   EnsureSuccessOrThrowKoreanAsync 가 4xx/5xx 를 InvalidOperationException 으로
    //   변환 → Controller 가 502 ErrorResponseDto 한국어 본문으로 응답.
    // ══════════════════════════════════════════════════════════════════════

    // 1) GetDashboardMetricsAsync — GET /api/v1/dashboard/metrics
    public async Task<DocUtilDashboardMetrics> GetDashboardMetricsAsync(
        CancellationToken cancellationToken = default)
    {
        const string path = "/api/v1/dashboard/metrics";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DashboardMetricsDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 대시보드 메트릭 응답을 디시리얼라이즈하지 못했습니다.");
        }

        // feature_usage 는 free-form (additionalProperties=true). 정수 캐스팅 안전 변환.
        var featureUsage = new Dictionary<string, int>(StringComparer.Ordinal);
        if (dto.FeatureUsage is JsonElement el && el.ValueKind == JsonValueKind.Object)
        {
            foreach (var prop in el.EnumerateObject())
            {
                if (prop.Value.ValueKind == JsonValueKind.Number && prop.Value.TryGetInt32(out var n))
                {
                    featureUsage[prop.Name] = n;
                }
            }
        }

        return new DocUtilDashboardMetrics(
            dto.TotalUsers,
            dto.ActiveUsers,
            dto.TotalDocuments,
            dto.TotalSearches,
            featureUsage);
    }

    // 2) GetDashboardResponseTimesAsync — GET /api/v1/dashboard/response-times
    public async Task<DocUtilResponseTimes> GetDashboardResponseTimesAsync(
        string? period = null,
        CancellationToken cancellationToken = default)
    {
        var path = string.IsNullOrWhiteSpace(period)
            ? "/api/v1/dashboard/response-times"
            : $"/api/v1/dashboard/response-times?period={Uri.EscapeDataString(period)}";

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<ResponseTimeDataDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 응답시간 데이터 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return new DocUtilResponseTimes(
            dto.Timestamps ?? Array.Empty<string>(),
            dto.Values ?? Array.Empty<double>());
    }

    // 3) GetDashboardSearchErrorsAsync — GET /api/v1/dashboard/search-errors
    public async Task<DocUtilSearchErrors> GetDashboardSearchErrorsAsync(
        string? period = null,
        CancellationToken cancellationToken = default)
    {
        var path = string.IsNullOrWhiteSpace(period)
            ? "/api/v1/dashboard/search-errors"
            : $"/api/v1/dashboard/search-errors?period={Uri.EscapeDataString(period)}";

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<SearchErrorDataDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 검색 오류 데이터 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return new DocUtilSearchErrors(
            dto.Dates ?? Array.Empty<string>(),
            dto.ErrorCounts ?? Array.Empty<int>());
    }

    // 4) GetDashboardSearchUsageAsync — GET /api/v1/dashboard/search-usage
    public async Task<DocUtilSearchUsage> GetDashboardSearchUsageAsync(
        string? period = null,
        CancellationToken cancellationToken = default)
    {
        var path = string.IsNullOrWhiteSpace(period)
            ? "/api/v1/dashboard/search-usage"
            : $"/api/v1/dashboard/search-usage?period={Uri.EscapeDataString(period)}";

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<SearchUsageStatsDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 검색 사용량 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return new DocUtilSearchUsage(
            dto.TotalRequests,
            dto.TotalResponses,
            dto.TotalFailures,
            dto.Period ?? string.Empty);
    }

    // 5) GetDashboardUploadStatusAsync — GET /api/v1/dashboard/upload-status
    public async Task<DocUtilUploadStatus> GetDashboardUploadStatusAsync(
        CancellationToken cancellationToken = default)
    {
        const string path = "/api/v1/dashboard/upload-status";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<UploadStatusChartDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 업로드 상태 응답을 디시리얼라이즈하지 못했습니다.");
        }

        return new DocUtilUploadStatus(
            dto.Completed,
            dto.Processing,
            dto.Waiting,
            dto.Error);
    }

    // 6) ListAuditLogsAsync — GET /api/v1/audit-logs
    public async Task<DocUtilAuditLogList> ListAuditLogsAsync(
        int page = 1,
        int size = 50,
        string? action = null,
        string? resourceType = null,
        string? userId = null,
        DateTime? startDate = null,
        DateTime? endDate = null,
        CancellationToken cancellationToken = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 200) size = 50;

        var queryParts = new List<string>
        {
            $"page={page}",
            $"size={size}",
        };
        if (!string.IsNullOrWhiteSpace(action))
        {
            queryParts.Add($"action={Uri.EscapeDataString(action)}");
        }
        if (!string.IsNullOrWhiteSpace(resourceType))
        {
            queryParts.Add($"resource_type={Uri.EscapeDataString(resourceType)}");
        }
        if (!string.IsNullOrWhiteSpace(userId))
        {
            queryParts.Add($"user_id={Uri.EscapeDataString(userId)}");
        }
        if (startDate.HasValue)
        {
            queryParts.Add($"start_date={Uri.EscapeDataString(startDate.Value.ToUniversalTime().ToString("o"))}");
        }
        if (endDate.HasValue)
        {
            queryParts.Add($"end_date={Uri.EscapeDataString(endDate.Value.ToUniversalTime().ToString("o"))}");
        }
        var path = $"/api/v1/audit-logs?{string.Join("&", queryParts)}";

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        _logger.LogDebug(
            "DocUtil 감사 로그 호출 - Page={Page}, Size={Size}, Action={Action}, ResourceType={ResourceType}, UserId={UserId}",
            page, size, action ?? "(any)", resourceType ?? "(any)", userId ?? "(any)");

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<AuditLogListResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 감사 로그 목록 응답을 디시리얼라이즈하지 못했습니다.");
        }

        var items = (dto.Items ?? Array.Empty<AuditLogResponseDto>())
            .Select(MapAuditLog)
            .ToArray();
        return new DocUtilAuditLogList(items, dto.Total, dto.Page, dto.Size);
    }

    // 7) ExportAuditLogsAsync — GET /api/v1/audit-logs/export (text/csv binary stream)
    public async Task<DocUtilAuditExport> ExportAuditLogsAsync(
        string? action = null,
        string? resourceType = null,
        string? userId = null,
        DateTime? startDate = null,
        DateTime? endDate = null,
        CancellationToken cancellationToken = default)
    {
        var queryParts = new List<string>();
        if (!string.IsNullOrWhiteSpace(action))
        {
            queryParts.Add($"action={Uri.EscapeDataString(action)}");
        }
        if (!string.IsNullOrWhiteSpace(resourceType))
        {
            queryParts.Add($"resource_type={Uri.EscapeDataString(resourceType)}");
        }
        if (!string.IsNullOrWhiteSpace(userId))
        {
            queryParts.Add($"user_id={Uri.EscapeDataString(userId)}");
        }
        if (startDate.HasValue)
        {
            queryParts.Add($"start_date={Uri.EscapeDataString(startDate.Value.ToUniversalTime().ToString("o"))}");
        }
        if (endDate.HasValue)
        {
            queryParts.Add($"end_date={Uri.EscapeDataString(endDate.Value.ToUniversalTime().ToString("o"))}");
        }
        var path = queryParts.Count == 0
            ? "/api/v1/audit-logs/export"
            : $"/api/v1/audit-logs/export?{string.Join("&", queryParts)}";

        // Long-running named client (5분 timeout) — N만 건 CSV 스트리밍은 60s 초과 가능.
        var client = _httpClientFactory.CreateClient(LongRunningHttpClientName);
        var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        // 본 메서드는 stream 반환 — using 으로 감싸지 않음(호출자 소유).

        _logger.LogInformation(
            "DocUtil 감사 로그 export 호출 - Action={Action}, ResourceType={ResourceType}, UserId={UserId}",
            action ?? "(any)", resourceType ?? "(any)", userId ?? "(any)");

        // ResponseHeadersRead — 큰 CSV 도 헤더 파싱 후 stream 반환(메모리 buffering 회피).
        var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseHeadersRead, cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            try
            {
                await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
            }
            finally
            {
                response.Dispose();
                httpRequest.Dispose();
            }
            // EnsureSuccessOrThrow 가 throw 하므로 여기 도달하지 않음.
        }

        var contentType = response.Content.Headers.ContentType?.ToString()
            ?? "text/csv; charset=utf-8";

        // Content-Disposition 의 filename 추출(없으면 fallback).
        var disposition = response.Content.Headers.ContentDisposition;
        var fileName = disposition?.FileNameStar
            ?? disposition?.FileName?.Trim('"')
            ?? "audit_logs.csv";

        // Stream 은 호출자(Controller) 가 Dispose 책임. response 객체는 stream 의 lifetime
        // 까지 살아 있어야 하므로 response Dispose 는 stream Dispose 시점에 함께 호출되도록
        // CompositeStream 으로 wrap 한다.
        var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var owned = new HttpResponseOwnedStream(stream, response, httpRequest);
        return new DocUtilAuditExport(owned, contentType, fileName);
    }

    // ══════════════════════════════════════════════════════════════════════
    // Phase 10.2b (2026-05-10) — DocUtil Search Scopes + Evaluation BFF 15 메서드
    //
    // org_id 자동 부착:
    //   DocUtil 의 search-scopes / evaluation 은 token 의 org claim 으로 자동 scope.
    //   본 클라이언트는 path 에 orgId 를 명시하지 않는다(추정 금지 — OpenAPI 검증 결과).
    //
    // 한국어 502 매핑:
    //   EnsureSuccessOrThrowKoreanAsync 가 4xx/5xx 를 InvalidOperationException 으로
    //   변환 → Controller 가 502 ErrorResponseDto 한국어 본문으로 응답.
    // ══════════════════════════════════════════════════════════════════════

    // ── Search Scopes (9) ─────────────────────────────────────────────────

    public async Task<DocUtilSearchScopeList> ListSearchScopesAsync(
        int page = 1,
        int size = 20,
        CancellationToken cancellationToken = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 100) size = 20;

        var path = $"/api/v1/search-scopes?page={page}&size={size}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<SearchScopeListResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 검색범위 목록 응답을 디시리얼라이즈하지 못했습니다.");
        }

        var items = (dto.Items ?? Array.Empty<SearchScopeResponseDto>())
            .Select(MapSearchScopeSummary)
            .ToArray();
        return new DocUtilSearchScopeList(items, dto.Total, dto.Page, dto.Size);
    }

    public async Task<List<DocUtilSearchScopeOption>> ListSearchScopeOptionsAsync(
        CancellationToken cancellationToken = default)
    {
        const string path = "/api/v1/search-scopes/options";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var arr = await JsonSerializer.DeserializeAsync<SearchScopeOptionDto[]>(stream, JsonOptions, cancellationToken);
        if (arr is null)
        {
            return new List<DocUtilSearchScopeOption>();
        }
        return arr.Select(d => new DocUtilSearchScopeOption(
            d.Id ?? string.Empty,
            d.Name ?? string.Empty,
            d.LocationPath)).ToList();
    }

    public async Task<List<DocUtilLocationOption>> ListSearchScopeLocationsAsync(
        string locationType,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(locationType))
        {
            throw new InvalidOperationException("location_type 파라미터가 비어 있습니다(project/board/folder 중 하나).");
        }

        var path = $"/api/v1/search-scopes/locations?location_type={Uri.EscapeDataString(locationType)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var arr = await JsonSerializer.DeserializeAsync<LocationOptionDto[]>(stream, JsonOptions, cancellationToken);
        if (arr is null)
        {
            return new List<DocUtilLocationOption>();
        }
        return arr.Select(d => new DocUtilLocationOption(
            d.Id ?? string.Empty,
            d.Name ?? string.Empty,
            d.Type ?? string.Empty,
            d.Path)).ToList();
    }

    public async Task<DocUtilSearchScopeDetail?> GetSearchScopeAsync(
        string scopeId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(scopeId))
        {
            throw new InvalidOperationException("scope_id 가 비어 있습니다.");
        }

        var path = $"/api/v1/search-scopes/{Uri.EscapeDataString(scopeId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return null;
        }
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<SearchScopeResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 검색범위 상세 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapSearchScopeDetail(dto);
    }

    public async Task<DocUtilSearchScopeDetail> CreateSearchScopeAsync(
        DocUtilCreateScopeRequest request,
        CancellationToken cancellationToken = default)
    {
        if (request is null || string.IsNullOrWhiteSpace(request.Name))
        {
            throw new InvalidOperationException("검색범위 이름이 비어 있습니다.");
        }

        const string path = "/api/v1/search-scopes";
        var body = new SearchScopeCreateRequestDto
        {
            Name = request.Name,
            Description = request.Description,
            ProjectId = request.ProjectId,
            BoardId = request.BoardId,
            FolderId = request.FolderId,
            ChatbotEnabled = request.ChatbotEnabled,
            QaEnabled = request.QaEnabled,
            KeywordSearchEnabled = request.KeywordSearchEnabled,
            AgentEnabled = request.AgentEnabled,
            ChunkSize = request.ChunkSize,
            ChunkOverlap = request.ChunkOverlap,
            TitleWeight = request.TitleWeight,
            KeywordWeight = request.KeywordWeight,
            ContentWeight = request.ContentWeight,
            MaxResults = request.MaxResults,
            SimilarityThreshold = request.SimilarityThreshold,
        };

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<SearchScopeResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 검색범위 생성 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapSearchScopeDetail(dto);
    }

    public async Task<DocUtilSearchScopeDetail> UpdateSearchScopeAsync(
        string scopeId,
        DocUtilUpdateScopeRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(scopeId))
        {
            throw new InvalidOperationException("scope_id 가 비어 있습니다.");
        }
        if (request is null)
        {
            throw new InvalidOperationException("수정 요청 본문이 비어 있습니다.");
        }

        var path = $"/api/v1/search-scopes/{Uri.EscapeDataString(scopeId)}";
        var body = new SearchScopeUpdateRequestDto
        {
            Name = request.Name,
            Description = request.Description,
            ProjectId = request.ProjectId,
            BoardId = request.BoardId,
            FolderId = request.FolderId,
            ChatbotEnabled = request.ChatbotEnabled,
            QaEnabled = request.QaEnabled,
            KeywordSearchEnabled = request.KeywordSearchEnabled,
            AgentEnabled = request.AgentEnabled,
            ChunkSize = request.ChunkSize,
            ChunkOverlap = request.ChunkOverlap,
            TitleWeight = request.TitleWeight,
            KeywordWeight = request.KeywordWeight,
            ContentWeight = request.ContentWeight,
            MaxResults = request.MaxResults,
            SimilarityThreshold = request.SimilarityThreshold,
        };

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Put, path, body, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<SearchScopeResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 검색범위 수정 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapSearchScopeDetail(dto);
    }

    public async Task DeleteSearchScopeAsync(
        string scopeId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(scopeId))
        {
            throw new InvalidOperationException("scope_id 가 비어 있습니다.");
        }

        var path = $"/api/v1/search-scopes/{Uri.EscapeDataString(scopeId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Delete, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
    }

    public async Task<DocUtilSearchScopeDetail> UpdateSearchScopeEnvironmentAsync(
        string scopeId,
        DocUtilUpdateScopeEnvironmentRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(scopeId))
        {
            throw new InvalidOperationException("scope_id 가 비어 있습니다.");
        }
        if (request is null)
        {
            throw new InvalidOperationException("환경 설정 요청 본문이 비어 있습니다.");
        }

        var path = $"/api/v1/search-scopes/{Uri.EscapeDataString(scopeId)}/environment";
        // SearchScopeEnvironment schema 는 모든 필드 default 가 있어 nullable 로 보내면 default 적용.
        var body = new SearchScopeEnvironmentRequestDto
        {
            ChatbotEnabled = request.ChatbotEnabled,
            ChatbotFaqTemplate = request.ChatbotFaqTemplate,
            QaEnabled = request.QaEnabled,
            QaPromptTemplate = request.QaPromptTemplate,
            QaLlmModel = request.QaLlmModel,
            KeywordSearchEnabled = request.KeywordSearchEnabled,
            AgentEnabled = request.AgentEnabled,
            ChunkSize = request.ChunkSize,
            ChunkOverlap = request.ChunkOverlap,
            TitleWeight = request.TitleWeight,
            KeywordWeight = request.KeywordWeight,
            ContentWeight = request.ContentWeight,
            MaxResults = request.MaxResults,
            SimilarityThreshold = request.SimilarityThreshold,
        };

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Put, path, body, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<SearchScopeResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 검색범위 환경 수정 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapSearchScopeDetail(dto);
    }

    public async Task<DocUtilSearchScopeValidIdResponse> GetSearchScopeValidIdAsync(
        string scopeId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(scopeId))
        {
            throw new InvalidOperationException("scope_id 가 비어 있습니다.");
        }

        var path = $"/api/v1/search-scopes/{Uri.EscapeDataString(scopeId)}/valid-id";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        // 응답 schema 미정의 — JsonElement 로 받아 dict 변환.
        var element = await JsonSerializer.DeserializeAsync<JsonElement>(stream, JsonOptions, cancellationToken);
        var data = ConvertJsonElementToDict(element);
        return new DocUtilSearchScopeValidIdResponse(data);
    }

    // ── Evaluation (7) ────────────────────────────────────────────────────

    public async Task<DocUtilEvaluationConfig> GetEvaluationConfigAsync(
        CancellationToken cancellationToken = default)
    {
        const string path = "/api/v1/evaluation/config";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<EvaluationConfigResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 평가 설정 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapEvaluationConfig(dto);
    }

    public async Task<DocUtilEvaluationConfig> UpdateEvaluationConfigAsync(
        DocUtilUpdateEvaluationConfigRequest request,
        CancellationToken cancellationToken = default)
    {
        if (request is null)
        {
            throw new InvalidOperationException("평가 설정 요청 본문이 비어 있습니다.");
        }

        const string path = "/api/v1/evaluation/config";
        var body = new EvaluationConfigUpdateRequestDto
        {
            ContextRelevancyWeight = request.ContextRelevancyWeight,
            AnswerFaithfulnessWeight = request.AnswerFaithfulnessWeight,
            AnswerRelevancyWeight = request.AnswerRelevancyWeight,
            HallucinationWeight = request.HallucinationWeight,
        };

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Put, path, body, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<EvaluationConfigResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 평가 설정 수정 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapEvaluationConfig(dto);
    }

    public async Task<DocUtilEvaluationLogList> ListEvaluationLogsAsync(
        int page = 1,
        int size = 20,
        string? runId = null,
        string? runType = null,
        bool? hasHallucination = null,
        double? minScore = null,
        double? maxScore = null,
        CancellationToken cancellationToken = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 100) size = 20;

        var queryParts = new List<string>
        {
            $"page={page}",
            $"size={size}",
        };
        if (!string.IsNullOrWhiteSpace(runId))
        {
            queryParts.Add($"run_id={Uri.EscapeDataString(runId)}");
        }
        if (!string.IsNullOrWhiteSpace(runType))
        {
            queryParts.Add($"run_type={Uri.EscapeDataString(runType)}");
        }
        if (hasHallucination.HasValue)
        {
            queryParts.Add($"has_hallucination={(hasHallucination.Value ? "true" : "false")}");
        }
        if (minScore.HasValue)
        {
            queryParts.Add($"min_score={minScore.Value.ToString(System.Globalization.CultureInfo.InvariantCulture)}");
        }
        if (maxScore.HasValue)
        {
            queryParts.Add($"max_score={maxScore.Value.ToString(System.Globalization.CultureInfo.InvariantCulture)}");
        }
        var path = $"/api/v1/evaluation/logs?{string.Join("&", queryParts)}";

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<EvaluationLogListResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 평가 로그 응답을 디시리얼라이즈하지 못했습니다.");
        }

        var items = (dto.Items ?? Array.Empty<EvaluationLogResponseDto>())
            .Select(MapEvaluationLog)
            .ToArray();
        return new DocUtilEvaluationLogList(items, dto.Total, dto.Page, dto.Size);
    }

    public async Task<DocUtilEvaluationQuestions> GetEvaluationQuestionsAsync(
        CancellationToken cancellationToken = default)
    {
        const string path = "/api/v1/evaluation/questions";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var element = await JsonSerializer.DeserializeAsync<JsonElement>(stream, JsonOptions, cancellationToken);
        var data = ConvertJsonElementToDict(element);
        return new DocUtilEvaluationQuestions(data);
    }

    public async Task<DocUtilEvaluationRunResponse> RunEvaluationAsync(
        DocUtilRunEvaluationRequest request,
        CancellationToken cancellationToken = default)
    {
        if (request is null)
        {
            throw new InvalidOperationException("평가 실행 요청 본문이 비어 있습니다.");
        }

        const string path = "/api/v1/evaluation/run";
        // body 가 빈 questions 면 null 로 직렬화 → DocUtil 측 default 질문 셋 사용.
        var body = new EvaluationRunRequestDto
        {
            Questions = (request.Questions != null && request.Questions.Length > 0) ? request.Questions : null,
        };

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var element = await JsonSerializer.DeserializeAsync<JsonElement>(stream, JsonOptions, cancellationToken);
        var data = ConvertJsonElementToDict(element);
        _logger.LogInformation("DocUtil 평가 실행 트리거 - Status={Status}, BodyKeys=[{Keys}]",
            (int)response.StatusCode, string.Join(",", data.Keys));
        return new DocUtilEvaluationRunResponse(data);
    }

    public async Task<DocUtilEvaluationRunList> ListEvaluationRunsAsync(
        int limit = 30,
        CancellationToken cancellationToken = default)
    {
        if (limit < 1 || limit > 100) limit = 30;

        var path = $"/api/v1/evaluation/runs?limit={limit}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<EvaluationRunListResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 평가 실행 목록 응답을 디시리얼라이즈하지 못했습니다.");
        }

        var items = (dto.Items ?? Array.Empty<EvaluationRunSummaryDto>())
            .Select(MapEvaluationRunSummary)
            .ToArray();
        return new DocUtilEvaluationRunList(items, dto.Total);
    }

    public async Task<DocUtilEvaluationTrend> GetEvaluationTrendAsync(
        int days = 30,
        CancellationToken cancellationToken = default)
    {
        if (days < 1 || days > 365) days = 30;

        var path = $"/api/v1/evaluation/trend?days={days}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<EvaluationTrendResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 평가 추이 응답을 디시리얼라이즈하지 못했습니다.");
        }

        var data = (dto.Data ?? Array.Empty<EvaluationTrendPointDto>())
            .Select(p => new DocUtilEvaluationTrendDataPoint(
                p.Date ?? string.Empty,
                p.AvgContextRelevancy,
                p.AvgAnswerFaithfulness,
                p.AvgAnswerRelevancy,
                p.AvgHallucinationScore,
                p.AvgCompositeScore))
            .ToArray();
        return new DocUtilEvaluationTrend(data);
    }

    // ── Phase 10.2b 매핑 헬퍼 ──────────────────────────────────────────────

    private static DocUtilSearchScopeSummary MapSearchScopeSummary(SearchScopeResponseDto dto) => new(
        dto.Id ?? string.Empty,
        dto.Name ?? string.Empty,
        dto.Description,
        dto.OrganizationId ?? string.Empty,
        dto.CreatedBy ?? string.Empty,
        dto.ProjectId,
        dto.BoardId,
        dto.FolderId,
        dto.LocationPath,
        dto.ChatbotEnabled,
        dto.ChatbotFaqTemplate,
        dto.QaEnabled,
        dto.QaPromptTemplate,
        dto.QaLlmModel,
        dto.KeywordSearchEnabled,
        dto.AgentEnabled,
        dto.ChunkSize,
        dto.ChunkOverlap,
        dto.TitleWeight,
        dto.KeywordWeight,
        dto.ContentWeight,
        dto.MaxResults,
        dto.SimilarityThreshold,
        dto.CreatedAt,
        dto.UpdatedAt);

    private static DocUtilSearchScopeDetail MapSearchScopeDetail(SearchScopeResponseDto dto) => new(
        dto.Id ?? string.Empty,
        dto.Name ?? string.Empty,
        dto.Description,
        dto.OrganizationId ?? string.Empty,
        dto.CreatedBy ?? string.Empty,
        dto.ProjectId,
        dto.BoardId,
        dto.FolderId,
        dto.LocationPath,
        dto.ChatbotEnabled,
        dto.ChatbotFaqTemplate,
        dto.QaEnabled,
        dto.QaPromptTemplate,
        dto.QaLlmModel,
        dto.KeywordSearchEnabled,
        dto.AgentEnabled,
        dto.ChunkSize,
        dto.ChunkOverlap,
        dto.TitleWeight,
        dto.KeywordWeight,
        dto.ContentWeight,
        dto.MaxResults,
        dto.SimilarityThreshold,
        dto.CreatedAt,
        dto.UpdatedAt);

    private static DocUtilEvaluationConfig MapEvaluationConfig(EvaluationConfigResponseDto dto) => new(
        dto.Id ?? string.Empty,
        dto.OrganizationId ?? string.Empty,
        dto.ContextRelevancyWeight,
        dto.AnswerFaithfulnessWeight,
        dto.AnswerRelevancyWeight,
        dto.HallucinationWeight);

    private static DocUtilEvaluationLogEntry MapEvaluationLog(EvaluationLogResponseDto dto)
    {
        IDictionary<string, object?>? contexts = null;
        if (dto.Contexts is JsonElement ce && ce.ValueKind == JsonValueKind.Object)
        {
            contexts = ConvertJsonElementToDict(ce);
        }
        IDictionary<string, object?>? evidence = null;
        if (dto.HallucinationEvidence is JsonElement he && he.ValueKind == JsonValueKind.Object)
        {
            evidence = ConvertJsonElementToDict(he);
        }
        IDictionary<string, object?>? judge = null;
        if (dto.JudgeDetails is JsonElement je && je.ValueKind == JsonValueKind.Object)
        {
            judge = ConvertJsonElementToDict(je);
        }

        return new DocUtilEvaluationLogEntry(
            dto.Id ?? string.Empty,
            dto.OrganizationId ?? string.Empty,
            dto.RunId ?? string.Empty,
            dto.Question ?? string.Empty,
            dto.Answer ?? string.Empty,
            contexts,
            dto.ContextRelevancy,
            dto.AnswerFaithfulness,
            dto.AnswerRelevancy,
            dto.HallucinationScore,
            dto.HasHallucination,
            evidence,
            dto.CompositeScore,
            judge,
            dto.RunType ?? string.Empty,
            dto.QuestionIndex,
            dto.CreatedAt);
    }

    private static DocUtilEvaluationRunSummary MapEvaluationRunSummary(EvaluationRunSummaryDto dto) => new(
        dto.RunId ?? string.Empty,
        dto.RunType ?? string.Empty,
        dto.CreatedAt,
        dto.QuestionCount,
        dto.AvgContextRelevancy,
        dto.AvgAnswerFaithfulness,
        dto.AvgAnswerRelevancy,
        dto.AvgHallucinationScore,
        dto.AvgCompositeScore,
        dto.HallucinationCount);

    /// <summary>
    /// JsonElement 를 IDictionary&lt;string, object?&gt; 로 변환(free-form 응답용).
    /// 객체가 아닌 값(null/array/scalar) 이면 단일 키 "_value" 로 wrap 하여 빈 dict 회피.
    /// </summary>
    private static IDictionary<string, object?> ConvertJsonElementToDict(JsonElement element)
    {
        var dict = new Dictionary<string, object?>(StringComparer.Ordinal);
        if (element.ValueKind == JsonValueKind.Object)
        {
            foreach (var prop in element.EnumerateObject())
            {
                dict[prop.Name] = JsonElementToObject(prop.Value);
            }
        }
        else if (element.ValueKind != JsonValueKind.Undefined && element.ValueKind != JsonValueKind.Null)
        {
            dict["_value"] = JsonElementToObject(element);
        }
        return dict;
    }

    // ── Phase 10.2a 매핑 헬퍼 ──────────────────────────────────────────────
    private static DocUtilAuditLogEntry MapAuditLog(AuditLogResponseDto dto)
    {
        // details 는 free-form dict (additionalProperties=true) 또는 null.
        IDictionary<string, object?>? details = null;
        if (dto.Details is JsonElement el && el.ValueKind == JsonValueKind.Object)
        {
            details = new Dictionary<string, object?>(StringComparer.Ordinal);
            foreach (var prop in el.EnumerateObject())
            {
                details[prop.Name] = JsonElementToObject(prop.Value);
            }
        }

        return new DocUtilAuditLogEntry(
            dto.Id ?? string.Empty,
            dto.OrganizationId ?? string.Empty,
            dto.UserId,
            dto.Action ?? string.Empty,
            dto.ResourceType ?? string.Empty,
            dto.ResourceId,
            details,
            dto.IpAddress,
            dto.CreatedAt);
    }

    private static object? JsonElementToObject(JsonElement el)
    {
        return el.ValueKind switch
        {
            JsonValueKind.String => el.GetString(),
            JsonValueKind.Number => el.TryGetInt64(out var l) ? l : el.GetDouble(),
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            JsonValueKind.Null => null,
            _ => el.GetRawText(),  // object/array 는 raw JSON 보존
        };
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
    // Phase 10.2c (2026-05-11) — DocUtil FAQ + Reports + Templates BFF 14 메서드
    //
    // org_id 자동 부착:
    //   DocUtil 의 faq / reports / templates 는 token 의 org claim 으로 자동 scope.
    //   본 클라이언트는 path 에 orgId 명시 X (추정 금지 — OpenAPI 검증 결과 일치).
    //
    // 한국어 502 매핑:
    //   EnsureSuccessOrThrowKoreanAsync 가 4xx/5xx 를 InvalidOperationException 으로
    //   변환 → Controller 가 502 ErrorResponseDto 한국어 본문으로 응답.
    //
    // POST /reports/generate, POST/PUT/DELETE /reports/templates 의 OpenAPI 응답 코드가
    // "410" 으로 표기되어 있음 — DocUtil 측이 deprecate 표식했을 가능성.
    // 라이브 호출에서 200/201/202 가 돌아오면 정상 처리, 4xx/5xx 면 502 한국어 매핑.
    // ══════════════════════════════════════════════════════════════════════

    // ── FAQ (5) ────────────────────────────────────────────────────────────

    public async Task<DocUtilFaqList> ListFaqsAsync(
        int page = 1,
        int size = 20,
        string? scopeId = null,
        string? category = null,
        string? q = null,
        CancellationToken cancellationToken = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 100) size = 20;

        var qb = new List<string> { $"page={page}", $"size={size}" };
        if (!string.IsNullOrWhiteSpace(scopeId)) qb.Add($"scope_id={Uri.EscapeDataString(scopeId)}");
        if (!string.IsNullOrWhiteSpace(category)) qb.Add($"category={Uri.EscapeDataString(category)}");
        if (!string.IsNullOrWhiteSpace(q)) qb.Add($"q={Uri.EscapeDataString(q)}");
        var path = $"/api/v1/faq?{string.Join("&", qb)}";

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<FaqListResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil FAQ 목록 응답을 디시리얼라이즈하지 못했습니다.");
        }
        var items = (dto.Items ?? Array.Empty<FaqResponseDto>()).Select(MapFaq).ToArray();
        return new DocUtilFaqList(items, dto.Total, dto.Page, dto.Size);
    }

    public async Task<DocUtilFaqDetail?> GetFaqAsync(
        string faqId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(faqId))
        {
            throw new ArgumentException("faqId 가 비어 있습니다.", nameof(faqId));
        }

        var path = $"/api/v1/faq/{Uri.EscapeDataString(faqId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return null;
        }
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<FaqResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil FAQ 상세 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapFaqDetail(dto);
    }

    public async Task<DocUtilFaqDetail> CreateFaqAsync(
        DocUtilCreateFaqRequest request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);
        if (string.IsNullOrWhiteSpace(request.Question))
        {
            throw new ArgumentException("question 이 비어 있습니다.", nameof(request));
        }
        if (string.IsNullOrWhiteSpace(request.Answer))
        {
            throw new ArgumentException("answer 가 비어 있습니다.", nameof(request));
        }

        var body = new FaqCreateRequestDto
        {
            Question = request.Question,
            Answer = request.Answer,
            Category = request.Category,
            DisplayOrder = request.DisplayOrder ?? 0,
            SearchScopeId = request.SearchScopeId,
        };

        const string path = "/api/v1/faq";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<FaqResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil FAQ 생성 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapFaqDetail(dto);
    }

    public async Task<DocUtilFaqDetail> UpdateFaqAsync(
        string faqId,
        DocUtilUpdateFaqRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(faqId))
        {
            throw new ArgumentException("faqId 가 비어 있습니다.", nameof(faqId));
        }
        ArgumentNullException.ThrowIfNull(request);

        var body = new FaqUpdateRequestDto
        {
            Question = request.Question,
            Answer = request.Answer,
            Category = request.Category,
            DisplayOrder = request.DisplayOrder,
            IsActive = request.IsActive,
        };

        var path = $"/api/v1/faq/{Uri.EscapeDataString(faqId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Put, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<FaqResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil FAQ 수정 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapFaqDetail(dto);
    }

    public async Task DeleteFaqAsync(
        string faqId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(faqId))
        {
            throw new ArgumentException("faqId 가 비어 있습니다.", nameof(faqId));
        }

        var path = $"/api/v1/faq/{Uri.EscapeDataString(faqId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Delete, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
    }

    // ── Reports (5) ────────────────────────────────────────────────────────

    public async Task<DocUtilReportList> ListReportsAsync(
        int page = 1,
        int size = 20,
        CancellationToken cancellationToken = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 100) size = 20;

        var path = $"/api/v1/reports?page={page}&size={size}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<ReportListResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 보고서 목록 응답을 디시리얼라이즈하지 못했습니다.");
        }
        var items = (dto.Items ?? Array.Empty<ReportResponseDto>()).Select(MapReport).ToArray();
        return new DocUtilReportList(items, dto.Total, dto.Page, dto.Size);
    }

    public async Task<DocUtilReportDetail?> GetReportAsync(
        string reportId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(reportId))
        {
            throw new ArgumentException("reportId 가 비어 있습니다.", nameof(reportId));
        }

        var path = $"/api/v1/reports/{Uri.EscapeDataString(reportId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return null;
        }
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<ReportResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 보고서 상세 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapReportDetail(dto);
    }

    public async Task<DocUtilReportGenerationResponse> GenerateReportAsync(
        DocUtilGenerateReportRequest request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);
        if (string.IsNullOrWhiteSpace(request.Title))
        {
            throw new ArgumentException("title 이 비어 있습니다.", nameof(request));
        }

        var body = new ReportGenerateRequestDto
        {
            Title = request.Title,
            TemplateId = request.TemplateId,
            OutputFormat = string.IsNullOrWhiteSpace(request.OutputFormat) ? "docx" : request.OutputFormat,
            SourceDocumentIds = request.SourceDocumentIds,
            SourceChatSessionId = request.SourceChatSessionId,
            GenerationParams = request.GenerationParams,
        };

        const string path = "/api/v1/reports/generate";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        // 응답 schema 미정의 — JsonElement 로 받아서 free-form dict 로 변환.
        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var element = await JsonSerializer.DeserializeAsync<JsonElement>(stream, JsonOptions, cancellationToken);
        var dict = ConvertJsonElementToDict(element);
        return new DocUtilReportGenerationResponse(dict);
    }

    public async Task DeleteReportAsync(
        string reportId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(reportId))
        {
            throw new ArgumentException("reportId 가 비어 있습니다.", nameof(reportId));
        }

        var path = $"/api/v1/reports/{Uri.EscapeDataString(reportId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Delete, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
    }

    public async Task<DocUtilReportDownload> DownloadReportAsync(
        string reportId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(reportId))
        {
            throw new ArgumentException("reportId 가 비어 있습니다.", nameof(reportId));
        }

        var path = $"/api/v1/reports/{Uri.EscapeDataString(reportId)}/download";
        // Long-running named client (5분 timeout) — Report 파일(zip/xlsx/csv) 다운로드는 대용량 가능.
        var client = _httpClientFactory.CreateClient(LongRunningHttpClientName);
        var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        // 본 메서드는 stream 반환 — using 으로 감싸지 않음(호출자 소유, HttpResponseOwnedStream 으로 lifetime 결합).

        _logger.LogInformation("DocUtil 보고서 다운로드 호출 - ReportId={ReportId}", reportId);

        var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseHeadersRead, cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            try
            {
                await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
            }
            finally
            {
                response.Dispose();
                httpRequest.Dispose();
            }
        }

        var contentType = response.Content.Headers.ContentType?.ToString()
            ?? "application/octet-stream";

        var disposition = response.Content.Headers.ContentDisposition;
        var fileName = disposition?.FileNameStar
            ?? disposition?.FileName?.Trim('"')
            ?? $"report-{reportId}";

        var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var owned = new HttpResponseOwnedStream(stream, response, httpRequest);
        return new DocUtilReportDownload(owned, contentType, fileName);
    }

    // ── Report Templates (5) ───────────────────────────────────────────────

    public async Task<DocUtilReportTemplateList> ListReportTemplatesAsync(
        int page = 1,
        int size = 20,
        CancellationToken cancellationToken = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 100) size = 20;

        var path = $"/api/v1/reports/templates?page={page}&size={size}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<ReportTemplateListResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 보고서 템플릿 목록 응답을 디시리얼라이즈하지 못했습니다.");
        }
        var items = (dto.Items ?? Array.Empty<ReportTemplateResponseDto>()).Select(MapReportTemplate).ToArray();
        return new DocUtilReportTemplateList(items, dto.Total, dto.Page, dto.Size);
    }

    public async Task<DocUtilReportTemplateDetail?> GetReportTemplateAsync(
        string templateId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            throw new ArgumentException("templateId 가 비어 있습니다.", nameof(templateId));
        }

        var path = $"/api/v1/reports/templates/{Uri.EscapeDataString(templateId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return null;
        }
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<ReportTemplateResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 보고서 템플릿 상세 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapReportTemplateDetail(dto);
    }

    public async Task<DocUtilReportTemplateDetail> CreateReportTemplateAsync(
        DocUtilCreateReportTemplateRequest request,
        Stream? fileStream,
        string? fileName,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            throw new ArgumentException("name 이 비어 있습니다.", nameof(request));
        }

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var multipart = new MultipartFormDataContent();
        multipart.Add(new StringContent(request.Name, Encoding.UTF8), "name");
        multipart.Add(new StringContent(request.Format ?? string.Empty, Encoding.UTF8), "format");
        if (!string.IsNullOrEmpty(request.Description))
        {
            multipart.Add(new StringContent(request.Description, Encoding.UTF8), "description");
        }
        if (fileStream != null && !string.IsNullOrWhiteSpace(fileName))
        {
            var streamContent = new StreamContent(fileStream);
            streamContent.Headers.ContentType = new MediaTypeHeaderValue("application/octet-stream");
            multipart.Add(streamContent, "file", fileName);
        }

        const string path = "/api/v1/reports/templates";
        using var httpRequest = new HttpRequestMessage(HttpMethod.Post, path)
        {
            Content = multipart,
        };
        var token = await _tokenProvider.GetTokenAsync(cancellationToken);
        if (!string.IsNullOrWhiteSpace(token))
        {
            httpRequest.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        }
        else
        {
            _logger.LogWarning("DocUtil 토큰 미설정 — 템플릿 생성 multipart 호출이 401 로 실패할 수 있음.");
        }

        _logger.LogDebug(
            "DocUtil 보고서 템플릿 생성 호출 - Name={Name}, Format={Format}, HasFile={HasFile}",
            request.Name, request.Format, fileStream != null);

        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<ReportTemplateResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 보고서 템플릿 생성 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapReportTemplateDetail(dto);
    }

    public async Task<DocUtilReportTemplateDetail> UpdateReportTemplateAsync(
        string templateId,
        DocUtilUpdateReportTemplateRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            throw new ArgumentException("templateId 가 비어 있습니다.", nameof(templateId));
        }
        ArgumentNullException.ThrowIfNull(request);

        var body = new ReportTemplateUpdateRequestDto
        {
            Name = request.Name,
            Description = request.Description,
        };

        var path = $"/api/v1/reports/templates/{Uri.EscapeDataString(templateId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Put, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<ReportTemplateResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 보고서 템플릿 수정 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapReportTemplateDetail(dto);
    }

    public async Task DeleteReportTemplateAsync(
        string templateId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            throw new ArgumentException("templateId 가 비어 있습니다.", nameof(templateId));
        }

        var path = $"/api/v1/reports/templates/{Uri.EscapeDataString(templateId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Delete, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
    }

    // ══════════════════════════════════════════════════════════════════════
    // Phase 10.2d (2026-05-11): Document Templates (15 endpoints)
    //
    // 모든 endpoint 는 DocUtil 의 `/api/v1/templates/*` (router prefix=""에서 main.py 가
    // f"{API_V1}" 로 마운트). org_id 는 DocUtil 라우터의 `_check_org` 가 토큰의
    // organization_id 를 자동 검증하므로 본 클라이언트는 별도 헤더 부착 안 함.
    // multipart 업로드(3종) 는 BuildJsonRequestAsync 대신 직접 HttpRequestMessage + MultipartFormDataContent
    // 구성 — Authorization 헤더는 동일 패턴(IDocUtilTokenProvider).
    // ══════════════════════════════════════════════════════════════════════

    public async Task<DocUtilDocumentTemplateList> ListDocumentTemplatesAsync(
        string? templateType = null,
        int page = 1,
        int size = 20,
        CancellationToken cancellationToken = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 100) size = 20;

        // DocUtil query 는 template_type / page / size. snake_case 그대로 전달.
        var qs = new List<string> { $"page={page}", $"size={size}" };
        if (!string.IsNullOrWhiteSpace(templateType))
        {
            qs.Add($"template_type={Uri.EscapeDataString(templateType)}");
        }
        var path = $"/api/v1/templates?{string.Join("&", qs)}";

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentTemplateListResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 문서 템플릿 목록 응답을 디시리얼라이즈하지 못했습니다.");
        }
        var items = (dto.Items ?? Array.Empty<DocumentTemplateResponseDto>())
            .Select(MapDocumentTemplate).ToArray();
        return new DocUtilDocumentTemplateList(items, dto.Total, dto.Page, dto.Size);
    }

    public async Task<DocUtilDocumentTemplateDetail?> GetDocumentTemplateAsync(
        string templateId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            throw new ArgumentException("templateId 가 비어 있습니다.", nameof(templateId));
        }

        var path = $"/api/v1/templates/{Uri.EscapeDataString(templateId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return null;
        }
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentTemplateResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 문서 템플릿 상세 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapDocumentTemplateDetail(dto);
    }

    public async Task<DocUtilDocumentTemplateDetail> CreateDocumentTemplateAsync(
        DocUtilCreateDocumentTemplateRequest request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            throw new ArgumentException("name 이 비어 있습니다.", nameof(request));
        }

        // DocUtil TemplateCreate — schema 필드는 Pydantic alias 'schema'(예약어 회피용 schema_) →
        // JSON 키는 "schema". JsonNamingPolicy.SnakeCaseLower 는 PascalCase 'Schema' → 'schema' 매핑.
        var body = new DocumentTemplateCreateRequestDto
        {
            Name = request.Name,
            Description = request.Description,
            TemplateType = request.TemplateType,
            Tone = request.Tone,
            OutputFormat = request.OutputFormat,
            Schema = request.Schema,
            SamplePrompt = request.SamplePrompt,
            RenderingMode = request.RenderingMode,
            ImageGenerationConfig = request.ImageGenerationConfig,
        };

        const string path = "/api/v1/templates";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentTemplateResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 문서 템플릿 생성 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapDocumentTemplateDetail(dto);
    }

    public async Task<DocUtilDocumentTemplateDetail> UpdateDocumentTemplateAsync(
        string templateId,
        DocUtilUpdateDocumentTemplateRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            throw new ArgumentException("templateId 가 비어 있습니다.", nameof(templateId));
        }
        ArgumentNullException.ThrowIfNull(request);

        var body = new DocumentTemplateUpdateRequestDto
        {
            Name = request.Name,
            Description = request.Description,
            TemplateType = request.TemplateType,
            Tone = request.Tone,
            OutputFormat = request.OutputFormat,
            Schema = request.Schema,
            SamplePrompt = request.SamplePrompt,
            IsActive = request.IsActive,
            RenderingMode = request.RenderingMode,
            ImageGenerationConfig = request.ImageGenerationConfig,
        };

        var path = $"/api/v1/templates/{Uri.EscapeDataString(templateId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Put, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentTemplateResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 문서 템플릿 수정 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapDocumentTemplateDetail(dto);
    }

    public async Task DeleteDocumentTemplateAsync(
        string templateId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            throw new ArgumentException("templateId 가 비어 있습니다.", nameof(templateId));
        }

        var path = $"/api/v1/templates/{Uri.EscapeDataString(templateId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Delete, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
    }

    public Task<DocUtilDocumentTemplateUpload> UploadDocumentTemplateAsync(
        DocUtilUploadDocumentTemplateRequest request,
        Stream fileStream,
        string fileName,
        CancellationToken cancellationToken = default)
        => UploadDocumentTemplateInternalAsync(
            "/api/v1/templates/upload",
            request,
            smartRequest: null,
            fileStream,
            fileName,
            cancellationToken);

    public Task<DocUtilDocumentTemplateUpload> UploadBlankFormAsync(
        DocUtilUploadDocumentTemplateRequest request,
        Stream fileStream,
        string fileName,
        CancellationToken cancellationToken = default)
        => UploadDocumentTemplateInternalAsync(
            "/api/v1/templates/upload-blank",
            request,
            smartRequest: null,
            fileStream,
            fileName,
            cancellationToken);

    public Task<DocUtilDocumentTemplateUpload> UploadSmartTemplateAsync(
        DocUtilUploadSmartTemplateRequest request,
        Stream fileStream,
        string fileName,
        CancellationToken cancellationToken = default)
        => UploadDocumentTemplateInternalAsync(
            "/api/v1/templates/upload-smart",
            standardRequest: null,
            smartRequest: request,
            fileStream,
            fileName,
            cancellationToken);

    /// <summary>
    /// 3종 업로드 endpoint 의 공통 multipart 구성 + 응답 매핑.
    /// 일반/빈양식: template_type/output_format 필수. 스마트: 모두 nullable.
    /// </summary>
    private async Task<DocUtilDocumentTemplateUpload> UploadDocumentTemplateInternalAsync(
        string path,
        DocUtilUploadDocumentTemplateRequest? standardRequest,
        DocUtilUploadSmartTemplateRequest? smartRequest,
        Stream fileStream,
        string fileName,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(fileStream);
        if (string.IsNullOrWhiteSpace(fileName))
        {
            throw new ArgumentException("fileName 이 비어 있습니다.", nameof(fileName));
        }

        var client = _httpClientFactory.CreateClient(HttpClientName);

        using var multipart = new MultipartFormDataContent();
        if (standardRequest != null)
        {
            // 일반/빈양식 — template_type/output_format 필수, tone(기본 formal), name/description 선택.
            multipart.Add(new StringContent(standardRequest.TemplateType, Encoding.UTF8), "template_type");
            multipart.Add(new StringContent(standardRequest.OutputFormat, Encoding.UTF8), "output_format");
            multipart.Add(new StringContent(standardRequest.Tone ?? "formal", Encoding.UTF8), "tone");
            if (!string.IsNullOrEmpty(standardRequest.Name))
            {
                multipart.Add(new StringContent(standardRequest.Name, Encoding.UTF8), "name");
            }
            if (!string.IsNullOrEmpty(standardRequest.Description))
            {
                multipart.Add(new StringContent(standardRequest.Description, Encoding.UTF8), "description");
            }
        }
        else if (smartRequest != null)
        {
            // 스마트 — 모두 nullable. tone 만 기본값 적용.
            multipart.Add(new StringContent(smartRequest.Tone ?? "formal", Encoding.UTF8), "tone");
            if (!string.IsNullOrEmpty(smartRequest.Name))
            {
                multipart.Add(new StringContent(smartRequest.Name, Encoding.UTF8), "name");
            }
            if (!string.IsNullOrEmpty(smartRequest.Description))
            {
                multipart.Add(new StringContent(smartRequest.Description, Encoding.UTF8), "description");
            }
            if (!string.IsNullOrEmpty(smartRequest.TemplateType))
            {
                multipart.Add(new StringContent(smartRequest.TemplateType, Encoding.UTF8), "template_type");
            }
        }
        else
        {
            throw new InvalidOperationException("UploadDocumentTemplateInternal: standardRequest 또는 smartRequest 중 하나 필요.");
        }

        var streamContent = new StreamContent(fileStream);
        streamContent.Headers.ContentType = new MediaTypeHeaderValue("application/octet-stream");
        multipart.Add(streamContent, "file", fileName);

        using var httpRequest = new HttpRequestMessage(HttpMethod.Post, path)
        {
            Content = multipart,
        };
        var token = await _tokenProvider.GetTokenAsync(cancellationToken);
        if (!string.IsNullOrWhiteSpace(token))
        {
            httpRequest.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        }
        else
        {
            _logger.LogWarning("DocUtil 토큰 미설정 — 문서 템플릿 업로드 호출이 401 로 실패할 수 있음.");
        }

        _logger.LogDebug(
            "DocUtil 문서 템플릿 업로드 호출 - Path={Path}, FileName={FileName}",
            path, fileName);

        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentTemplateUploadResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 문서 템플릿 업로드 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapDocumentTemplateUpload(dto);
    }

    public async Task<DocUtilDocumentTemplateDetail> ConvertDocumentTemplateAsync(
        string templateId,
        IDictionary<string, object?> aiAnalysis,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            throw new ArgumentException("templateId 가 비어 있습니다.", nameof(templateId));
        }
        ArgumentNullException.ThrowIfNull(aiAnalysis);

        // DocUtil 라우터는 body=dict 형식: { "ai_analysis": {...} } 만 추출하여 사용.
        var body = new Dictionary<string, object?> { ["ai_analysis"] = aiAnalysis };

        var path = $"/api/v1/templates/{Uri.EscapeDataString(templateId)}/convert";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentTemplateResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 문서 템플릿 변환 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapDocumentTemplateDetail(dto);
    }

    public async Task<DocUtilDocumentTemplateAutoFill> AutoFillDocumentTemplateAsync(
        string templateId,
        DocUtilAutoFillDocumentTemplateRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            throw new ArgumentException("templateId 가 비어 있습니다.", nameof(templateId));
        }
        ArgumentNullException.ThrowIfNull(request);
        if (request.SourceDocumentIds == null || request.SourceDocumentIds.Length == 0)
        {
            throw new ArgumentException("source_document_ids 가 비어 있습니다.", nameof(request));
        }

        // DocUtil 라우터의 Body 파라미터 — source_document_ids(필수) + ai_prompt(선택).
        var body = new Dictionary<string, object?>
        {
            ["source_document_ids"] = request.SourceDocumentIds,
        };
        if (!string.IsNullOrEmpty(request.AiPrompt))
        {
            body["ai_prompt"] = request.AiPrompt;
        }

        var path = $"/api/v1/templates/{Uri.EscapeDataString(templateId)}/auto-fill";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentTemplateAutoFillResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 자동채움 응답을 디시리얼라이즈하지 못했습니다.");
        }

        IDictionary<string, object?> context;
        if (dto.Context is JsonElement ctxEl && ctxEl.ValueKind == JsonValueKind.Object)
        {
            context = ConvertJsonElementToDict(ctxEl);
        }
        else
        {
            context = new Dictionary<string, object?>(StringComparer.Ordinal);
        }
        return new DocUtilDocumentTemplateAutoFill(context);
    }

    public async Task<List<DocUtilDocumentTemplateVariable>> GetDocumentTemplateVariablesAsync(
        string templateId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            throw new ArgumentException("templateId 가 비어 있습니다.", nameof(templateId));
        }

        var path = $"/api/v1/templates/{Uri.EscapeDataString(templateId)}/variables";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dtos = await JsonSerializer.DeserializeAsync<List<DocumentTemplateVariableDto>>(stream, JsonOptions, cancellationToken);
        if (dtos is null)
        {
            return new List<DocUtilDocumentTemplateVariable>();
        }
        return dtos.Select(MapDocumentTemplateVariable).ToList();
    }

    public async Task<DocUtilDocumentTemplateDetail> UpdateDocumentTemplateVariablesAsync(
        string templateId,
        DocUtilUpdateDocumentTemplateVariablesRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            throw new ArgumentException("templateId 가 비어 있습니다.", nameof(templateId));
        }
        ArgumentNullException.ThrowIfNull(request);
        if (request.Variables == null)
        {
            throw new ArgumentException("variables 배열이 null 입니다.", nameof(request));
        }

        var body = new DocumentTemplateVariablesUpdateRequestDto
        {
            Variables = request.Variables.Select(v => new DocumentTemplateVariableDto
            {
                Name = v.Name,
                VarType = v.VarType,
                Label = v.Label,
                Description = v.Description,
                Required = v.Required,
                Category = v.Category,
            }).ToArray(),
        };

        var path = $"/api/v1/templates/{Uri.EscapeDataString(templateId)}/variables";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Put, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentTemplateResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 문서 템플릿 변수 수정 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapDocumentTemplateDetail(dto);
    }

    public async Task<DocUtilDocumentTemplatePreview> PreviewDocumentTemplateAsync(
        string templateId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            throw new ArgumentException("templateId 가 비어 있습니다.", nameof(templateId));
        }

        var path = $"/api/v1/templates/{Uri.EscapeDataString(templateId)}/preview";
        // Long-running named client (5분 timeout) — Jinja2 템플릿 렌더(이미지 합성 포함) 가 60s 초과 가능.
        var client = _httpClientFactory.CreateClient(LongRunningHttpClientName);
        var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        // stream 반환 — using 사용 안 함(호출자 소유, HttpResponseOwnedStream 으로 lifetime 결합).

        _logger.LogInformation("DocUtil 문서 템플릿 미리보기 호출 - TemplateId={TemplateId}", templateId);

        var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseHeadersRead, cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            try
            {
                await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
            }
            finally
            {
                response.Dispose();
                httpRequest.Dispose();
            }
        }

        var contentType = response.Content.Headers.ContentType?.ToString()
            ?? "application/octet-stream";

        var disposition = response.Content.Headers.ContentDisposition;
        var fileName = disposition?.FileNameStar
            ?? disposition?.FileName?.Trim('"')
            ?? $"template-{templateId}";

        var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var owned = new HttpResponseOwnedStream(stream, response, httpRequest);
        return new DocUtilDocumentTemplatePreview(owned, contentType, fileName);
    }

    public async Task<IDictionary<string, object?>> GetDocumentTemplateStructureAsync(
        string templateId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            throw new ArgumentException("templateId 가 비어 있습니다.", nameof(templateId));
        }

        var path = $"/api/v1/templates/{Uri.EscapeDataString(templateId)}/structure";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        // 응답은 free-form dict — JsonElement 로 받아 ConvertJsonElementToDict 변환.
        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var element = await JsonSerializer.DeserializeAsync<JsonElement>(stream, JsonOptions, cancellationToken);
        return ConvertJsonElementToDict(element);
    }

    public async Task<DocUtilDocumentTemplateDetail> ApplyDocumentTemplateMappingAsync(
        string templateId,
        DocUtilApplyDocumentTemplateMappingRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(templateId))
        {
            throw new ArgumentException("templateId 가 비어 있습니다.", nameof(templateId));
        }
        ArgumentNullException.ThrowIfNull(request);
        if (request.Mappings == null || request.Mappings.Length == 0)
        {
            throw new ArgumentException("mappings 가 비어 있습니다.", nameof(request));
        }

        // DocUtil VariableMappingPayload — mappings 배열.
        var body = new DocumentTemplateMappingPayloadDto
        {
            Mappings = request.Mappings.Select(m => new DocumentTemplateMappingDto
            {
                LocationType = m.LocationType,
                TableIndex = m.TableIndex,
                Row = m.Row,
                Col = m.Col,
                ParagraphIndex = m.ParagraphIndex,
                VariableName = m.VariableName,
                VarType = m.VarType,
                Label = m.Label,
                Category = m.Category,
                FieldType = m.FieldType,
            }).ToArray(),
        };

        var path = $"/api/v1/templates/{Uri.EscapeDataString(templateId)}/apply-mapping";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentTemplateResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 문서 템플릿 매핑 적용 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapDocumentTemplateDetail(dto);
    }

    // ── Phase 10.2d 매핑 헬퍼 ──────────────────────────────────────────────

    private static DocUtilDocumentTemplate MapDocumentTemplate(DocumentTemplateResponseDto dto)
    {
        return new DocUtilDocumentTemplate(
            dto.Id ?? string.Empty,
            dto.OrganizationId ?? string.Empty,
            dto.Name ?? string.Empty,
            dto.Description,
            dto.TemplateType ?? string.Empty,
            dto.Tone ?? "formal",
            dto.OutputFormat ?? string.Empty,
            ConvertJsonElementToOptionalDict(dto.Schema),
            dto.SamplePrompt,
            dto.IsActive,
            dto.CreatedBy ?? string.Empty,
            dto.CreatedAt,
            dto.UpdatedAt,
            dto.TemplateStoragePath,
            ConvertJsonElementToOptionalDict(dto.Jinja2Variables),
            dto.RenderingMode ?? "jinja2",
            ConvertJsonElementToOptionalDict(dto.ImageGenerationConfig));
    }

    private static DocUtilDocumentTemplateDetail MapDocumentTemplateDetail(DocumentTemplateResponseDto dto)
    {
        return new DocUtilDocumentTemplateDetail(
            dto.Id ?? string.Empty,
            dto.OrganizationId ?? string.Empty,
            dto.Name ?? string.Empty,
            dto.Description,
            dto.TemplateType ?? string.Empty,
            dto.Tone ?? "formal",
            dto.OutputFormat ?? string.Empty,
            ConvertJsonElementToOptionalDict(dto.Schema),
            dto.SamplePrompt,
            dto.IsActive,
            dto.CreatedBy ?? string.Empty,
            dto.CreatedAt,
            dto.UpdatedAt,
            dto.TemplateStoragePath,
            ConvertJsonElementToOptionalDict(dto.Jinja2Variables),
            dto.RenderingMode ?? "jinja2",
            ConvertJsonElementToOptionalDict(dto.ImageGenerationConfig));
    }

    private static DocUtilDocumentTemplateVariable MapDocumentTemplateVariable(DocumentTemplateVariableDto dto)
    {
        return new DocUtilDocumentTemplateVariable(
            dto.Name ?? string.Empty,
            string.IsNullOrEmpty(dto.VarType) ? "string" : dto.VarType,
            dto.Label,
            dto.Description,
            dto.Required,
            string.IsNullOrEmpty(dto.Category) ? "ai_generated" : dto.Category);
    }

    private static DocUtilDocumentTemplateUpload MapDocumentTemplateUpload(DocumentTemplateUploadResponseDto dto)
    {
        var vars = (dto.Variables ?? Array.Empty<DocumentTemplateVariableDto>())
            .Select(MapDocumentTemplateVariable).ToArray();
        return new DocUtilDocumentTemplateUpload(
            dto.Id ?? string.Empty,
            dto.Name ?? string.Empty,
            dto.OutputFormat ?? string.Empty,
            dto.RenderingMode ?? "jinja2",
            dto.TemplateStoragePath,
            vars);
    }

    /// <summary>
    /// JsonElement → IDictionary 변환 — null/Undefined 면 null 반환(record nullable 필드용).
    /// </summary>
    private static IDictionary<string, object?>? ConvertJsonElementToOptionalDict(JsonElement? element)
    {
        if (!element.HasValue) return null;
        var el = element.Value;
        if (el.ValueKind == JsonValueKind.Null || el.ValueKind == JsonValueKind.Undefined) return null;
        if (el.ValueKind != JsonValueKind.Object) return null;
        return ConvertJsonElementToDict(el);
    }

    // ── Phase 10.2c 매핑 헬퍼 ──────────────────────────────────────────────

    private static DocUtilFaq MapFaq(FaqResponseDto dto) => new(
        dto.Id ?? string.Empty,
        dto.SearchScopeId,
        dto.OrganizationId ?? string.Empty,
        dto.Question ?? string.Empty,
        dto.Answer ?? string.Empty,
        dto.Category,
        dto.DisplayOrder,
        dto.IsActive,
        dto.CreatedAt,
        dto.UpdatedAt);

    private static DocUtilFaqDetail MapFaqDetail(FaqResponseDto dto) => new(
        dto.Id ?? string.Empty,
        dto.SearchScopeId,
        dto.OrganizationId ?? string.Empty,
        dto.Question ?? string.Empty,
        dto.Answer ?? string.Empty,
        dto.Category,
        dto.DisplayOrder,
        dto.IsActive,
        dto.CreatedAt,
        dto.UpdatedAt);

    private static DocUtilReport MapReport(ReportResponseDto dto)
    {
        IDictionary<string, object?>? generationParams = null;
        if (dto.GenerationParams is JsonElement gp && gp.ValueKind == JsonValueKind.Object)
        {
            generationParams = ConvertJsonElementToDict(gp);
        }
        IDictionary<string, object?>? jinjaCtx = null;
        if (dto.Jinja2Context is JsonElement jc && jc.ValueKind == JsonValueKind.Object)
        {
            jinjaCtx = ConvertJsonElementToDict(jc);
        }

        return new DocUtilReport(
            dto.Id ?? string.Empty,
            dto.TemplateId,
            dto.OrganizationId ?? string.Empty,
            dto.Title ?? string.Empty,
            dto.Status ?? string.Empty,
            dto.OutputFormat ?? "docx",
            dto.OutputStoragePath,
            dto.SourceDocumentIds,
            dto.SourceChatSessionId,
            generationParams,
            dto.RenderingMode,
            jinjaCtx,
            dto.ErrorMessage,
            dto.GeneratedBy ?? string.Empty,
            dto.CreatedAt,
            dto.CompletedAt);
    }

    private static DocUtilReportDetail MapReportDetail(ReportResponseDto dto)
    {
        IDictionary<string, object?>? generationParams = null;
        if (dto.GenerationParams is JsonElement gp && gp.ValueKind == JsonValueKind.Object)
        {
            generationParams = ConvertJsonElementToDict(gp);
        }
        IDictionary<string, object?>? jinjaCtx = null;
        if (dto.Jinja2Context is JsonElement jc && jc.ValueKind == JsonValueKind.Object)
        {
            jinjaCtx = ConvertJsonElementToDict(jc);
        }

        return new DocUtilReportDetail(
            dto.Id ?? string.Empty,
            dto.TemplateId,
            dto.OrganizationId ?? string.Empty,
            dto.Title ?? string.Empty,
            dto.Status ?? string.Empty,
            dto.OutputFormat ?? "docx",
            dto.OutputStoragePath,
            dto.SourceDocumentIds,
            dto.SourceChatSessionId,
            generationParams,
            dto.RenderingMode,
            jinjaCtx,
            dto.ErrorMessage,
            dto.GeneratedBy ?? string.Empty,
            dto.CreatedAt,
            dto.CompletedAt);
    }

    private static DocUtilReportTemplate MapReportTemplate(ReportTemplateResponseDto dto)
    {
        IDictionary<string, object?>? schema = null;
        if (dto.Schema is JsonElement se && se.ValueKind == JsonValueKind.Object)
        {
            schema = ConvertJsonElementToDict(se);
        }

        return new DocUtilReportTemplate(
            dto.Id ?? string.Empty,
            dto.OrganizationId ?? string.Empty,
            dto.Name ?? string.Empty,
            dto.Description,
            dto.Format ?? string.Empty,
            dto.TemplateStoragePath,
            schema,
            dto.CreatedBy ?? string.Empty,
            dto.CreatedAt,
            dto.UpdatedAt);
    }

    private static DocUtilReportTemplateDetail MapReportTemplateDetail(ReportTemplateResponseDto dto)
    {
        IDictionary<string, object?>? schema = null;
        if (dto.Schema is JsonElement se && se.ValueKind == JsonValueKind.Object)
        {
            schema = ConvertJsonElementToDict(se);
        }

        return new DocUtilReportTemplateDetail(
            dto.Id ?? string.Empty,
            dto.OrganizationId ?? string.Empty,
            dto.Name ?? string.Empty,
            dto.Description,
            dto.Format ?? string.Empty,
            dto.TemplateStoragePath,
            schema,
            dto.CreatedBy ?? string.Empty,
            dto.CreatedAt,
            dto.UpdatedAt);
    }

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
    /// DocUtil 응답 상태 코드를 검사하고, 실패 시 한국어 <see cref="DocUtilUpstreamException"/> 으로 변환.
    /// AgentHub GlobalExceptionHandlerMiddleware 또는 BFF 컨트롤러가 502/410 등으로 응답 합성한다.
    /// <para>
    /// Phase 10.x (2026-05-11) 보강 — 클라이언트 응답에 DocUtil 영문 body 를 그대로
    /// 노출하지 않는다(정보 누출 위험 + UX 비일관). 원본 body 는 LogError/LogWarning 에만 기록.
    /// 단, 422 validation error 의 경우 detail[0].msg 를 한국어 안내와 함께 추출 시도.
    /// </para>
    /// <para>
    /// Phase 10.x Medium/Low 보강 (2026-05-11) — 410 Gone 분기 신설. DocUtil 측이 deprecate 한
    /// 엔드포인트(Reports 4개) 호출 시 BFF 가 일반 502 가 아닌 410 + 한국어 안내로 응답하도록
    /// status code 를 <see cref="DocUtilUpstreamException.StatusCode"/> 로 전파.
    /// 기존 catch (InvalidOperationException) 분기는 그대로 동작(상속 관계 유지).
    /// </para>
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
            throw new DocUtilUpstreamException(
                response.StatusCode,
                path,
                "DocUtil 인증 실패. JwtToken 또는 ApiKey 설정을 확인하세요.");
        }

        // 410 Gone — DocUtil 측이 deprecate 한 엔드포인트.
        // 호출자(컨트롤러) 가 catch (DocUtilUpstreamException) 으로 분기하여 410 + 한국어 안내 노출.
        if (response.StatusCode == HttpStatusCode.Gone)
        {
            _logger.LogWarning(
                "DocUtil 엔드포인트 deprecate(410 Gone) - Path={Path}, Body={Body}",
                path, body);
            throw new DocUtilUpstreamException(
                response.StatusCode,
                path,
                "이 기능은 DocUtil 측에서 deprecate 되었습니다. 신규 디자이너 워크플로(/admin/docutil-documents-v2) 를 사용하세요.");
        }

        // 5xx — DocUtil 서비스 장애.
        if (status >= 500)
        {
            _logger.LogError(
                "DocUtil 서비스 오류 - Path={Path}, Status={Status}, Body={Body}",
                path, status, body);
            throw new DocUtilUpstreamException(
                response.StatusCode,
                path,
                $"DocUtil 응답 실패. 네트워크 또는 서비스 상태를 확인하세요. (HTTP {status})");
        }

        // 422 Unprocessable Entity — FastAPI/Pydantic validation 표준 응답.
        // detail 배열의 첫 항목 메시지를 사용자 안내에 포함(나머지는 로그에만).
        // 매핑 실패 시 일반 4xx 안내로 폴백.
        if (status == 422)
        {
            var hint = TryExtractValidationHint(body);
            _logger.LogWarning(
                "DocUtil 입력 검증 실패 - Path={Path}, Status={Status}, Body={Body}",
                path, status, body);
            if (!string.IsNullOrEmpty(hint))
            {
                throw new DocUtilUpstreamException(
                    response.StatusCode,
                    path,
                    $"DocUtil 입력 검증에 실패했습니다 (HTTP 422): {hint}");
            }
            throw new DocUtilUpstreamException(
                response.StatusCode,
                path,
                "DocUtil 입력 검증에 실패했습니다 (HTTP 422). 운영자에게 문의하세요.");
        }

        // 그 외 4xx — 호출자 책임. 영문 body 는 로그에만 — 응답에는 status code 와 한국어 안내만.
        _logger.LogWarning(
            "DocUtil 호출 실패 - Path={Path}, Status={Status}, Body={Body}",
            path, status, body);
        throw new DocUtilUpstreamException(
            response.StatusCode,
            path,
            $"DocUtil 호출이 실패했습니다 (HTTP {status}). 입력값 또는 권한을 확인하세요.");
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

    /// <summary>
    /// FastAPI/Pydantic 422 응답 본문에서 사용자에게 보일 한국어 친화 hint 추출.
    /// 표준 응답 형태:
    ///   { "detail": [ { "loc": ["body","name"], "msg": "...", "type": "value_error" }, ... ] }
    /// 또는 단순:
    ///   { "detail": "..." }
    /// 추출 우선순위:
    ///   1. detail 이 string → 그대로 반환(영문일 수 있으나 422 한정 한 줄 메시지 허용)
    ///   2. detail[0] 의 loc 마지막 component + msg → "{field}: {msg}" 형태
    ///   3. 추출 실패 → null
    /// 반환값은 길이 200 자로 truncate.
    /// </summary>
    private static string? TryExtractValidationHint(string body)
    {
        if (string.IsNullOrWhiteSpace(body)) return null;
        try
        {
            using var doc = JsonDocument.Parse(body);
            if (!doc.RootElement.TryGetProperty("detail", out var detailEl)) return null;

            // 단순 문자열 case.
            if (detailEl.ValueKind == JsonValueKind.String)
            {
                var s = detailEl.GetString();
                return string.IsNullOrEmpty(s) ? null : Truncate(s, 200);
            }

            // 배열 case — 첫 항목.
            if (detailEl.ValueKind == JsonValueKind.Array && detailEl.GetArrayLength() > 0)
            {
                var first = detailEl[0];
                string? field = null;
                string? msg = null;
                if (first.TryGetProperty("loc", out var locEl) && locEl.ValueKind == JsonValueKind.Array)
                {
                    // loc 의 마지막 component 가 필드명에 가까움(예: ["body","name"] → "name").
                    var len = locEl.GetArrayLength();
                    if (len > 0)
                    {
                        var last = locEl[len - 1];
                        if (last.ValueKind == JsonValueKind.String)
                        {
                            field = last.GetString();
                        }
                    }
                }
                if (first.TryGetProperty("msg", out var msgEl) && msgEl.ValueKind == JsonValueKind.String)
                {
                    msg = msgEl.GetString();
                }
                if (!string.IsNullOrEmpty(msg))
                {
                    var combined = string.IsNullOrEmpty(field) ? msg! : $"{field}: {msg}";
                    return Truncate(combined, 200);
                }
            }
        }
        catch
        {
            // 파싱 실패 — null 반환하여 호출자가 일반 안내로 폴백.
        }
        return null;
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

    // ── Phase 10.2a (2026-05-10): DocUtil Dashboard + Audit API 응답 매핑 DTO ─
    // OpenAPI 캡처(2026-05-10):
    //   - DashboardMetrics: total_users/active_users/total_documents/total_searches + feature_usage(dict)
    //   - ResponseTimeData: timestamps[] + values[] (period 미지정 시 빈 배열)
    //   - SearchErrorData: dates[] + error_counts[]
    //   - SearchUsageStats: total_requests/total_responses/total_failures + period
    //   - UploadStatusChart: completed/processing/waiting/error
    //   - AuditLogResponse: id/organization_id/user_id?/action/resource_type/resource_id?/details(dict)?/ip_address?/created_at
    //   - AuditLogListResponse: items + total + page + size

    private sealed class DashboardMetricsDto
    {
        [JsonPropertyName("total_users")] public int TotalUsers { get; set; }
        [JsonPropertyName("active_users")] public int ActiveUsers { get; set; }
        [JsonPropertyName("total_documents")] public int TotalDocuments { get; set; }
        [JsonPropertyName("total_searches")] public int TotalSearches { get; set; }
        // free-form dict — JsonElement 로 받아 안전 enumerate.
        [JsonPropertyName("feature_usage")] public JsonElement? FeatureUsage { get; set; }
    }

    private sealed class ResponseTimeDataDto
    {
        [JsonPropertyName("timestamps")] public string[]? Timestamps { get; set; }
        [JsonPropertyName("values")] public double[]? Values { get; set; }
    }

    private sealed class SearchErrorDataDto
    {
        [JsonPropertyName("dates")] public string[]? Dates { get; set; }
        [JsonPropertyName("error_counts")] public int[]? ErrorCounts { get; set; }
    }

    private sealed class SearchUsageStatsDto
    {
        [JsonPropertyName("total_requests")] public int TotalRequests { get; set; }
        [JsonPropertyName("total_responses")] public int TotalResponses { get; set; }
        [JsonPropertyName("total_failures")] public int TotalFailures { get; set; }
        [JsonPropertyName("period")] public string? Period { get; set; }
    }

    private sealed class UploadStatusChartDto
    {
        [JsonPropertyName("completed")] public int Completed { get; set; }
        [JsonPropertyName("processing")] public int Processing { get; set; }
        [JsonPropertyName("waiting")] public int Waiting { get; set; }
        [JsonPropertyName("error")] public int Error { get; set; }
    }

    private sealed class AuditLogResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("organization_id")] public string? OrganizationId { get; set; }
        [JsonPropertyName("user_id")] public string? UserId { get; set; }
        [JsonPropertyName("action")] public string? Action { get; set; }
        [JsonPropertyName("resource_type")] public string? ResourceType { get; set; }
        [JsonPropertyName("resource_id")] public string? ResourceId { get; set; }
        [JsonPropertyName("details")] public JsonElement? Details { get; set; }
        [JsonPropertyName("ip_address")] public string? IpAddress { get; set; }
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
    }

    private sealed class AuditLogListResponseDto
    {
        [JsonPropertyName("items")] public AuditLogResponseDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
        [JsonPropertyName("page")] public int Page { get; set; }
        [JsonPropertyName("size")] public int Size { get; set; }
    }

    // ── Phase 10.2b (2026-05-10): DocUtil Search Scopes + Evaluation API DTO ──
    // OpenAPI 캡처(2026-05-10) SearchScopeResponse / SearchScopeListResponse / SearchScopeOption /
    // LocationOption / SearchScopeCreate / SearchScopeUpdate / SearchScopeEnvironment /
    // EvaluationConfigResponse / EvaluationConfigUpdate / EvaluationLogResponse /
    // EvaluationLogListResponse / EvaluationRunSummary / EvaluationRunListResponse /
    // EvaluationRunRequest / EvaluationTrendPoint / EvaluationTrendResponse 에 1:1 매핑.
    // 추정 금지 — schema 에 없는 필드는 추가하지 않음.

    private sealed class SearchScopeResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
        [JsonPropertyName("organization_id")] public string? OrganizationId { get; set; }
        [JsonPropertyName("created_by")] public string? CreatedBy { get; set; }
        [JsonPropertyName("project_id")] public string? ProjectId { get; set; }
        [JsonPropertyName("board_id")] public string? BoardId { get; set; }
        [JsonPropertyName("folder_id")] public string? FolderId { get; set; }
        [JsonPropertyName("location_path")] public string? LocationPath { get; set; }
        [JsonPropertyName("chatbot_enabled")] public bool ChatbotEnabled { get; set; }
        [JsonPropertyName("chatbot_faq_template")] public string? ChatbotFaqTemplate { get; set; }
        [JsonPropertyName("qa_enabled")] public bool QaEnabled { get; set; }
        [JsonPropertyName("qa_prompt_template")] public string? QaPromptTemplate { get; set; }
        [JsonPropertyName("qa_llm_model")] public string? QaLlmModel { get; set; }
        [JsonPropertyName("keyword_search_enabled")] public bool KeywordSearchEnabled { get; set; }
        [JsonPropertyName("agent_enabled")] public bool AgentEnabled { get; set; }
        [JsonPropertyName("chunk_size")] public int ChunkSize { get; set; }
        [JsonPropertyName("chunk_overlap")] public int ChunkOverlap { get; set; }
        [JsonPropertyName("title_weight")] public double TitleWeight { get; set; }
        [JsonPropertyName("keyword_weight")] public double KeywordWeight { get; set; }
        [JsonPropertyName("content_weight")] public double ContentWeight { get; set; }
        [JsonPropertyName("max_results")] public int MaxResults { get; set; }
        [JsonPropertyName("similarity_threshold")] public double SimilarityThreshold { get; set; }
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
        [JsonPropertyName("updated_at")] public DateTime UpdatedAt { get; set; }
    }

    private sealed class SearchScopeListResponseDto
    {
        [JsonPropertyName("items")] public SearchScopeResponseDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
        [JsonPropertyName("page")] public int Page { get; set; }
        [JsonPropertyName("size")] public int Size { get; set; }
    }

    private sealed class SearchScopeOptionDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("location_path")] public string? LocationPath { get; set; }
    }

    private sealed class LocationOptionDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("type")] public string? Type { get; set; }
        [JsonPropertyName("path")] public string? Path { get; set; }
    }

    private sealed class SearchScopeCreateRequestDto
    {
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
        [JsonPropertyName("project_id")] public string? ProjectId { get; set; }
        [JsonPropertyName("board_id")] public string? BoardId { get; set; }
        [JsonPropertyName("folder_id")] public string? FolderId { get; set; }
        [JsonPropertyName("chatbot_enabled")] public bool? ChatbotEnabled { get; set; }
        [JsonPropertyName("qa_enabled")] public bool? QaEnabled { get; set; }
        [JsonPropertyName("keyword_search_enabled")] public bool? KeywordSearchEnabled { get; set; }
        [JsonPropertyName("agent_enabled")] public bool? AgentEnabled { get; set; }
        [JsonPropertyName("chunk_size")] public int? ChunkSize { get; set; }
        [JsonPropertyName("chunk_overlap")] public int? ChunkOverlap { get; set; }
        [JsonPropertyName("title_weight")] public double? TitleWeight { get; set; }
        [JsonPropertyName("keyword_weight")] public double? KeywordWeight { get; set; }
        [JsonPropertyName("content_weight")] public double? ContentWeight { get; set; }
        [JsonPropertyName("max_results")] public int? MaxResults { get; set; }
        [JsonPropertyName("similarity_threshold")] public double? SimilarityThreshold { get; set; }
    }

    private sealed class SearchScopeUpdateRequestDto
    {
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
        [JsonPropertyName("project_id")] public string? ProjectId { get; set; }
        [JsonPropertyName("board_id")] public string? BoardId { get; set; }
        [JsonPropertyName("folder_id")] public string? FolderId { get; set; }
        [JsonPropertyName("chatbot_enabled")] public bool? ChatbotEnabled { get; set; }
        [JsonPropertyName("qa_enabled")] public bool? QaEnabled { get; set; }
        [JsonPropertyName("keyword_search_enabled")] public bool? KeywordSearchEnabled { get; set; }
        [JsonPropertyName("agent_enabled")] public bool? AgentEnabled { get; set; }
        [JsonPropertyName("chunk_size")] public int? ChunkSize { get; set; }
        [JsonPropertyName("chunk_overlap")] public int? ChunkOverlap { get; set; }
        [JsonPropertyName("title_weight")] public double? TitleWeight { get; set; }
        [JsonPropertyName("keyword_weight")] public double? KeywordWeight { get; set; }
        [JsonPropertyName("content_weight")] public double? ContentWeight { get; set; }
        [JsonPropertyName("max_results")] public int? MaxResults { get; set; }
        [JsonPropertyName("similarity_threshold")] public double? SimilarityThreshold { get; set; }
    }

    private sealed class SearchScopeEnvironmentRequestDto
    {
        [JsonPropertyName("chatbot_enabled")] public bool? ChatbotEnabled { get; set; }
        [JsonPropertyName("chatbot_faq_template")] public string? ChatbotFaqTemplate { get; set; }
        [JsonPropertyName("qa_enabled")] public bool? QaEnabled { get; set; }
        [JsonPropertyName("qa_prompt_template")] public string? QaPromptTemplate { get; set; }
        [JsonPropertyName("qa_llm_model")] public string? QaLlmModel { get; set; }
        [JsonPropertyName("keyword_search_enabled")] public bool? KeywordSearchEnabled { get; set; }
        [JsonPropertyName("agent_enabled")] public bool? AgentEnabled { get; set; }
        [JsonPropertyName("chunk_size")] public int? ChunkSize { get; set; }
        [JsonPropertyName("chunk_overlap")] public int? ChunkOverlap { get; set; }
        [JsonPropertyName("title_weight")] public double? TitleWeight { get; set; }
        [JsonPropertyName("keyword_weight")] public double? KeywordWeight { get; set; }
        [JsonPropertyName("content_weight")] public double? ContentWeight { get; set; }
        [JsonPropertyName("max_results")] public int? MaxResults { get; set; }
        [JsonPropertyName("similarity_threshold")] public double? SimilarityThreshold { get; set; }
    }

    private sealed class EvaluationConfigResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("organization_id")] public string? OrganizationId { get; set; }
        [JsonPropertyName("context_relevancy_weight")] public double ContextRelevancyWeight { get; set; }
        [JsonPropertyName("answer_faithfulness_weight")] public double AnswerFaithfulnessWeight { get; set; }
        [JsonPropertyName("answer_relevancy_weight")] public double AnswerRelevancyWeight { get; set; }
        [JsonPropertyName("hallucination_weight")] public double HallucinationWeight { get; set; }
    }

    private sealed class EvaluationConfigUpdateRequestDto
    {
        [JsonPropertyName("context_relevancy_weight")] public double ContextRelevancyWeight { get; set; }
        [JsonPropertyName("answer_faithfulness_weight")] public double AnswerFaithfulnessWeight { get; set; }
        [JsonPropertyName("answer_relevancy_weight")] public double AnswerRelevancyWeight { get; set; }
        [JsonPropertyName("hallucination_weight")] public double HallucinationWeight { get; set; }
    }

    private sealed class EvaluationLogResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("organization_id")] public string? OrganizationId { get; set; }
        [JsonPropertyName("run_id")] public string? RunId { get; set; }
        [JsonPropertyName("question")] public string? Question { get; set; }
        [JsonPropertyName("answer")] public string? Answer { get; set; }
        [JsonPropertyName("contexts")] public JsonElement? Contexts { get; set; }
        [JsonPropertyName("context_relevancy")] public double ContextRelevancy { get; set; }
        [JsonPropertyName("answer_faithfulness")] public double AnswerFaithfulness { get; set; }
        [JsonPropertyName("answer_relevancy")] public double AnswerRelevancy { get; set; }
        [JsonPropertyName("hallucination_score")] public double HallucinationScore { get; set; }
        [JsonPropertyName("has_hallucination")] public bool HasHallucination { get; set; }
        [JsonPropertyName("hallucination_evidence")] public JsonElement? HallucinationEvidence { get; set; }
        [JsonPropertyName("composite_score")] public double CompositeScore { get; set; }
        [JsonPropertyName("judge_details")] public JsonElement? JudgeDetails { get; set; }
        [JsonPropertyName("run_type")] public string? RunType { get; set; }
        [JsonPropertyName("question_index")] public int QuestionIndex { get; set; }
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
    }

    private sealed class EvaluationLogListResponseDto
    {
        [JsonPropertyName("items")] public EvaluationLogResponseDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
        [JsonPropertyName("page")] public int Page { get; set; }
        [JsonPropertyName("size")] public int Size { get; set; }
    }

    private sealed class EvaluationRunRequestDto
    {
        [JsonPropertyName("questions")] public string[]? Questions { get; set; }
    }

    private sealed class EvaluationRunSummaryDto
    {
        [JsonPropertyName("run_id")] public string? RunId { get; set; }
        [JsonPropertyName("run_type")] public string? RunType { get; set; }
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
        [JsonPropertyName("question_count")] public int QuestionCount { get; set; }
        [JsonPropertyName("avg_context_relevancy")] public double AvgContextRelevancy { get; set; }
        [JsonPropertyName("avg_answer_faithfulness")] public double AvgAnswerFaithfulness { get; set; }
        [JsonPropertyName("avg_answer_relevancy")] public double AvgAnswerRelevancy { get; set; }
        [JsonPropertyName("avg_hallucination_score")] public double AvgHallucinationScore { get; set; }
        [JsonPropertyName("avg_composite_score")] public double AvgCompositeScore { get; set; }
        [JsonPropertyName("hallucination_count")] public int HallucinationCount { get; set; }
    }

    private sealed class EvaluationRunListResponseDto
    {
        [JsonPropertyName("items")] public EvaluationRunSummaryDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
    }

    private sealed class EvaluationTrendPointDto
    {
        [JsonPropertyName("date")] public string? Date { get; set; }
        [JsonPropertyName("avg_context_relevancy")] public double AvgContextRelevancy { get; set; }
        [JsonPropertyName("avg_answer_faithfulness")] public double AvgAnswerFaithfulness { get; set; }
        [JsonPropertyName("avg_answer_relevancy")] public double AvgAnswerRelevancy { get; set; }
        [JsonPropertyName("avg_hallucination_score")] public double AvgHallucinationScore { get; set; }
        [JsonPropertyName("avg_composite_score")] public double AvgCompositeScore { get; set; }
    }

    private sealed class EvaluationTrendResponseDto
    {
        [JsonPropertyName("data")] public EvaluationTrendPointDto[]? Data { get; set; }
    }

    /// <summary>
    /// HttpResponseMessage 의 본문 stream 을 wrap — Dispose 시 응답/요청까지 함께 정리.
    /// <para>
    /// ExportAuditLogsAsync 가 stream 을 호출자(Controller) 에게 반환하면서 response/request
    /// 객체의 lifetime 도 stream 과 동일하게 묶어주는 패턴(누수 방지).
    /// </para>
    /// </summary>
    // ── Phase 10.2c FAQ + Reports + Templates DTOs ────────────────────────

    private sealed class FaqResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("search_scope_id")] public string? SearchScopeId { get; set; }
        [JsonPropertyName("organization_id")] public string? OrganizationId { get; set; }
        [JsonPropertyName("question")] public string? Question { get; set; }
        [JsonPropertyName("answer")] public string? Answer { get; set; }
        [JsonPropertyName("category")] public string? Category { get; set; }
        [JsonPropertyName("display_order")] public int DisplayOrder { get; set; }
        [JsonPropertyName("is_active")] public bool IsActive { get; set; }
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
        [JsonPropertyName("updated_at")] public DateTime UpdatedAt { get; set; }
    }

    private sealed class FaqListResponseDto
    {
        [JsonPropertyName("items")] public FaqResponseDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
        [JsonPropertyName("page")] public int Page { get; set; }
        [JsonPropertyName("size")] public int Size { get; set; }
    }

    private sealed class FaqCreateRequestDto
    {
        [JsonPropertyName("question")] public string? Question { get; set; }
        [JsonPropertyName("answer")] public string? Answer { get; set; }
        [JsonPropertyName("category")] public string? Category { get; set; }
        [JsonPropertyName("display_order")] public int DisplayOrder { get; set; }
        [JsonPropertyName("search_scope_id")] public string? SearchScopeId { get; set; }
    }

    private sealed class FaqUpdateRequestDto
    {
        [JsonPropertyName("question")] public string? Question { get; set; }
        [JsonPropertyName("answer")] public string? Answer { get; set; }
        [JsonPropertyName("category")] public string? Category { get; set; }
        [JsonPropertyName("display_order")] public int? DisplayOrder { get; set; }
        [JsonPropertyName("is_active")] public bool? IsActive { get; set; }
    }

    private sealed class ReportResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("template_id")] public string? TemplateId { get; set; }
        [JsonPropertyName("organization_id")] public string? OrganizationId { get; set; }
        [JsonPropertyName("title")] public string? Title { get; set; }
        [JsonPropertyName("status")] public string? Status { get; set; }
        [JsonPropertyName("output_format")] public string? OutputFormat { get; set; }
        [JsonPropertyName("output_storage_path")] public string? OutputStoragePath { get; set; }
        [JsonPropertyName("source_document_ids")] public string[]? SourceDocumentIds { get; set; }
        [JsonPropertyName("source_chat_session_id")] public string? SourceChatSessionId { get; set; }
        [JsonPropertyName("generation_params")] public object? GenerationParams { get; set; }
        [JsonPropertyName("rendering_mode")] public string? RenderingMode { get; set; }
        [JsonPropertyName("jinja2_context")] public object? Jinja2Context { get; set; }
        [JsonPropertyName("error_message")] public string? ErrorMessage { get; set; }
        [JsonPropertyName("generated_by")] public string? GeneratedBy { get; set; }
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
        [JsonPropertyName("completed_at")] public DateTime? CompletedAt { get; set; }
    }

    private sealed class ReportListResponseDto
    {
        [JsonPropertyName("items")] public ReportResponseDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
        [JsonPropertyName("page")] public int Page { get; set; }
        [JsonPropertyName("size")] public int Size { get; set; }
    }

    private sealed class ReportGenerateRequestDto
    {
        [JsonPropertyName("template_id")] public string? TemplateId { get; set; }
        [JsonPropertyName("title")] public string? Title { get; set; }
        [JsonPropertyName("output_format")] public string? OutputFormat { get; set; }
        [JsonPropertyName("source_document_ids")] public string[]? SourceDocumentIds { get; set; }
        [JsonPropertyName("source_chat_session_id")] public string? SourceChatSessionId { get; set; }
        [JsonPropertyName("generation_params")] public IDictionary<string, object?>? GenerationParams { get; set; }
    }

    private sealed class ReportTemplateResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("organization_id")] public string? OrganizationId { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
        [JsonPropertyName("format")] public string? Format { get; set; }
        [JsonPropertyName("template_storage_path")] public string? TemplateStoragePath { get; set; }
        [JsonPropertyName("schema")] public object? Schema { get; set; }
        [JsonPropertyName("created_by")] public string? CreatedBy { get; set; }
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
        [JsonPropertyName("updated_at")] public DateTime UpdatedAt { get; set; }
    }

    private sealed class ReportTemplateListResponseDto
    {
        [JsonPropertyName("items")] public ReportTemplateResponseDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
        [JsonPropertyName("page")] public int Page { get; set; }
        [JsonPropertyName("size")] public int Size { get; set; }
    }

    private sealed class ReportTemplateUpdateRequestDto
    {
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
    }

    // ── Phase 10.2d (2026-05-11): Document Templates 직렬화 DTO ──────────────
    //
    // DocUtil 의 schemas.py 와 1:1. snake_case JSON 키 명시(JsonPropertyName) — JsonNamingPolicy 와 중복이지만
    // 명시성을 우선해 다른 DTO 패턴과 일관성 유지. JsonElement? 필드는 free-form dict 매핑용.

    private sealed class DocumentTemplateResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("organization_id")] public string? OrganizationId { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
        [JsonPropertyName("template_type")] public string? TemplateType { get; set; }
        [JsonPropertyName("tone")] public string? Tone { get; set; }
        [JsonPropertyName("output_format")] public string? OutputFormat { get; set; }
        [JsonPropertyName("schema")] public JsonElement? Schema { get; set; }
        [JsonPropertyName("sample_prompt")] public string? SamplePrompt { get; set; }
        [JsonPropertyName("is_active")] public bool IsActive { get; set; }
        [JsonPropertyName("created_by")] public string? CreatedBy { get; set; }
        // DocUtil TemplateResponse 는 ins_dt/upd_dt 를 validation_alias 로 받는다 — 응답 본문에 created_at/updated_at 으로 직렬화.
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
        [JsonPropertyName("updated_at")] public DateTime UpdatedAt { get; set; }
        [JsonPropertyName("template_storage_path")] public string? TemplateStoragePath { get; set; }
        [JsonPropertyName("jinja2_variables")] public JsonElement? Jinja2Variables { get; set; }
        [JsonPropertyName("rendering_mode")] public string? RenderingMode { get; set; }
        [JsonPropertyName("image_generation_config")] public JsonElement? ImageGenerationConfig { get; set; }
    }

    private sealed class DocumentTemplateListResponseDto
    {
        [JsonPropertyName("items")] public DocumentTemplateResponseDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
        [JsonPropertyName("page")] public int Page { get; set; }
        [JsonPropertyName("size")] public int Size { get; set; }
    }

    private sealed class DocumentTemplateCreateRequestDto
    {
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
        [JsonPropertyName("template_type")] public string? TemplateType { get; set; }
        [JsonPropertyName("tone")] public string? Tone { get; set; }
        [JsonPropertyName("output_format")] public string? OutputFormat { get; set; }
        [JsonPropertyName("schema")] public IDictionary<string, object?>? Schema { get; set; }
        [JsonPropertyName("sample_prompt")] public string? SamplePrompt { get; set; }
        [JsonPropertyName("rendering_mode")] public string? RenderingMode { get; set; }
        [JsonPropertyName("image_generation_config")] public IDictionary<string, object?>? ImageGenerationConfig { get; set; }
    }

    private sealed class DocumentTemplateUpdateRequestDto
    {
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
        [JsonPropertyName("template_type")] public string? TemplateType { get; set; }
        [JsonPropertyName("tone")] public string? Tone { get; set; }
        [JsonPropertyName("output_format")] public string? OutputFormat { get; set; }
        [JsonPropertyName("schema")] public IDictionary<string, object?>? Schema { get; set; }
        [JsonPropertyName("sample_prompt")] public string? SamplePrompt { get; set; }
        [JsonPropertyName("is_active")] public bool? IsActive { get; set; }
        [JsonPropertyName("rendering_mode")] public string? RenderingMode { get; set; }
        [JsonPropertyName("image_generation_config")] public IDictionary<string, object?>? ImageGenerationConfig { get; set; }
    }

    private sealed class DocumentTemplateVariableDto
    {
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("var_type")] public string? VarType { get; set; }
        [JsonPropertyName("label")] public string? Label { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
        [JsonPropertyName("required")] public bool Required { get; set; } = true;
        [JsonPropertyName("category")] public string? Category { get; set; }
    }

    private sealed class DocumentTemplateVariablesUpdateRequestDto
    {
        [JsonPropertyName("variables")] public DocumentTemplateVariableDto[]? Variables { get; set; }
    }

    private sealed class DocumentTemplateUploadResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("output_format")] public string? OutputFormat { get; set; }
        [JsonPropertyName("rendering_mode")] public string? RenderingMode { get; set; }
        [JsonPropertyName("template_storage_path")] public string? TemplateStoragePath { get; set; }
        [JsonPropertyName("variables")] public DocumentTemplateVariableDto[]? Variables { get; set; }
    }

    private sealed class DocumentTemplateAutoFillResponseDto
    {
        [JsonPropertyName("context")] public JsonElement? Context { get; set; }
    }

    private sealed class DocumentTemplateMappingDto
    {
        [JsonPropertyName("location_type")] public string? LocationType { get; set; }
        [JsonPropertyName("table_index")] public int? TableIndex { get; set; }
        [JsonPropertyName("row")] public int? Row { get; set; }
        [JsonPropertyName("col")] public int? Col { get; set; }
        [JsonPropertyName("paragraph_index")] public int? ParagraphIndex { get; set; }
        [JsonPropertyName("variable_name")] public string? VariableName { get; set; }
        [JsonPropertyName("var_type")] public string? VarType { get; set; }
        [JsonPropertyName("label")] public string? Label { get; set; }
        [JsonPropertyName("category")] public string? Category { get; set; }
        [JsonPropertyName("field_type")] public string? FieldType { get; set; }
    }

    private sealed class DocumentTemplateMappingPayloadDto
    {
        [JsonPropertyName("mappings")] public DocumentTemplateMappingDto[]? Mappings { get; set; }
    }

    // ══════════════════════════════════════════════════════════════════════
    // Phase 10.2e (2026-05-11) — DocUtil API Keys + Agents + Documents V2 BFF 16 메서드
    //
    // - API Keys (4)        : 등록/조회/삭제/검증
    // - DocUtil Agents (5)  : 챗봇/보고서/제안서/회의록용 페르소나 CRUD (AgentHub Agent 와 별개)
    // - Documents V2 (7)    : 디자이너 워크플로 — 생성/조회/패치 + 비동기 export + 결과 다운로드
    //
    // org_id 자동 부착:
    //   세 도메인 모두 DocUtil 측이 운영자 JWT 의 organization_id claim 으로 자동 scope.
    //   본 클라이언트는 path 에 orgId 명시 X (OpenAPI 검증 결과 일치).
    //
    // 4xx/5xx → InvalidOperationException 통일 → Controller 502 한국어 매핑.
    // 404 (GET 단건) → null 정규화 (이미 패턴 정립됨).
    // 502 ↔ 200 stream(다운로드) → HttpResponseOwnedStream 으로 lifetime 결합.
    // ══════════════════════════════════════════════════════════════════════

    // ── API Keys (4) ───────────────────────────────────────────────────────

    public async Task<DocUtilApiKeyList> ListApiKeysAsync(
        int page = 1,
        int size = 20,
        CancellationToken cancellationToken = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 100) size = 20;

        var path = $"/api/v1/api-keys?page={page}&size={size}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<ApiKeyListResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil API Key 목록 응답을 디시리얼라이즈하지 못했습니다.");
        }
        var items = (dto.Items ?? Array.Empty<ApiKeyResponseDto>()).Select(MapApiKey).ToArray();
        return new DocUtilApiKeyList(items, dto.Total, dto.Page, dto.Size);
    }

    public async Task<DocUtilApiKeyDetail> CreateApiKeyAsync(
        DocUtilCreateApiKeyRequest request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);
        if (string.IsNullOrWhiteSpace(request.LlmName))
        {
            throw new ArgumentException("llm_name 이 비어 있습니다.", nameof(request));
        }
        if (string.IsNullOrWhiteSpace(request.ApiKey))
        {
            throw new ArgumentException("api_key 가 비어 있습니다.", nameof(request));
        }

        var body = new ApiKeyCreateRequestDto
        {
            LlmName = request.LlmName,
            ApiKey = request.ApiKey,
        };

        const string path = "/api/v1/api-keys";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<ApiKeyResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil API Key 생성 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapApiKey(dto);
    }

    public async Task DeleteApiKeyAsync(
        string keyId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(keyId))
        {
            throw new ArgumentException("keyId 가 비어 있습니다.", nameof(keyId));
        }

        var path = $"/api/v1/api-keys/{Uri.EscapeDataString(keyId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Delete, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
    }

    public async Task<DocUtilApiKeyVerifyResult> VerifyApiKeyAsync(
        string keyId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(keyId))
        {
            throw new ArgumentException("keyId 가 비어 있습니다.", nameof(keyId));
        }

        var path = $"/api/v1/api-keys/{Uri.EscapeDataString(keyId)}/verify";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<ApiKeyVerifyResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil API Key 검증 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return new DocUtilApiKeyVerifyResult(dto.IsValid, dto.Message ?? string.Empty);
    }

    private static DocUtilApiKeyDetail MapApiKey(ApiKeyResponseDto dto)
        => new(
            dto.Id ?? string.Empty,
            dto.OrganizationId ?? string.Empty,
            dto.LlmName ?? string.Empty,
            dto.ApiKeyPrefix ?? string.Empty,
            dto.IsVerified,
            dto.RegisteredBy,
            dto.CreatedAt,
            dto.UpdatedAt);

    // ── DocUtil Agents (5) ─────────────────────────────────────────────────

    public async Task<DocUtilDocAgentList> ListDocAgentsAsync(
        string? agentType = null,
        int page = 1,
        int size = 20,
        CancellationToken cancellationToken = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 100) size = 20;

        var qb = new List<string> { $"page={page}", $"size={size}" };
        if (!string.IsNullOrWhiteSpace(agentType))
        {
            qb.Add($"agent_type={Uri.EscapeDataString(agentType)}");
        }
        var path = $"/api/v1/agents?{string.Join("&", qb)}";

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocAgentListResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 에이전트 목록 응답을 디시리얼라이즈하지 못했습니다.");
        }
        var items = (dto.Items ?? Array.Empty<DocAgentResponseDto>()).Select(MapDocAgent).ToArray();
        return new DocUtilDocAgentList(items, dto.Total, dto.Page, dto.Size);
    }

    public async Task<DocUtilDocAgentDetail?> GetDocAgentAsync(
        string agentId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(agentId))
        {
            throw new ArgumentException("agentId 가 비어 있습니다.", nameof(agentId));
        }

        var path = $"/api/v1/agents/{Uri.EscapeDataString(agentId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return null;
        }
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocAgentResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 에이전트 상세 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapDocAgent(dto);
    }

    public async Task<DocUtilDocAgentDetail> CreateDocAgentAsync(
        DocUtilCreateDocAgentRequest request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            throw new ArgumentException("name 이 비어 있습니다.", nameof(request));
        }
        if (string.IsNullOrWhiteSpace(request.AgentType))
        {
            throw new ArgumentException("agent_type 이 비어 있습니다.", nameof(request));
        }
        if (string.IsNullOrWhiteSpace(request.SystemPrompt))
        {
            throw new ArgumentException("system_prompt 가 비어 있습니다.", nameof(request));
        }

        var body = new DocAgentCreateRequestDto
        {
            Name = request.Name,
            Description = request.Description,
            AgentType = request.AgentType,
            SystemPrompt = request.SystemPrompt,
            LlmProvider = request.LlmProvider,
            LlmModel = request.LlmModel,
            Temperature = request.Temperature,
            MaxTokens = request.MaxTokens,
        };

        const string path = "/api/v1/agents";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocAgentResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 에이전트 생성 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapDocAgent(dto);
    }

    public async Task<DocUtilDocAgentDetail> UpdateDocAgentAsync(
        string agentId,
        DocUtilUpdateDocAgentRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(agentId))
        {
            throw new ArgumentException("agentId 가 비어 있습니다.", nameof(agentId));
        }
        ArgumentNullException.ThrowIfNull(request);

        // partial update — null 필드는 직렬화 제외(JsonOptions.WhenWritingNull).
        var body = new DocAgentUpdateRequestDto
        {
            Name = request.Name,
            Description = request.Description,
            AgentType = request.AgentType,
            SystemPrompt = request.SystemPrompt,
            LlmProvider = request.LlmProvider,
            LlmModel = request.LlmModel,
            Temperature = request.Temperature,
            MaxTokens = request.MaxTokens,
            IsActive = request.IsActive,
        };

        var path = $"/api/v1/agents/{Uri.EscapeDataString(agentId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Put, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocAgentResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 에이전트 수정 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapDocAgent(dto);
    }

    public async Task DeleteDocAgentAsync(
        string agentId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(agentId))
        {
            throw new ArgumentException("agentId 가 비어 있습니다.", nameof(agentId));
        }

        var path = $"/api/v1/agents/{Uri.EscapeDataString(agentId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Delete, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
    }

    private static DocUtilDocAgentDetail MapDocAgent(DocAgentResponseDto dto)
        => new(
            dto.Id ?? string.Empty,
            dto.OrganizationId ?? string.Empty,
            dto.Name ?? string.Empty,
            dto.Description,
            dto.AgentType ?? string.Empty,
            dto.SystemPrompt ?? string.Empty,
            dto.LlmProvider,
            dto.LlmModel ?? "gpt-4o",
            dto.Temperature,
            dto.MaxTokens,
            dto.IsActive,
            dto.CreatedBy ?? string.Empty,
            dto.CreatedAt,
            dto.UpdatedAt);

    // ── Documents V2 (7) ──────────────────────────────────────────────────

    public async Task<DocUtilDocumentV2Detail> GenerateDocumentV2Async(
        DocUtilGenerateDocumentV2Request request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);
        if (string.IsNullOrWhiteSpace(request.Prompt))
        {
            throw new ArgumentException("prompt 가 비어 있습니다.", nameof(request));
        }
        if (string.IsNullOrWhiteSpace(request.DocumentType))
        {
            throw new ArgumentException("document_type 이 비어 있습니다.", nameof(request));
        }

        var body = new DocumentV2GenerateRequestDto
        {
            Prompt = request.Prompt,
            DocumentType = request.DocumentType,
            Mode = string.IsNullOrWhiteSpace(request.Mode) ? "free_generation" : request.Mode,
            SourceDocumentIds = request.SourceDocumentIds,
            AgentId = request.AgentId,
            DesignTokens = request.DesignTokens,
        };

        const string path = "/api/v1/v2/documents";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentV2ResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 문서 V2 생성 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapDocumentV2(dto);
    }

    public async Task<DocUtilDocumentV2List> ListDocumentsV2Async(
        string? documentType = null,
        string? mode = null,
        int limit = 20,
        int offset = 0,
        CancellationToken cancellationToken = default)
    {
        if (limit < 1 || limit > 100) limit = 20;
        if (offset < 0) offset = 0;

        var qb = new List<string> { $"limit={limit}", $"offset={offset}" };
        if (!string.IsNullOrWhiteSpace(documentType))
        {
            qb.Add($"document_type={Uri.EscapeDataString(documentType)}");
        }
        if (!string.IsNullOrWhiteSpace(mode))
        {
            qb.Add($"mode={Uri.EscapeDataString(mode)}");
        }
        var path = $"/api/v1/v2/documents?{string.Join("&", qb)}";

        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentV2ListResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 문서 V2 목록 응답을 디시리얼라이즈하지 못했습니다.");
        }
        var items = (dto.Items ?? Array.Empty<DocumentV2ResponseDto>()).Select(MapDocumentV2).ToArray();
        return new DocUtilDocumentV2List(items, dto.Total, dto.Limit, dto.Offset);
    }

    public async Task<DocUtilDocumentV2Detail?> GetDocumentV2Async(
        string documentId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(documentId))
        {
            throw new ArgumentException("documentId 가 비어 있습니다.", nameof(documentId));
        }

        var path = $"/api/v1/v2/documents/{Uri.EscapeDataString(documentId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return null;
        }
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentV2ResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 문서 V2 상세 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapDocumentV2(dto);
    }

    public async Task<DocUtilDocumentV2Detail> PatchDocumentV2Async(
        string documentId,
        DocUtilPatchDocumentV2Request request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(documentId))
        {
            throw new ArgumentException("documentId 가 비어 있습니다.", nameof(documentId));
        }
        ArgumentNullException.ThrowIfNull(request);
        if (string.IsNullOrWhiteSpace(request.PatchType))
        {
            throw new ArgumentException("patch_type 이 비어 있습니다.", nameof(request));
        }
        if (request.PatchType is not ("page" or "component" or "tokens"))
        {
            throw new ArgumentException(
                "patch_type 은 page/component/tokens 중 하나여야 합니다.", nameof(request));
        }
        // 식별자 사전 검증(서비스 호출 전 BFF 차원에서 한국어 에러 명시).
        if (request.PatchType == "page" && string.IsNullOrWhiteSpace(request.PageId))
        {
            throw new ArgumentException("patch_type=page 에는 page_id 가 필요합니다.", nameof(request));
        }
        if (request.PatchType == "component"
            && (string.IsNullOrWhiteSpace(request.PageId) || string.IsNullOrWhiteSpace(request.ComponentId)))
        {
            throw new ArgumentException(
                "patch_type=component 에는 page_id 와 component_id 가 모두 필요합니다.", nameof(request));
        }

        var body = new DocumentV2PatchRequestDto
        {
            PatchType = request.PatchType,
            PageId = request.PageId,
            ComponentId = request.ComponentId,
            Data = request.Data,
            ExpectedVersion = request.ExpectedVersion,
        };

        var path = $"/api/v1/v2/documents/{Uri.EscapeDataString(documentId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Patch, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentV2ResponseDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 문서 V2 패치 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return MapDocumentV2(dto);
    }

    public async Task<DocUtilExportJobAck> RequestDocumentV2ExportAsync(
        string documentId,
        DocUtilRequestDocumentV2ExportRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(documentId))
        {
            throw new ArgumentException("documentId 가 비어 있습니다.", nameof(documentId));
        }
        ArgumentNullException.ThrowIfNull(request);
        if (string.IsNullOrWhiteSpace(request.Format))
        {
            throw new ArgumentException("format 이 비어 있습니다.", nameof(request));
        }
        // DocUtil 측 Literal — 사전 차단(서비스 호출 비용 절감).
        if (request.Format is not ("pptx" or "docx" or "hwpx" or "pdf" or "html"))
        {
            throw new ArgumentException(
                "format 은 pptx/docx/hwpx/pdf/html 중 하나여야 합니다.", nameof(request));
        }

        var body = new DocumentV2ExportRequestDto { Format = request.Format };
        var path = $"/api/v1/v2/documents/{Uri.EscapeDataString(documentId)}/export";
        // Long-running named client (5분 timeout) — Export job 큐잉이 동기 처리되는 경우 60s 초과 가능.
        var client = _httpClientFactory.CreateClient(LongRunningHttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Post, path, body, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentV2ExportJobAckDto>(stream, JsonOptions, cancellationToken);
        if (dto is null || string.IsNullOrWhiteSpace(dto.JobId))
        {
            throw new InvalidOperationException("DocUtil 문서 V2 export 요청 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return new DocUtilExportJobAck(dto.JobId);
    }

    public async Task<DocUtilExportJobStatus> GetDocumentV2ExportStatusAsync(
        string jobId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(jobId))
        {
            throw new ArgumentException("jobId 가 비어 있습니다.", nameof(jobId));
        }

        var path = $"/api/v1/v2/documents/exports/{Uri.EscapeDataString(jobId)}";
        var client = _httpClientFactory.CreateClient(HttpClientName);
        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);
        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<DocumentV2ExportStatusDto>(stream, JsonOptions, cancellationToken);
        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 문서 V2 export 상태 응답을 디시리얼라이즈하지 못했습니다.");
        }
        return new DocUtilExportJobStatus(
            dto.Status ?? "pending",
            dto.Progress,
            dto.DownloadUrl,
            dto.Error);
    }

    public async Task<DocUtilDocumentV2Download> DownloadDocumentV2ExportAsync(
        string jobId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(jobId))
        {
            throw new ArgumentException("jobId 가 비어 있습니다.", nameof(jobId));
        }

        var path = $"/api/v1/v2/documents/exports/{Uri.EscapeDataString(jobId)}/download";
        // Long-running named client (5분 timeout) — 대용량 export 파일(pptx/docx/pdf) 다운로드.
        var client = _httpClientFactory.CreateClient(LongRunningHttpClientName);
        var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);
        // stream 반환 — using 사용 안 함(호출자 소유, HttpResponseOwnedStream 으로 lifetime 결합).

        _logger.LogInformation("DocUtil 문서 V2 export 다운로드 호출 - JobId={JobId}", jobId);

        var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseHeadersRead, cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            try
            {
                await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);
            }
            finally
            {
                response.Dispose();
                httpRequest.Dispose();
            }
        }

        var contentType = response.Content.Headers.ContentType?.ToString()
            ?? "application/octet-stream";

        var disposition = response.Content.Headers.ContentDisposition;
        var fileName = disposition?.FileNameStar
            ?? disposition?.FileName?.Trim('"')
            ?? $"document-{jobId}";

        var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var owned = new HttpResponseOwnedStream(stream, response, httpRequest);
        return new DocUtilDocumentV2Download(owned, contentType, fileName);
    }

    private static DocUtilDocumentV2Detail MapDocumentV2(DocumentV2ResponseDto dto)
        => new(
            dto.Id ?? string.Empty,
            dto.OrganizationId ?? string.Empty,
            dto.GeneratedByUserId,
            dto.AgentId,
            dto.TemplateId,
            dto.DocumentType ?? string.Empty,
            dto.Mode ?? "free_generation",
            dto.Title ?? string.Empty,
            dto.Status ?? string.Empty,
            dto.ErrorMessage,
            dto.LlmProvider,
            dto.LlmModel,
            dto.PromptTokens,
            dto.CompletionTokens,
            dto.CreatedAt,
            dto.CompletedAt,
            ConvertJsonElementToOptionalDict(dto.DocumentSchema));

    // ── Phase 10.2e DTO (private, DocUtil 응답 매핑) ───────────────────────

    private sealed class ApiKeyResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("organization_id")] public string? OrganizationId { get; set; }
        [JsonPropertyName("llm_name")] public string? LlmName { get; set; }
        [JsonPropertyName("api_key_prefix")] public string? ApiKeyPrefix { get; set; }
        [JsonPropertyName("is_verified")] public bool IsVerified { get; set; }
        [JsonPropertyName("registered_by")] public string? RegisteredBy { get; set; }
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
        [JsonPropertyName("updated_at")] public DateTime UpdatedAt { get; set; }
    }

    private sealed class ApiKeyListResponseDto
    {
        [JsonPropertyName("items")] public ApiKeyResponseDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
        [JsonPropertyName("page")] public int Page { get; set; }
        [JsonPropertyName("size")] public int Size { get; set; }
    }

    private sealed class ApiKeyCreateRequestDto
    {
        [JsonPropertyName("llm_name")] public string? LlmName { get; set; }
        [JsonPropertyName("api_key")] public string? ApiKey { get; set; }
    }

    private sealed class ApiKeyVerifyResponseDto
    {
        [JsonPropertyName("is_valid")] public bool IsValid { get; set; }
        [JsonPropertyName("message")] public string? Message { get; set; }
    }

    private sealed class DocAgentResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("organization_id")] public string? OrganizationId { get; set; }
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
        [JsonPropertyName("agent_type")] public string? AgentType { get; set; }
        [JsonPropertyName("system_prompt")] public string? SystemPrompt { get; set; }
        [JsonPropertyName("llm_provider")] public string? LlmProvider { get; set; }
        [JsonPropertyName("llm_model")] public string? LlmModel { get; set; }
        [JsonPropertyName("temperature")] public double Temperature { get; set; }
        [JsonPropertyName("max_tokens")] public int MaxTokens { get; set; }
        [JsonPropertyName("is_active")] public bool IsActive { get; set; }
        [JsonPropertyName("created_by")] public string? CreatedBy { get; set; }
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
        [JsonPropertyName("updated_at")] public DateTime UpdatedAt { get; set; }
    }

    private sealed class DocAgentListResponseDto
    {
        [JsonPropertyName("items")] public DocAgentResponseDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
        [JsonPropertyName("page")] public int Page { get; set; }
        [JsonPropertyName("size")] public int Size { get; set; }
    }

    private sealed class DocAgentCreateRequestDto
    {
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
        [JsonPropertyName("agent_type")] public string? AgentType { get; set; }
        [JsonPropertyName("system_prompt")] public string? SystemPrompt { get; set; }
        [JsonPropertyName("llm_provider")] public string? LlmProvider { get; set; }
        [JsonPropertyName("llm_model")] public string? LlmModel { get; set; }
        [JsonPropertyName("temperature")] public double Temperature { get; set; }
        [JsonPropertyName("max_tokens")] public int MaxTokens { get; set; }
    }

    private sealed class DocAgentUpdateRequestDto
    {
        [JsonPropertyName("name")] public string? Name { get; set; }
        [JsonPropertyName("description")] public string? Description { get; set; }
        [JsonPropertyName("agent_type")] public string? AgentType { get; set; }
        [JsonPropertyName("system_prompt")] public string? SystemPrompt { get; set; }
        [JsonPropertyName("llm_provider")] public string? LlmProvider { get; set; }
        [JsonPropertyName("llm_model")] public string? LlmModel { get; set; }
        [JsonPropertyName("temperature")] public double? Temperature { get; set; }
        [JsonPropertyName("max_tokens")] public int? MaxTokens { get; set; }
        [JsonPropertyName("is_active")] public bool? IsActive { get; set; }
    }

    private sealed class DocumentV2ResponseDto
    {
        [JsonPropertyName("id")] public string? Id { get; set; }
        [JsonPropertyName("organization_id")] public string? OrganizationId { get; set; }
        [JsonPropertyName("generated_by_user_id")] public string? GeneratedByUserId { get; set; }
        [JsonPropertyName("agent_id")] public string? AgentId { get; set; }
        [JsonPropertyName("template_id")] public string? TemplateId { get; set; }
        [JsonPropertyName("document_type")] public string? DocumentType { get; set; }
        [JsonPropertyName("mode")] public string? Mode { get; set; }
        [JsonPropertyName("title")] public string? Title { get; set; }
        [JsonPropertyName("status")] public string? Status { get; set; }
        [JsonPropertyName("error_message")] public string? ErrorMessage { get; set; }
        [JsonPropertyName("llm_provider")] public string? LlmProvider { get; set; }
        [JsonPropertyName("llm_model")] public string? LlmModel { get; set; }
        [JsonPropertyName("prompt_tokens")] public int? PromptTokens { get; set; }
        [JsonPropertyName("completion_tokens")] public int? CompletionTokens { get; set; }
        [JsonPropertyName("created_at")] public DateTime CreatedAt { get; set; }
        [JsonPropertyName("completed_at")] public DateTime? CompletedAt { get; set; }
        [JsonPropertyName("document_schema")] public JsonElement? DocumentSchema { get; set; }
    }

    private sealed class DocumentV2ListResponseDto
    {
        [JsonPropertyName("items")] public DocumentV2ResponseDto[]? Items { get; set; }
        [JsonPropertyName("total")] public long Total { get; set; }
        [JsonPropertyName("limit")] public int Limit { get; set; }
        [JsonPropertyName("offset")] public int Offset { get; set; }
    }

    private sealed class DocumentV2GenerateRequestDto
    {
        [JsonPropertyName("prompt")] public string? Prompt { get; set; }
        [JsonPropertyName("document_type")] public string? DocumentType { get; set; }
        [JsonPropertyName("mode")] public string? Mode { get; set; }
        [JsonPropertyName("source_document_ids")] public string[]? SourceDocumentIds { get; set; }
        [JsonPropertyName("agent_id")] public string? AgentId { get; set; }
        [JsonPropertyName("design_tokens")] public IDictionary<string, object?>? DesignTokens { get; set; }
    }

    private sealed class DocumentV2PatchRequestDto
    {
        [JsonPropertyName("patch_type")] public string? PatchType { get; set; }
        [JsonPropertyName("page_id")] public string? PageId { get; set; }
        [JsonPropertyName("component_id")] public string? ComponentId { get; set; }
        [JsonPropertyName("data")] public IDictionary<string, object?>? Data { get; set; }
        [JsonPropertyName("expected_version")] public int? ExpectedVersion { get; set; }
    }

    private sealed class DocumentV2ExportRequestDto
    {
        [JsonPropertyName("format")] public string? Format { get; set; }
    }

    private sealed class DocumentV2ExportJobAckDto
    {
        [JsonPropertyName("job_id")] public string? JobId { get; set; }
    }

    private sealed class DocumentV2ExportStatusDto
    {
        [JsonPropertyName("status")] public string? Status { get; set; }
        [JsonPropertyName("progress")] public int Progress { get; set; }
        [JsonPropertyName("download_url")] public string? DownloadUrl { get; set; }
        [JsonPropertyName("error")] public string? Error { get; set; }
    }

    private sealed class HttpResponseOwnedStream : Stream
    {
        private readonly Stream _inner;
        private readonly HttpResponseMessage _response;
        private readonly HttpRequestMessage _request;
        private bool _disposed;

        public HttpResponseOwnedStream(Stream inner, HttpResponseMessage response, HttpRequestMessage request)
        {
            _inner = inner;
            _response = response;
            _request = request;
        }

        public override bool CanRead => _inner.CanRead;
        public override bool CanSeek => _inner.CanSeek;
        public override bool CanWrite => _inner.CanWrite;
        public override long Length => _inner.Length;
        public override long Position { get => _inner.Position; set => _inner.Position = value; }
        public override void Flush() => _inner.Flush();
        public override int Read(byte[] buffer, int offset, int count) => _inner.Read(buffer, offset, count);
        public override Task<int> ReadAsync(byte[] buffer, int offset, int count, CancellationToken cancellationToken)
            => _inner.ReadAsync(buffer, offset, count, cancellationToken);
        public override ValueTask<int> ReadAsync(Memory<byte> buffer, CancellationToken cancellationToken = default)
            => _inner.ReadAsync(buffer, cancellationToken);
        public override long Seek(long offset, SeekOrigin origin) => _inner.Seek(offset, origin);
        public override void SetLength(long value) => _inner.SetLength(value);
        public override void Write(byte[] buffer, int offset, int count) => _inner.Write(buffer, offset, count);

        protected override void Dispose(bool disposing)
        {
            if (!_disposed && disposing)
            {
                _inner.Dispose();
                _response.Dispose();
                _request.Dispose();
                _disposed = true;
            }
            base.Dispose(disposing);
        }

        public override async ValueTask DisposeAsync()
        {
            if (!_disposed)
            {
                await _inner.DisposeAsync().ConfigureAwait(false);
                _response.Dispose();
                _request.Dispose();
                _disposed = true;
            }
            await base.DisposeAsync().ConfigureAwait(false);
        }
    }
}
