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
