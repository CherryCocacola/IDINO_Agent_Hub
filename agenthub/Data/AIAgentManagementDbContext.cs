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
    public DbSet<KnowledgeBaseDocument> KnowledgeBaseDocuments { get; set; }
    public DbSet<DocumentChunk> DocumentChunks { get; set; }
    public DbSet<SystemSetting> SystemSettings { get; set; }
    public DbSet<ApiKey> ApiKeys { get; set; }
    public DbSet<Team> Teams { get; set; }
    public DbSet<TeamMember> TeamMembers { get; set; }
    public DbSet<AgentDocument> AgentDocuments { get; set; }
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

        // UserPreference unique constraint
        modelBuilder.Entity<UserPreference>()
            .HasIndex(up => new { up.UserId, up.PreferenceKey })
            .IsUnique();

        // ChatMessage Role check constraint
        modelBuilder.Entity<ChatMessage>()
            .ToTable(t => t.HasCheckConstraint("CK_ChatMessages_Role", "[Role] IN ('user', 'assistant', 'system')"));

        // User Status check constraint
        modelBuilder.Entity<User>()
            .ToTable(t => t.HasCheckConstraint("CK_Users_Status", "[Status] IN ('Active', 'Pending', 'Inactive')"));

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

        // TeamMember unique constraint (활성 멤버만)
        modelBuilder.Entity<TeamMember>()
            .HasIndex(tm => new { tm.TeamId, tm.UserId })
            .IsUnique()
            .HasFilter("[IsActive] = 1");

        // AgentDocument unique constraint
        modelBuilder.Entity<AgentDocument>()
            .HasIndex(ad => new { ad.AgentId, ad.DocumentId })
            .IsUnique();

        // ExamplePrompt Prompt 컬럼을 nvarchar(max)로 명시적으로 설정
        modelBuilder.Entity<ExamplePrompt>()
            .Property(e => e.Prompt)
            .HasColumnType("nvarchar(max)");

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

        // Presentation.Slides: nvarchar(max) 명시 (레거시 컬럼, 신규는 PresentationSlides 테이블 사용)
        modelBuilder.Entity<Presentation>()
            .Property(p => p.Slides)
            .HasColumnType("nvarchar(max)");

        // PresentationSlide — PresentationId + SlideNumber 복합 인덱스 (순서 조회용)
        modelBuilder.Entity<PresentationSlide>()
            .HasIndex(s => new { s.PresentationId, s.SlideNumber });

        // PresentationSlide — Content/ChartsJson/TablesJson/ImagesJson nvarchar(max) 명시
        modelBuilder.Entity<PresentationSlide>()
            .Property(s => s.Content).HasColumnType("nvarchar(max)");
        modelBuilder.Entity<PresentationSlide>()
            .Property(s => s.ChartsJson).HasColumnType("nvarchar(max)");
        modelBuilder.Entity<PresentationSlide>()
            .Property(s => s.TablesJson).HasColumnType("nvarchar(max)");
        modelBuilder.Entity<PresentationSlide>()
            .Property(s => s.ImagesJson).HasColumnType("nvarchar(max)");

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

        // KnowledgeBaseDocument.UserId: 사용자별 문서 목록 조회
        modelBuilder.Entity<KnowledgeBaseDocument>()
            .HasIndex(d => d.UserId)
            .HasDatabaseName("IX_KnowledgeBaseDocuments_UserId");

        // DocumentChunk.DocumentId: RAG 검색 시 청크 조회
        modelBuilder.Entity<DocumentChunk>()
            .HasIndex(c => c.DocumentId)
            .HasDatabaseName("IX_DocumentChunks_DocumentId");
    }
}
