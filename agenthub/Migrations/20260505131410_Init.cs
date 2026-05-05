using System;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace AIAgentManagement.Migrations
{
    /// <inheritdoc />
    public partial class Init : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.EnsureSchema(
                name: "AIAgentManagement");

            migrationBuilder.CreateTable(
                name: "ApiServices",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    ServiceId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    ServiceCode = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    ServiceName = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    Description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    IconClass = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    ColorCode = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: true),
                    ApiEndpoint = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    DefaultModel = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    CostPerRequest = table.Column<decimal>(type: "numeric(10,4)", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    SortOrder = table.Column<int>(type: "integer", nullable: false),
                    ServiceType = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ApiServices", x => x.ServiceId);
                });

            migrationBuilder.CreateTable(
                name: "ExamplePrompts",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    ExamplePromptId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    Title = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    Prompt = table.Column<string>(type: "text", nullable: false),
                    Description = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: true),
                    ServiceCode = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    Model = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    Category = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    IconClass = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    SortOrder = table.Column<int>(type: "integer", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ExamplePrompts", x => x.ExamplePromptId);
                });

            migrationBuilder.CreateTable(
                name: "Faqs",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    FaqId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    Question = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    Answer = table.Column<string>(type: "text", nullable: false),
                    Category = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    SortOrder = table.Column<int>(type: "integer", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Faqs", x => x.FaqId);
                });

            migrationBuilder.CreateTable(
                name: "Roles",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    RoleId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    RoleName = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    DisplayName = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    Description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    Permissions = table.Column<string>(type: "text", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Roles", x => x.RoleId);
                });

            migrationBuilder.CreateTable(
                name: "SystemSettings",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    SettingId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    SettingKey = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    SettingValue = table.Column<string>(type: "text", nullable: true),
                    DataType = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    Category = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    Description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    IsEncrypted = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_SystemSettings", x => x.SettingId);
                });

            migrationBuilder.CreateTable(
                name: "Tutorials",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    TutorialId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    Title = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    Description = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: true),
                    VideoUrl = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    ThumbnailUrl = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    Duration = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    Category = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    SortOrder = table.Column<int>(type: "integer", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    ViewCount = table.Column<int>(type: "integer", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Tutorials", x => x.TutorialId);
                });

            migrationBuilder.CreateTable(
                name: "Users",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    UserId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    Email = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    PasswordHash = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: false),
                    FullName = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    PhoneNumber = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: true),
                    Department = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    Bio = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    ProfileImageUrl = table.Column<string>(type: "text", nullable: true),
                    Status = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    IsEmailVerified = table.Column<bool>(type: "boolean", nullable: false),
                    LastLoginAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    IsDeleted = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    TwoFactorSecret = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: true),
                    IsTwoFactorEnabled = table.Column<bool>(type: "boolean", nullable: false),
                    TwoFactorBackupCodes = table.Column<string>(type: "text", nullable: true),
                    PasswordResetToken = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: true),
                    PasswordResetTokenExpiry = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Users", x => x.UserId);
                    table.CheckConstraint("CK_Users_Status", "[Status] IN ('Active', 'Pending', 'Inactive')");
                });

            migrationBuilder.CreateTable(
                name: "ApiServiceModels",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    ModelId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    ServiceId = table.Column<int>(type: "integer", nullable: false),
                    ModelName = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    Description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    SortOrder = table.Column<int>(type: "integer", nullable: false),
                    ModelType = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ApiServiceModels", x => x.ModelId);
                    table.ForeignKey(
                        name: "FK_ApiServiceModels_ApiServices_ServiceId",
                        column: x => x.ServiceId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "ApiServices",
                        principalColumn: "ServiceId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ActivityLogs",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    LogId = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    UserId = table.Column<int>(type: "integer", nullable: true),
                    ActivityType = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    EntityType = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    EntityId = table.Column<int>(type: "integer", nullable: true),
                    Description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    IpAddress = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    UserAgent = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    Details = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ActivityLogs", x => x.LogId);
                    table.ForeignKey(
                        name: "FK_ActivityLogs_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId");
                });

            migrationBuilder.CreateTable(
                name: "Agents",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    AgentId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    AgentCode = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    AgentName = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    Description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    ServiceId = table.Column<int>(type: "integer", nullable: false),
                    SystemPrompt = table.Column<string>(type: "text", nullable: true),
                    IconClass = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    ColorCode = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: true),
                    Temperature = table.Column<decimal>(type: "numeric(3,2)", nullable: true),
                    MaxTokens = table.Column<int>(type: "integer", nullable: true),
                    DefaultModel = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    IsPublic = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedBy = table.Column<int>(type: "integer", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    SortOrder = table.Column<int>(type: "integer", nullable: false),
                    EnableRag = table.Column<bool>(type: "boolean", nullable: false),
                    PiiProtectionEnabled = table.Column<bool>(type: "boolean", nullable: false),
                    PiiProtectionMode = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: true),
                    WelcomeMessage = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    PlaceholderText = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: true),
                    ChatTheme = table.Column<string>(type: "character varying(10)", maxLength: 10, nullable: true),
                    AllowGuestChat = table.Column<bool>(type: "boolean", nullable: false),
                    AllowedEmbedDomains = table.Column<string>(type: "character varying(2000)", maxLength: 2000, nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Agents", x => x.AgentId);
                    table.ForeignKey(
                        name: "FK_Agents_ApiServices_ServiceId",
                        column: x => x.ServiceId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "ApiServices",
                        principalColumn: "ServiceId",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Agents_Users_CreatedBy",
                        column: x => x.CreatedBy,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ApiQuotas",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    QuotaId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    UserId = table.Column<int>(type: "integer", nullable: false),
                    ServiceId = table.Column<int>(type: "integer", nullable: false),
                    MonthlyLimit = table.Column<int>(type: "integer", nullable: false),
                    MonthlyTokenLimit = table.Column<long>(type: "bigint", nullable: true),
                    DailyLimit = table.Column<int>(type: "integer", nullable: false),
                    CostLimit = table.Column<decimal>(type: "numeric(10,2)", nullable: false),
                    CurrentUsage = table.Column<int>(type: "integer", nullable: false),
                    CurrentTokens = table.Column<long>(type: "bigint", nullable: false, defaultValue: 0L),
                    CurrentCost = table.Column<decimal>(type: "numeric(10,2)", nullable: false),
                    AlertThreshold = table.Column<int>(type: "integer", nullable: false),
                    IsAlertEnabled = table.Column<bool>(type: "boolean", nullable: false),
                    LastResetAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ApiQuotas", x => x.QuotaId);
                    table.ForeignKey(
                        name: "FK_ApiQuotas_ApiServices_ServiceId",
                        column: x => x.ServiceId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "ApiServices",
                        principalColumn: "ServiceId",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ApiQuotas_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "KnowledgeBaseDocuments",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    DocumentId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    UserId = table.Column<int>(type: "integer", nullable: false),
                    Title = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    Content = table.Column<string>(type: "text", nullable: false),
                    SourceType = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    SourceId = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: true),
                    IsIndexed = table.Column<bool>(type: "boolean", nullable: false),
                    IndexedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_KnowledgeBaseDocuments", x => x.DocumentId);
                    table.ForeignKey(
                        name: "FK_KnowledgeBaseDocuments_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Presentations",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    PresentationId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    UserId = table.Column<int>(type: "integer", nullable: false),
                    Title = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    Slides = table.Column<string>(type: "text", nullable: true),
                    ThemeId = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    SlideSize = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Presentations", x => x.PresentationId);
                    table.ForeignKey(
                        name: "FK_Presentations_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "PresentationTemplates",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    TemplateId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    TemplateName = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    Description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    TemplateFilePath = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    TemplateStructure = table.Column<string>(type: "text", nullable: true),
                    Category = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    IsPublic = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedBy = table.Column<int>(type: "integer", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_PresentationTemplates", x => x.TemplateId);
                    table.ForeignKey(
                        name: "FK_PresentationTemplates_Users_CreatedBy",
                        column: x => x.CreatedBy,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId");
                });

            migrationBuilder.CreateTable(
                name: "Teams",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    TeamId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    TeamName = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    Description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    Department = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    ManagerId = table.Column<int>(type: "integer", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Teams", x => x.TeamId);
                    table.ForeignKey(
                        name: "FK_Teams_Users_ManagerId",
                        column: x => x.ManagerId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId");
                });

            migrationBuilder.CreateTable(
                name: "Tools",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    ToolId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    ToolCode = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    ToolName = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    Description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    ToolType = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    Category = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    IconClass = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    ColorCode = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: true),
                    CreatedBy = table.Column<int>(type: "integer", nullable: false),
                    IsPublic = table.Column<bool>(type: "boolean", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Tools", x => x.ToolId);
                    table.ForeignKey(
                        name: "FK_Tools_Users_CreatedBy",
                        column: x => x.CreatedBy,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "UserPreferences",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    PreferenceId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    UserId = table.Column<int>(type: "integer", nullable: false),
                    PreferenceKey = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    PreferenceValue = table.Column<string>(type: "text", nullable: true),
                    DataType = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    Category = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    Description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_UserPreferences", x => x.PreferenceId);
                    table.ForeignKey(
                        name: "FK_UserPreferences_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "UserRoles",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    UserRoleId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    UserId = table.Column<int>(type: "integer", nullable: false),
                    RoleId = table.Column<int>(type: "integer", nullable: false),
                    AssignedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    AssignedBy = table.Column<int>(type: "integer", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_UserRoles", x => x.UserRoleId);
                    table.ForeignKey(
                        name: "FK_UserRoles_Roles_RoleId",
                        column: x => x.RoleId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Roles",
                        principalColumn: "RoleId",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_UserRoles_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "UserSessions",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    SessionId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    UserId = table.Column<int>(type: "integer", nullable: false),
                    SessionToken = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: false),
                    DeviceInfo = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    IpAddress = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    UserAgent = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    LoginAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    LastActivityAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    LogoutAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_UserSessions", x => x.SessionId);
                    table.ForeignKey(
                        name: "FK_UserSessions_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Workflows",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    WorkflowId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    WorkflowCode = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    WorkflowName = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    Description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    WorkflowDefinition = table.Column<string>(type: "text", nullable: true),
                    IconClass = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    ColorCode = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: true),
                    CreatedBy = table.Column<int>(type: "integer", nullable: false),
                    IsPublic = table.Column<bool>(type: "boolean", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Workflows", x => x.WorkflowId);
                    table.ForeignKey(
                        name: "FK_Workflows_Users_CreatedBy",
                        column: x => x.CreatedBy,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ApiKeys",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    ApiKeyId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    UserId = table.Column<int>(type: "integer", nullable: false),
                    KeyName = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    ServiceCode = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    AgentId = table.Column<int>(type: "integer", nullable: true),
                    EncryptedKey = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    KeyIv = table.Column<byte[]>(type: "bytea", nullable: true),
                    KeyTag = table.Column<byte[]>(type: "bytea", nullable: true),
                    KeyHash = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: true),
                    Description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    ExpiresAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    LastUsedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    UsageCount = table.Column<int>(type: "integer", nullable: false),
                    AllowedIps = table.Column<string>(type: "character varying(2000)", maxLength: 2000, nullable: true),
                    Scopes = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: true),
                    RateLimitPerMinute = table.Column<int>(type: "integer", nullable: true),
                    RateLimitPerDay = table.Column<int>(type: "integer", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ApiKeys", x => x.ApiKeyId);
                    table.ForeignKey(
                        name: "FK_ApiKeys_Agents_AgentId",
                        column: x => x.AgentId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Agents",
                        principalColumn: "AgentId");
                    table.ForeignKey(
                        name: "FK_ApiKeys_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "BannedWords",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    BannedWordId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    Word = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    AgentId = table.Column<int>(type: "integer", nullable: true),
                    Description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedBy = table.Column<int>(type: "integer", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BannedWords", x => x.BannedWordId);
                    table.ForeignKey(
                        name: "FK_BannedWords_Agents_AgentId",
                        column: x => x.AgentId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Agents",
                        principalColumn: "AgentId");
                    table.ForeignKey(
                        name: "FK_BannedWords_Users_CreatedBy",
                        column: x => x.CreatedBy,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ChatConversations",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    ConversationId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    UserId = table.Column<int>(type: "integer", nullable: false),
                    AgentId = table.Column<int>(type: "integer", nullable: true),
                    ServiceId = table.Column<int>(type: "integer", nullable: false),
                    Title = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: true),
                    Model = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    Temperature = table.Column<decimal>(type: "numeric(3,2)", nullable: true),
                    MaxTokens = table.Column<int>(type: "integer", nullable: true),
                    MessageCount = table.Column<int>(type: "integer", nullable: false),
                    TotalTokens = table.Column<int>(type: "integer", nullable: false),
                    TotalCost = table.Column<decimal>(type: "numeric(10,4)", nullable: false),
                    LastMessageAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    IsArchived = table.Column<bool>(type: "boolean", nullable: false),
                    IsPinned = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    SystemPrompt = table.Column<string>(type: "text", nullable: true),
                    Language = table.Column<string>(type: "character varying(10)", maxLength: 10, nullable: true),
                    EnableRag = table.Column<bool>(type: "boolean", nullable: false),
                    EnableWebSearch = table.Column<bool>(type: "boolean", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ChatConversations", x => x.ConversationId);
                    table.ForeignKey(
                        name: "FK_ChatConversations_Agents_AgentId",
                        column: x => x.AgentId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Agents",
                        principalColumn: "AgentId");
                    table.ForeignKey(
                        name: "FK_ChatConversations_ApiServices_ServiceId",
                        column: x => x.ServiceId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "ApiServices",
                        principalColumn: "ServiceId",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ChatConversations_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "PiiDetectionLogs",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    LogId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    UserId = table.Column<int>(type: "integer", nullable: true),
                    AgentId = table.Column<int>(type: "integer", nullable: true),
                    ConversationId = table.Column<int>(type: "integer", nullable: true),
                    DetectionType = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    OriginalMessage = table.Column<string>(type: "text", nullable: false),
                    ActionTaken = table.Column<string>(type: "text", nullable: false),
                    DetectedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    IpAddress = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_PiiDetectionLogs", x => x.LogId);
                    table.ForeignKey(
                        name: "FK_PiiDetectionLogs_Agents_AgentId",
                        column: x => x.AgentId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Agents",
                        principalColumn: "AgentId");
                    table.ForeignKey(
                        name: "FK_PiiDetectionLogs_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId");
                });

            migrationBuilder.CreateTable(
                name: "AgentDocuments",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    AgentDocumentId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    AgentId = table.Column<int>(type: "integer", nullable: false),
                    DocumentId = table.Column<int>(type: "integer", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_AgentDocuments", x => x.AgentDocumentId);
                    table.ForeignKey(
                        name: "FK_AgentDocuments_Agents_AgentId",
                        column: x => x.AgentId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Agents",
                        principalColumn: "AgentId",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_AgentDocuments_KnowledgeBaseDocuments_DocumentId",
                        column: x => x.DocumentId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "KnowledgeBaseDocuments",
                        principalColumn: "DocumentId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "DocumentChunks",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    ChunkId = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    DocumentId = table.Column<int>(type: "integer", nullable: false),
                    ChunkIndex = table.Column<int>(type: "integer", nullable: false),
                    Content = table.Column<string>(type: "text", nullable: false),
                    Embedding = table.Column<string>(type: "text", nullable: true),
                    Metadata = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_DocumentChunks", x => x.ChunkId);
                    table.ForeignKey(
                        name: "FK_DocumentChunks_KnowledgeBaseDocuments_DocumentId",
                        column: x => x.DocumentId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "KnowledgeBaseDocuments",
                        principalColumn: "DocumentId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "PresentationSlides",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    SlideId = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    PresentationId = table.Column<int>(type: "integer", nullable: false),
                    SlideNumber = table.Column<int>(type: "integer", nullable: false),
                    Title = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    Content = table.Column<string>(type: "text", nullable: false),
                    Layout = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    ImageUrl = table.Column<string>(type: "character varying(2000)", maxLength: 2000, nullable: true),
                    ImageDescription = table.Column<string>(type: "character varying(2000)", maxLength: 2000, nullable: true),
                    ImagePrompt = table.Column<string>(type: "character varying(2000)", maxLength: 2000, nullable: true),
                    ChartsJson = table.Column<string>(type: "text", nullable: true),
                    TablesJson = table.Column<string>(type: "text", nullable: true),
                    ImagesJson = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_PresentationSlides", x => x.SlideId);
                    table.ForeignKey(
                        name: "FK_PresentationSlides_Presentations_PresentationId",
                        column: x => x.PresentationId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Presentations",
                        principalColumn: "PresentationId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "TeamMembers",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    TeamMemberId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    TeamId = table.Column<int>(type: "integer", nullable: false),
                    UserId = table.Column<int>(type: "integer", nullable: false),
                    Role = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    JoinedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    LeftAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    AddedBy = table.Column<int>(type: "integer", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_TeamMembers", x => x.TeamMemberId);
                    table.ForeignKey(
                        name: "FK_TeamMembers_Teams_TeamId",
                        column: x => x.TeamId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Teams",
                        principalColumn: "TeamId",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_TeamMembers_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ToolVersions",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    VersionId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    ToolId = table.Column<int>(type: "integer", nullable: false),
                    Version = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    Code = table.Column<string>(type: "text", nullable: true),
                    Config = table.Column<string>(type: "text", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ToolVersions", x => x.VersionId);
                    table.ForeignKey(
                        name: "FK_ToolVersions_Tools_ToolId",
                        column: x => x.ToolId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Tools",
                        principalColumn: "ToolId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "WorkflowExecutions",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    ExecutionId = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    WorkflowId = table.Column<int>(type: "integer", nullable: false),
                    UserId = table.Column<int>(type: "integer", nullable: true),
                    InputData = table.Column<string>(type: "text", nullable: true),
                    OutputData = table.Column<string>(type: "text", nullable: true),
                    Status = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    ErrorMessage = table.Column<string>(type: "text", nullable: true),
                    StartedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    CompletedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    ExecutionTime = table.Column<int>(type: "integer", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_WorkflowExecutions", x => x.ExecutionId);
                    table.ForeignKey(
                        name: "FK_WorkflowExecutions_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId");
                    table.ForeignKey(
                        name: "FK_WorkflowExecutions_Workflows_WorkflowId",
                        column: x => x.WorkflowId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Workflows",
                        principalColumn: "WorkflowId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "WorkflowNodes",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    NodeId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    WorkflowId = table.Column<int>(type: "integer", nullable: false),
                    NodeCode = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    NodeType = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    NodeConfig = table.Column<string>(type: "text", nullable: true),
                    PositionX = table.Column<double>(type: "double precision", nullable: true),
                    PositionY = table.Column<double>(type: "double precision", nullable: true),
                    Connections = table.Column<string>(type: "text", nullable: true),
                    SortOrder = table.Column<int>(type: "integer", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_WorkflowNodes", x => x.NodeId);
                    table.ForeignKey(
                        name: "FK_WorkflowNodes_Workflows_WorkflowId",
                        column: x => x.WorkflowId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Workflows",
                        principalColumn: "WorkflowId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ApiUsages",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    UsageId = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    UserId = table.Column<int>(type: "integer", nullable: false),
                    ServiceId = table.Column<int>(type: "integer", nullable: false),
                    ConversationId = table.Column<int>(type: "integer", nullable: true),
                    Model = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    TokensUsed = table.Column<int>(type: "integer", nullable: true),
                    RequestCost = table.Column<decimal>(type: "numeric(10,4)", nullable: false),
                    RequestTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    ResponseTime = table.Column<int>(type: "integer", nullable: true),
                    StatusCode = table.Column<int>(type: "integer", nullable: true),
                    ErrorMessage = table.Column<string>(type: "text", nullable: true),
                    Prompt = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ApiUsages", x => x.UsageId);
                    table.ForeignKey(
                        name: "FK_ApiUsages_ApiServices_ServiceId",
                        column: x => x.ServiceId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "ApiServices",
                        principalColumn: "ServiceId",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ApiUsages_ChatConversations_ConversationId",
                        column: x => x.ConversationId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "ChatConversations",
                        principalColumn: "ConversationId");
                    table.ForeignKey(
                        name: "FK_ApiUsages_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ChatMessages",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    MessageId = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    ConversationId = table.Column<int>(type: "integer", nullable: false),
                    Role = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    Content = table.Column<string>(type: "text", nullable: false),
                    TokensUsed = table.Column<int>(type: "integer", nullable: true),
                    Model = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    FinishReason = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    Attachments = table.Column<string>(type: "text", nullable: true),
                    Metadata = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ChatMessages", x => x.MessageId);
                    table.CheckConstraint("CK_ChatMessages_Role", "[Role] IN ('user', 'assistant', 'system')");
                    table.ForeignKey(
                        name: "FK_ChatMessages_ChatConversations_ConversationId",
                        column: x => x.ConversationId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "ChatConversations",
                        principalColumn: "ConversationId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ToolExecutions",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    ExecutionId = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    ToolId = table.Column<int>(type: "integer", nullable: false),
                    VersionId = table.Column<int>(type: "integer", nullable: true),
                    UserId = table.Column<int>(type: "integer", nullable: true),
                    InputData = table.Column<string>(type: "text", nullable: true),
                    OutputData = table.Column<string>(type: "text", nullable: true),
                    Status = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    ErrorMessage = table.Column<string>(type: "text", nullable: true),
                    ExecutionTime = table.Column<int>(type: "integer", nullable: true),
                    MemoryUsage = table.Column<long>(type: "bigint", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ToolExecutions", x => x.ExecutionId);
                    table.ForeignKey(
                        name: "FK_ToolExecutions_ToolVersions_VersionId",
                        column: x => x.VersionId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "ToolVersions",
                        principalColumn: "VersionId");
                    table.ForeignKey(
                        name: "FK_ToolExecutions_Tools_ToolId",
                        column: x => x.ToolId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Tools",
                        principalColumn: "ToolId",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ToolExecutions_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId");
                });

            migrationBuilder.CreateTable(
                name: "WorkflowNodeExecutions",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    NodeExecutionId = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    ExecutionId = table.Column<long>(type: "bigint", nullable: false),
                    NodeId = table.Column<int>(type: "integer", nullable: false),
                    InputData = table.Column<string>(type: "text", nullable: true),
                    OutputData = table.Column<string>(type: "text", nullable: true),
                    Status = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    ErrorMessage = table.Column<string>(type: "text", nullable: true),
                    StartedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    CompletedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    ExecutionTime = table.Column<int>(type: "integer", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_WorkflowNodeExecutions", x => x.NodeExecutionId);
                    table.ForeignKey(
                        name: "FK_WorkflowNodeExecutions_WorkflowExecutions_ExecutionId",
                        column: x => x.ExecutionId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "WorkflowExecutions",
                        principalColumn: "ExecutionId",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_WorkflowNodeExecutions_WorkflowNodes_NodeId",
                        column: x => x.NodeId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "WorkflowNodes",
                        principalColumn: "NodeId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_ActivityLogs_UserId_CreatedAt",
                schema: "AIAgentManagement",
                table: "ActivityLogs",
                columns: new[] { "UserId", "CreatedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_AgentDocuments_AgentId_DocumentId",
                schema: "AIAgentManagement",
                table: "AgentDocuments",
                columns: new[] { "AgentId", "DocumentId" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_AgentDocuments_DocumentId",
                schema: "AIAgentManagement",
                table: "AgentDocuments",
                column: "DocumentId");

            migrationBuilder.CreateIndex(
                name: "IX_Agents_AgentCode",
                schema: "AIAgentManagement",
                table: "Agents",
                column: "AgentCode",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Agents_CreatedBy",
                schema: "AIAgentManagement",
                table: "Agents",
                column: "CreatedBy");

            migrationBuilder.CreateIndex(
                name: "IX_Agents_IsActive",
                schema: "AIAgentManagement",
                table: "Agents",
                column: "IsActive");

            migrationBuilder.CreateIndex(
                name: "IX_Agents_IsActive_CreatedBy",
                schema: "AIAgentManagement",
                table: "Agents",
                columns: new[] { "IsActive", "CreatedBy" });

            migrationBuilder.CreateIndex(
                name: "IX_Agents_IsActive_IsPublic",
                schema: "AIAgentManagement",
                table: "Agents",
                columns: new[] { "IsActive", "IsPublic" });

            migrationBuilder.CreateIndex(
                name: "IX_Agents_IsActive_SortOrder_CreatedAt",
                schema: "AIAgentManagement",
                table: "Agents",
                columns: new[] { "IsActive", "SortOrder", "CreatedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_Agents_ServiceId",
                schema: "AIAgentManagement",
                table: "Agents",
                column: "ServiceId");

            migrationBuilder.CreateIndex(
                name: "IX_ApiKeys_AgentId",
                schema: "AIAgentManagement",
                table: "ApiKeys",
                column: "AgentId");

            migrationBuilder.CreateIndex(
                name: "IX_ApiKeys_KeyHash",
                schema: "AIAgentManagement",
                table: "ApiKeys",
                column: "KeyHash",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ApiKeys_UserId",
                schema: "AIAgentManagement",
                table: "ApiKeys",
                column: "UserId");

            migrationBuilder.CreateIndex(
                name: "IX_ApiQuotas_ServiceId",
                schema: "AIAgentManagement",
                table: "ApiQuotas",
                column: "ServiceId");

            migrationBuilder.CreateIndex(
                name: "IX_ApiQuotas_UserId_ServiceId",
                schema: "AIAgentManagement",
                table: "ApiQuotas",
                columns: new[] { "UserId", "ServiceId" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ApiServiceModels_ServiceId_IsActive_SortOrder",
                schema: "AIAgentManagement",
                table: "ApiServiceModels",
                columns: new[] { "ServiceId", "IsActive", "SortOrder" });

            migrationBuilder.CreateIndex(
                name: "IX_ApiServiceModels_ServiceId_ModelName",
                schema: "AIAgentManagement",
                table: "ApiServiceModels",
                columns: new[] { "ServiceId", "ModelName" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ApiServices_ServiceCode",
                schema: "AIAgentManagement",
                table: "ApiServices",
                column: "ServiceCode",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ApiUsages_ConversationId",
                schema: "AIAgentManagement",
                table: "ApiUsages",
                column: "ConversationId");

            migrationBuilder.CreateIndex(
                name: "IX_ApiUsages_RequestTime",
                schema: "AIAgentManagement",
                table: "ApiUsages",
                column: "RequestTime");

            migrationBuilder.CreateIndex(
                name: "IX_ApiUsages_RequestTime_ServiceId",
                schema: "AIAgentManagement",
                table: "ApiUsages",
                columns: new[] { "RequestTime", "ServiceId" });

            migrationBuilder.CreateIndex(
                name: "IX_ApiUsages_RequestTime_StatusCode",
                schema: "AIAgentManagement",
                table: "ApiUsages",
                columns: new[] { "RequestTime", "StatusCode" });

            migrationBuilder.CreateIndex(
                name: "IX_ApiUsages_ServiceId",
                schema: "AIAgentManagement",
                table: "ApiUsages",
                column: "ServiceId");

            migrationBuilder.CreateIndex(
                name: "IX_ApiUsages_UserId_ServiceId_RequestTime",
                schema: "AIAgentManagement",
                table: "ApiUsages",
                columns: new[] { "UserId", "ServiceId", "RequestTime" });

            migrationBuilder.CreateIndex(
                name: "IX_BannedWords_AgentId_IsActive",
                schema: "AIAgentManagement",
                table: "BannedWords",
                columns: new[] { "AgentId", "IsActive" });

            migrationBuilder.CreateIndex(
                name: "IX_BannedWords_CreatedBy",
                schema: "AIAgentManagement",
                table: "BannedWords",
                column: "CreatedBy");

            migrationBuilder.CreateIndex(
                name: "IX_BannedWords_Word_IsActive",
                schema: "AIAgentManagement",
                table: "BannedWords",
                columns: new[] { "Word", "IsActive" });

            migrationBuilder.CreateIndex(
                name: "IX_ChatConversations_AgentId",
                schema: "AIAgentManagement",
                table: "ChatConversations",
                column: "AgentId");

            migrationBuilder.CreateIndex(
                name: "IX_ChatConversations_ServiceId",
                schema: "AIAgentManagement",
                table: "ChatConversations",
                column: "ServiceId");

            migrationBuilder.CreateIndex(
                name: "IX_ChatConversations_UserId_LastMessageAt",
                schema: "AIAgentManagement",
                table: "ChatConversations",
                columns: new[] { "UserId", "LastMessageAt" });

            migrationBuilder.CreateIndex(
                name: "IX_ChatMessages_ConversationId",
                schema: "AIAgentManagement",
                table: "ChatMessages",
                column: "ConversationId");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentChunks_DocumentId",
                schema: "AIAgentManagement",
                table: "DocumentChunks",
                column: "DocumentId");

            migrationBuilder.CreateIndex(
                name: "IX_KnowledgeBaseDocuments_UserId",
                schema: "AIAgentManagement",
                table: "KnowledgeBaseDocuments",
                column: "UserId");

            migrationBuilder.CreateIndex(
                name: "IX_PiiDetectionLogs_AgentId_DetectedAt",
                schema: "AIAgentManagement",
                table: "PiiDetectionLogs",
                columns: new[] { "AgentId", "DetectedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_PiiDetectionLogs_DetectedAt",
                schema: "AIAgentManagement",
                table: "PiiDetectionLogs",
                column: "DetectedAt");

            migrationBuilder.CreateIndex(
                name: "IX_PiiDetectionLogs_DetectionType",
                schema: "AIAgentManagement",
                table: "PiiDetectionLogs",
                column: "DetectionType");

            migrationBuilder.CreateIndex(
                name: "IX_PiiDetectionLogs_UserId_DetectedAt",
                schema: "AIAgentManagement",
                table: "PiiDetectionLogs",
                columns: new[] { "UserId", "DetectedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_Presentations_UserId",
                schema: "AIAgentManagement",
                table: "Presentations",
                column: "UserId");

            migrationBuilder.CreateIndex(
                name: "IX_PresentationSlides_PresentationId_SlideNumber",
                schema: "AIAgentManagement",
                table: "PresentationSlides",
                columns: new[] { "PresentationId", "SlideNumber" });

            migrationBuilder.CreateIndex(
                name: "IX_PresentationTemplates_CreatedBy",
                schema: "AIAgentManagement",
                table: "PresentationTemplates",
                column: "CreatedBy");

            migrationBuilder.CreateIndex(
                name: "IX_Roles_RoleName",
                schema: "AIAgentManagement",
                table: "Roles",
                column: "RoleName",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_SystemSettings_SettingKey",
                schema: "AIAgentManagement",
                table: "SystemSettings",
                column: "SettingKey",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_TeamMembers_TeamId_UserId",
                schema: "AIAgentManagement",
                table: "TeamMembers",
                columns: new[] { "TeamId", "UserId" },
                unique: true,
                filter: "[IsActive] = 1");

            migrationBuilder.CreateIndex(
                name: "IX_TeamMembers_UserId",
                schema: "AIAgentManagement",
                table: "TeamMembers",
                column: "UserId");

            migrationBuilder.CreateIndex(
                name: "IX_Teams_ManagerId",
                schema: "AIAgentManagement",
                table: "Teams",
                column: "ManagerId");

            migrationBuilder.CreateIndex(
                name: "IX_ToolExecutions_ToolId",
                schema: "AIAgentManagement",
                table: "ToolExecutions",
                column: "ToolId");

            migrationBuilder.CreateIndex(
                name: "IX_ToolExecutions_UserId",
                schema: "AIAgentManagement",
                table: "ToolExecutions",
                column: "UserId");

            migrationBuilder.CreateIndex(
                name: "IX_ToolExecutions_VersionId",
                schema: "AIAgentManagement",
                table: "ToolExecutions",
                column: "VersionId");

            migrationBuilder.CreateIndex(
                name: "IX_Tools_CreatedBy",
                schema: "AIAgentManagement",
                table: "Tools",
                column: "CreatedBy");

            migrationBuilder.CreateIndex(
                name: "IX_Tools_IsActive",
                schema: "AIAgentManagement",
                table: "Tools",
                column: "IsActive");

            migrationBuilder.CreateIndex(
                name: "IX_Tools_IsActive_ToolType",
                schema: "AIAgentManagement",
                table: "Tools",
                columns: new[] { "IsActive", "ToolType" });

            migrationBuilder.CreateIndex(
                name: "IX_Tools_ToolCode",
                schema: "AIAgentManagement",
                table: "Tools",
                column: "ToolCode",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ToolVersions_ToolId",
                schema: "AIAgentManagement",
                table: "ToolVersions",
                column: "ToolId");

            migrationBuilder.CreateIndex(
                name: "IX_UserPreferences_UserId_PreferenceKey",
                schema: "AIAgentManagement",
                table: "UserPreferences",
                columns: new[] { "UserId", "PreferenceKey" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_UserRoles_RoleId",
                schema: "AIAgentManagement",
                table: "UserRoles",
                column: "RoleId");

            migrationBuilder.CreateIndex(
                name: "IX_UserRoles_UserId_RoleId",
                schema: "AIAgentManagement",
                table: "UserRoles",
                columns: new[] { "UserId", "RoleId" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Users_Email",
                schema: "AIAgentManagement",
                table: "Users",
                column: "Email",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_UserSessions_SessionToken",
                schema: "AIAgentManagement",
                table: "UserSessions",
                column: "SessionToken",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_UserSessions_UserId",
                schema: "AIAgentManagement",
                table: "UserSessions",
                column: "UserId");

            migrationBuilder.CreateIndex(
                name: "IX_WorkflowExecutions_UserId",
                schema: "AIAgentManagement",
                table: "WorkflowExecutions",
                column: "UserId");

            migrationBuilder.CreateIndex(
                name: "IX_WorkflowExecutions_WorkflowId",
                schema: "AIAgentManagement",
                table: "WorkflowExecutions",
                column: "WorkflowId");

            migrationBuilder.CreateIndex(
                name: "IX_WorkflowNodeExecutions_ExecutionId",
                schema: "AIAgentManagement",
                table: "WorkflowNodeExecutions",
                column: "ExecutionId");

            migrationBuilder.CreateIndex(
                name: "IX_WorkflowNodeExecutions_NodeId",
                schema: "AIAgentManagement",
                table: "WorkflowNodeExecutions",
                column: "NodeId");

            migrationBuilder.CreateIndex(
                name: "IX_WorkflowNodes_WorkflowId",
                schema: "AIAgentManagement",
                table: "WorkflowNodes",
                column: "WorkflowId");

            migrationBuilder.CreateIndex(
                name: "IX_Workflows_CreatedBy",
                schema: "AIAgentManagement",
                table: "Workflows",
                column: "CreatedBy");

            migrationBuilder.CreateIndex(
                name: "IX_Workflows_IsActive",
                schema: "AIAgentManagement",
                table: "Workflows",
                column: "IsActive");

            migrationBuilder.CreateIndex(
                name: "IX_Workflows_IsActive_CreatedBy",
                schema: "AIAgentManagement",
                table: "Workflows",
                columns: new[] { "IsActive", "CreatedBy" });

            migrationBuilder.CreateIndex(
                name: "IX_Workflows_WorkflowCode",
                schema: "AIAgentManagement",
                table: "Workflows",
                column: "WorkflowCode",
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "ActivityLogs",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "AgentDocuments",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "ApiKeys",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "ApiQuotas",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "ApiServiceModels",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "ApiUsages",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "BannedWords",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "ChatMessages",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "DocumentChunks",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "ExamplePrompts",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "Faqs",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "PiiDetectionLogs",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "PresentationSlides",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "PresentationTemplates",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "SystemSettings",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "TeamMembers",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "ToolExecutions",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "Tutorials",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "UserPreferences",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "UserRoles",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "UserSessions",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "WorkflowNodeExecutions",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "ChatConversations",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "KnowledgeBaseDocuments",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "Presentations",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "Teams",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "ToolVersions",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "Roles",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "WorkflowExecutions",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "WorkflowNodes",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "Agents",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "Tools",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "Workflows",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "ApiServices",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "Users",
                schema: "AIAgentManagement");
        }
    }
}
