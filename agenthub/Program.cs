using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using System.Security.Claims;
using System.Text;
using System.Threading.RateLimiting;
using AIAgentManagement.Data;
using AIAgentManagement.Services;
using AIAgentManagement.Hubs;
using AIAgentManagement.BackgroundJobs;
using AIAgentManagement.Tools;
using StackExchange.Redis;
using Hangfire;
using Hangfire.SqlServer;
using Microsoft.Extensions.FileProviders;

var builder = WebApplication.CreateBuilder(args);

// Kestrel 요청 본문 크기 제한 설정 (100MB)
builder.WebHost.ConfigureKestrel(options =>
{
    options.Limits.MaxRequestBodySize = 104857600; // 100MB in bytes
});

// Add services to the container
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase;
        // ChartDto.Data 등 Dictionary<string, object> 내 JsonElement 직렬화 지원 (저장 오류 방지)
        options.JsonSerializerOptions.Converters.Add(new AIAgentManagement.Infrastructure.JsonElementRawConverter());
        options.JsonSerializerOptions.Converters.Add(new AIAgentManagement.Infrastructure.DictionaryStringObjectJsonConverter());
    });
// [ApiController] ModelState 자동 검증 오류를 ErrorResponseDto 형식으로 통일
builder.Services.Configure<Microsoft.AspNetCore.Mvc.ApiBehaviorOptions>(options =>
{
    options.InvalidModelStateResponseFactory = context =>
    {
        var errors = context.ModelState
            .Where(e => e.Value?.Errors.Count > 0)
            .SelectMany(e => e.Value!.Errors.Select(err => $"{e.Key}: {err.ErrorMessage}"))
            .ToList();

        var response = new AIAgentManagement.DTOs.ErrorResponseDto(
            message: "입력값이 올바르지 않습니다.",
            errorCode: "VALIDATION_ERROR",
            details: new { Errors = errors }
        );

        return new Microsoft.AspNetCore.Mvc.BadRequestObjectResult(response);
    };
});

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "AI Agent Management API", Version = "v1" });
    
    // JWT 인증을 위한 Swagger 설정
    c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Description = "JWT Authorization header using the Bearer scheme. Enter 'Bearer' [space] and then your token",
        Name = "Authorization",
        In = ParameterLocation.Header,
        Type = SecuritySchemeType.ApiKey,
        Scheme = "Bearer"
    });
    
    c.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference
                {
                    Type = ReferenceType.SecurityScheme,
                    Id = "Bearer"
                }
            },
            Array.Empty<string>()
        }
    });
});

// Entity Framework Core
builder.Services.AddDbContext<AIAgentManagementDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection"), sqlOptions =>
    {
        sqlOptions.CommandTimeout(30); // 30초 타임아웃
    }));

// MemoryCache 추가 (금칙어 캐싱용)
builder.Services.AddMemoryCache();

// Hangfire services
builder.Services.AddScoped<QuotaResetJob>();
builder.Services.AddScoped<ReportGenerationJob>();

// JWT 인증 설정
var jwtSettings = builder.Configuration.GetSection("JwtSettings");
var secretKey = jwtSettings["SecretKey"] ?? throw new InvalidOperationException("JWT SecretKey not configured");

builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = true,
        ValidateAudience = true,
        ValidateLifetime = true,
        ValidateIssuerSigningKey = true,
        ValidIssuer = jwtSettings["Issuer"],
        ValidAudience = jwtSettings["Audience"],
        IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secretKey)),
        ClockSkew = TimeSpan.Zero
    };
});

// SignalR
builder.Services.AddSignalR();

// Redis (선택적) - Redis가 없으면 자동으로 MemoryCache 사용
var redisConnection = builder.Configuration.GetConnectionString("Redis");
if (!string.IsNullOrEmpty(redisConnection))
{
    try
    {
        builder.Services.AddStackExchangeRedisCache(options =>
        {
            options.Configuration = redisConnection;
            options.InstanceName = "AIAgentManagement:";
        });
        
        // Redis 연결 테스트 (선택적)
        var loggerFactory = LoggerFactory.Create(b => b.AddConsole());
        var testLogger = loggerFactory.CreateLogger<Program>();
        testLogger.LogInformation("Redis cache configured with connection: {Connection}", redisConnection);
    }
    catch (Exception ex)
    {
        // Redis 설정 실패 시 MemoryCache 사용 (Redis 없어도 정상 작동)
        var loggerFactory = LoggerFactory.Create(b => b.AddConsole());
        var testLogger = loggerFactory.CreateLogger<Program>();
        testLogger.LogWarning(ex, "Redis configuration failed, falling back to in-memory cache. Redis is optional. Connection: {Connection}", redisConnection);
        builder.Services.AddDistributedMemoryCache();
    }
}
else
{
    // Redis 연결 문자열이 없으면 MemoryCache 사용 (기본값)
    builder.Services.AddDistributedMemoryCache();
}

// Hangfire
try
{
    var hangfireConnection = builder.Configuration.GetConnectionString("DefaultConnection");
    if (!string.IsNullOrEmpty(hangfireConnection))
    {
        builder.Services.AddHangfire(configuration => configuration
            .SetDataCompatibilityLevel(CompatibilityLevel.Version_180)
            .UseSimpleAssemblyNameTypeSerializer()
            .UseRecommendedSerializerSettings()
            .UseSqlServerStorage(hangfireConnection, new SqlServerStorageOptions
            {
                CommandBatchMaxTimeout = TimeSpan.FromMinutes(5),
                SlidingInvisibilityTimeout = TimeSpan.FromMinutes(5),
                QueuePollInterval = TimeSpan.Zero,
                UseRecommendedIsolationLevel = true,
                DisableGlobalLocks = true,
                PrepareSchemaIfNecessary = true // 스키마 자동 생성
            }));
        
        builder.Services.AddHangfireServer();
    }
}
catch (Exception)
{
    // Hangfire 설정 실패 시 MemoryCache만 사용하고 계속 진행
    // 로깅은 나중에 서비스가 등록된 후에 수행
}

// CORS 설정
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowVueApp", policy =>
    {
        policy.WithOrigins(
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1",
                "http://localhost",
                "https://agenthub.idino.co.kr"   // 프로덕션 도메인
              )
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials()
              // 파일 다운로드 폴백 헤더를 브라우저에서 읽을 수 있도록 노출
              .WithExposedHeaders("X-Pdf-Fallback-Pptx", "Content-Disposition");
    });
});

// HttpClient for AI Proxy — Named Client로 연결 풀링 및 타임아웃 사전 설정
var defaultAiTimeout = builder.Configuration.GetValue<int>("AiApiSettings:DefaultTimeout", 120);

builder.Services.AddHttpClient("openai",
    c => c.Timeout = TimeSpan.FromSeconds(defaultAiTimeout));
builder.Services.AddHttpClient("claude",
    c => c.Timeout = TimeSpan.FromSeconds(defaultAiTimeout));
builder.Services.AddHttpClient("gemini",
    c => c.Timeout = TimeSpan.FromSeconds(defaultAiTimeout));
builder.Services.AddHttpClient("perplexity",
    c => c.Timeout = TimeSpan.FromSeconds(defaultAiTimeout));
builder.Services.AddHttpClient("mistral",
    c => c.Timeout = TimeSpan.FromSeconds(defaultAiTimeout));
builder.Services.AddHttpClient(); // 기본 클라이언트 (기타 HTTP 호출용)

// HttpContextAccessor 추가 (PII 로깅용)
builder.Services.AddHttpContextAccessor();

// 서비스 등록
builder.Services.AddScoped<IAuthService, AuthService>();
builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddScoped<IAgentService, AgentService>();
builder.Services.AddScoped<IChatService, ChatService>();
builder.Services.AddScoped<IEmbeddingService, EmbeddingService>();
builder.Services.AddScoped<IDocumentIndexingService, DocumentIndexingService>();
builder.Services.AddScoped<IRagService, RagService>();
builder.Services.AddScoped<IKnowledgeBaseService, KnowledgeBaseService>();
builder.Services.AddScoped<IQuotaService, QuotaService>();
builder.Services.AddScoped<IAiProxyService, AiProxyService>();
builder.Services.AddScoped<IAnalyticsService, AnalyticsService>();
builder.Services.AddScoped<IActivityLogService, ActivityLogService>();
builder.Services.AddScoped<INotificationService, NotificationService>();
builder.Services.AddScoped<IEmailService, EmailService>();
builder.Services.AddScoped<IFileService, FileService>();
builder.Services.AddScoped<IFileParsingService, FileParsingService>();
builder.Services.AddScoped<IApiKeyService, ApiKeyService>();
builder.Services.AddScoped<IApiKeyAuthService, ApiKeyAuthService>();
builder.Services.AddScoped<IBannedWordService, BannedWordService>();
builder.Services.AddScoped<IPiiDetectionService, PiiDetectionService>();
builder.Services.AddScoped<ISystemSettingsService, SystemSettingsService>();
builder.Services.AddScoped<ITeamService, TeamService>();
builder.Services.AddScoped<ITextExtractionService, TextExtractionService>();
builder.Services.AddScoped<PptxGenerationService>();
builder.Services.AddScoped<IPresentationService, PresentationService>();
builder.Services.AddScoped<IPptxTemplateParser, PptxTemplateParser>();
builder.Services.AddScoped<IPresentationTemplateService, PresentationTemplateService>();
builder.Services.AddScoped<IToolService, ToolService>();
builder.Services.AddScoped<IToolExecutionService, ToolExecutionService>();
builder.Services.AddScoped<ICSharpToolExecutor, CSharpToolExecutor>();
builder.Services.AddScoped<IScriptToolExecutor, ScriptToolExecutor>();
builder.Services.AddScoped<IApiToolExecutor, ApiToolExecutor>();
builder.Services.AddScoped<IWorkflowService, WorkflowService>();
builder.Services.AddScoped<IWorkflowExecutionService, WorkflowExecutionService>();
builder.Services.AddScoped<IWorkflowEngine, WorkflowEngine>();
builder.Services.AddSingleton<IJwtService, JwtService>();
builder.Services.AddSingleton<CachingService>();
// API Key Rate Limiter (Singleton: 상태를 메모리에 유지해야 함)
builder.Services.AddSingleton<IApiKeyRateLimiter, ApiKeyRateLimiter>();
// API Key Pool — 다중 API 키 라운드로빈 Load Balancing (Singleton)
builder.Services.AddSingleton<IApiKeyPoolService, ApiKeyPoolService>();
// ActivityLog 비동기 배치 처리 — 미들웨어에서 DB 직접 접근 제거
builder.Services.AddSingleton<AIAgentManagement.Infrastructure.ActivityLogChannel>();
builder.Services.AddHostedService<AIAgentManagement.BackgroundJobs.ActivityLogWorker>();

// ── IP Rate Limiting (ASP.NET Core 8 내장) ────────────────────────────────────
builder.Services.AddRateLimiter(options =>
{
    // 게스트(비로그인) 공개 채팅 API: IP당 분당 20회
    options.AddPolicy("ip-guest", httpContext =>
        RateLimitPartition.GetFixedWindowLimiter(
            partitionKey: httpContext.Connection.RemoteIpAddress?.ToString() ?? "unknown",
            factory: _ => new FixedWindowRateLimiterOptions
            {
                PermitLimit              = 20,
                Window                   = TimeSpan.FromMinutes(1),
                QueueProcessingOrder     = QueueProcessingOrder.OldestFirst,
                QueueLimit               = 0
            }));

    // OpenAI 호환 API (/v1/*): IP당 분당 30회
    options.AddPolicy("ip-openai", httpContext =>
        RateLimitPartition.GetFixedWindowLimiter(
            partitionKey: httpContext.Connection.RemoteIpAddress?.ToString() ?? "unknown",
            factory: _ => new FixedWindowRateLimiterOptions
            {
                PermitLimit              = 30,
                Window                   = TimeSpan.FromMinutes(1),
                QueueProcessingOrder     = QueueProcessingOrder.OldestFirst,
                QueueLimit               = 0
            }));

    // 로그인 사용자 API: 사용자별 분당 60회
    options.AddPolicy("per-user", httpContext =>
    {
        var userId = httpContext.User?.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        var key = string.IsNullOrEmpty(userId)
            ? httpContext.Connection.RemoteIpAddress?.ToString() ?? "unknown"
            : $"user:{userId}";

        return RateLimitPartition.GetFixedWindowLimiter(
            partitionKey: key,
            factory: _ => new FixedWindowRateLimiterOptions
            {
                PermitLimit          = 60,
                Window               = TimeSpan.FromMinutes(1),
                QueueProcessingOrder = QueueProcessingOrder.OldestFirst,
                QueueLimit           = 0
            });
    });

    // 429 응답 공통 처리
    options.RejectionStatusCode = 429;
    options.OnRejected = async (context, token) =>
    {
        context.HttpContext.Response.Headers["Retry-After"] = "60";
        context.HttpContext.Response.ContentType = "application/json";
        await context.HttpContext.Response.WriteAsync(
            "{\"message\":\"요청이 너무 많습니다. 60초 후 다시 시도해주세요.\",\"retryAfterSeconds\":60}",
            token);
    };
});

// SPA 설정
builder.Services.AddSpaStaticFiles(configuration =>
{
    // 프로덕션에서는 wwwroot에 빌드된 파일이 복사됨
    if (builder.Environment.IsDevelopment())
    {
        configuration.RootPath = "ClientApp/dist";
    }
    else
    {
        configuration.RootPath = "wwwroot";
    }
});

var app = builder.Build();

// Database initialization
try
{
    using (var scope = app.Services.CreateScope())
    {
        var context = scope.ServiceProvider.GetRequiredService<AIAgentManagementDbContext>();
        var logger = scope.ServiceProvider.GetRequiredService<ILogger<Program>>();
        
        try
        {
            logger.LogInformation("=== 데이터베이스 연결 테스트 시작 ===");
            var configuration = scope.ServiceProvider.GetRequiredService<IConfiguration>();
            var connectionString = configuration.GetConnectionString("DefaultConnection");
            logger.LogInformation($"연결 문자열: {connectionString?.Replace("Password=rnehrwhgdk20@^", "Password=***")}");
            
            // 데이터베이스 연결 테스트
            var canConnect = await context.Database.CanConnectAsync();
            if (canConnect)
            {
                logger.LogInformation("✓ 데이터베이스 연결 성공!");
                
                // 추가 정보 확인
                try
                {
                    var connection = context.Database.GetDbConnection();
                    var dbName = connection.Database;
                    var serverVersion = connection.ServerVersion;
                    logger.LogInformation($"  - 서버 버전: {serverVersion}");
                    logger.LogInformation($"  - 데이터베이스: {dbName}");
                }
                catch { }
                
                // 데이터베이스 초기화
                await DatabaseInitializer.SeedAsync(context);
                logger.LogInformation("✓ 데이터베이스 초기화 완료");
                
                // 모든 사용자 비밀번호 재설정 (임시 - 한 번 실행 후 주석 처리 권장)
                // try
                // {
                //     logger.LogInformation("=== 모든 사용자 비밀번호 재설정 시작 ===");
                //     await Tools.ResetAllUsersPassword.ResetPasswordsAsync(scope.ServiceProvider, "Admin123!");
                //     logger.LogInformation("✓ 비밀번호 재설정 완료");
                // }
                // catch (Exception resetEx)
                // {
                //     logger.LogError(resetEx, "비밀번호 재설정 중 오류 발생 (계속 진행)");
                // }
            }
            else
            {
                logger.LogWarning("✗ 데이터베이스 연결 실패 - CanConnectAsync()가 false를 반환했습니다.");
                logger.LogWarning("연결 문자열을 확인하세요.");
            }
        }
        catch (Microsoft.Data.SqlClient.SqlException sqlEx)
        {
            logger.LogError(sqlEx, "=== SQL Server 오류 발생 ===");
            logger.LogError($"오류 번호: {sqlEx.Number}");
            logger.LogError($"오류 메시지: {sqlEx.Message}");
            logger.LogError($"서버: {sqlEx.Server}");
            logger.LogError($"상태: {sqlEx.State}");
            logger.LogError($"심각도: {sqlEx.Class}");
            logger.LogError("애플리케이션은 계속 실행되지만 데이터베이스 기능은 작동하지 않을 수 있습니다.");
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "=== 데이터베이스 초기화 실패 ===");
            logger.LogError($"오류 타입: {ex.GetType().Name}");
            logger.LogError($"오류 메시지: {ex.Message}");
            logger.LogError("애플리케이션은 계속 실행되지만 데이터베이스 기능은 작동하지 않을 수 있습니다.");
        }
    }
}
catch (Exception ex)
{
    var appLogger = app.Services.GetRequiredService<ILogger<Program>>();
    appLogger.LogError(ex, "Failed to initialize database. Application will continue.");
}

// Configure the HTTP request pipeline
// 전역 예외 처리 — 환경 무관하게 최상단 등록
app.UseMiddleware<AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware>();

// 보안 헤더 (GS인증 보안성 요구사항)
app.UseMiddleware<AIAgentManagement.Middleware.SecurityHeadersMiddleware>();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// agenthub.idino.co.kr 도메인일 때만 HTTP → HTTPS 리다이렉트 (다른 호스트는 그대로)
app.UseMiddleware<AIAgentManagement.Middleware.RequireHttpsForDomainMiddleware>();

// 프로덕션 환경에서 정적 파일 제공 설정
if (app.Environment.IsDevelopment())
{
    // 개발 환경: SPA 정적 파일 사용
    app.UseSpaStaticFiles();
}
else
{
    // 프로덕션 환경: wwwroot의 정적 파일 제공
    // UseDefaultFiles는 UseStaticFiles보다 먼저 와야 함
    app.UseDefaultFiles();
    app.UseStaticFiles(new StaticFileOptions
    {
        OnPrepareResponse = ctx =>
        {
            // 정적 파일이 성공적으로 제공되면 로깅 (선택사항)
            // ctx.Context.Response.Headers.Append("Cache-Control", "public,max-age=31536000");
        }
    });
}

app.UseCors("AllowVueApp");

app.UseAuthentication();
app.UseAuthorization();

// IP Rate Limiting (인증 후에 배치: 로그인 사용자 정책이 User 클레임을 참조하므로)
app.UseRateLimiter();

// Activity Logging Middleware (인증 후에 실행되어야 함)
app.UseMiddleware<AIAgentManagement.Middleware.ActivityLoggingMiddleware>();

app.MapControllers();
app.MapHub<ChatHub>("/hubs/chat");
app.MapHub<NotificationHub>("/hubs/notification");

// Hangfire Dashboard (Hangfire가 설정된 경우에만)
try
{
    var configuration = app.Services.GetRequiredService<IConfiguration>();
    var hangfireConnection = configuration.GetConnectionString("DefaultConnection");
    if (!string.IsNullOrEmpty(hangfireConnection))
    {
        app.UseHangfireDashboard("/hangfire", new DashboardOptions
        {
            Authorization = new[] { new HangfireAuthorizationFilter() }
        });
    }
}
catch (Exception ex)
{
    var dashboardLogger = app.Services.GetRequiredService<ILogger<Program>>();
    dashboardLogger.LogWarning(ex, "Hangfire Dashboard initialization failed. Dashboard will not be available.");
}

// Schedule Hangfire jobs
try
{
    using (var scope = app.Services.CreateScope())
    {
        var recurringJobManager = scope.ServiceProvider.GetRequiredService<IRecurringJobManager>();
        var logger = scope.ServiceProvider.GetRequiredService<ILogger<Program>>();
        
        // Daily quota reset at midnight UTC
        recurringJobManager.AddOrUpdate(
            "daily-quota-reset",
            () => scope.ServiceProvider.GetRequiredService<QuotaResetJob>().ResetDailyQuotas(),
            Cron.Daily
        );
        
        // Monthly quota reset on the 1st of each month
        recurringJobManager.AddOrUpdate(
            "monthly-quota-reset",
            () => scope.ServiceProvider.GetRequiredService<QuotaResetJob>().ResetMonthlyQuotas(),
            Cron.Monthly
        );
        
        // Daily report generation
        recurringJobManager.AddOrUpdate(
            "daily-report",
            () => scope.ServiceProvider.GetRequiredService<ReportGenerationJob>().GenerateDailyReport(),
            Cron.Daily(1) // At 1 AM
        );
        
        // Monthly report generation
        recurringJobManager.AddOrUpdate(
            "monthly-report",
            () => scope.ServiceProvider.GetRequiredService<ReportGenerationJob>().GenerateMonthlyReport(),
            Cron.Monthly(1, 2) // On the 1st at 2 AM
        );
        
        logger.LogInformation("Hangfire jobs scheduled successfully");
    }
}
catch (Exception ex)
{
    var jobLogger = app.Services.GetRequiredService<ILogger<Program>>();
    jobLogger.LogWarning(ex, "Failed to schedule Hangfire jobs. Application will continue.");
}

// SPA fallback
if (app.Environment.IsDevelopment())
{
    app.UseSpa(spa =>
    {
        spa.Options.SourcePath = "ClientApp";
        spa.UseProxyToSpaDevelopmentServer("http://localhost:5173");
    });
}
else
{
    // 프로덕션 환경: SPA 라우팅을 위한 fallback
    // API, hubs, hangfire 경로는 제외하고 나머지는 index.html로
    app.MapFallbackToFile("/index.html");
}

// 애플리케이션 시작 로그
var startupLogger = app.Services.GetRequiredService<ILogger<Program>>();
startupLogger.LogInformation("=== 애플리케이션 시작 ===");
startupLogger.LogInformation($"Environment: {app.Environment.EnvironmentName}");
startupLogger.LogInformation("애플리케이션이 요청을 수신할 준비가 되었습니다.");

try
{
    app.Run();
}
catch (Exception ex)
{
    startupLogger.LogCritical(ex, "애플리케이션 시작 실패!");
    throw;
}
