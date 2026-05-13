using Microsoft.EntityFrameworkCore;
using AIAgentManagement.Models;

namespace AIAgentManagement.Data;

public class AIAgentManagementDbContext : DbContext
{
    public AIAgentManagementDbContext(DbContextOptions<AIAgentManagementDbContext> options)
        : base(options)
    {
    }

    public DbSet<User> Users { get; set; }
    public DbSet<Role> Roles { get; set; }
    public DbSet<UserRole> UserRoles { get; set; }
    public DbSet<Agent> Agents { get; set; }
    public DbSet<ApiService> ApiServices { get; set; }
    public DbSet<ApiQuota> ApiQuotas { get; set; }
    public DbSet<ApiUsage> ApiUsages { get; set; }
    public DbSet<ChatConversation> ChatConversations { get; set; }
    public DbSet<ChatMessage> ChatMessages { get; set; }
    public DbSet<ActivityLog> ActivityLogs { get; set; }
    public DbSet<UserSession> UserSessions { get; set; }
    public DbSet<UserPreference> UserPreferences { get; set; }
    // ── Phase 8 (ADR-2): KnowledgeBaseDocuments / DocumentChunks / AgentDocuments
    // DbSet 은 자체 KB 코드/스키마 제거와 함께 삭제됨. RAG 단일 권위는 DocUtil.
    public DbSet<SystemSetting> SystemSettings { get; set; }
    public DbSet<ApiKey> ApiKeys { get; set; }
    public DbSet<Team> Teams { get; set; }
    public DbSet<TeamMember> TeamMembers { get; set; }
    public DbSet<Faq> Faqs { get; set; }
    public DbSet<Tutorial> Tutorials { get; set; }
    public DbSet<ExamplePrompt> ExamplePrompts { get; set; }
    public DbSet<Presentation> Presentations { get; set; }
    public DbSet<PresentationSlide> PresentationSlides { get; set; }
    public DbSet<PresentationTemplate> PresentationTemplates { get; set; }
    public DbSet<Tool> Tools { get; set; }
    public DbSet<ToolVersion> ToolVersions { get; set; }
    public DbSet<ToolExecution> ToolExecutions { get; set; }
    public DbSet<Workflow> Workflows { get; set; }
    public DbSet<WorkflowNode> WorkflowNodes { get; set; }
    public DbSet<WorkflowExecution> WorkflowExecutions { get; set; }
    public DbSet<WorkflowNodeExecution> WorkflowNodeExecutions { get; set; }
    public DbSet<ApiServiceModel> ApiServiceModels { get; set; }
    public DbSet<BannedWord> BannedWords { get; set; }
    public DbSet<PiiDetectionLog> PiiDetectionLogs { get; set; }

    // ── Phase 4.3 — Tenants + Departments (ADR-8 / Q1 옵션 B) ───────────────
    // 멀티테넌시 단일 권위 엔티티. 4개 서브프로젝트의 Tenant 식별 진입점.
    public DbSet<Tenant> Tenants { get; set; }
    public DbSet<Department> Departments { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // PostgreSQL 단일 인스턴스 안에서 schema 격리 (TECHSPEC §5.2 / P4)
        modelBuilder.HasDefaultSchema("AIAgentManagement");

        // UserRole unique constraint
        modelBuilder.Entity<UserRole>()
            .HasIndex(ur => new { ur.UserId, ur.RoleId })
            .IsUnique();

        // ApiQuota unique constraint
        modelBuilder.Entity<ApiQuota>()
            .HasIndex(aq => new { aq.UserId, aq.ServiceId })
            .IsUnique();

        // ApiQuota — Phase 3.3d (TECHSPEC §16 H10) 신규 컬럼 기본값 명시.
        // EF 가 .NET 기본값(0L)도 처리하지만, 운영 DB 에 직접 ALTER TABLE 시 default 가 필요한 경우를 대비.
        modelBuilder.Entity<ApiQuota>()
            .Property(e => e.CurrentTokens)
            .HasDefaultValue(0L);

        // UserPreference unique constraint
        modelBuilder.Entity<UserPreference>()
            .HasIndex(up => new { up.UserId, up.PreferenceKey })
            .IsUnique();

        // ChatMessage Role check constraint (PG 호환 식별자 표기 — Phase 3.6)
        modelBuilder.Entity<ChatMessage>()
            .ToTable(t => t.HasCheckConstraint("CK_ChatMessages_Role", "\"Role\" IN ('user', 'assistant', 'system')"));

        // User Status check constraint (PG 호환 식별자 표기 — Phase 3.6)
        modelBuilder.Entity<User>()
            .ToTable(t => t.HasCheckConstraint("CK_Users_Status", "\"Status\" IN ('Active', 'Pending', 'Inactive')"));

        // ApiService unique ServiceCode
        modelBuilder.Entity<ApiService>()
            .HasIndex(s => s.ServiceCode)
            .IsUnique();

        // Agent unique AgentCode
        modelBuilder.Entity<Agent>()
            .HasIndex(a => a.AgentCode)
            .IsUnique();

        // Agent performance indexes
        modelBuilder.Entity<Agent>()
            .HasIndex(a => a.IsActive);

        modelBuilder.Entity<Agent>()
            .HasIndex(a => new { a.IsActive, a.IsPublic });

        modelBuilder.Entity<Agent>()
            .HasIndex(a => new { a.IsActive, a.CreatedBy });

        modelBuilder.Entity<Agent>()
            .HasIndex(a => new { a.IsActive, a.SortOrder, a.CreatedAt });

        // UserSession unique SessionToken
        modelBuilder.Entity<UserSession>()
            .HasIndex(s => s.SessionToken)
            .IsUnique();

        // SystemSetting unique SettingKey
        modelBuilder.Entity<SystemSetting>()
            .HasIndex(s => s.SettingKey)
            .IsUnique();

        // Role unique RoleName
        modelBuilder.Entity<Role>()
            .HasIndex(r => r.RoleName)
            .IsUnique();

        // User.Email UNIQUE — Phase 3.3b (TECHSPEC §16 C4)
        // 이메일 중복 가입 + race condition 차단. 기존 코드는 [Required]+MaxLength(100)만 부여하고
        // DB 레벨 UNIQUE 가 부재하여 동시 가입 요청 시 중복 행 생성 가능했음.
        modelBuilder.Entity<User>()
            .HasIndex(u => u.Email)
            .IsUnique();

        // ApiKey.KeyHash UNIQUE — Phase 3.3c (TECHSPEC §16 C3)
        // 인증 핫패스(`ApiKeyAuthService.ValidateApiKeyAsync`)가 활성 키 전체 로드 후 풀스캔
        // 복호화 비교(O(N))하던 결함 해소. SHA-256 hex 64자 컬럼에 UNIQUE 인덱스를 부착하여
        // 단건 조회로 단축. NULL(legacy 행) 다수 허용을 위해 PG 의 부분 인덱스로 자동 매핑됨.
        modelBuilder.Entity<ApiKey>()
            .HasIndex(k => k.KeyHash)
            .IsUnique();

        // ApiKey.(KeyType, IsActive, ServiceCode) 복합 인덱스 — 트랙 #91 (ApiKeyPoolService DB 통합).
        // `IApiKeyPoolService.RefreshAsync()` 가 5분 주기로 `WHERE KeyType='Provider' AND IsActive=true AND ServiceCode=...`
        // 형태로 외부 LLM 풀 키만 조회하므로 좌측 prefix 최적화를 위해 (KeyType → IsActive → ServiceCode) 순서로 정렬.
        // External 키 인증 핫패스(KeyHash UNIQUE 단건 조회)와 영향 무관.
        modelBuilder.Entity<ApiKey>()
            .HasIndex(k => new { k.KeyType, k.IsActive, k.ServiceCode })
            .HasDatabaseName("IX_ApiKeys_KeyType_IsActive_ServiceCode");

        // TeamMember unique constraint (활성 멤버만)
        modelBuilder.Entity<TeamMember>()
            .HasIndex(tm => new { tm.TeamId, tm.UserId })
            .IsUnique()
            .HasFilter("\"IsActive\" = true");

        // ── Phase 8 (ADR-2): AgentDocument 의 (AgentId, DocumentId) UNIQUE 인덱스는
        // 자체 KB 제거와 함께 삭제됨.

        // ExamplePrompt Prompt 컬럼을 text(PG)로 명시 — 길이 제한 없음 (Phase 3.2: 이전 nvarchar(max) → text)
        modelBuilder.Entity<ExamplePrompt>()
            .Property(e => e.Prompt)
            .HasColumnType("text");

        // Tool unique ToolCode
        modelBuilder.Entity<Tool>()
            .HasIndex(t => t.ToolCode)
            .IsUnique();

        // Tool performance indexes
        modelBuilder.Entity<Tool>()
            .HasIndex(t => t.IsActive);

        modelBuilder.Entity<Tool>()
            .HasIndex(t => new { t.IsActive, t.ToolType });

        // Workflow unique WorkflowCode
        modelBuilder.Entity<Workflow>()
            .HasIndex(w => w.WorkflowCode)
            .IsUnique();

        // Workflow performance indexes
        modelBuilder.Entity<Workflow>()
            .HasIndex(w => w.IsActive);

        modelBuilder.Entity<Workflow>()
            .HasIndex(w => new { w.IsActive, w.CreatedBy });

        // ApiServiceModel indexes
        modelBuilder.Entity<ApiServiceModel>()
            .HasIndex(asm => new { asm.ServiceId, asm.ModelName })
            .IsUnique();

        modelBuilder.Entity<ApiServiceModel>()
            .HasIndex(asm => new { asm.ServiceId, asm.IsActive, asm.SortOrder });

        // BannedWord indexes
        modelBuilder.Entity<BannedWord>()
            .HasIndex(bw => new { bw.AgentId, bw.IsActive });

        modelBuilder.Entity<BannedWord>()
            .HasIndex(bw => new { bw.Word, bw.IsActive });

        // PiiDetectionLog indexes
        modelBuilder.Entity<PiiDetectionLog>()
            .HasIndex(pdl => new { pdl.UserId, pdl.DetectedAt });

        modelBuilder.Entity<PiiDetectionLog>()
            .HasIndex(pdl => new { pdl.AgentId, pdl.DetectedAt });

        modelBuilder.Entity<PiiDetectionLog>()
            .HasIndex(pdl => pdl.DetectionType);

        modelBuilder.Entity<PiiDetectionLog>()
            .HasIndex(pdl => pdl.DetectedAt);

        // Presentation.Slides: text(PG) 명시 — JSON 문자열 (레거시 컬럼, 신규는 PresentationSlides 테이블 사용)
        modelBuilder.Entity<Presentation>()
            .Property(p => p.Slides)
            .HasColumnType("text");

        // PresentationSlide — PresentationId + SlideNumber 복합 인덱스 (순서 조회용)
        modelBuilder.Entity<PresentationSlide>()
            .HasIndex(s => new { s.PresentationId, s.SlideNumber });

        // PresentationSlide — Content/ChartsJson/TablesJson/ImagesJson text(PG) 명시 (Phase 3.2: 이전 nvarchar(max) → text)
        modelBuilder.Entity<PresentationSlide>()
            .Property(s => s.Content).HasColumnType("text");
        modelBuilder.Entity<PresentationSlide>()
            .Property(s => s.ChartsJson).HasColumnType("text");
        modelBuilder.Entity<PresentationSlide>()
            .Property(s => s.TablesJson).HasColumnType("text");
        modelBuilder.Entity<PresentationSlide>()
            .Property(s => s.ImagesJson).HasColumnType("text");

        // ── Performance Indexes ──────────────────────────────────────────────────
        // ChatMessage.ConversationId: 대화별 메시지 조회 (GetMessagesAsync)
        modelBuilder.Entity<ChatMessage>()
            .HasIndex(m => m.ConversationId)
            .HasDatabaseName("IX_ChatMessages_ConversationId");

        // ChatConversation.(UserId, LastMessageAt): 사용자별 대화 목록 + 정렬
        modelBuilder.Entity<ChatConversation>()
            .HasIndex(c => new { c.UserId, c.LastMessageAt })
            .HasDatabaseName("IX_ChatConversations_UserId_LastMessageAt");

        // ActivityLog.(UserId, CreatedAt): 사용자별 활동 로그 기간 조회
        modelBuilder.Entity<ActivityLog>()
            .HasIndex(a => new { a.UserId, a.CreatedAt })
            .HasDatabaseName("IX_ActivityLogs_UserId_CreatedAt");

        // ApiUsage.(UserId, ServiceId, RequestTime): Analytics 집계 쿼리
        modelBuilder.Entity<ApiUsage>()
            .HasIndex(u => new { u.UserId, u.ServiceId, u.RequestTime })
            .HasDatabaseName("IX_ApiUsages_UserId_ServiceId_RequestTime");

        // ApiUsage.RequestTime: 날짜 범위 단독 필터 (전체/서비스 불문 조회)
        modelBuilder.Entity<ApiUsage>()
            .HasIndex(u => u.RequestTime)
            .HasDatabaseName("IX_ApiUsages_RequestTime");

        // ApiUsage.(RequestTime, ServiceId): 서비스별 날짜 범위 필터
        modelBuilder.Entity<ApiUsage>()
            .HasIndex(u => new { u.RequestTime, u.ServiceId })
            .HasDatabaseName("IX_ApiUsages_RequestTime_ServiceId");

        // ApiUsage.(RequestTime, StatusCode): 상태별 날짜 범위 필터
        modelBuilder.Entity<ApiUsage>()
            .HasIndex(u => new { u.RequestTime, u.StatusCode })
            .HasDatabaseName("IX_ApiUsages_RequestTime_StatusCode");

        // ApiUsage.Prompt: 최대 500자
        modelBuilder.Entity<ApiUsage>()
            .Property(u => u.Prompt)
            .HasMaxLength(500);

        // ── Phase 8 (ADR-2): KnowledgeBaseDocuments / DocumentChunks 인덱스는
        // 자체 KB 코드/스키마 제거와 함께 삭제됨. RAG 단일 권위는 DocUtil.

        // ── Phase 4.3 — Tenants + Departments (ADR-8 / Q1 옵션 B) ───────────
        // Tenant.TenantCode UNIQUE — 외부 노출 식별자의 단일성 보장
        modelBuilder.Entity<Tenant>()
            .HasIndex(t => t.TenantCode)
            .IsUnique();

        // Tenant.Creator (선택 FK, Users.UserId) — DELETE 시 SET NULL.
        // 운영자 계정 삭제가 Tenant 행을 함께 지우지 않도록 한다.
        modelBuilder.Entity<Tenant>()
            .HasOne(t => t.Creator)
            .WithMany()
            .HasForeignKey(t => t.CreatedBy)
            .OnDelete(DeleteBehavior.SetNull);

        // Department.DepartmentCode UNIQUE — 외부 노출 식별자의 단일성 보장
        modelBuilder.Entity<Department>()
            .HasIndex(d => d.DepartmentCode)
            .IsUnique();

        // Department.TenantId 조회 인덱스 — Tenant 별 부서 목록 조회용
        modelBuilder.Entity<Department>()
            .HasIndex(d => d.TenantId)
            .HasDatabaseName("IX_Departments_TenantId");

        // Department.ParentDepartmentId 조회 인덱스 — 트리 탐색용
        modelBuilder.Entity<Department>()
            .HasIndex(d => d.ParentDepartmentId)
            .HasDatabaseName("IX_Departments_ParentDepartmentId");

        // Department → Tenant FK (NOT NULL). DELETE 시 RESTRICT —
        // Tenant 가 부서를 가지고 있으면 Tenant 삭제를 차단해 데이터 무결성을 강제.
        modelBuilder.Entity<Department>()
            .HasOne(d => d.Tenant)
            .WithMany(t => t.Departments)
            .HasForeignKey(d => d.TenantId)
            .OnDelete(DeleteBehavior.Restrict);

        // Department → ParentDepartment self-FK (선택). DELETE 시 RESTRICT —
        // 상위 부서 삭제 전에 하위 부서를 명시적으로 재배치하도록 강제.
        modelBuilder.Entity<Department>()
            .HasOne(d => d.ParentDepartment)
            .WithMany(d => d.ChildDepartments)
            .HasForeignKey(d => d.ParentDepartmentId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
