using System.Net;
using System.Net.Http.Headers;
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

    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IConfiguration _configuration;
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
        ILogger<DocUtilClient> logger)
    {
        _httpClientFactory = httpClientFactory;
        _configuration = configuration;
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
            return new DocUtilSearchResult(Array.Empty<DocUtilSearchHit>(), 0d, null);
        }

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

        using var httpRequest = BuildJsonRequest(HttpMethod.Post, "/api/v1/search", requestBody);

        _logger.LogDebug(
            "DocUtil 하이브리드 검색 호출 - CollectionRef={CollectionRef}, MaxResults={MaxResults}, QueryLen={QueryLen}",
            collectionRef ?? "(global)", maxResults, query.Length);

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
            "DocUtil 검색 응답 - Hits={HitCount}, TotalTime={TotalTime}s",
            hits.Length, dto.TotalTime);

        return new DocUtilSearchResult(hits, dto.TotalTime, dto.Metadata);
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

        using var httpRequest = BuildJsonRequest(HttpMethod.Get, path, body: null);

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

        using var httpRequest = BuildJsonRequest(HttpMethod.Get, path, body: null);

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
        ApplyAuthorizationHeader(httpRequest);

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

        using var httpRequest = BuildJsonRequest(HttpMethod.Delete, path, body: null);

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

        using var httpRequest = BuildJsonRequest(HttpMethod.Get, path, body: null);

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
    // 헬퍼
    // ══════════════════════════════════════════════════════════════════════

    /// <summary>
    /// JSON 요청 빌더 — 인증 헤더 + (선택) JSON body 부착.
    /// </summary>
    private HttpRequestMessage BuildJsonRequest(HttpMethod method, string relativePath, object? body)
    {
        var httpRequest = new HttpRequestMessage(method, relativePath);
        ApplyAuthorizationHeader(httpRequest);

        if (body is not null)
        {
            var jsonBody = JsonSerializer.Serialize(body, JsonOptions);
            httpRequest.Content = new StringContent(jsonBody, Encoding.UTF8, "application/json");
        }

        return httpRequest;
    }

    /// <summary>
    /// DocUtil 운영자 JWT 또는 ApiKey 를 Authorization: Bearer 헤더로 부착한다.
    /// 우선순위: JwtToken > ApiKey. 둘 다 비어있으면 헤더 미부착(401 발생 시 한국어 예외 매핑).
    /// </summary>
    private void ApplyAuthorizationHeader(HttpRequestMessage request)
    {
        var jwt = _configuration["DocUtil:JwtToken"];
        var apiKey = _configuration["DocUtil:ApiKey"];

        if (!string.IsNullOrWhiteSpace(jwt))
        {
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", jwt);
            return;
        }

        if (!string.IsNullOrWhiteSpace(apiKey))
        {
            // DocUtil 의 ApiKey 검증 미들웨어가 Bearer 또는 X-API-Key 어느 쪽이든 받도록 설계되어 있는 가정.
            // (Phase 7.2 의 AgentHubClient 와 동일 컨벤션 — Bearer 통일).
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);
            return;
        }

        // 토큰 미설정 — 401 이 나면 EnsureSuccessOrThrowKoreanAsync 가 한국어 메시지로 안내한다.
        _logger.LogWarning(
            "DocUtil:JwtToken / DocUtil:ApiKey 모두 미설정 — 운영자 토큰 발급 후 환경변수 / appsettings 에 주입 필요.");
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
}
