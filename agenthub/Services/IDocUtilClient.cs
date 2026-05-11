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

    // ── Phase 10.1a (2026-05-10): DocUtil 사용자 운영자 BFF — 4 메서드 ────
    //
    // 통합 비전 매핑(P1 Control Plane / P5 인증):
    //   AgentHub 운영자 콘솔이 DocUtil 사용자 카탈로그를 단일 진입점에서 관리한다.
    //   DocUtil 의 사용자 라이프사이클(목록/상세/상태 토글/삭제) 을 BFF 표면화하여
    //   운영자가 DocUtil 콘솔에 별도 로그인하지 않아도 된다.
    //
    // 인증/권한:
    //   - AgentHub 측: [Authorize(Roles="Admin,SuperAdmin")] 게이트 (Controller 레벨)
    //   - DocUtil 측: IDocUtilTokenProvider 의 4단계 폴백으로 운영자 JWT 자동 부착
    //   - org_id 는 GetOrganizationIdAsync() 가 자동 추출 — 호출자 무관여
    //
    // 데이터 소스: DocUtil schema 캡처(2026-05-10) 결과:
    //   GET /api/v1/users?org_id={uuid}&page&size&role&status&search → UserListResponse
    //   GET /api/v1/users/{user_id} → UserResponse
    //   PUT /api/v1/users/{user_id}/status body {status: "active|inactive|locked"} → UserResponse
    //   DELETE /api/v1/users/{user_id} → 204
    //
    // BFF 표면 단순화:
    //   UserResponse 의 organization_id / language / last_login_at 은 운영자 콘솔 UX 에
    //   필요하므로 모두 노출. UserResponse 의 모든 필드를 record DocUtilUserSummary /
    //   DocUtilUserDetail 에 1:1 매핑 (department_id 도 보존 — 향후 10.1b Departments 트랙
    //   에서 부서명 조인할 예정).

    /// <summary>
    /// 사용자 목록 — GET /api/v1/users (운영자 콘솔용).
    /// <para>
    /// org_id 는 IDocUtilTokenProvider.GetOrganizationIdAsync 로 자동 추출되어
    /// 호출자(Controller) 가 직접 다루지 않는다.
    /// </para>
    /// </summary>
    /// <param name="page">DocUtil 페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 20, DocUtil 한도 1~100).</param>
    /// <param name="role">role 필터(선택, 예: "admin", "member").</param>
    /// <param name="status">status 필터(선택, 예: "active", "inactive", "locked").</param>
    /// <param name="search">username/email LIKE 검색(선택).</param>
    Task<DocUtilUserList> ListUsersAsync(
        int page = 1,
        int size = 20,
        string? role = null,
        string? status = null,
        string? search = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 사용자 상세 — GET /api/v1/users/{user_id}.
    /// 404 응답은 null 로 정규화한다(NotFoundException 미사용 — 호출자 분기 단순화).
    /// </summary>
    Task<DocUtilUserDetail?> GetUserAsync(
        string userId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 사용자 상태 변경 — PUT /api/v1/users/{user_id}/status.
    /// <para>
    /// status 값은 DocUtil 측이 검증("active" | "inactive" | "locked"). 그 외 값은 422.
    /// </para>
    /// 응답은 변경 후의 UserResponse — 호출자가 변경 결과를 즉시 표시할 수 있다.
    /// </summary>
    Task<DocUtilUserDetail> UpdateUserStatusAsync(
        string userId,
        string status,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 사용자 삭제 — DELETE /api/v1/users/{user_id}.
    /// <para>
    /// DocUtil 측이 영구 삭제(204). 본 메서드는 성공 시 반환값 없음, 실패 시 InvalidOperationException.
    /// </para>
    /// </summary>
    Task DeleteUserAsync(
        string userId,
        CancellationToken cancellationToken = default);

    // ── Phase 10.1b (2026-05-10): DocUtil 조직/부서/할당량 운영자 BFF — 9 메서드 ──
    //
    // 통합 비전 매핑(P1 Control Plane / P5 인증):
    //   AgentHub 운영자 콘솔이 DocUtil 의 조직 메타 / 부서 트리 / 월 할당량까지
    //   단일 진입점에서 관리한다. 10.1a 의 사용자 트랙과 같은 BFF 패턴을 그대로
    //   적용 — 운영자가 DocUtil 콘솔에 별도 로그인하지 않아도 됨.
    //
    // 인증/권한 / org_id 자동 부착:
    //   - AgentHub 측: [Authorize(Roles="Admin,SuperAdmin")] 게이트 (Controller 레벨)
    //   - DocUtil 측: IDocUtilTokenProvider 4단계 폴백 + GetOrganizationIdAsync()
    //   - 따라서 본 인터페이스의 메서드는 orgId 를 파라미터로 받지 않는다(자동 추출).
    //
    // 데이터 소스: DocUtil OpenAPI 캡처(2026-05-10) + 직접 호출 응답 검증:
    //   GET    /api/v1/organizations/{org_id}                                   → OrganizationResponse
    //   PUT    /api/v1/organizations/{org_id}                                   → OrganizationResponse
    //   GET    /api/v1/organizations/{org_id}/departments                       → List<DepartmentResponse>
    //   POST   /api/v1/organizations/{org_id}/departments                       → DepartmentResponse(201)
    //   PUT    /api/v1/organizations/{org_id}/departments/{dept_id}             → DepartmentResponse
    //   DELETE /api/v1/organizations/{org_id}/departments/{dept_id}             → 204
    //   GET    /api/v1/organizations/{org_id}/departments/{dept_id}/members     → List(free-form: id/username/email/role)
    //   GET    /api/v1/organizations/{org_id}/quotas/current                    → OrganizationQuotasCurrentResponse
    //   PUT    /api/v1/organizations/{org_id}/quotas/{quota_type}               → QuotaStatusResponse
    //
    // BFF 표면 단순화 / 표면 매핑:
    //   - DepartmentResponse 는 path / depth 까지 보존(트리 들여쓰기 UX 용).
    //   - DepartmentCreate 는 name + parent_id (DocUtil schema 가 description 필드 미보유 — 추정 금지).
    //   - QuotaStatusResponse 는 4 정수 필드 + quota_type/year_month 를 모두 보존.
    //   - OrganizationQuotasCurrentResponse.quotas 는 map(quota_type → QuotaStatusResponse).
    //     운영자 UI 가 dropdown 형태로 dalle_monthly / unsplash_monthly 를 분리 표시할 수 있도록
    //     Dictionary 가 아닌 List<DocUtilOrganizationQuotaStatus> 로 평탄화한다.

    /// <summary>
    /// 조직 정보 조회 — GET /api/v1/organizations/{org_id}.
    /// <para>org_id 는 IDocUtilTokenProvider.GetOrganizationIdAsync 로 자동 추출.</para>
    /// 404 응답은 null 로 정규화한다(빈 organization 토큰 폴백 시나리오 대비).
    /// </summary>
    Task<DocUtilOrganization?> GetOrganizationAsync(
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 조직 정보 수정 — PUT /api/v1/organizations/{org_id}.
    /// <para>요청 body: {name?, description?, settings?} (모두 nullable, partial update).</para>
    /// 응답은 변경 후의 OrganizationResponse — 호출자가 즉시 반영.
    /// </summary>
    Task<DocUtilOrganization> UpdateOrganizationAsync(
        DocUtilUpdateOrganizationRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 부서 목록 조회 — GET /api/v1/organizations/{org_id}/departments.
    /// <para>
    /// DocUtil 응답은 평탄한 List 이며 path/depth 컬럼으로 트리 위치를 표현한다.
    /// children 필드는 본 endpoint 에 없음(DepartmentTreeResponse 별도) — 현재 트랙에선
    /// 평탄 List 응답을 그대로 반환하고 클라이언트에서 path 기반으로 정렬/들여쓰기.
    /// </para>
    /// </summary>
    Task<List<DocUtilDepartment>> ListDepartmentsAsync(
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 부서 생성 — POST /api/v1/organizations/{org_id}/departments.
    /// <para>요청 body: {name, parent_id?} — DocUtil schema 가 description 필드 미보유.</para>
    /// 응답은 생성된 DepartmentResponse(201).
    /// </summary>
    Task<DocUtilDepartment> CreateDepartmentAsync(
        DocUtilCreateDepartmentRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 부서 수정 — PUT /api/v1/organizations/{org_id}/departments/{dept_id}.
    /// <para>요청 body: {name?, parent_id?} (partial update — DocUtil schema 보존).</para>
    /// </summary>
    Task<DocUtilDepartment> UpdateDepartmentAsync(
        string departmentId,
        DocUtilUpdateDepartmentRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 부서 삭제 — DELETE /api/v1/organizations/{org_id}/departments/{dept_id}.
    /// <para>DocUtil 측이 영구 삭제(204). 본 메서드는 성공 시 반환값 없음.</para>
    /// </summary>
    Task DeleteDepartmentAsync(
        string departmentId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 부서 멤버 조회 — GET /api/v1/organizations/{org_id}/departments/{dept_id}/members.
    /// <para>
    /// DocUtil 응답은 free-form list — 캡처한 실제 응답에서 id/username/email/role 4 필드 확인.
    /// 본 인터페이스는 안정성 우선으로 4 필드만 노출(추가 필드는 DocUtil 측 변경 시에 대응).
    /// </para>
    /// </summary>
    Task<List<DocUtilDepartmentMember>> GetDepartmentMembersAsync(
        string departmentId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 조직 월 할당량 현황 — GET /api/v1/organizations/{org_id}/quotas/current.
    /// <para>
    /// DocUtil 응답: { organization_id, year_month, quotas: {quota_type → QuotaStatusResponse} }.
    /// 본 메서드는 quotas map 을 List 로 평탄화하여 운영자 UI 의 표 표시를 단순화.
    /// </para>
    /// </summary>
    Task<DocUtilOrganizationQuotaCurrent> GetOrganizationQuotaAsync(
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 조직 월 할당량 한도 조정 — PUT /api/v1/organizations/{org_id}/quotas/{quota_type}.
    /// <para>요청 body: {monthly_limit: int (>=0)} — 음수 = DB CHECK 위반(422).</para>
    /// 응답은 변경된 QuotaStatusResponse — 호출자가 UI 즉시 반영.
    /// </summary>
    Task<DocUtilOrganizationQuotaStatus> UpdateOrganizationQuotaAsync(
        string quotaType,
        DocUtilUpdateQuotaRequest request,
        CancellationToken cancellationToken = default);

    // ── Phase 10.1c (2026-05-10): DocUtil 프로젝트/보드 운영자 BFF — 13 메서드 ──
    //
    // 통합 비전 매핑(P1 Control Plane / P5 인증 / R2 단일 진입점):
    //   AgentHub 운영자 콘솔이 DocUtil 의 프로젝트(=collection) 카탈로그 + 멤버십 +
    //   부서 매핑 + 보드(KB collection 내부 권한 단위) 를 모두 단일 진입점에서 관리.
    //   10.1a/10.1b 와 동일 BFF 패턴으로 운영자가 DocUtil 콘솔 별도 로그인 불필요.
    //
    // 기존 ListCollectionsAsync 보존(294e8a6 commit, AgentBuilder.vue dropdown UX 의존):
    //   - 시그니처 / 동작 / 캐시 prefix `du:c:` / 응답 형태(BFF 단순화 3 필드) 모두 동일 유지.
    //   - 본 트랙의 프로젝트 운영 메서드는 별도 이름(`ListProjectsAsync` 등) 으로 추가.
    //   - 운영자가 본 화면에서 프로젝트 mutation 시 Controller 가
    //     IncrementVersionAsync("docutil-collections") 호출 → ListCollectionsAsync 의 캐시(`du:c:`)
    //     도 자연 무효화(통합 namespace 효과 — AgentBuilder dropdown 즉시 신규 프로젝트 노출).
    //
    // 데이터 소스: DocUtil OpenAPI 캡처(2026-05-10) + 13 endpoint 직접 호출 검증:
    //   GET    /api/v1/projects?page=&size=&search=                       → ProjectListResponse
    //   POST   /api/v1/projects                                             → ProjectResponse(201)
    //   GET    /api/v1/projects/tree                                        → List(free-form: id/name/boards[])
    //   GET    /api/v1/projects/{pid}                                       → ProjectResponse
    //   PUT    /api/v1/projects/{pid}                                       → ProjectResponse
    //   DELETE /api/v1/projects/{pid}                                       → 204
    //   GET    /api/v1/projects/{pid}/members                               → List(free-form: id/username/email/role)
    //   GET    /api/v1/projects/{pid}/departments                           → List(free-form: id/name/path/depth)
    //   GET    /api/v1/projects/{pid}/boards                                → BoardListResponse
    //   POST   /api/v1/projects/{pid}/boards                                → BoardResponse(201)
    //   GET    /api/v1/projects/{pid}/boards/{bid}                          → BoardResponse
    //   PUT    /api/v1/projects/{pid}/boards/{bid}                          → BoardResponse
    //   DELETE /api/v1/projects/{pid}/boards/{bid}                          → 204
    //
    // BFF 표면 매핑 정확도(추정 금지 — 실제 OpenAPI + 응답 캡처 일치):
    //   - DocUtilProject: 8 필드(Id/Name/Description?/AllowOriginalDownload/OrganizationId/CreatedBy/CreatedAt/UpdatedAt)
    //   - DocUtilCreateProjectRequest: Name + Description? + AllowOriginalDownload? (default true) — POST 만
    //   - DocUtilUpdateProjectRequest: Name? + Description? — DocUtil schema 가 update 엔 allow_original_download 미보유
    //   - DocUtilBoard: 7 필드(Id/ProjectId/Name/Description?/CreatedBy/CreatedAt/UpdatedAt) — NO folder_id
    //   - DocUtilCreateBoardRequest / DocUtilUpdateBoardRequest: Name + Description? 만 (DocUtil schema 가 folder_id 미보유)
    //   - DocUtilProjectTreeNode: free-form {id, name, boards: []} — depth 없음, children 없음(boards 만)
    //   - DocUtilProjectMember: free-form {id, username, email, role} (DepartmentMember 와 동일 형태이나 record 별도 정의 — 의미 분리)
    //   - DocUtilProjectDepartment: free-form {id, name, path, depth} (DepartmentResponse 와 다름 — 4 필드만)

    /// <summary>
    /// 프로젝트 목록 조회(페이징) — GET /api/v1/projects.
    /// </summary>
    /// <param name="page">DocUtil 페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 20, DocUtil 한도 1~200).</param>
    /// <param name="search">name/description LIKE 검색(선택).</param>
    Task<DocUtilProjectList> ListProjectsAsync(
        int page = 1,
        int size = 20,
        string? search = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 프로젝트 트리 — GET /api/v1/projects/tree.
    /// <para>
    /// DocUtil 응답: List of {id, name, boards: BoardResponse[]}.
    /// 프로젝트는 부모-자식 관계 없음 — 트리는 프로젝트 → 보드 의 2단계 평면.
    /// </para>
    /// </summary>
    Task<List<DocUtilProjectTreeNode>> GetProjectTreeAsync(
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 프로젝트 상세 조회 — GET /api/v1/projects/{project_id}.
    /// 404 응답은 null 로 정규화한다.
    /// </summary>
    Task<DocUtilProject?> GetProjectAsync(
        string projectId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 프로젝트 생성 — POST /api/v1/projects.
    /// <para>요청 body: {name, description?, allow_original_download?(default true)}.</para>
    /// 응답은 생성된 ProjectResponse(201).
    /// </summary>
    Task<DocUtilProject> CreateProjectAsync(
        DocUtilCreateProjectRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 프로젝트 수정 — PUT /api/v1/projects/{project_id}.
    /// <para>요청 body: {name?, description?} — DocUtil ProjectUpdate schema 에는 allow_original_download 미존재.</para>
    /// </summary>
    Task<DocUtilProject> UpdateProjectAsync(
        string projectId,
        DocUtilUpdateProjectRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 프로젝트 삭제 — DELETE /api/v1/projects/{project_id}.
    /// <para>DocUtil 측이 영구 삭제(204). 본 메서드는 성공 시 반환값 없음.</para>
    /// </summary>
    Task DeleteProjectAsync(
        string projectId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 프로젝트 멤버 조회 — GET /api/v1/projects/{project_id}/members.
    /// <para>DocUtil free-form 응답에서 4 필드(id/username/email/role) 안정적으로 노출.</para>
    /// </summary>
    Task<List<DocUtilProjectMember>> GetProjectMembersAsync(
        string projectId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 프로젝트 참여 부서 조회 — GET /api/v1/projects/{project_id}/departments.
    /// <para>DocUtil free-form 응답에서 4 필드(id/name/path/depth) 안정적으로 노출.</para>
    /// </summary>
    Task<List<DocUtilProjectDepartment>> GetProjectDepartmentsAsync(
        string projectId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 프로젝트의 보드 목록 — GET /api/v1/projects/{project_id}/boards.
    /// <para>BoardListResponse 페이지네이션 응답을 그대로 BFF 표면화.</para>
    /// </summary>
    Task<DocUtilBoardList> ListProjectBoardsAsync(
        string projectId,
        int page = 1,
        int size = 50,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 보드 생성 — POST /api/v1/projects/{project_id}/boards.
    /// </summary>
    Task<DocUtilBoard> CreateProjectBoardAsync(
        string projectId,
        DocUtilCreateBoardRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 보드 상세 조회 — GET /api/v1/projects/{project_id}/boards/{board_id}.
    /// <para>404 응답은 null 로 정규화한다.</para>
    /// </summary>
    Task<DocUtilBoard?> GetProjectBoardAsync(
        string projectId,
        string boardId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 보드 수정 — PUT /api/v1/projects/{project_id}/boards/{board_id}.
    /// </summary>
    Task<DocUtilBoard> UpdateProjectBoardAsync(
        string projectId,
        string boardId,
        DocUtilUpdateBoardRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 보드 삭제 — DELETE /api/v1/projects/{project_id}/boards/{board_id}.
    /// <para>DocUtil 측이 영구 삭제(204).</para>
    /// </summary>
    Task DeleteProjectBoardAsync(
        string projectId,
        string boardId,
        CancellationToken cancellationToken = default);

    // ── Phase 10.2a (2026-05-10): DocUtil Dashboard + Audit BFF — 7 메서드 ──
    //
    // 통합 비전 매핑(P1 Control Plane):
    //   AgentHub 운영자가 DocUtil 의 운영 모니터링(대시보드 5종) + 감사 로그(2종) 까지
    //   단일 진입점에서 확인. Phase 10.1 의 사용자/조직/부서/할당량/프로젝트 트랙과
    //   같은 BFF 패턴(IDocUtilTokenProvider 4단계 폴백 + 한국어 502 매핑) 그대로 적용.
    //
    // 인증/권한:
    //   - AgentHub 측: [Authorize(Roles="Admin,SuperAdmin")] 게이트(Controller 레벨)
    //   - DocUtil 측: IDocUtilTokenProvider 가 운영자 JWT 자동 부착(token 의 org claim 으로 응답 자동 scope)
    //
    // 데이터 소스: DocUtil OpenAPI 캡처(2026-05-10) 결과:
    //   GET /api/v1/dashboard/metrics → DashboardMetrics
    //   GET /api/v1/dashboard/response-times?period={...} → ResponseTimeData
    //   GET /api/v1/dashboard/search-errors?period={...} → SearchErrorData
    //   GET /api/v1/dashboard/search-usage?period={...} → SearchUsageStats
    //   GET /api/v1/dashboard/upload-status → UploadStatusChart
    //   GET /api/v1/audit-logs?page=&size=&action=&resource_type=&user_id=&start_date=&end_date= → AuditLogListResponse
    //   GET /api/v1/audit-logs/export?action=&resource_type=&user_id=&start_date=&end_date= → text/csv binary stream
    //
    // BFF 표면 매핑 정확도(추정 금지 — OpenAPI 캡처 + 실 호출 응답 일치):
    //   - DocUtilDashboardMetrics: total_users/active_users/total_documents/total_searches + feature_usage(dict)
    //   - DocUtilResponseTimes: timestamps[] + values[] 평행 배열(시계열) — period 미지정 시 빈 배열, "7d" 등 가능
    //   - DocUtilSearchErrors: dates[] + error_counts[] 평행 배열(일별)
    //   - DocUtilSearchUsage: total_requests/total_responses/total_failures + period(label)
    //   - DocUtilUploadStatus: completed/processing/waiting/error 4 필드(default 0)
    //   - DocUtilAuditLogList: items + total + page + size
    //   - DocUtilAuditLogEntry: id/organization_id/user_id?/action/resource_type/resource_id?/details(dict)?/ip_address?/created_at
    //     (DocUtil 의 user_agent 필드는 schema 미존재 — 추정 금지 원칙 따라 미포함)
    //   - 감사 로그 export: text/csv 응답 — Stream + content-type/filename 메타 동반 record 반환

    /// <summary>
    /// 대시보드 요약 메트릭 — GET /api/v1/dashboard/metrics.
    /// <para>운영자 콘솔의 KPI 카드(총 사용자/활성 사용자/총 문서/총 검색)에 바로 사용.</para>
    /// </summary>
    Task<DocUtilDashboardMetrics> GetDashboardMetricsAsync(
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 시간별 평균 응답시간 시계열 — GET /api/v1/dashboard/response-times.
    /// <para>period 가 null/빈 문자열이면 DocUtil 기본(빈 배열). "7d" / "24h" 등.</para>
    /// </summary>
    Task<DocUtilResponseTimes> GetDashboardResponseTimesAsync(
        string? period = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 일별 검색 오류 카운트 — GET /api/v1/dashboard/search-errors.
    /// </summary>
    Task<DocUtilSearchErrors> GetDashboardSearchErrorsAsync(
        string? period = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 검색 사용량 통계 — GET /api/v1/dashboard/search-usage.
    /// <para>period 라벨(예: "7d")로 집계 기간을 명시. 응답에는 그 라벨이 포함됨.</para>
    /// </summary>
    Task<DocUtilSearchUsage> GetDashboardSearchUsageAsync(
        string? period = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 업로드 상태 분포 — GET /api/v1/dashboard/upload-status.
    /// </summary>
    Task<DocUtilUploadStatus> GetDashboardUploadStatusAsync(
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 감사 로그 목록(페이징 + 필터) — GET /api/v1/audit-logs.
    /// </summary>
    /// <param name="page">DocUtil 페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 50, DocUtil 한도 1~200).</param>
    /// <param name="action">action 정확 일치 필터(예: "auth.login").</param>
    /// <param name="resourceType">resource_type 정확 일치 필터(예: "auth").</param>
    /// <param name="userId">user_id(UUID) 정확 일치 필터.</param>
    /// <param name="startDate">시작 시각(ISO-8601 UTC, 포함).</param>
    /// <param name="endDate">종료 시각(ISO-8601 UTC, 포함).</param>
    Task<DocUtilAuditLogList> ListAuditLogsAsync(
        int page = 1,
        int size = 50,
        string? action = null,
        string? resourceType = null,
        string? userId = null,
        DateTime? startDate = null,
        DateTime? endDate = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 감사 로그 CSV 내보내기 — GET /api/v1/audit-logs/export.
    /// <para>
    /// 응답은 text/csv binary stream. 호출자는 받은 Stream 을 그대로 클라이언트로 흘려보내야 한다.
    /// (Content-Type / Content-Disposition 헤더는 DocUtilAuditExport 안에 캡처되어 같이 전달).
    /// </para>
    /// </summary>
    Task<DocUtilAuditExport> ExportAuditLogsAsync(
        string? action = null,
        string? resourceType = null,
        string? userId = null,
        DateTime? startDate = null,
        DateTime? endDate = null,
        CancellationToken cancellationToken = default);

    // ── Phase 10.2b (2026-05-10): DocUtil Search Scopes + Evaluation 운영자 BFF — 15 메서드 ──
    //
    // 통합 비전 매핑(P1 Control Plane / P5 인증 / R2 단일 진입점 / P8 RAG 단일 권위):
    //   AgentHub 운영자 콘솔이 DocUtil 의 검색 범위(Search Scopes — 프로젝트/보드/폴더 단위
    //   RAG 튜닝 + Chatbot/QA/Keyword/Agent 4 기능 토글) + 평가(Evaluation — 4개 가중치
    //   설정 / 평가 실행 / 로그 / 트렌드) 까지 단일 진입점에서 관리. Phase 10.1/10.2a 와
    //   동일 BFF 패턴(IDocUtilTokenProvider 4단계 폴백 + 한국어 502 매핑) 적용.
    //
    // 인증/권한:
    //   - AgentHub 측: [Authorize(Roles="Admin,SuperAdmin")] 게이트(Controller 레벨)
    //   - DocUtil 측: IDocUtilTokenProvider 가 운영자 JWT 자동 부착(token 의 org claim 으로
    //     응답 자동 scope — Search Scopes 도 organization 단위로 자동 격리됨).
    //
    // 데이터 소스: DocUtil OpenAPI 캡처(2026-05-10) 결과:
    //   GET    /api/v1/search-scopes?page=&size=                                → SearchScopeListResponse
    //   POST   /api/v1/search-scopes                                            → SearchScopeResponse(201)
    //   GET    /api/v1/search-scopes/locations?location_type=                   → List<LocationOption>  (location_type 필수)
    //   GET    /api/v1/search-scopes/options                                    → List<SearchScopeOption>
    //   GET    /api/v1/search-scopes/{scope_id}                                 → SearchScopeResponse
    //   PUT    /api/v1/search-scopes/{scope_id}                                 → SearchScopeResponse
    //   DELETE /api/v1/search-scopes/{scope_id}                                 → 204
    //   PUT    /api/v1/search-scopes/{scope_id}/environment                     → SearchScopeResponse
    //   GET    /api/v1/search-scopes/{scope_id}/valid-id                        → object (free-form, 응답 schema 미정의)
    //
    //   GET    /api/v1/evaluation/config                                        → EvaluationConfigResponse
    //   PUT    /api/v1/evaluation/config                                        → EvaluationConfigResponse
    //   GET    /api/v1/evaluation/logs?page=&size=&run_id=&run_type=&...        → EvaluationLogListResponse
    //   GET    /api/v1/evaluation/questions                                     → object (free-form dict)
    //   POST   /api/v1/evaluation/run                                           → object (202, free-form: task_id 등)
    //   GET    /api/v1/evaluation/runs?limit=                                   → EvaluationRunListResponse
    //   GET    /api/v1/evaluation/trend?days=                                   → EvaluationTrendResponse
    //
    // BFF 표면 매핑 정확도(추정 금지 — OpenAPI 캡처 + 실 호출 응답 일치):
    //   - DocUtilSearchScopeSummary/Detail: 24 필드(SearchScopeResponse 1:1) — id/name/description/
    //     organization_id/created_by/project_id?/board_id?/folder_id?/location_path?/chatbot_enabled/
    //     chatbot_faq_template?/qa_enabled/qa_prompt_template?/qa_llm_model?/keyword_search_enabled/
    //     agent_enabled/chunk_size/chunk_overlap/title_weight/keyword_weight/content_weight/
    //     max_results/similarity_threshold/created_at/updated_at
    //   - DocUtilCreateScopeRequest: name(필수) + description? + project_id?/board_id?/folder_id? +
    //     모든 환경 설정 nullable (DocUtil 측 default 적용)
    //   - DocUtilUpdateScopeRequest: 모든 필드 nullable (partial update)
    //   - DocUtilUpdateScopeEnvironmentRequest: 13 환경 설정(default 값 OpenAPI 와 일치)
    //   - DocUtilSearchScopeOption: 3 필드(id/name/location_path?) — 드롭다운 셀렉터용
    //   - DocUtilLocationOption: 4 필드(id/name/type/path?)
    //   - DocUtilSearchScopeValidIdResponse: 응답 schema 미정의 → free-form dict 로 노출
    //
    //   - DocUtilEvaluationConfig: 6 필드(id/organization_id + 4개 weight)
    //   - DocUtilUpdateEvaluationConfigRequest: 4 weight (모두 0~1, default 값 OpenAPI 일치)
    //   - DocUtilEvaluationLogEntry: 17 필드 (composite_score 포함, contexts/judge_details 는 free-form)
    //   - DocUtilEvaluationRunSummary: 10 필드(run_id/run_type/created_at + question_count + 5 avg + hallucination_count)
    //   - DocUtilEvaluationTrendPoint: 6 필드(date + 5 avg)
    //   - DocUtilRunEvaluationRequest: questions[]?(optional — null/미지정 시 default 질문 셋 사용)
    //   - DocUtilEvaluationRunResponse: free-form (DocUtil 의 202 응답이 schema 미정의 — task_id 등을 dict 로 보존)

    /// <summary>
    /// 검색 범위 목록 — GET /api/v1/search-scopes (페이징).
    /// <para>운영자 콘솔의 검색범위 카탈로그 표시용. organization 단위 자동 scope.</para>
    /// </summary>
    /// <param name="page">DocUtil 페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 20, DocUtil 한도 1~100).</param>
    Task<DocUtilSearchScopeList> ListSearchScopesAsync(
        int page = 1,
        int size = 20,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 검색 범위 옵션 목록(드롭다운용) — GET /api/v1/search-scopes/options.
    /// <para>3 필드(id/name/location_path?) 만 포함된 가벼운 응답.</para>
    /// </summary>
    Task<List<DocUtilSearchScopeOption>> ListSearchScopeOptionsAsync(
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 위치 카탈로그(검색 범위 할당 가능한 프로젝트/보드/폴더) — GET /api/v1/search-scopes/locations.
    /// <para>
    /// location_type 은 DocUtil 측 필수 query parameter — "project" | "board" | "folder".
    /// 운영자가 새 검색 범위 만들 때 어느 단위로 할당할지 선택하기 위한 카탈로그.
    /// </para>
    /// </summary>
    /// <param name="locationType">"project" | "board" | "folder" (DocUtil 422 위험 — 검증 후 호출).</param>
    Task<List<DocUtilLocationOption>> ListSearchScopeLocationsAsync(
        string locationType,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 검색 범위 상세 — GET /api/v1/search-scopes/{scope_id}.
    /// 404 응답은 null 로 정규화한다.
    /// </summary>
    Task<DocUtilSearchScopeDetail?> GetSearchScopeAsync(
        string scopeId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 검색 범위 생성 — POST /api/v1/search-scopes.
    /// <para>최소 필드 name(필수). 위치는 project_id / board_id / folder_id 중 하나(선택).</para>
    /// 응답은 생성된 SearchScopeResponse(201).
    /// </summary>
    Task<DocUtilSearchScopeDetail> CreateSearchScopeAsync(
        DocUtilCreateScopeRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 검색 범위 수정 — PUT /api/v1/search-scopes/{scope_id} (partial update).
    /// </summary>
    Task<DocUtilSearchScopeDetail> UpdateSearchScopeAsync(
        string scopeId,
        DocUtilUpdateScopeRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 검색 범위 삭제 — DELETE /api/v1/search-scopes/{scope_id}.
    /// </summary>
    Task DeleteSearchScopeAsync(
        string scopeId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 검색 범위 환경 설정 — PUT /api/v1/search-scopes/{scope_id}/environment.
    /// <para>chunk_size/chunk_overlap/weights/max_results/similarity_threshold + 4 기능 토글.</para>
    /// </summary>
    Task<DocUtilSearchScopeDetail> UpdateSearchScopeEnvironmentAsync(
        string scopeId,
        DocUtilUpdateScopeEnvironmentRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 검색 범위 valid-id 조회 — GET /api/v1/search-scopes/{scope_id}/valid-id.
    /// <para>임베드 위젯의 scope_id 검증용. 응답 schema 가 OpenAPI 미정의 — free-form dict.</para>
    /// </summary>
    Task<DocUtilSearchScopeValidIdResponse> GetSearchScopeValidIdAsync(
        string scopeId,
        CancellationToken cancellationToken = default);

    // ── Evaluation (7) ────────────────────────────────────────────────────

    /// <summary>
    /// 평가 가중치 설정 조회 — GET /api/v1/evaluation/config.
    /// </summary>
    Task<DocUtilEvaluationConfig> GetEvaluationConfigAsync(
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 평가 가중치 설정 수정 — PUT /api/v1/evaluation/config.
    /// <para>4 weight 모두 0~1 범위. DocUtil 측 default: 0.25 / 0.3 / 0.25 / 0.2.</para>
    /// </summary>
    Task<DocUtilEvaluationConfig> UpdateEvaluationConfigAsync(
        DocUtilUpdateEvaluationConfigRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 평가 로그 목록(페이징 + 필터) — GET /api/v1/evaluation/logs.
    /// </summary>
    /// <param name="page">DocUtil 페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 20, DocUtil 한도 1~100).</param>
    /// <param name="runId">특정 run 의 로그만 조회.</param>
    /// <param name="runType">run_type 정확 일치 필터.</param>
    /// <param name="hasHallucination">hallucination 발생 여부 필터.</param>
    /// <param name="minScore">composite_score 최소값(0~1).</param>
    /// <param name="maxScore">composite_score 최대값(0~1).</param>
    Task<DocUtilEvaluationLogList> ListEvaluationLogsAsync(
        int page = 1,
        int size = 20,
        string? runId = null,
        string? runType = null,
        bool? hasHallucination = null,
        double? minScore = null,
        double? maxScore = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 기본 평가 질문 목록 — GET /api/v1/evaluation/questions.
    /// <para>응답 schema 가 OpenAPI 에 free-form dict 로 정의 — 그대로 pass-through.</para>
    /// </summary>
    Task<DocUtilEvaluationQuestions> GetEvaluationQuestionsAsync(
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 수동 평가 실행 — POST /api/v1/evaluation/run.
    /// <para>
    /// 응답은 202 Accepted + 비동기 task. questions 가 null/빈 배열이면 DocUtil 의
    /// default 질문 셋 사용. 응답 schema 가 OpenAPI 에 free-form dict 로 정의됨.
    /// </para>
    /// <para>
    /// 주의: 본 메서드는 실제 LLM 호출(평가용 judge LLM)을 트리거할 수 있어 비용/시간
    /// 영향 가능. 운영자는 신중히 사용해야 함.
    /// </para>
    /// </summary>
    Task<DocUtilEvaluationRunResponse> RunEvaluationAsync(
        DocUtilRunEvaluationRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 최근 평가 실행 목록 — GET /api/v1/evaluation/runs.
    /// </summary>
    /// <param name="limit">반환할 run 수(1~100, 기본 30). DocUtil page/size 패턴 미지원, limit 만 사용.</param>
    Task<DocUtilEvaluationRunList> ListEvaluationRunsAsync(
        int limit = 30,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 평가 점수 추이(최근 N일) — GET /api/v1/evaluation/trend.
    /// </summary>
    /// <param name="days">조회 기간(일, 1~365, 기본 30).</param>
    Task<DocUtilEvaluationTrend> GetEvaluationTrendAsync(
        int days = 30,
        CancellationToken cancellationToken = default);

    // ── Phase 10.2c (2026-05-11): DocUtil FAQ + Reports + Templates 운영자 BFF — 14 메서드 ──
    //
    // 통합 비전 매핑(P1 Control Plane / P5 인증 / R2 단일 진입점):
    //   AgentHub 운영자 콘솔이 DocUtil 의 FAQ(질문/답변 카탈로그) + Reports(보고서 생성/이력) +
    //   Report Templates(보고서 템플릿 카탈로그) 까지 단일 진입점에서 운영. Phase 10.1/10.2a/10.2b
    //   와 동일 BFF 패턴.
    //
    // DocUtil OpenAPI 캡처(2026-05-11) 매핑:
    //   FAQ (5):
    //     GET    /api/v1/faq?page&size&scope_id?&category?&q?               → FAQListResponse
    //     POST   /api/v1/faq               (FAQCreate)                       → FAQResponse 201
    //     GET    /api/v1/faq/{faq_id}                                        → FAQResponse
    //     PUT    /api/v1/faq/{faq_id}      (FAQUpdate)                       → FAQResponse
    //     DELETE /api/v1/faq/{faq_id}                                        → 204
    //   Reports (5):
    //     GET    /api/v1/reports?page&size                                   → GeneratedReportListResponse
    //     POST   /api/v1/reports/generate  (ReportGenerateRequest)           → free-form 응답(202/410 가능)
    //     GET    /api/v1/reports/{report_id}                                 → GeneratedReportResponse
    //     DELETE /api/v1/reports/{report_id}                                 → 204
    //     GET    /api/v1/reports/{report_id}/download                        → binary stream
    //   Report Templates (4):
    //     GET    /api/v1/reports/templates?page&size                         → ReportTemplateListResponse
    //     GET    /api/v1/reports/templates/{template_id}                     → ReportTemplateResponse
    //     POST   /api/v1/reports/templates (multipart/form-data — name/format/description?/file?) → ReportTemplateResponse
    //     PUT    /api/v1/reports/templates/{template_id} (ReportTemplateUpdate — name?/description?) → ReportTemplateResponse
    //     DELETE /api/v1/reports/templates/{template_id}                     → 204
    //
    // 주의(추정 금지 — OpenAPI 캡처 결과):
    //   - POST /reports/generate / POST PUT DELETE /templates 의 OpenAPI 응답 코드가 "410" 으로
    //     명시되어 있음(deprecate 표식일 가능성). 본 클라이언트는 4xx/5xx 를 InvalidOperationException
    //     으로 변환하므로 호출자가 502 한국어로 인식. 라이브 호출 결과를 e2e 검증 단계에서 확인.
    //   - POST /reports/templates 는 multipart/form-data — JSON 이 아님. 호출자가 fileStream 제공 가능.
    //   - GET /api/v1/reports 에 status 필터 query param 없음(page/size 만). status 별 분류는 클라이언트 측 처리.
    //   - GET /api/v1/faq 에 scope_id/category/q 필터 query param 존재.

    // ── FAQ (5) ────────────────────────────────────────────────────────────

    /// <summary>
    /// FAQ 목록 — GET /api/v1/faq (페이징 + 검색/카테고리/스코프 필터).
    /// </summary>
    /// <param name="page">DocUtil 페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 20, DocUtil 한도 1~100).</param>
    /// <param name="scopeId">검색 범위 필터(UUID, 선택).</param>
    /// <param name="category">카테고리 필터(선택).</param>
    /// <param name="q">질문/답변 텍스트 LIKE 검색(선택).</param>
    Task<DocUtilFaqList> ListFaqsAsync(
        int page = 1,
        int size = 20,
        string? scopeId = null,
        string? category = null,
        string? q = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// FAQ 상세 — GET /api/v1/faq/{faq_id}.
    /// 404 응답은 null 로 정규화.
    /// </summary>
    Task<DocUtilFaqDetail?> GetFaqAsync(
        string faqId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// FAQ 생성 — POST /api/v1/faq (FAQCreate).
    /// </summary>
    Task<DocUtilFaqDetail> CreateFaqAsync(
        DocUtilCreateFaqRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// FAQ 수정 — PUT /api/v1/faq/{faq_id} (FAQUpdate, partial).
    /// </summary>
    Task<DocUtilFaqDetail> UpdateFaqAsync(
        string faqId,
        DocUtilUpdateFaqRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// FAQ 삭제 — DELETE /api/v1/faq/{faq_id} (204).
    /// </summary>
    Task DeleteFaqAsync(
        string faqId,
        CancellationToken cancellationToken = default);

    // ── Reports (5) ────────────────────────────────────────────────────────

    /// <summary>
    /// 보고서 목록 — GET /api/v1/reports (페이징).
    /// <para>OpenAPI 에 status 필터 없음 — 클라이언트 측에서 GeneratedReportResponse.Status 로 필터.</para>
    /// </summary>
    /// <param name="page">DocUtil 페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 20, DocUtil 한도 1~100).</param>
    Task<DocUtilReportList> ListReportsAsync(
        int page = 1,
        int size = 20,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 보고서 상세 — GET /api/v1/reports/{report_id}.
    /// 404 응답은 null 로 정규화.
    /// </summary>
    Task<DocUtilReportDetail?> GetReportAsync(
        string reportId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 보고서 생성 — POST /api/v1/reports/generate (ReportGenerateRequest).
    /// <para>
    /// 응답은 schema 미정의(free-form). 비동기 job 가능성 — 본 메서드는 raw dict 로 노출.
    /// 호출자(Controller) 가 status/id 등을 그대로 운영자 콘솔에 전달.
    /// </para>
    /// </summary>
    Task<DocUtilReportGenerationResponse> GenerateReportAsync(
        DocUtilGenerateReportRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 보고서 삭제 — DELETE /api/v1/reports/{report_id} (204).
    /// </summary>
    Task DeleteReportAsync(
        string reportId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 보고서 다운로드 — GET /api/v1/reports/{report_id}/download (binary stream).
    /// <para>
    /// 응답은 stream(파일 본문). Content-Type / Content-Disposition 헤더 메타가 함께 캡처되어
    /// DocUtilReportDownload 안에 전달된다. 호출자(Controller)가 FileStreamResult 로 그대로 흘려보낸다.
    /// Stream 은 호출자가 Dispose 책임을 갖는다 — HttpResponseOwnedStream 으로 wrap.
    /// </para>
    /// </summary>
    Task<DocUtilReportDownload> DownloadReportAsync(
        string reportId,
        CancellationToken cancellationToken = default);

    // ── Report Templates (4) ───────────────────────────────────────────────

    /// <summary>
    /// 보고서 템플릿 목록 — GET /api/v1/reports/templates (페이징).
    /// </summary>
    Task<DocUtilReportTemplateList> ListReportTemplatesAsync(
        int page = 1,
        int size = 20,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 보고서 템플릿 상세 — GET /api/v1/reports/templates/{template_id}.
    /// 404 응답은 null 로 정규화.
    /// </summary>
    Task<DocUtilReportTemplateDetail?> GetReportTemplateAsync(
        string templateId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 보고서 템플릿 생성 — POST /api/v1/reports/templates (multipart/form-data).
    /// <para>
    /// fileStream 이 null 이면 이름/설명/format 만 등록(파일 미첨부). non-null 이면 multipart 의 file 필드에 부착.
    /// fileStream 은 호출자(Controller) 가 소유 — 본 클라이언트는 Read 만 한다(자동 Dispose 금지).
    /// </para>
    /// </summary>
    Task<DocUtilReportTemplateDetail> CreateReportTemplateAsync(
        DocUtilCreateReportTemplateRequest request,
        Stream? fileStream,
        string? fileName,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 보고서 템플릿 수정 — PUT /api/v1/reports/templates/{template_id} (ReportTemplateUpdate — name?/description? partial).
    /// </summary>
    Task<DocUtilReportTemplateDetail> UpdateReportTemplateAsync(
        string templateId,
        DocUtilUpdateReportTemplateRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 보고서 템플릿 삭제 — DELETE /api/v1/reports/templates/{template_id} (204).
    /// </summary>
    Task DeleteReportTemplateAsync(
        string templateId,
        CancellationToken cancellationToken = default);

    // ── Phase 10.2d (2026-05-11): DocUtil 문서 템플릿(Document Templates) 운영자 BFF ─
    //
    // 통합 비전 매핑(P1 Control Plane / P5 인증 / R2 단일 진입점):
    //   AgentHub 운영자 콘솔이 DocUtil 의 문서 템플릿(Jinja2 기반 문서 생성용) 카탈로그 +
    //   파일 업로드(일반/빈양식/스마트) + AI 자동채움 + 변환 + 변수 메타 편집 + 미리보기 다운로드 +
    //   구조 조회 + 변수 매핑 적용까지 단일 진입점에서 운영. Phase 10.1/10.2a~10.2c 와 동일 BFF 패턴.
    //
    // 데이터 소스: DocUtil 소스 인스펙션(`docutil/backend/app/modules/templates/`):
    //   - router 마운트: app.main 에서 `prefix="/api/v1"`로 마운트 + router 내부 `prefix=""` + 라우트 path "/templates/..."
    //   - 즉, 모든 endpoint 는 `/api/v1/templates/...` 절대 경로.
    //   - 410(deprecate) 표식 없음 — 모두 정상 라이브 endpoint.
    //
    //   1. GET    /api/v1/templates                                       → TemplateListResponse (member)
    //   2. POST   /api/v1/templates (JSON)                                → TemplateResponse 201 (admin)
    //   3. POST   /api/v1/templates/upload (multipart)                    → TemplateUploadResponse 201 (admin)
    //   4. POST   /api/v1/templates/upload-blank (multipart)              → TemplateUploadResponse 201 (admin)
    //   5. POST   /api/v1/templates/upload-smart (multipart)              → TemplateUploadResponse 201 (admin)
    //   6. GET    /api/v1/templates/{template_id}                         → TemplateResponse (member)
    //   7. PUT    /api/v1/templates/{template_id}                         → TemplateResponse (admin)
    //   8. DELETE /api/v1/templates/{template_id}                         → 204 (admin)
    //   9. POST   /api/v1/templates/{template_id}/convert (JSON ai_analysis) → TemplateResponse (admin)
    //  10. POST   /api/v1/templates/{template_id}/auto-fill (JSON)        → AutoFillResponse (member)
    //  11. GET    /api/v1/templates/{template_id}/variables               → List<TemplateVariableSchema> (member)
    //  12. PUT    /api/v1/templates/{template_id}/variables               → TemplateResponse (admin)
    //  13. GET    /api/v1/templates/{template_id}/preview                 → StreamingResponse(file) (member)
    //  14. GET    /api/v1/templates/{template_id}/structure               → free-form dict (admin)
    //  15. POST   /api/v1/templates/{template_id}/apply-mapping           → TemplateResponse (admin)
    //
    // 인증/권한 / org_id 자동 부착:
    //   - AgentHub 측: [Authorize(Roles="Admin,SuperAdmin")] 게이트 (Controller 레벨)
    //   - DocUtil 측: IDocUtilTokenProvider 4단계 폴백 + DocUtil 라우터의 `_check_org` 가 토큰의
    //     organization_id 를 자동 검증(403 if missing). 본 클라이언트는 org_id 헤더를 별도 부착하지
    //     않음 — DocUtil 의 dependency injection 으로 토큰에서 추출.
    //   - DocUtil 의 require_role 로 admin 인 endpoint 들도 운영자 토큰이면 통과(super_admin/admin/org_admin).
    //
    // BFF 표면 매핑(추정 금지):
    //   - TemplateResponse: 모든 19 필드(id/organization_id/name/description/template_type/tone/output_format/
    //     schema/sample_prompt/is_active/created_by/created_at(=ins_dt)/updated_at(=upd_dt)/
    //     template_storage_path/jinja2_variables/rendering_mode/image_generation_config) 보존.
    //   - TemplateVariableSchema: name/var_type/label/description/required/category 6 필드.
    //   - VariableMapping: location_type/table_index/row/col/paragraph_index/variable_name/var_type/
    //     label/category/field_type 10 필드.
    //   - schema (alias of schema_): Pydantic alias 처리 — Python 측 reserved word 회피용. JSON 상에서는
    //     "schema" 키. 본 record 는 "Schema" property.

    /// <summary>
    /// 문서 템플릿 목록 — GET /api/v1/templates (페이징 + 필터).
    /// </summary>
    /// <param name="templateType">템플릿 유형 필터(예: "report", "proposal"). 선택.</param>
    /// <param name="page">DocUtil 페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 20, DocUtil 한도 1~100).</param>
    Task<DocUtilDocumentTemplateList> ListDocumentTemplatesAsync(
        string? templateType = null,
        int page = 1,
        int size = 20,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 템플릿 상세 — GET /api/v1/templates/{template_id}.
    /// 404 응답은 null 로 정규화한다.
    /// </summary>
    Task<DocUtilDocumentTemplateDetail?> GetDocumentTemplateAsync(
        string templateId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 템플릿 생성(메타데이터만) — POST /api/v1/templates (JSON TemplateCreate).
    /// 파일 업로드는 UploadDocumentTemplateAsync 또는 UploadBlankFormAsync, UploadSmartTemplateAsync.
    /// </summary>
    Task<DocUtilDocumentTemplateDetail> CreateDocumentTemplateAsync(
        DocUtilCreateDocumentTemplateRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 템플릿 수정(partial) — PUT /api/v1/templates/{template_id} (TemplateUpdate).
    /// </summary>
    Task<DocUtilDocumentTemplateDetail> UpdateDocumentTemplateAsync(
        string templateId,
        DocUtilUpdateDocumentTemplateRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 템플릿 삭제 — DELETE /api/v1/templates/{template_id} (204).
    /// </summary>
    Task DeleteDocumentTemplateAsync(
        string templateId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 템플릿 파일 업로드(일반 Jinja2) — POST /api/v1/templates/upload (multipart/form-data).
    /// 업로드된 파일 내 {{ }} 변수가 자동 추출되어 응답에 포함된다.
    /// </summary>
    /// <param name="request">templateType/tone/outputFormat 등 메타.</param>
    /// <param name="fileStream">파일 본문 stream — 호출자(Controller) 소유, Dispose 도 호출자 책임.</param>
    /// <param name="fileName">원본 파일명(확장자 포함).</param>
    Task<DocUtilDocumentTemplateUpload> UploadDocumentTemplateAsync(
        DocUtilUploadDocumentTemplateRequest request,
        Stream fileStream,
        string fileName,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 빈 양식 업로드(AI 자동 Jinja2 변환) — POST /api/v1/templates/upload-blank (multipart/form-data).
    /// 빈 양식 DOCX/PPTX 를 업로드하면 AI 가 구조를 분석하고 각 빈 섹션에 Jinja2 변수를 자동 삽입한다.
    /// </summary>
    Task<DocUtilDocumentTemplateUpload> UploadBlankFormAsync(
        DocUtilUploadDocumentTemplateRequest request,
        Stream fileStream,
        string fileName,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 스마트 업로드(자동 라우팅) — POST /api/v1/templates/upload-smart (multipart/form-data).
    /// 파일 내 {{ }} 패턴 존재 여부로 일반 vs 빈양식 경로를 자동 선택한다.
    /// name/template_type 생략 시 파일명/내용에서 자동 추측(둘 다 nullable).
    /// </summary>
    Task<DocUtilDocumentTemplateUpload> UploadSmartTemplateAsync(
        DocUtilUploadSmartTemplateRequest request,
        Stream fileStream,
        string fileName,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 일반 문서 → Jinja2 템플릿 변환 — POST /api/v1/templates/{template_id}/convert.
    /// AI 분석 결과(replacements 배열)를 body 의 ai_analysis 로 전달하면 원본의 텍스트가
    /// {{ 변수명 }} 으로 치환된 새 파일이 저장된다.
    /// </summary>
    /// <param name="aiAnalysis">AI 분석 결과 free-form dict (예: { "replacements": [...] }).</param>
    Task<DocUtilDocumentTemplateDetail> ConvertDocumentTemplateAsync(
        string templateId,
        IDictionary<string, object?> aiAnalysis,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// AI 자동채움 — POST /api/v1/templates/{template_id}/auto-fill.
    /// 소스 문서 ID 목록을 전달하면 GPT-4o 가 템플릿 변수에 맞는 값들을 자동 생성하여 context dict 로 반환.
    /// </summary>
    Task<DocUtilDocumentTemplateAutoFill> AutoFillDocumentTemplateAsync(
        string templateId,
        DocUtilAutoFillDocumentTemplateRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 변수 메타 조회 — GET /api/v1/templates/{template_id}/variables.
    /// jinja2_variables 가 비어 있으면 빈 배열을 반환.
    /// </summary>
    Task<List<DocUtilDocumentTemplateVariable>> GetDocumentTemplateVariablesAsync(
        string templateId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 변수 메타 일괄 수정 — PUT /api/v1/templates/{template_id}/variables (TemplateVariablesUpdate).
    /// 변수 라벨/타입/필수 여부/카테고리 등 사용자 편집을 저장.
    /// </summary>
    Task<DocUtilDocumentTemplateDetail> UpdateDocumentTemplateVariablesAsync(
        string templateId,
        DocUtilUpdateDocumentTemplateVariablesRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 템플릿 원본 파일 미리보기/다운로드 — GET /api/v1/templates/{template_id}/preview.
    /// <para>
    /// 응답은 stream — MinIO 의 원본 파일. Content-Type / Content-Disposition 헤더 메타 동봉.
    /// 호출자(Controller) 가 FileStreamResult 로 흘려보내며 HttpResponseOwnedStream 으로 lifetime 결합.
    /// </para>
    /// </summary>
    Task<DocUtilDocumentTemplatePreview> PreviewDocumentTemplateAsync(
        string templateId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 에디터용 문서 구조 — GET /api/v1/templates/{template_id}/structure.
    /// 응답은 free-form dict: { "paragraphs": [...], "tables": [...], "existing_variables": [...] }.
    /// 프론트엔드의 변수 매핑 에디터가 표 셀/문단을 시각화하는 데 사용.
    /// </summary>
    Task<IDictionary<string, object?>> GetDocumentTemplateStructureAsync(
        string templateId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 변수 매핑 적용 — POST /api/v1/templates/{template_id}/apply-mapping.
    /// 에디터에서 사용자가 설정한 셀/문단 ↔ 변수 매핑을 원본 DOCX 에 적용하여 {{ 변수명 }} 삽입 + MinIO 재저장.
    /// </summary>
    Task<DocUtilDocumentTemplateDetail> ApplyDocumentTemplateMappingAsync(
        string templateId,
        DocUtilApplyDocumentTemplateMappingRequest request,
        CancellationToken cancellationToken = default);

    // ── Phase 10.2e (2026-05-11): DocUtil API Keys + Agents + Documents V2 운영자 BFF ──
    //
    // 통합 비전(ADR-2 / R2 단일 진입점):
    //   AgentHub 운영자 콘솔이 DocUtil 의 다음 3개 도메인까지 단일 진입점에서 운영한다.
    //
    //   A) API Keys — LLM 프로바이더(OpenAI/Anthropic/Gemini) API 키 등록/회수/검증
    //      /api/v1/api-keys                       (GET 페이징 조회)
    //      /api/v1/api-keys                       (POST 등록 — 평문 key 는 한 번만 응답)
    //      /api/v1/api-keys/{key_id}              (DELETE 회수)
    //      /api/v1/api-keys/{key_id}/verify       (POST 검증 — 프로바이더에 한 번 호출)
    //
    //   B) Agents — DocUtil 자체 AI 에이전트(챗봇/보고서/제안서/회의록용 페르소나)
    //      ※ AgentHub 의 `Agent` 엔티티와는 다른 별도 도메인 — UI 에 명확히 구분 표기.
    //      /api/v1/agents                         (GET 페이징 + agent_type 필터)
    //      /api/v1/agents                         (POST 생성 — admin only)
    //      /api/v1/agents/{agent_id}              (GET 단건)
    //      /api/v1/agents/{agent_id}              (PUT partial 수정 — admin only)
    //      /api/v1/agents/{agent_id}              (DELETE 삭제 — admin only)
    //
    //   C) Documents V2 — 신규 디자이너 기반 문서 워크플로(Phase 4 S1/S2). 보고서 템플릿의 후속.
    //      /api/v1/v2/documents                   (POST Mode A 자유 생성)
    //      /api/v1/v2/documents                   (GET 페이징 + document_type / mode 필터)
    //      /api/v1/v2/documents/{document_id}     (GET 단건)
    //      /api/v1/v2/documents/{document_id}     (PATCH 부분 패치 — page/component/tokens)
    //      /api/v1/v2/documents/{document_id}/export    (POST 비동기 export — 202 + job_id)
    //      /api/v1/v2/documents/exports/{job_id}        (GET 작업 상태 폴링)
    //      /api/v1/v2/documents/exports/{job_id}/download (GET 결과 파일 프록시 다운로드)
    //
    // 인증/스코프:
    //   세 도메인 모두 운영자 JWT 의 organization_id claim 으로 자동 scope.
    //   본 클라이언트는 path 에 orgId 명시 X (DocUtil 측이 토큰에서 추출).
    //
    // 4xx/5xx 매핑:
    //   EnsureSuccessOrThrowKoreanAsync 가 InvalidOperationException 으로 통일,
    //   Controller 가 502 ErrorResponseDto 한국어 본문으로 응답한다(Phase 10.1/10.2 동일 패턴).

    // ── API Keys (4) ───────────────────────────────────────────────────────

    /// <summary>
    /// LLM API Key 목록 — GET /api/v1/api-keys?page&amp;size.
    /// 응답의 ``api_key_prefix`` 는 마스킹된 prefix (예: ``sk-abc1****``) — 평문은 등록 시 단 한 번만 반환된다.
    /// </summary>
    Task<DocUtilApiKeyList> ListApiKeysAsync(
        int page = 1,
        int size = 20,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// LLM API Key 등록 — POST /api/v1/api-keys (ApiKeyCreate — llm_name + api_key 평문).
    /// DocUtil 측이 AES 암호화 후 DB 저장. 응답에 마스킹 prefix 만 포함된다.
    /// </summary>
    Task<DocUtilApiKeyDetail> CreateApiKeyAsync(
        DocUtilCreateApiKeyRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// LLM API Key 삭제 — DELETE /api/v1/api-keys/{key_id} (204).
    /// </summary>
    Task DeleteApiKeyAsync(
        string keyId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// LLM API Key 검증 — POST /api/v1/api-keys/{key_id}/verify.
    /// DocUtil 이 복호화된 키로 프로바이더에 1회 호출하고 ``is_valid`` + ``message`` 반환.
    /// </summary>
    Task<DocUtilApiKeyVerifyResult> VerifyApiKeyAsync(
        string keyId,
        CancellationToken cancellationToken = default);

    // ── Agents (DocUtil 자체) (5) ──────────────────────────────────────────

    /// <summary>
    /// DocUtil 에이전트 목록 — GET /api/v1/agents (페이징 + agent_type 필터).
    /// <para>
    /// ※ AgentHub 의 ``Agents`` 와 별개 — DocUtil 자체 챗봇 / 보고서 / 제안서 / 회의록용 페르소나.
    /// </para>
    /// </summary>
    /// <param name="agentType">에이전트 유형 필터(chatbot/report/proposal/minutes 등). 선택.</param>
    /// <param name="page">페이지 번호(1-based, 기본 1).</param>
    /// <param name="size">페이지 크기(기본 20, DocUtil 한도 1~100).</param>
    Task<DocUtilDocAgentList> ListDocAgentsAsync(
        string? agentType = null,
        int page = 1,
        int size = 20,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// DocUtil 에이전트 단건 — GET /api/v1/agents/{agent_id}.
    /// 404 응답은 null 로 정규화한다.
    /// </summary>
    Task<DocUtilDocAgentDetail?> GetDocAgentAsync(
        string agentId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// DocUtil 에이전트 생성 — POST /api/v1/agents (AgentCreate).
    /// </summary>
    Task<DocUtilDocAgentDetail> CreateDocAgentAsync(
        DocUtilCreateDocAgentRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// DocUtil 에이전트 부분 수정 — PUT /api/v1/agents/{agent_id} (AgentUpdate).
    /// 비어 있는 필드는 직렬화에서 제외(JsonOptions.WhenWritingNull).
    /// </summary>
    Task<DocUtilDocAgentDetail> UpdateDocAgentAsync(
        string agentId,
        DocUtilUpdateDocAgentRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// DocUtil 에이전트 삭제 — DELETE /api/v1/agents/{agent_id} (204).
    /// </summary>
    Task DeleteDocAgentAsync(
        string agentId,
        CancellationToken cancellationToken = default);

    // ── Documents V2 (7) ──────────────────────────────────────────────────

    /// <summary>
    /// 문서 V2 자유 생성 — POST /api/v1/v2/documents (GenerateDocumentRequest, 202 Accepted).
    /// 현재는 mode=free_generation 만 허용 — template_fill 은 DocUtil 측 D8 단계에서 활성화 예정.
    /// 응답에 생성된 DocumentV2 (id/status/document_schema) 가 동봉.
    /// </summary>
    Task<DocUtilDocumentV2Detail> GenerateDocumentV2Async(
        DocUtilGenerateDocumentV2Request request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 V2 목록 — GET /api/v1/v2/documents?document_type&amp;mode&amp;limit&amp;offset.
    /// DocUtil 측은 ``limit/offset`` 페이지네이션을 사용한다(``page/size`` 와 별개).
    /// </summary>
    /// <param name="documentType">문서 타입 필터(slide_report/proposal/minutes/...). 선택.</param>
    /// <param name="mode">생성 모드 필터(free_generation / template_fill). 선택.</param>
    /// <param name="limit">페이지 크기(기본 20, 1~100).</param>
    /// <param name="offset">조회 시작 오프셋(기본 0, ≥0).</param>
    Task<DocUtilDocumentV2List> ListDocumentsV2Async(
        string? documentType = null,
        string? mode = null,
        int limit = 20,
        int offset = 0,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 V2 단건 — GET /api/v1/v2/documents/{document_id}.
    /// 404 응답은 null 로 정규화한다.
    /// </summary>
    Task<DocUtilDocumentV2Detail?> GetDocumentV2Async(
        string documentId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 V2 부분 패치 — PATCH /api/v1/v2/documents/{document_id} (PartialDocumentPatch).
    /// patch_type: page | component | tokens. expected_version(낙관적 락) 선택.
    /// 409 Conflict — 다른 사용자가 먼저 수정한 경우.
    /// </summary>
    Task<DocUtilDocumentV2Detail> PatchDocumentV2Async(
        string documentId,
        DocUtilPatchDocumentV2Request request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 V2 비동기 Export 요청 — POST /api/v1/v2/documents/{document_id}/export (ExportJobRequest, 202 Accepted).
    /// Celery 작업 등록 후 job_id 를 반환. 실제 빌드는 백그라운드.
    /// 포맷: pptx/docx/hwpx/pdf/html.
    /// </summary>
    Task<DocUtilExportJobAck> RequestDocumentV2ExportAsync(
        string documentId,
        DocUtilRequestDocumentV2ExportRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Export 작업 상태 — GET /api/v1/v2/documents/exports/{job_id}.
    /// status: pending | running | completed | failed. completed 시 download 가능.
    /// </summary>
    Task<DocUtilExportJobStatus> GetDocumentV2ExportStatusAsync(
        string jobId,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Export 결과 다운로드(백엔드 프록시) — GET /api/v1/v2/documents/exports/{job_id}/download.
    /// <para>
    /// 응답은 stream — MinIO 의 결과 파일. Content-Type / Content-Disposition 헤더 메타 동봉.
    /// 호출자(Controller) 가 FileStreamResult 로 흘려보내며 HttpResponseOwnedStream 으로 lifetime 결합.
    /// </para>
    /// 상태: 200 정상 / 403 권한 / 404 만료 / 409 미완료 / 410 파일 삭제.
    /// </summary>
    Task<DocUtilDocumentV2Download> DownloadDocumentV2ExportAsync(
        string jobId,
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

// ── Phase 10.1a (2026-05-10): DocUtil 사용자 BFF DTO ────────────────────────
//
// DocUtil OpenAPI(2026-05-10 캡처) UserResponse / UserListResponse 에 1:1 매핑.
// PascalCase 외부 표면(camelCase JSON), snake_case ↔ JsonNamingPolicy.SnakeCaseLower
// 직렬화는 DocUtilClient 내부에서 처리한다.

/// <summary>
/// 사용자 목록 응답 — DocUtil UserListResponse 매핑.
/// items 는 record array, total/page/size 는 DocUtil 측이 보장하는 페이징 메타.
/// </summary>
public sealed record DocUtilUserList(
    DocUtilUserSummary[] Items,
    long Total,
    int Page,
    int Size);

/// <summary>
/// 사용자 목록 한 행 — DocUtil UserResponse 매핑(요약 표시).
/// 운영자 콘솔의 표 컬럼에 직접 사용된다.
/// </summary>
/// <param name="Id">DocUtil user UUID.</param>
/// <param name="Username">사용자 표기명(한글 이름 또는 ID 형식).</param>
/// <param name="Email">사용자 이메일.</param>
/// <param name="Role">사용자 역할(예: "admin", "member").</param>
/// <param name="Status">사용자 상태(예: "active", "inactive", "locked").</param>
/// <param name="OrganizationId">소속 organization UUID.</param>
/// <param name="DepartmentId">소속 부서 UUID(선택). 향후 10.1b 트랙에서 부서명 조인 예정.</param>
/// <param name="Language">선호 언어 코드(선택, 예: "ko", "en").</param>
/// <param name="LastLoginAt">최근 로그인 시각(선택).</param>
/// <param name="CreatedAt">생성 시각(DocUtil 측은 ins_dt 컬럼을 created_at 으로 alias).</param>
public sealed record DocUtilUserSummary(
    string Id,
    string Username,
    string Email,
    string Role,
    string Status,
    string OrganizationId,
    string? DepartmentId,
    string? Language,
    DateTime? LastLoginAt,
    DateTime CreatedAt);

/// <summary>
/// 사용자 상세 — DocUtil UserResponse 매핑. 본 트랙에서는 Summary 와 동일 필드 셋(전체 노출).
/// 향후 트랙(10.1b/10.1c)에서 부서명 / 프로젝트 멤버십 등 합성 필드가 추가될 수 있다.
/// </summary>
public sealed record DocUtilUserDetail(
    string Id,
    string Username,
    string Email,
    string Role,
    string Status,
    string OrganizationId,
    string? DepartmentId,
    string? Language,
    DateTime? LastLoginAt,
    DateTime CreatedAt);

// ── Phase 10.1b (2026-05-10): DocUtil 조직/부서/할당량 BFF DTO ─────────────
//
// DocUtil OpenAPI(2026-05-10 캡처) 의 OrganizationResponse / DepartmentResponse /
// OrganizationQuotasCurrentResponse / QuotaStatusResponse 에 1:1 매핑.
// PascalCase 외부 표면(camelCase JSON), snake_case ↔ JsonNamingPolicy.SnakeCaseLower
// 직렬화는 DocUtilClient 내부에서 처리한다.

/// <summary>
/// 조직 응답 — DocUtil OrganizationResponse 매핑.
/// settings 는 free-form object (DocUtil 측 향후 확장 대비 pass-through).
/// </summary>
/// <param name="Id">조직 UUID.</param>
/// <param name="Name">조직 이름.</param>
/// <param name="Slug">조직 slug(URL/식별자).</param>
/// <param name="Description">조직 설명(선택).</param>
/// <param name="Settings">조직 설정 free-form 객체(선택).</param>
/// <param name="CreatedAt">생성 시각(DocUtil 의 ins_dt 를 created_at 으로 alias).</param>
public sealed record DocUtilOrganization(
    string Id,
    string Name,
    string Slug,
    string? Description,
    object? Settings,
    DateTime CreatedAt);

/// <summary>
/// 조직 수정 요청 — DocUtil OrganizationUpdate 매핑.
/// 모든 필드 nullable (partial update).
/// </summary>
public sealed record DocUtilUpdateOrganizationRequest(
    string? Name = null,
    string? Description = null,
    object? Settings = null);

/// <summary>
/// 부서 응답 — DocUtil DepartmentResponse 매핑.
/// path/depth 가 트리 위치를 표현(materialized path 패턴).
/// </summary>
/// <param name="Id">부서 UUID.</param>
/// <param name="OrganizationId">소속 조직 UUID.</param>
/// <param name="ParentId">상위 부서 UUID(루트는 null).</param>
/// <param name="Name">부서 이름.</param>
/// <param name="Depth">트리 깊이(루트 = 0).</param>
/// <param name="Path">materialized path (예: /uuid1/uuid2/).</param>
/// <param name="CreatedAt">생성 시각.</param>
public sealed record DocUtilDepartment(
    string Id,
    string OrganizationId,
    string? ParentId,
    string Name,
    int Depth,
    string Path,
    DateTime CreatedAt);

/// <summary>
/// 부서 생성 요청 — DocUtil DepartmentCreate 매핑.
/// description 은 DocUtil schema 에 미존재 — 추가하지 않는다(추정 금지).
/// </summary>
public sealed record DocUtilCreateDepartmentRequest(
    string Name,
    string? ParentId = null);

/// <summary>
/// 부서 수정 요청 — DocUtil DepartmentUpdate 매핑(partial update).
/// </summary>
public sealed record DocUtilUpdateDepartmentRequest(
    string? Name = null,
    string? ParentId = null);

/// <summary>
/// 부서 멤버 한 행 — DocUtil 응답이 free-form 이지만 실제 캡처 응답에서
/// id/username/email/role 4 필드 확인 후 매핑.
/// </summary>
/// <param name="Id">멤버(사용자) UUID.</param>
/// <param name="Username">사용자 표기명.</param>
/// <param name="Email">사용자 이메일.</param>
/// <param name="Role">사용자 역할(admin / member 등).</param>
public sealed record DocUtilDepartmentMember(
    string Id,
    string Username,
    string Email,
    string Role);

/// <summary>
/// 조직 월 할당량 현황 — DocUtil OrganizationQuotasCurrentResponse 매핑.
/// quotas map 을 List 로 평탄화(quota_type 별 1행).
/// </summary>
/// <param name="OrganizationId">조직 UUID.</param>
/// <param name="YearMonth">대상 연-월(YYYY-MM).</param>
/// <param name="Quotas">할당량 항목 배열(quota_type 별).</param>
public sealed record DocUtilOrganizationQuotaCurrent(
    string OrganizationId,
    string YearMonth,
    DocUtilOrganizationQuotaStatus[] Quotas);

/// <summary>
/// 단일 할당량 항목 — DocUtil QuotaStatusResponse 매핑.
/// </summary>
/// <param name="QuotaType">쿼터 유형(예: dalle_monthly, unsplash_monthly).</param>
/// <param name="MonthlyLimit">월 허용 한도(0 이상 정수).</param>
/// <param name="UsedCount">이번 달 누적 사용량.</param>
/// <param name="Remaining">잔여 가능량(limit - used).</param>
/// <param name="YearMonth">대상 연-월(YYYY-MM).</param>
public sealed record DocUtilOrganizationQuotaStatus(
    string QuotaType,
    int MonthlyLimit,
    int UsedCount,
    int Remaining,
    string YearMonth);

/// <summary>
/// 할당량 한도 조정 요청 — DocUtil QuotaUpdateRequest 매핑.
/// monthly_limit 만 변경 가능(used_count 는 차감 로직에서만 갱신).
/// </summary>
public sealed record DocUtilUpdateQuotaRequest(
    int MonthlyLimit);

// ── Phase 10.1c (2026-05-10): DocUtil 프로젝트/보드 BFF DTO ────────────────
//
// DocUtil OpenAPI(2026-05-10 캡처) ProjectResponse / ProjectListResponse /
// BoardResponse / BoardListResponse 에 1:1 매핑. 본 트랙은 운영자 콘솔에서
// 프로젝트의 모든 메타(allow_original_download / 생성자 / timestamps) 를 노출 —
// 기존 ListCollectionsAsync (DocUtilCollection 3 필드) 과는 별도의 풍부 표면.
//
// PascalCase 외부 표면(camelCase JSON), snake_case ↔ JsonNamingPolicy.SnakeCaseLower
// 직렬화는 DocUtilClient 내부에서 처리한다.

/// <summary>
/// DocUtil 프로젝트 응답 — ProjectResponse 매핑(8 필드).
/// 운영자 콘솔의 프로젝트 카드/상세 패널에 직접 사용.
/// </summary>
/// <param name="Id">프로젝트 UUID.</param>
/// <param name="Name">프로젝트 이름.</param>
/// <param name="Description">프로젝트 설명(선택).</param>
/// <param name="AllowOriginalDownload">원본 파일 다운로드 허용 여부(기본 true).</param>
/// <param name="OrganizationId">소속 조직 UUID.</param>
/// <param name="CreatedBy">생성자 UUID.</param>
/// <param name="CreatedAt">생성 시각(DocUtil ins_dt → created_at alias).</param>
/// <param name="UpdatedAt">수정 시각(DocUtil upd_dt → updated_at alias).</param>
public sealed record DocUtilProject(
    string Id,
    string Name,
    string? Description,
    bool AllowOriginalDownload,
    string OrganizationId,
    string CreatedBy,
    DateTime CreatedAt,
    DateTime UpdatedAt);

/// <summary>
/// 프로젝트 목록 응답 — ProjectListResponse 매핑.
/// </summary>
public sealed record DocUtilProjectList(
    DocUtilProject[] Items,
    long Total,
    int Page,
    int Size);

/// <summary>
/// 프로젝트 트리 노드 — DocUtil `/api/v1/projects/tree` 응답.
/// <para>
/// DocUtil 트리는 프로젝트 → 보드 2단계 평면(프로젝트 부모-자식 없음).
/// 응답은 free-form: {id, name, boards: BoardResponse[]}.
/// </para>
/// </summary>
public sealed record DocUtilProjectTreeNode(
    string Id,
    string Name,
    DocUtilBoard[] Boards);

/// <summary>
/// 프로젝트 멤버 한 행 — DocUtil free-form 응답에서 4 필드 안정적으로 노출.
/// (DocUtilDepartmentMember 와 형태는 동일하나 의미 분리 — 멤버 도메인 차이).
/// </summary>
public sealed record DocUtilProjectMember(
    string Id,
    string Username,
    string Email,
    string Role);

/// <summary>
/// 프로젝트 참여 부서 한 행 — DocUtil free-form 응답에서 4 필드 안정적으로 노출.
/// (DocUtilDepartment 의 풍부 응답과 다름 — 본 endpoint 는 부서 핵심 정보만 반환).
/// </summary>
public sealed record DocUtilProjectDepartment(
    string Id,
    string Name,
    string Path,
    int Depth);

/// <summary>
/// 프로젝트 생성 요청 — DocUtil ProjectCreate 매핑.
/// allow_original_download 의 DocUtil 기본값은 true.
/// </summary>
public sealed record DocUtilCreateProjectRequest(
    string Name,
    string? Description = null,
    bool? AllowOriginalDownload = null);

/// <summary>
/// 프로젝트 수정 요청 — DocUtil ProjectUpdate 매핑(partial update).
/// <para>주의: DocUtil ProjectUpdate schema 에는 allow_original_download 가 없다.</para>
/// </summary>
public sealed record DocUtilUpdateProjectRequest(
    string? Name = null,
    string? Description = null);

/// <summary>
/// DocUtil 보드 응답 — BoardResponse 매핑(7 필드).
/// 보드는 프로젝트 내부의 KB collection 단위.
/// </summary>
/// <param name="Id">보드 UUID.</param>
/// <param name="ProjectId">상위 프로젝트 UUID.</param>
/// <param name="Name">보드 이름.</param>
/// <param name="Description">보드 설명(선택).</param>
/// <param name="CreatedBy">생성자 UUID.</param>
/// <param name="CreatedAt">생성 시각.</param>
/// <param name="UpdatedAt">수정 시각.</param>
public sealed record DocUtilBoard(
    string Id,
    string ProjectId,
    string Name,
    string? Description,
    string CreatedBy,
    DateTime CreatedAt,
    DateTime UpdatedAt);

/// <summary>
/// 보드 목록 응답 — BoardListResponse 매핑.
/// </summary>
public sealed record DocUtilBoardList(
    DocUtilBoard[] Items,
    long Total,
    int Page,
    int Size);

/// <summary>
/// 보드 생성 요청 — DocUtil BoardCreate 매핑.
/// <para>주의: DocUtil BoardCreate 에는 folder_id 가 없다(별도 endpoint /api/v1/boards/{board_id}/folders).</para>
/// </summary>
public sealed record DocUtilCreateBoardRequest(
    string Name,
    string? Description = null);

/// <summary>
/// 보드 수정 요청 — DocUtil BoardUpdate 매핑(partial update).
/// </summary>
public sealed record DocUtilUpdateBoardRequest(
    string? Name = null,
    string? Description = null);

// ── Phase 10.2a (2026-05-10): DocUtil Dashboard + Audit BFF DTO ──────────────
//
// DocUtil OpenAPI(2026-05-10 캡처):
//   - DashboardMetrics: total_users/active_users/total_documents/total_searches + feature_usage(dict, additionalProperties=true)
//   - ResponseTimeData: timestamps[] + values[]
//   - SearchErrorData: dates[] + error_counts[]
//   - SearchUsageStats: total_requests + total_responses + total_failures + period
//   - UploadStatusChart: completed + processing + waiting + error (default 0 each)
//   - AuditLogResponse: id/organization_id/user_id?/action/resource_type/resource_id?/details?/ip_address?/created_at
//   - AuditLogListResponse: items + total + page + size
//   - export: text/csv (binary stream + filename header)
//
// 1:1 매핑 — 추정 금지 원칙 적용. user_agent 등 schema 에 없는 필드는 추가하지 않음.
// PascalCase 외부 표면(camelCase JSON), snake_case ↔ JsonNamingPolicy.SnakeCaseLower
// 직렬화는 DocUtilClient 내부에서 처리한다.

/// <summary>
/// 대시보드 요약 메트릭 — DocUtil DashboardMetrics 매핑.
/// </summary>
/// <param name="TotalUsers">조직 전체 등록 사용자 수.</param>
/// <param name="ActiveUsers">status='active' 사용자 수.</param>
/// <param name="TotalDocuments">업로드된 총 문서 수.</param>
/// <param name="TotalSearches">누적 검색 요청 수.</param>
/// <param name="FeatureUsage">자유 형식 기능별 카운터(예: chat/qa/keyword). DocUtil additionalProperties=true.</param>
public sealed record DocUtilDashboardMetrics(
    int TotalUsers,
    int ActiveUsers,
    int TotalDocuments,
    int TotalSearches,
    IDictionary<string, int> FeatureUsage);

/// <summary>
/// 시간별 평균 응답시간 시계열 — DocUtil ResponseTimeData 매핑.
/// timestamps 와 values 는 동일 길이 평행 배열(같은 인덱스가 한 데이터 포인트).
/// </summary>
/// <param name="Timestamps">ISO 시각(시간 단위 버킷).</param>
/// <param name="Values">버킷별 평균 응답시간(ms, double).</param>
public sealed record DocUtilResponseTimes(
    string[] Timestamps,
    double[] Values);

/// <summary>
/// 일별 검색 오류 카운트 — DocUtil SearchErrorData 매핑.
/// dates 와 error_counts 는 동일 길이 평행 배열.
/// </summary>
public sealed record DocUtilSearchErrors(
    string[] Dates,
    int[] ErrorCounts);

/// <summary>
/// 검색 사용량 집계 — DocUtil SearchUsageStats 매핑.
/// </summary>
/// <param name="TotalRequests">기간 내 검색 요청 수.</param>
/// <param name="TotalResponses">성공 응답 수.</param>
/// <param name="TotalFailures">실패 수.</param>
/// <param name="Period">집계 기간 라벨(예: "7d").</param>
public sealed record DocUtilSearchUsage(
    int TotalRequests,
    int TotalResponses,
    int TotalFailures,
    string Period);

/// <summary>
/// 문서 업로드 상태 분포 — DocUtil UploadStatusChart 매핑.
/// </summary>
public sealed record DocUtilUploadStatus(
    int Completed,
    int Processing,
    int Waiting,
    int Error);

/// <summary>
/// 감사 로그 한 항목 — DocUtil AuditLogResponse 매핑.
/// <para>
/// user_id / resource_id / details / ip_address 는 nullable.
/// details 는 DocUtil 의 free-form dict — IDictionary&lt;string, object?&gt; 로 노출.
/// </para>
/// </summary>
public sealed record DocUtilAuditLogEntry(
    string Id,
    string OrganizationId,
    string? UserId,
    string Action,
    string ResourceType,
    string? ResourceId,
    IDictionary<string, object?>? Details,
    string? IpAddress,
    DateTime CreatedAt);

/// <summary>
/// 감사 로그 페이지 응답 — DocUtil AuditLogListResponse 매핑.
/// </summary>
public sealed record DocUtilAuditLogList(
    DocUtilAuditLogEntry[] Items,
    long Total,
    int Page,
    int Size);

/// <summary>
/// 감사 로그 CSV 내보내기 응답 — text/csv binary stream + 헤더 메타.
/// <para>
/// 호출자(Controller) 는 Stream 을 FileStreamResult 로 그대로 흘려보낸다.
/// Stream 은 호출자가 Dispose 책임을 갖는다(using 으로 감싸면 됨).
/// </para>
/// </summary>
/// <param name="Stream">DocUtil 응답 본문 stream(text/csv).</param>
/// <param name="ContentType">DocUtil 응답의 Content-Type 헤더(보통 "text/csv; charset=utf-8").</param>
/// <param name="FileName">DocUtil Content-Disposition 의 filename(없으면 fallback "audit_logs.csv").</param>
public sealed record DocUtilAuditExport(
    Stream Stream,
    string ContentType,
    string FileName);

// ── Phase 10.2b (2026-05-10): DocUtil Search Scopes + Evaluation BFF DTO ───
//
// DocUtil OpenAPI(2026-05-10 캡처) 의 SearchScopeResponse / SearchScopeListResponse /
// SearchScopeOption / LocationOption / SearchScopeCreate / SearchScopeUpdate /
// SearchScopeEnvironment 에 1:1 매핑 (24 필드 SearchScopeResponse 전체).
// EvaluationConfigResponse / EvaluationLogResponse / EvaluationRunSummary /
// EvaluationTrendPoint / EvaluationConfigUpdate / EvaluationRunRequest 도 동일 매핑.
// PascalCase 외부 표면(camelCase JSON), snake_case ↔ JsonNamingPolicy.SnakeCaseLower
// 직렬화는 DocUtilClient 내부에서 처리한다.

// ── Search Scopes ──────────────────────────────────────────────────────────

/// <summary>
/// 검색 범위 한 행(목록 표시용 요약 — Detail 과 동일 24 필드 셋).
/// DocUtil SearchScopeResponse 와 1:1.
/// </summary>
public sealed record DocUtilSearchScopeSummary(
    string Id,
    string Name,
    string? Description,
    string OrganizationId,
    string CreatedBy,
    string? ProjectId,
    string? BoardId,
    string? FolderId,
    string? LocationPath,
    bool ChatbotEnabled,
    string? ChatbotFaqTemplate,
    bool QaEnabled,
    string? QaPromptTemplate,
    string? QaLlmModel,
    bool KeywordSearchEnabled,
    bool AgentEnabled,
    int ChunkSize,
    int ChunkOverlap,
    double TitleWeight,
    double KeywordWeight,
    double ContentWeight,
    int MaxResults,
    double SimilarityThreshold,
    DateTime CreatedAt,
    DateTime UpdatedAt);

/// <summary>
/// 검색 범위 상세 — Summary 와 동일 셋. 의미 분리(상세 진입 시 Detail 사용)로 record 별도 정의.
/// </summary>
public sealed record DocUtilSearchScopeDetail(
    string Id,
    string Name,
    string? Description,
    string OrganizationId,
    string CreatedBy,
    string? ProjectId,
    string? BoardId,
    string? FolderId,
    string? LocationPath,
    bool ChatbotEnabled,
    string? ChatbotFaqTemplate,
    bool QaEnabled,
    string? QaPromptTemplate,
    string? QaLlmModel,
    bool KeywordSearchEnabled,
    bool AgentEnabled,
    int ChunkSize,
    int ChunkOverlap,
    double TitleWeight,
    double KeywordWeight,
    double ContentWeight,
    int MaxResults,
    double SimilarityThreshold,
    DateTime CreatedAt,
    DateTime UpdatedAt);

/// <summary>
/// 검색 범위 목록 응답 — DocUtil SearchScopeListResponse 매핑.
/// </summary>
public sealed record DocUtilSearchScopeList(
    DocUtilSearchScopeSummary[] Items,
    long Total,
    int Page,
    int Size);

/// <summary>
/// 검색 범위 옵션(드롭다운용) — DocUtil SearchScopeOption 매핑.
/// </summary>
public sealed record DocUtilSearchScopeOption(
    string Id,
    string Name,
    string? LocationPath);

/// <summary>
/// 위치 옵션(프로젝트/보드/폴더) — DocUtil LocationOption 매핑.
/// </summary>
/// <param name="Type">"project" | "board" | "folder".</param>
public sealed record DocUtilLocationOption(
    string Id,
    string Name,
    string Type,
    string? Path);

/// <summary>
/// 검색 범위 생성 요청 — DocUtil SearchScopeCreate 매핑.
/// <para>
/// name 필수. project_id/board_id/folder_id 중 하나로 위치 지정(모두 선택).
/// 환경 설정 필드는 DocUtil 측 default 적용을 위해 모두 nullable.
/// </para>
/// </summary>
public sealed record DocUtilCreateScopeRequest(
    string Name,
    string? Description = null,
    string? ProjectId = null,
    string? BoardId = null,
    string? FolderId = null,
    bool? ChatbotEnabled = null,
    bool? QaEnabled = null,
    bool? KeywordSearchEnabled = null,
    bool? AgentEnabled = null,
    int? ChunkSize = null,
    int? ChunkOverlap = null,
    double? TitleWeight = null,
    double? KeywordWeight = null,
    double? ContentWeight = null,
    int? MaxResults = null,
    double? SimilarityThreshold = null);

/// <summary>
/// 검색 범위 수정 요청 — DocUtil SearchScopeUpdate 매핑(모두 nullable, partial update).
/// </summary>
public sealed record DocUtilUpdateScopeRequest(
    string? Name = null,
    string? Description = null,
    string? ProjectId = null,
    string? BoardId = null,
    string? FolderId = null,
    bool? ChatbotEnabled = null,
    bool? QaEnabled = null,
    bool? KeywordSearchEnabled = null,
    bool? AgentEnabled = null,
    int? ChunkSize = null,
    int? ChunkOverlap = null,
    double? TitleWeight = null,
    double? KeywordWeight = null,
    double? ContentWeight = null,
    int? MaxResults = null,
    double? SimilarityThreshold = null);

/// <summary>
/// 검색 범위 환경 설정 — DocUtil SearchScopeEnvironment 매핑.
/// <para>모든 필드 default 가 OpenAPI 에 정의됨 — 운영자가 일부만 변경하더라도 DocUtil 측에서 나머지 default 보존.</para>
/// </summary>
public sealed record DocUtilUpdateScopeEnvironmentRequest(
    bool? ChatbotEnabled = null,
    string? ChatbotFaqTemplate = null,
    bool? QaEnabled = null,
    string? QaPromptTemplate = null,
    string? QaLlmModel = null,
    bool? KeywordSearchEnabled = null,
    bool? AgentEnabled = null,
    int? ChunkSize = null,
    int? ChunkOverlap = null,
    double? TitleWeight = null,
    double? KeywordWeight = null,
    double? ContentWeight = null,
    int? MaxResults = null,
    double? SimilarityThreshold = null);

/// <summary>
/// 검색 범위 valid-id 응답 — OpenAPI 에 schema 미정의로 free-form dict 보존.
/// 임베드 위젯의 scope_id 검증 결과(예: { valid: true } 등) 로 짐작되나 추정 금지 — 그대로 노출.
/// </summary>
public sealed record DocUtilSearchScopeValidIdResponse(
    IDictionary<string, object?> Data);

// ── Evaluation ─────────────────────────────────────────────────────────────

/// <summary>
/// 평가 가중치 설정 — DocUtil EvaluationConfigResponse 매핑.
/// </summary>
/// <param name="Id">설정 row UUID.</param>
/// <param name="OrganizationId">조직 UUID.</param>
/// <param name="ContextRelevancyWeight">컨텍스트 관련성 가중치(0~1).</param>
/// <param name="AnswerFaithfulnessWeight">답변 충실도 가중치(0~1).</param>
/// <param name="AnswerRelevancyWeight">답변 관련성 가중치(0~1).</param>
/// <param name="HallucinationWeight">할루시네이션 페널티 가중치(0~1).</param>
public sealed record DocUtilEvaluationConfig(
    string Id,
    string OrganizationId,
    double ContextRelevancyWeight,
    double AnswerFaithfulnessWeight,
    double AnswerRelevancyWeight,
    double HallucinationWeight);

/// <summary>
/// 평가 가중치 수정 요청 — DocUtil EvaluationConfigUpdate 매핑.
/// <para>모든 필드 0~1, default: 0.25 / 0.3 / 0.25 / 0.2 (합=1.0 권장).</para>
/// </summary>
public sealed record DocUtilUpdateEvaluationConfigRequest(
    double ContextRelevancyWeight,
    double AnswerFaithfulnessWeight,
    double AnswerRelevancyWeight,
    double HallucinationWeight);

/// <summary>
/// 평가 로그 한 항목 — DocUtil EvaluationLogResponse 매핑(17 필드).
/// </summary>
public sealed record DocUtilEvaluationLogEntry(
    string Id,
    string OrganizationId,
    string RunId,
    string Question,
    string Answer,
    IDictionary<string, object?>? Contexts,
    double ContextRelevancy,
    double AnswerFaithfulness,
    double AnswerRelevancy,
    double HallucinationScore,
    bool HasHallucination,
    IDictionary<string, object?>? HallucinationEvidence,
    double CompositeScore,
    IDictionary<string, object?>? JudgeDetails,
    string RunType,
    int QuestionIndex,
    DateTime CreatedAt);

/// <summary>
/// 평가 로그 목록 응답 — DocUtil EvaluationLogListResponse 매핑.
/// </summary>
public sealed record DocUtilEvaluationLogList(
    DocUtilEvaluationLogEntry[] Items,
    long Total,
    int Page,
    int Size);

/// <summary>
/// 기본 평가 질문 목록 — DocUtil 응답 schema 가 free-form dict.
/// (그대로 pass-through — 운영자 콘솔에서 키-값 표시).
/// </summary>
public sealed record DocUtilEvaluationQuestions(
    IDictionary<string, object?> Data);

/// <summary>
/// 평가 실행 요청 — DocUtil EvaluationRunRequest 매핑.
/// <para>questions 가 null/빈 배열이면 DocUtil 측 default 질문 셋 사용.</para>
/// </summary>
public sealed record DocUtilRunEvaluationRequest(
    string[]? Questions = null);

/// <summary>
/// 평가 실행 응답 — DocUtil 202 응답이 free-form (task_id 등). dict 로 보존.
/// </summary>
public sealed record DocUtilEvaluationRunResponse(
    IDictionary<string, object?> Data);

/// <summary>
/// 평가 실행 요약 — DocUtil EvaluationRunSummary 매핑(10 필드).
/// </summary>
public sealed record DocUtilEvaluationRunSummary(
    string RunId,
    string RunType,
    DateTime CreatedAt,
    int QuestionCount,
    double AvgContextRelevancy,
    double AvgAnswerFaithfulness,
    double AvgAnswerRelevancy,
    double AvgHallucinationScore,
    double AvgCompositeScore,
    int HallucinationCount);

/// <summary>
/// 평가 실행 목록 응답 — DocUtil EvaluationRunListResponse 매핑.
/// <para>page/size 없음 — items + total 만.</para>
/// </summary>
public sealed record DocUtilEvaluationRunList(
    DocUtilEvaluationRunSummary[] Items,
    long Total);

/// <summary>
/// 평가 트렌드 데이터 포인트 — DocUtil EvaluationTrendPoint 매핑.
/// </summary>
public sealed record DocUtilEvaluationTrendDataPoint(
    string Date,
    double AvgContextRelevancy,
    double AvgAnswerFaithfulness,
    double AvgAnswerRelevancy,
    double AvgHallucinationScore,
    double AvgCompositeScore);

/// <summary>
/// 평가 트렌드 응답 — DocUtil EvaluationTrendResponse 매핑.
/// <para>data[] 시계열(일별).</para>
/// </summary>
public sealed record DocUtilEvaluationTrend(
    DocUtilEvaluationTrendDataPoint[] Data);

// ── Phase 10.2c (2026-05-11): DocUtil FAQ + Reports + Templates BFF DTO ───
//
// DocUtil OpenAPI(2026-05-11 캡처) FAQResponse / FAQListResponse / FAQCreate / FAQUpdate /
// GeneratedReportResponse / GeneratedReportListResponse / ReportGenerateRequest /
// ReportTemplateResponse / ReportTemplateListResponse / ReportTemplateUpdate /
// Body_create_template_api_v1_reports_templates_post 에 1:1 매핑.
// PascalCase 외부 표면(camelCase JSON), snake_case ↔ JsonNamingPolicy.SnakeCaseLower
// 직렬화는 DocUtilClient 내부에서 처리한다.

// ── FAQ (5) ────────────────────────────────────────────────────────────────

/// <summary>
/// FAQ 한 행(목록 표시용 요약) — DocUtil FAQResponse 와 1:1 (10 필드).
/// </summary>
/// <param name="Id">FAQ UUID.</param>
/// <param name="SearchScopeId">바인딩된 검색 범위 UUID(없으면 null).</param>
/// <param name="OrganizationId">조직 UUID.</param>
/// <param name="Question">질문 텍스트.</param>
/// <param name="Answer">답변 텍스트.</param>
/// <param name="Category">카테고리(없으면 null).</param>
/// <param name="DisplayOrder">표시 순서(0~).</param>
/// <param name="IsActive">활성 여부.</param>
/// <param name="CreatedAt">생성 시각.</param>
/// <param name="UpdatedAt">수정 시각.</param>
public sealed record DocUtilFaq(
    string Id,
    string? SearchScopeId,
    string OrganizationId,
    string Question,
    string Answer,
    string? Category,
    int DisplayOrder,
    bool IsActive,
    DateTime CreatedAt,
    DateTime UpdatedAt);

/// <summary>
/// FAQ 상세(요약과 동일 셋 — 의미적 분리를 위해 별도 record 정의).
/// </summary>
public sealed record DocUtilFaqDetail(
    string Id,
    string? SearchScopeId,
    string OrganizationId,
    string Question,
    string Answer,
    string? Category,
    int DisplayOrder,
    bool IsActive,
    DateTime CreatedAt,
    DateTime UpdatedAt);

/// <summary>
/// FAQ 목록 응답 — DocUtil FAQListResponse 매핑.
/// </summary>
public sealed record DocUtilFaqList(
    DocUtilFaq[] Items,
    long Total,
    int Page,
    int Size);

/// <summary>
/// FAQ 생성 요청 — DocUtil FAQCreate 매핑.
/// <para>question/answer 필수. category/display_order/search_scope_id 는 선택.</para>
/// </summary>
public sealed record DocUtilCreateFaqRequest(
    string Question,
    string Answer,
    string? Category = null,
    int? DisplayOrder = null,
    string? SearchScopeId = null);

/// <summary>
/// FAQ 수정 요청 — DocUtil FAQUpdate 매핑(모두 nullable, partial).
/// </summary>
public sealed record DocUtilUpdateFaqRequest(
    string? Question = null,
    string? Answer = null,
    string? Category = null,
    int? DisplayOrder = null,
    bool? IsActive = null);

// ── Reports (5) ────────────────────────────────────────────────────────────

/// <summary>
/// 보고서 한 행(목록 표시용) — DocUtil GeneratedReportResponse 매핑(15 필드).
/// </summary>
/// <param name="Id">보고서 UUID.</param>
/// <param name="TemplateId">사용된 템플릿 UUID(없으면 null — free-form 생성).</param>
/// <param name="OrganizationId">조직 UUID.</param>
/// <param name="Title">보고서 제목.</param>
/// <param name="Status">생성 상태(pending/generating/completed/failed 등 — DocUtil 측 free-form).</param>
/// <param name="OutputFormat">출력 포맷(docx/pdf/html/hwp/hwpx).</param>
/// <param name="OutputStoragePath">생성된 파일 저장 경로(없으면 null).</param>
/// <param name="SourceDocumentIds">근거 문서 ID 배열(없으면 null).</param>
/// <param name="SourceChatSessionId">근거 채팅 세션 UUID(없으면 null).</param>
/// <param name="GenerationParams">생성 파라미터 free-form dict(없으면 null).</param>
/// <param name="RenderingMode">렌더링 모드(없으면 null).</param>
/// <param name="Jinja2Context">Jinja2 컨텍스트 free-form dict(없으면 null).</param>
/// <param name="ErrorMessage">실패 시 에러 메시지(없으면 null).</param>
/// <param name="GeneratedBy">생성자 UUID.</param>
/// <param name="CreatedAt">생성 시각.</param>
/// <param name="CompletedAt">완료 시각(없으면 null — 생성 중).</param>
public sealed record DocUtilReport(
    string Id,
    string? TemplateId,
    string OrganizationId,
    string Title,
    string Status,
    string OutputFormat,
    string? OutputStoragePath,
    string[]? SourceDocumentIds,
    string? SourceChatSessionId,
    IDictionary<string, object?>? GenerationParams,
    string? RenderingMode,
    IDictionary<string, object?>? Jinja2Context,
    string? ErrorMessage,
    string GeneratedBy,
    DateTime CreatedAt,
    DateTime? CompletedAt);

/// <summary>
/// 보고서 상세 — 요약과 동일 셋(의미적 분리).
/// </summary>
public sealed record DocUtilReportDetail(
    string Id,
    string? TemplateId,
    string OrganizationId,
    string Title,
    string Status,
    string OutputFormat,
    string? OutputStoragePath,
    string[]? SourceDocumentIds,
    string? SourceChatSessionId,
    IDictionary<string, object?>? GenerationParams,
    string? RenderingMode,
    IDictionary<string, object?>? Jinja2Context,
    string? ErrorMessage,
    string GeneratedBy,
    DateTime CreatedAt,
    DateTime? CompletedAt);

/// <summary>
/// 보고서 목록 응답 — DocUtil GeneratedReportListResponse 매핑.
/// </summary>
public sealed record DocUtilReportList(
    DocUtilReport[] Items,
    long Total,
    int Page,
    int Size);

/// <summary>
/// 보고서 생성 요청 — DocUtil ReportGenerateRequest 매핑.
/// <para>title 필수(1~500자). 그 외 모두 선택.</para>
/// </summary>
public sealed record DocUtilGenerateReportRequest(
    string Title,
    string? TemplateId = null,
    string? OutputFormat = null,
    string[]? SourceDocumentIds = null,
    string? SourceChatSessionId = null,
    IDictionary<string, object?>? GenerationParams = null);

/// <summary>
/// 보고서 생성 응답 — DocUtil 측 schema 미정의(free-form, 비동기 job 가능성).
/// dict 로 보존하여 호출자가 status/id 등 그대로 전달.
/// </summary>
public sealed record DocUtilReportGenerationResponse(
    IDictionary<string, object?> Data);

/// <summary>
/// 보고서 다운로드 응답 — binary stream + 헤더 메타.
/// <para>
/// 호출자(Controller) 가 FileStreamResult 로 그대로 흘려보낸다.
/// Stream 은 호출자가 Dispose 책임을 갖는다(using 으로 감싸면 됨).
/// </para>
/// </summary>
/// <param name="Stream">DocUtil 응답 본문 stream.</param>
/// <param name="ContentType">Content-Type 헤더(application/pdf, application/vnd.openxmlformats-officedocument.* 등).</param>
/// <param name="FileName">Content-Disposition 의 filename(없으면 fallback "report-{id}").</param>
public sealed record DocUtilReportDownload(
    Stream Stream,
    string ContentType,
    string FileName);

// ── Report Templates (6) ───────────────────────────────────────────────────

/// <summary>
/// 보고서 템플릿 한 행(목록 표시용 요약) — DocUtil ReportTemplateResponse 매핑(10 필드).
/// </summary>
/// <param name="Id">템플릿 UUID.</param>
/// <param name="OrganizationId">조직 UUID.</param>
/// <param name="Name">템플릿 이름.</param>
/// <param name="Description">설명(없으면 null).</param>
/// <param name="Format">템플릿 포맷(docx/pdf/html/hwp/hwpx 등).</param>
/// <param name="TemplateStoragePath">템플릿 파일 저장 경로(없으면 null).</param>
/// <param name="Schema">템플릿 스키마 free-form dict(없으면 null).</param>
/// <param name="CreatedBy">생성자 UUID.</param>
/// <param name="CreatedAt">생성 시각.</param>
/// <param name="UpdatedAt">수정 시각.</param>
public sealed record DocUtilReportTemplate(
    string Id,
    string OrganizationId,
    string Name,
    string? Description,
    string Format,
    string? TemplateStoragePath,
    IDictionary<string, object?>? Schema,
    string CreatedBy,
    DateTime CreatedAt,
    DateTime UpdatedAt);

/// <summary>
/// 보고서 템플릿 상세 — 요약과 동일 셋(의미적 분리).
/// </summary>
public sealed record DocUtilReportTemplateDetail(
    string Id,
    string OrganizationId,
    string Name,
    string? Description,
    string Format,
    string? TemplateStoragePath,
    IDictionary<string, object?>? Schema,
    string CreatedBy,
    DateTime CreatedAt,
    DateTime UpdatedAt);

/// <summary>
/// 보고서 템플릿 목록 응답 — DocUtil ReportTemplateListResponse 매핑.
/// </summary>
public sealed record DocUtilReportTemplateList(
    DocUtilReportTemplate[] Items,
    long Total,
    int Page,
    int Size);

/// <summary>
/// 보고서 템플릿 생성 요청 — DocUtil Body_create_template_api_v1_reports_templates_post 매핑.
/// <para>multipart/form-data — name/format/description/file 4 필드. file 은 별도 Stream 으로 전달.</para>
/// </summary>
public sealed record DocUtilCreateReportTemplateRequest(
    string Name,
    string Format,
    string? Description = null);

/// <summary>
/// 보고서 템플릿 수정 요청 — DocUtil ReportTemplateUpdate 매핑(name? + description? partial).
/// <para>OpenAPI 에 따르면 format / file 은 PUT 으로 변경 불가 — 메타만 갱신.</para>
/// </summary>
public sealed record DocUtilUpdateReportTemplateRequest(
    string? Name = null,
    string? Description = null);

// ── Phase 10.2d (2026-05-11): DocUtil Document Templates BFF DTO ─────────────
//
// DocUtil 소스 인스펙션 결과(`docutil/backend/app/modules/templates/schemas.py`):
//   TemplateCreate(8 필드) / TemplateUpdate(10 필드, 모두 nullable) /
//   TemplateResponse(19 필드, ins_dt→created_at / upd_dt→updated_at alias) /
//   TemplateUploadResponse(6 필드, variables 포함) /
//   TemplateVariableSchema(6 필드, category 기본 "ai_generated") /
//   TemplateVariablesUpdate({variables:[...]}) /
//   AutoFillRequest / AutoFillResponse / VariableMappingPayload / VariableMapping(10 필드).
//
// 1:1 매핑 — 추정 금지 원칙 적용. PascalCase 외부 표면(camelCase JSON),
// snake_case ↔ JsonNamingPolicy.SnakeCaseLower 직렬화는 DocUtilClient 내부에서 처리.

/// <summary>
/// 문서 템플릿 한 행(목록 표시용 요약) — DocUtil TemplateResponse 와 동일 19 필드.
/// </summary>
/// <param name="Id">템플릿 UUID.</param>
/// <param name="OrganizationId">조직 UUID.</param>
/// <param name="Name">템플릿 이름.</param>
/// <param name="Description">설명(없으면 null).</param>
/// <param name="TemplateType">템플릿 유형 자유 텍스트 (예: report/proposal/계약서).</param>
/// <param name="Tone">문서 어조 (예: formal/casual). 기본 "formal".</param>
/// <param name="OutputFormat">출력 형식 (예: docx/pdf/html/pptx).</param>
/// <param name="Schema">템플릿 변수 정의 JSON 스키마(Pydantic 의 schema_ alias) — free-form dict.</param>
/// <param name="SamplePrompt">예시 프롬프트(없으면 null).</param>
/// <param name="IsActive">활성 여부.</param>
/// <param name="CreatedBy">생성자 UUID.</param>
/// <param name="CreatedAt">생성 시각(DocUtil ins_dt).</param>
/// <param name="UpdatedAt">수정 시각(DocUtil upd_dt).</param>
/// <param name="TemplateStoragePath">MinIO 저장 경로(파일 미업로드 시 null).</param>
/// <param name="Jinja2Variables">추출/저장된 Jinja2 변수 free-form dict (없으면 null).</param>
/// <param name="RenderingMode">렌더링 방식 (jinja2/structured). 기본 "jinja2".</param>
/// <param name="ImageGenerationConfig">이미지 생성 설정 (provider/enabled 등, 없으면 null).</param>
public sealed record DocUtilDocumentTemplate(
    string Id,
    string OrganizationId,
    string Name,
    string? Description,
    string TemplateType,
    string Tone,
    string OutputFormat,
    IDictionary<string, object?>? Schema,
    string? SamplePrompt,
    bool IsActive,
    string CreatedBy,
    DateTime CreatedAt,
    DateTime UpdatedAt,
    string? TemplateStoragePath,
    IDictionary<string, object?>? Jinja2Variables,
    string RenderingMode,
    IDictionary<string, object?>? ImageGenerationConfig);

/// <summary>
/// 문서 템플릿 상세 — 요약과 동일 셋(의미적 분리).
/// </summary>
public sealed record DocUtilDocumentTemplateDetail(
    string Id,
    string OrganizationId,
    string Name,
    string? Description,
    string TemplateType,
    string Tone,
    string OutputFormat,
    IDictionary<string, object?>? Schema,
    string? SamplePrompt,
    bool IsActive,
    string CreatedBy,
    DateTime CreatedAt,
    DateTime UpdatedAt,
    string? TemplateStoragePath,
    IDictionary<string, object?>? Jinja2Variables,
    string RenderingMode,
    IDictionary<string, object?>? ImageGenerationConfig);

/// <summary>
/// 문서 템플릿 목록 응답 — DocUtil TemplateListResponse 매핑.
/// </summary>
public sealed record DocUtilDocumentTemplateList(
    DocUtilDocumentTemplate[] Items,
    long Total,
    int Page,
    int Size);

/// <summary>
/// 문서 템플릿 생성 요청(메타데이터만) — DocUtil TemplateCreate 매핑.
/// 파일 업로드는 별도 endpoint(upload / upload-blank / upload-smart) 사용.
/// </summary>
/// <param name="Name">템플릿 이름(1~255자).</param>
/// <param name="TemplateType">템플릿 유형 자유 텍스트(~100자).</param>
/// <param name="OutputFormat">출력 형식(docx/pdf/html/pptx 등 ~20자).</param>
/// <param name="Description">설명(~2000자, 선택).</param>
/// <param name="Tone">문서 어조(기본 "formal").</param>
/// <param name="Schema">템플릿 변수 정의 JSON 스키마(선택).</param>
/// <param name="SamplePrompt">예시 프롬프트(~5000자, 선택).</param>
/// <param name="RenderingMode">렌더링 방식(기본 "jinja2").</param>
/// <param name="ImageGenerationConfig">이미지 생성 설정(선택).</param>
public sealed record DocUtilCreateDocumentTemplateRequest(
    string Name,
    string TemplateType,
    string OutputFormat,
    string? Description = null,
    string Tone = "formal",
    IDictionary<string, object?>? Schema = null,
    string? SamplePrompt = null,
    string RenderingMode = "jinja2",
    IDictionary<string, object?>? ImageGenerationConfig = null);

/// <summary>
/// 문서 템플릿 부분 수정 요청 — DocUtil TemplateUpdate 매핑(모두 nullable, partial).
/// </summary>
public sealed record DocUtilUpdateDocumentTemplateRequest(
    string? Name = null,
    string? Description = null,
    string? TemplateType = null,
    string? Tone = null,
    string? OutputFormat = null,
    IDictionary<string, object?>? Schema = null,
    string? SamplePrompt = null,
    bool? IsActive = null,
    string? RenderingMode = null,
    IDictionary<string, object?>? ImageGenerationConfig = null);

/// <summary>
/// 파일 업로드(일반/빈양식) 요청 메타 — multipart 의 form 필드(파일 외).
/// </summary>
/// <param name="TemplateType">템플릿 유형(필수, ~100자).</param>
/// <param name="OutputFormat">출력 형식(필수, ~20자).</param>
/// <param name="Tone">문서 어조(기본 "formal").</param>
/// <param name="Name">템플릿 이름(생략 시 파일명 사용).</param>
/// <param name="Description">템플릿 설명(선택).</param>
public sealed record DocUtilUploadDocumentTemplateRequest(
    string TemplateType,
    string OutputFormat,
    string Tone = "formal",
    string? Name = null,
    string? Description = null);

/// <summary>
/// 스마트 업로드 요청 메타 — 모두 nullable, 자동 추측 허용.
/// </summary>
/// <param name="Name">템플릿 이름(생략 시 파일명).</param>
/// <param name="Description">설명(선택).</param>
/// <param name="TemplateType">유형(생략 시 키워드 매칭으로 자동 추측).</param>
/// <param name="Tone">문서 어조(기본 "formal").</param>
public sealed record DocUtilUploadSmartTemplateRequest(
    string? Name = null,
    string? Description = null,
    string? TemplateType = null,
    string Tone = "formal");

/// <summary>
/// 템플릿 변수 한 행 — DocUtil TemplateVariableSchema 매핑(6 필드).
/// </summary>
/// <param name="Name">변수명({{ name }}). 영문/숫자/언더스코어, 숫자로 시작 불가.</param>
/// <param name="VarType">타입(string/array/boolean/image/date 등). 기본 "string".</param>
/// <param name="Label">사용자 표시 라벨(한글 등, 선택).</param>
/// <param name="Description">변수 상세 설명(선택).</param>
/// <param name="Required">필수 입력 여부(기본 true).</param>
/// <param name="Category">입력 방식 카테고리(user_input/session_auto/ai_generated). 기본 "ai_generated".</param>
public sealed record DocUtilDocumentTemplateVariable(
    string Name,
    string VarType,
    string? Label,
    string? Description,
    bool Required,
    string Category);

/// <summary>
/// 변수 메타 일괄 수정 요청 — DocUtil TemplateVariablesUpdate 매핑.
/// </summary>
public sealed record DocUtilUpdateDocumentTemplateVariablesRequest(
    DocUtilDocumentTemplateVariable[] Variables);

/// <summary>
/// 파일 업로드 응답 — DocUtil TemplateUploadResponse 매핑.
/// </summary>
public sealed record DocUtilDocumentTemplateUpload(
    string Id,
    string Name,
    string OutputFormat,
    string RenderingMode,
    string? TemplateStoragePath,
    DocUtilDocumentTemplateVariable[] Variables);

/// <summary>
/// AI 자동채움 요청 — DocUtil AutoFillRequest 매핑(JSON body 로 전달).
/// </summary>
/// <param name="SourceDocumentIds">참고할 소스 문서 ID 배열(1+).</param>
/// <param name="AiPrompt">AI 에게 전달할 추가 지시(선택, 예: "간결하게 작성").</param>
public sealed record DocUtilAutoFillDocumentTemplateRequest(
    string[] SourceDocumentIds,
    string? AiPrompt = null);

/// <summary>
/// AI 자동채움 응답 — DocUtil AutoFillResponse 매핑.
/// context 는 변수명 → 생성된 값 free-form 매핑.
/// </summary>
public sealed record DocUtilDocumentTemplateAutoFill(
    IDictionary<string, object?> Context);

/// <summary>
/// 변수 매핑 한 행 — DocUtil VariableMapping 매핑(10 필드).
/// </summary>
/// <param name="LocationType">"table_cell" 또는 "paragraph".</param>
/// <param name="VariableName">매핑할 Jinja2 변수명(영문/숫자/언더스코어, 숫자로 시작 불가).</param>
/// <param name="TableIndex">표 인덱스 (table_cell 일 때 필수).</param>
/// <param name="Row">행 인덱스 (table_cell 일 때 필수).</param>
/// <param name="Col">열 인덱스 (table_cell 일 때 필수).</param>
/// <param name="ParagraphIndex">문단 인덱스 (paragraph 일 때 필수).</param>
/// <param name="VarType">변수 타입(기본 "string").</param>
/// <param name="Label">사용자 표시 라벨(선택).</param>
/// <param name="Category">변수 카테고리(기본 "ai_generated").</param>
/// <param name="FieldType">입력란 유형(short / long, 기본 "short").</param>
public sealed record DocUtilDocumentTemplateMapping(
    string LocationType,
    string VariableName,
    int? TableIndex = null,
    int? Row = null,
    int? Col = null,
    int? ParagraphIndex = null,
    string VarType = "string",
    string? Label = null,
    string Category = "ai_generated",
    string FieldType = "short");

/// <summary>
/// 변수 매핑 적용 요청 — DocUtil VariableMappingPayload 매핑.
/// </summary>
public sealed record DocUtilApplyDocumentTemplateMappingRequest(
    DocUtilDocumentTemplateMapping[] Mappings);

/// <summary>
/// 템플릿 파일 미리보기 응답 — binary stream + 헤더 메타.
/// <para>
/// 호출자(Controller) 가 FileStreamResult 로 그대로 흘려보낸다.
/// Stream 은 HttpResponseOwnedStream 으로 wrap 되어 호출자가 Dispose 한다.
/// </para>
/// </summary>
public sealed record DocUtilDocumentTemplatePreview(
    Stream Stream,
    string ContentType,
    string FileName);

// ════════════════════════════════════════════════════════════════════════════
// Phase 10.2e (2026-05-11) — DocUtil API Keys + Agents + Documents V2 DTO
//
// 모든 record 는 DocUtil FastAPI 의 Pydantic 스키마와 1:1 매핑(snake_case <-> PascalCase).
// JsonNamingPolicy.SnakeCaseLower 가 DocUtilClient 에서 일관 적용된다.
// ════════════════════════════════════════════════════════════════════════════

// ── API Keys ──────────────────────────────────────────────────────────────

/// <summary>
/// LLM API Key 등록 요청 — DocUtil ApiKeyCreate 매핑.
/// </summary>
/// <param name="LlmName">프로바이더 이름(예: "openai", "anthropic"). 1~64자.</param>
/// <param name="ApiKey">평문 API Key — DocUtil 측이 AES 암호화 후 DB 저장. 응답에는 마스킹 prefix 만 노출.</param>
public sealed record DocUtilCreateApiKeyRequest(
    string LlmName,
    string ApiKey);

/// <summary>
/// LLM API Key 한 행(마스킹).
/// </summary>
/// <param name="Id">API Key UUID.</param>
/// <param name="OrganizationId">소속 조직 ID.</param>
/// <param name="LlmName">프로바이더 이름.</param>
/// <param name="ApiKeyPrefix">마스킹된 prefix(예: "sk-abc1****").</param>
/// <param name="IsVerified">VerifyApiKeyAsync 결과 — DocUtil 측이 검증 후 true 로 갱신.</param>
/// <param name="RegisteredBy">등록한 사용자 ID(선택).</param>
/// <param name="CreatedAt">등록 시각(DB ins_dt).</param>
/// <param name="UpdatedAt">최근 수정 시각(DB upd_dt).</param>
public sealed record DocUtilApiKeyDetail(
    string Id,
    string OrganizationId,
    string LlmName,
    string ApiKeyPrefix,
    bool IsVerified,
    string? RegisteredBy,
    DateTime CreatedAt,
    DateTime UpdatedAt);

/// <summary>
/// LLM API Key 목록 응답(페이징).
/// </summary>
public sealed record DocUtilApiKeyList(
    DocUtilApiKeyDetail[] Items,
    long Total,
    int Page,
    int Size);

/// <summary>
/// LLM API Key 검증 결과 — DocUtil 측이 프로바이더에 1회 호출 후 ApiKey.IsVerified 갱신.
/// </summary>
/// <param name="IsValid">검증 성공 여부.</param>
/// <param name="Message">한국어 또는 영어 상태 메시지(프로바이더 응답 기반).</param>
public sealed record DocUtilApiKeyVerifyResult(
    bool IsValid,
    string Message);

// ── DocUtil Agents (AgentHub Agent 와 별개) ───────────────────────────────

/// <summary>
/// DocUtil 에이전트 생성 요청 — DocUtil AgentCreate 매핑.
/// </summary>
/// <param name="Name">에이전트 이름(필수, 1~255자).</param>
/// <param name="Description">설명(선택, ~2000자).</param>
/// <param name="AgentType">에이전트 유형(chatbot / report / proposal / minutes 등 자유 입력, 1~20자).</param>
/// <param name="SystemPrompt">시스템 프롬프트(필수, 1자 이상).</param>
/// <param name="LlmProvider">LLM 프로바이더(openai / azure_openai / gemini / anthropic). null 이면 시스템 기본값.</param>
/// <param name="LlmModel">모델 식별자(기본 "gpt-4o").</param>
/// <param name="Temperature">LLM temperature(0.0~2.0, 기본 0.1).</param>
/// <param name="MaxTokens">최대 응답 토큰(1~128000, 기본 4096).</param>
public sealed record DocUtilCreateDocAgentRequest(
    string Name,
    string AgentType,
    string SystemPrompt,
    string? Description = null,
    string? LlmProvider = null,
    string LlmModel = "gpt-4o",
    double Temperature = 0.1,
    int MaxTokens = 4096);

/// <summary>
/// DocUtil 에이전트 부분 수정 요청 — DocUtil AgentUpdate 매핑(모두 nullable).
/// </summary>
public sealed record DocUtilUpdateDocAgentRequest(
    string? Name = null,
    string? Description = null,
    string? AgentType = null,
    string? SystemPrompt = null,
    string? LlmProvider = null,
    string? LlmModel = null,
    double? Temperature = null,
    int? MaxTokens = null,
    bool? IsActive = null);

/// <summary>
/// DocUtil 에이전트 한 행.
/// </summary>
/// <param name="Id">에이전트 UUID.</param>
/// <param name="OrganizationId">소속 조직 ID.</param>
/// <param name="Name">에이전트 이름.</param>
/// <param name="Description">설명(선택).</param>
/// <param name="AgentType">에이전트 유형.</param>
/// <param name="SystemPrompt">시스템 프롬프트.</param>
/// <param name="LlmProvider">LLM 프로바이더(선택).</param>
/// <param name="LlmModel">모델 식별자.</param>
/// <param name="Temperature">LLM temperature.</param>
/// <param name="MaxTokens">최대 응답 토큰.</param>
/// <param name="IsActive">활성화 여부.</param>
/// <param name="CreatedBy">생성한 사용자 ID.</param>
/// <param name="CreatedAt">생성 시각(DB ins_dt).</param>
/// <param name="UpdatedAt">최근 수정 시각(DB upd_dt).</param>
public sealed record DocUtilDocAgentDetail(
    string Id,
    string OrganizationId,
    string Name,
    string? Description,
    string AgentType,
    string SystemPrompt,
    string? LlmProvider,
    string LlmModel,
    double Temperature,
    int MaxTokens,
    bool IsActive,
    string CreatedBy,
    DateTime CreatedAt,
    DateTime UpdatedAt);

/// <summary>
/// DocUtil 에이전트 목록 응답(페이징).
/// </summary>
public sealed record DocUtilDocAgentList(
    DocUtilDocAgentDetail[] Items,
    long Total,
    int Page,
    int Size);

// ── Documents V2 ──────────────────────────────────────────────────────────

/// <summary>
/// 문서 V2 자유 생성 요청 — DocUtil GenerateDocumentRequest 매핑(Mode A).
/// </summary>
/// <param name="Prompt">사용자 자연어 요청(1~8000자).</param>
/// <param name="DocumentType">문서 타입(slide_report/docx_report/proposal/minutes/one_pager/weekly_status/freeform_doc).</param>
/// <param name="Mode">생성 모드 — 현재 "free_generation" 만 허용("template_fill" 은 추후).</param>
/// <param name="SourceDocumentIds">RAG 근거 문서 ID 배열(선택, 최대 10개).</param>
/// <param name="AgentId">사용할 DocUtil 에이전트 ID(선택).</param>
/// <param name="DesignTokens">브랜드 토큰 free-form JSON dict(선택). null 이면 idino_default.</param>
public sealed record DocUtilGenerateDocumentV2Request(
    string Prompt,
    string DocumentType,
    string Mode = "free_generation",
    string[]? SourceDocumentIds = null,
    string? AgentId = null,
    IDictionary<string, object?>? DesignTokens = null);

/// <summary>
/// 문서 V2 부분 패치 요청 — DocUtil PartialDocumentPatch 매핑.
/// </summary>
/// <param name="PatchType">"page" | "component" | "tokens".</param>
/// <param name="PageId">대상 페이지 id ("p1", "p2", ...). patch_type=page|component 시 필수.</param>
/// <param name="ComponentId">대상 컴포넌트 id ("c1", "c2", ...). patch_type=component 시 필수.</param>
/// <param name="Data">patch_type 별 페이로드 — free-form dict.</param>
/// <param name="ExpectedVersion">낙관적 락(선택). null 이면 락 생략.</param>
public sealed record DocUtilPatchDocumentV2Request(
    string PatchType,
    IDictionary<string, object?> Data,
    string? PageId = null,
    string? ComponentId = null,
    int? ExpectedVersion = null);

/// <summary>
/// 문서 V2 export 요청 — DocUtil ExportJobRequest 매핑.
/// </summary>
/// <param name="Format">"pptx" | "docx" | "hwpx" | "pdf" | "html".</param>
public sealed record DocUtilRequestDocumentV2ExportRequest(
    string Format);

/// <summary>
/// 문서 V2 단건 — DocUtil DocumentV2Response 매핑.
/// </summary>
/// <param name="Id">문서 UUID.</param>
/// <param name="OrganizationId">조직 ID.</param>
/// <param name="GeneratedByUserId">생성한 사용자 ID(선택).</param>
/// <param name="AgentId">사용된 DocUtil 에이전트 ID(선택).</param>
/// <param name="TemplateId">템플릿 ID(template_fill 모드 시).</param>
/// <param name="DocumentType">문서 타입.</param>
/// <param name="Mode">생성 모드(free_generation / template_fill).</param>
/// <param name="Title">문서 제목(LLM 생성).</param>
/// <param name="Status">상태(generating / completed / failed 등 DocUtil 내부 값).</param>
/// <param name="ErrorMessage">실패 사유(선택).</param>
/// <param name="LlmProvider">사용된 LLM 프로바이더(선택).</param>
/// <param name="LlmModel">사용된 모델(선택).</param>
/// <param name="PromptTokens">입력 토큰 수(선택).</param>
/// <param name="CompletionTokens">출력 토큰 수(선택).</param>
/// <param name="CreatedAt">생성 시각.</param>
/// <param name="CompletedAt">완료 시각(선택).</param>
/// <param name="DocumentSchema">DocumentSchema JSON — free-form dict(DocUtil 의 22개 컴포넌트 union).</param>
public sealed record DocUtilDocumentV2Detail(
    string Id,
    string OrganizationId,
    string? GeneratedByUserId,
    string? AgentId,
    string? TemplateId,
    string DocumentType,
    string Mode,
    string Title,
    string Status,
    string? ErrorMessage,
    string? LlmProvider,
    string? LlmModel,
    int? PromptTokens,
    int? CompletionTokens,
    DateTime CreatedAt,
    DateTime? CompletedAt,
    IDictionary<string, object?>? DocumentSchema);

/// <summary>
/// 문서 V2 목록 응답(limit/offset 페이지네이션).
/// </summary>
public sealed record DocUtilDocumentV2List(
    DocUtilDocumentV2Detail[] Items,
    long Total,
    int Limit,
    int Offset);

/// <summary>
/// 문서 V2 export 등록 응답 — { job_id }.
/// </summary>
public sealed record DocUtilExportJobAck(
    string JobId);

/// <summary>
/// 문서 V2 export 작업 상태.
/// </summary>
/// <param name="Status">pending | running | completed | failed.</param>
/// <param name="Progress">0~100 정수 진행률.</param>
/// <param name="DownloadUrl">completed 시 MinIO presigned URL 또는 null(프록시 다운로드 권장).</param>
/// <param name="Error">failed 시 한국어 에러 메시지.</param>
public sealed record DocUtilExportJobStatus(
    string Status,
    int Progress,
    string? DownloadUrl,
    string? Error);

/// <summary>
/// 문서 V2 export 결과 다운로드 응답 — 백엔드 프록시 stream + 헤더 메타.
/// <para>
/// 호출자(Controller) 가 FileStreamResult 로 그대로 흘려보낸다.
/// Stream 은 HttpResponseOwnedStream 으로 wrap 되어 호출자가 Dispose 한다.
/// </para>
/// </summary>
public sealed record DocUtilDocumentV2Download(
    Stream Stream,
    string ContentType,
    string FileName);
