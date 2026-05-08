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
    // 캐시 미적용: collection 목록은 자주 호출되지 않고, 운영자가 DocUtil 콘솔에서
    // 새 project 생성 직후 드롭다운에 즉시 반영되어야 하므로 fresh 응답 우선.
    // 향후 트랙: version-key 패턴 도입 시 SearchAsync 와 동일 namespace 또는 별도 분리 검토.
    // ══════════════════════════════════════════════════════════════════════
    public async Task<List<DocUtilCollection>> ListCollectionsAsync(
        int page = 1,
        int size = 50,
        CancellationToken cancellationToken = default)
    {
        if (page < 1) page = 1;
        if (size < 1 || size > 200) size = 50;

        var client = _httpClientFactory.CreateClient(HttpClientName);
        var path = $"/api/v1/projects?page={page}&size={size}";

        using var httpRequest = await BuildJsonRequestAsync(HttpMethod.Get, path, body: null, cancellationToken);

        _logger.LogDebug(
            "DocUtil 컬렉션(projects) 목록 호출 - Page={Page}, Size={Size}", page, size);

        using var response = await client.SendAsync(
            httpRequest, HttpCompletionOption.ResponseContentRead, cancellationToken);

        await EnsureSuccessOrThrowKoreanAsync(response, path, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var dto = await JsonSerializer.DeserializeAsync<ProjectListDto>(stream, JsonOptions, cancellationToken);

        if (dto is null)
        {
            throw new InvalidOperationException("DocUtil 컬렉션(projects) 목록 응답을 디시리얼라이즈하지 못했습니다.");
        }

        var items = (dto.Items ?? Array.Empty<ProjectSummaryDto>())
            .Select(p => new DocUtilCollection(
                p.Id ?? string.Empty,
                p.Name ?? string.Empty,
                p.Description))
            .Where(c => !string.IsNullOrWhiteSpace(c.Id))
            .ToList();

        _logger.LogDebug(
            "DocUtil 컬렉션 응답 - Count={Count}, Total={Total}", items.Count, dto.Total);

        return items;
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
}
