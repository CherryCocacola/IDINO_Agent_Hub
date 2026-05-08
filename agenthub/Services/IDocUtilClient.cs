namespace AIAgentManagement.Services;

// ════════════════════════════════════════════════════════════════════════════
// IDocUtilClient — DocUtil RAG/문서 운영 BFF 클라이언트 추상화 (Phase 6.1)
//
// 통합 비전(ADR-2): RAG 단일 권위 = DocUtil. AgentHub 의 자체 KnowledgeBase
// 는 deprecate 되며, 이후 모든 RAG 검색/문서 라이프사이클 호출은 본 인터페이스
// 를 통해 DocUtil FastAPI(/api/v1/*) 로 위임된다.
//
// 호출 흐름:
//   AgentHub Service (RagService / 운영자 KB 콘솔)
//     -> IDocUtilClient.SearchAsync 등
//     -> Named HttpClient "docutil" (Program.cs 등록)
//     -> DocUtil FastAPI /api/v1/{search|documents|chunks}
//
// 인증(.claude/rules/architecture.md P5):
//   AgentHub -> DocUtil 호출은 DocUtil 측이 발급한 운영자 JWT 또는 ApiKey 를
//   IConfiguration["DocUtil:JwtToken"] / "DocUtil:ApiKey" 에서 로드하여
//   Authorization: Bearer {token} 헤더로 부착한다(빈 값이면 401 발생 — 시연 시
//   운영자가 발급 후 환경변수 / appsettings.Development.json 에 주입).
//
// 외부 시그니처(IRagService 등) 변경 없음 — 본 인터페이스는 새로 도입된 BFF
// 합성 지점이며, RagService 내부에서 KnowledgeBaseSource="DocUtil" 분기일 때만
// 호출된다.
// ════════════════════════════════════════════════════════════════════════════

/// <summary>
/// DocUtil(RAG/문서 운영) FastAPI 클라이언트 인터페이스.
/// AgentHub 가 운영자 콘솔 BFF + RAG 라우팅 분기에서 합성한다.
/// 메서드는 7개로 한정 — Phase 6.1 ~ 6.4 의 운영자 시나리오 + Phase 6.2 의 RAG 검색 위임 +
/// 후속 트랙 KB collection dropdown(2026-05-08, AgentBuilder.vue 운영자 폼 UX 개선)에 필요한 최소 집합이다.
/// </summary>
public interface IDocUtilClient
{
    /// <summary>
    /// DocUtil 의 하이브리드 검색(RAG 핵심) — POST /api/v1/search.
    /// AgentHub 의 RagService 가 KnowledgeBaseSource="DocUtil" 인 Agent 를
    /// 만났을 때 자체 임베딩/유사도 계산을 건너뛰고 DocUtil 로 위임한다.
    /// </summary>
    /// <param name="query">사용자 질문(원문). DocUtil 측이 dense+sparse 임베딩 + BM25 합성 검색을 수행.</param>
    /// <param name="collectionRef">Agent.KnowledgeBaseRef 값. DocUtil 의 folder_id 또는 scope_id 로 매핑(미설정 시 글로벌 검색).</param>
    /// <param name="maxResults">상위 결과 개수(기본 10). RagService 의 topK 파라미터를 그대로 위임.</param>
    Task<DocUtilSearchResult> SearchAsync(
        string query,
        string? collectionRef,
        int maxResults = 10,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 목록 — GET /api/v1/documents (운영자 콘솔용).
    /// folder_id / 페이징 파라미터를 그대로 전달한다.
    /// </summary>
    Task<DocUtilDocumentList> ListDocumentsAsync(
        string? collectionRef,
        int page = 1,
        int size = 20,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 상세 — GET /api/v1/documents/{id}.
    /// 404 응답은 null 로 정규화한다(NotFoundException 미사용 — 호출자 분기 단순화).
    /// </summary>
    Task<DocUtilDocumentDetail?> GetDocumentAsync(
        string documentId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 업로드 — POST /api/v1/documents/upload (multipart/form-data).
    /// AgentHub 운영자가 Vue 콘솔에서 파일을 업로드하면 본 메서드로 위임된다.
    /// fileStream 은 호출자(Controller) 가 소유 — 본 클라이언트는 Read 만 한다(자동 Dispose 금지).
    /// </summary>
    Task<DocUtilUploadResult> UploadDocumentAsync(
        Stream fileStream,
        string fileName,
        string? collectionRef,
        string? visibility = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 삭제 — DELETE /api/v1/documents/{id}.
    /// DocUtil 측이 원본 + 청크 + Qdrant 인덱스 모두 정리한다(204 응답).
    /// </summary>
    Task DeleteDocumentAsync(
        string documentId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 청크 목록 — GET /api/v1/documents/{id}/chunks (운영자 콘솔용).
    /// 청크별 임베딩 결과 검수 / 인덱싱 디버깅에 사용.
    /// </summary>
    Task<List<DocUtilChunk>> GetChunksAsync(
        string documentId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// DocUtil 컬렉션(=projects) 카탈로그 — GET /api/v1/projects.
    ///
    /// 통합 비전 매핑(ADR-2):
    ///   DocUtil 의 `projects` 엔티티 = AgentHub 의 `KnowledgeBase collection` 추상.
    ///   AgentHub 운영자 콘솔(AgentBuilder.vue) 의 `Agent.KnowledgeBaseRef` 필드는
    ///   DocUtil 의 project id(UUID) 를 그대로 저장한다. 본 메서드는 운영자가 ID 를
    ///   수동 입력하지 않고 dropdown 에서 선택할 수 있도록 카탈로그를 제공한다.
    ///
    /// BFF 표면 단순화:
    ///   DocUtil 응답의 organization_id / created_by / created_at / updated_at /
    ///   allow_original_download 등 내부 메타는 의도적으로 비노출. 운영자 dropdown
    ///   UX 에 필요한 3 필드(id/name/description) 만 표면화하여 향후 DocUtil schema
    ///   변경 시 AgentHub 측 영향 면적을 최소화한다.
    ///
    /// 캐시 전략:
    ///   본 트랙에서는 캐시 미적용 — collection 카탈로그는 자주 변경되지 않으나
    ///   운영자가 DocUtil 콘솔에서 새 project 를 생성한 직후 드롭다운에 즉시 반영되어야
    ///   하므로 매 호출 fresh 응답을 우선한다(향후 트랙: version-key 패턴 도입 검토).
    /// </summary>
    /// <param name="page">DocUtil 페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 50, DocUtil 측 자체 한도 적용 — 200 이하 권장).</param>
    Task<List<DocUtilCollection>> ListCollectionsAsync(
        int page = 1,
        int size = 50,
        CancellationToken cancellationToken = default);
}

// ── DocUtil DTO (FastAPI 응답 1:1 매핑, snake_case 직렬화는 DocUtilClient 에서 처리) ──

/// <summary>하이브리드 검색 응답.</summary>
/// <param name="Results">검색 결과 배열(score 내림차순).</param>
/// <param name="TotalTime">DocUtil 측 검색 소요(초).</param>
/// <param name="Metadata">DocUtil 의 검색 메타(쿼리 임베딩 hash 등) — pass-through.</param>
public sealed record DocUtilSearchResult(
    DocUtilSearchHit[] Results,
    double TotalTime,
    object? Metadata);

/// <summary>단일 검색 결과.</summary>
/// <param name="Id">DocUtil 청크 식별자(string — DocUtil 측은 UUID 또는 정수문자열).</param>
/// <param name="Content">청크 본문.</param>
/// <param name="Score">유사도 점수(높을수록 관련 — DocUtil hybrid score).</param>
/// <param name="Metadata">청크 메타(document_id, page, source 등) — DocUtil 측 schema pass-through.</param>
public sealed record DocUtilSearchHit(
    string Id,
    string Content,
    double Score,
    object? Metadata);

/// <summary>문서 목록 응답.</summary>
public sealed record DocUtilDocumentList(
    DocUtilDocumentSummary[] Items,
    long Total,
    int Page,
    int Size);

/// <summary>문서 목록 한 행.</summary>
public sealed record DocUtilDocumentSummary(
    string Id,
    string Name,
    string Status,
    DateTime? CreatedAt);

/// <summary>문서 상세.</summary>
public sealed record DocUtilDocumentDetail(
    string Id,
    string Name,
    string Status,
    DateTime? CreatedAt,
    string? UploaderName,
    object? VisibilityTargets);

/// <summary>업로드 응답(비동기 인덱싱 시 JobId 가 동반).</summary>
public sealed record DocUtilUploadResult(
    string Id,
    string Name,
    string Status,
    string? JobId);

/// <summary>청크 한 건.</summary>
public sealed record DocUtilChunk(
    string ChunkId,
    string Content,
    int ChunkIndex,
    object? Metadata);

/// <summary>
/// DocUtil 컬렉션(projects) 카탈로그 한 행 — AgentBuilder dropdown UX 용.
/// 운영자가 ID(UUID) 를 수동 입력하지 않고 collection 을 선택할 수 있도록 BFF 표면화.
/// DocUtil 내부 메타(organization_id / created_by / timestamps / allow_original_download 등)는
/// 의도적으로 비노출하여 schema 변경 시 영향 면적 최소화.
/// </summary>
/// <param name="Id">DocUtil project UUID. AgentHub 의 Agent.KnowledgeBaseRef 에 그대로 저장.</param>
/// <param name="Name">사용자 표기명(예: "부산대"). dropdown option 라벨로 사용.</param>
/// <param name="Description">선택 설명(없으면 null). dropdown option 의 hover hint(:title) 로 사용.</param>
public sealed record DocUtilCollection(
    string Id,
    string Name,
    string? Description);
