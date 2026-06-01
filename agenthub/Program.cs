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
using Hangfire.PostgreSql;
using Microsoft.Extensions.FileProviders;
using Polly;
using Polly.Extensions.Http;

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

// Entity Framework Core — PostgreSQL (Phase 3.1, Npgsql provider 전환)
builder.Services.AddDbContext<AIAgentManagementDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection"), npg =>
    {
        npg.CommandTimeout(30); // 30초 타임아웃
    }));

// MemoryCache 추가 (금칙어 캐싱용)
builder.Services.AddMemoryCache();

// Hangfire services
builder.Services.AddScoped<QuotaResetJob>();
builder.Services.AddScoped<ReportGenerationJob>();
// 트랙 #91 — 외부 LLM 키 풀 5분 주기 갱신 잡.
builder.Services.AddScoped<ApiKeyPoolRefreshJob>();

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

    // SignalR(WebSocket)은 Authorization 헤더를 전달할 수 없으므로
    // /hubs/* 경로 한정으로 ?access_token= 쿼리 토큰을 인식한다.
    options.Events = new JwtBearerEvents
    {
        OnMessageReceived = context =>
        {
            var accessToken = context.Request.Query["access_token"];
            var path = context.HttpContext.Request.Path;
            if (!string.IsNullOrEmpty(accessToken) && path.StartsWithSegments("/hubs"))
            {
                context.Token = accessToken;
            }
            return Task.CompletedTask;
        }
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
            .UsePostgreSqlStorage(opt => opt.UseNpgsqlConnection(hangfireConnection),
                new PostgreSqlStorageOptions
                {
                    SchemaName = "hangfire", // AGENT_HUB.hangfire 스키마 사용
                    PrepareSchemaIfNecessary = true,
                    // Hangfire.PostgreSql 1.20+ 는 QueuePollInterval=Zero 를 unsafe 로 차단 (Phase 6.5).
                    // SQL Server 시점에는 Zero 가 효율적이었으나 PG 는 최소 500ms 권장.
                    QueuePollInterval = TimeSpan.FromMilliseconds(500)
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

// Nexus(사내 LAN-only LLM) Named HttpClient — Phase 5.1, ADR-1 옵션 B.
// BaseUrl 기본값은 LAN 의 Nexus FastAPI 인스턴스. SharedSecret 은 NexusClient 내부에서 헤더로 부착.
//
// 트랙 #92 보강:
//   - 운영 Nexus orchestrator(Machine A) 는 HTTPS + self-signed 인증서로 LAN 노출(8443).
//   - LAN 격리(ADR-11 air-gap) 환경이라 운영자가 `Nexus:AcceptSelfSignedCert=true` 토글 시
//     인증서 검증을 우회한다. 외부망 노출 시점에는 정식 cert 또는 운영 trust store 등록 필요.
builder.Services.AddHttpClient("nexus", client =>
{
    var nexusBaseUrl = builder.Configuration["Nexus:BaseUrl"]
                       ?? "https://192.168.22.223:8443"; // Machine A Nexus orchestrator(HTTPS LAN)
    client.BaseAddress = new Uri(nexusBaseUrl);
    client.Timeout = TimeSpan.FromSeconds(
        builder.Configuration.GetValue<int>("Nexus:DefaultTimeoutSeconds", 60));
})
.ConfigurePrimaryHttpMessageHandler(() =>
{
    var handler = new HttpClientHandler();

    // LAN-only Nexus 의 self-signed 인증서 허용 옵션.
    // 운영자가 명시적으로 `Nexus:AcceptSelfSignedCert=true` 설정한 경우에만 활성.
    // 미설정 시 .NET 기본 검증(루트 CA 신뢰 체인) 적용.
    var acceptSelfSigned = builder.Configuration.GetValue<bool>("Nexus:AcceptSelfSignedCert", false);
    if (acceptSelfSigned)
    {
        handler.ServerCertificateCustomValidationCallback = (_, _, _, _) => true;
    }
    return handler;
});

// ────────────────────────────────────────────────────────────────────────────
// DocUtil(RAG/문서 운영) Named HttpClient — Phase 6.1 도입, Phase 10.x 회복탄력성 보강.
// ADR-2 (RAG 단일 권위) — DocUtil 은 운영자 콘솔의 모든 BFF 호출 경로.
//
// 회복탄력성 정책 (Phase 10.x, 2026-05-11):
//   - 5xx / HttpRequestException 만 retry — 4xx (422 validation 등) 는 비즈니스
//     오류이므로 즉시 전파(retry 가 의미 없고 사용자 입력 검증 응답이 지연되면 안 됨).
//   - Retry 3회, exponential backoff: 200ms / 500ms / 1000ms.
//     (총 최대 추가 지연 ≈ 1.7s — 사용자 체감 가능하지만 운영자 콘솔에는 허용 범위)
//   - Circuit Breaker: 5회 연속 실패 시 30초 차단 — DocUtil 다운 시 즉시 502 전파
//     하여 cascade 차단(현재 60s 단일 timeout 보다 fail-fast).
//
// Named client 두 개:
//   1. "docutil"             — 일반 호출(60s timeout, 위 Retry/CB 동일)
//   2. "docutil-longrunning" — 5분 timeout (Report 다운로드 / Template preview /
//                                 Documents V2 export 등 long-running endpoint 전용)
//
// 참고:
//   - HttpClient.Timeout 은 "각 시도 + 모든 retry 합" 의 절대 상한이므로 60s 이내
//     1.7s retry budget 이 다 소진되지 않도록 retry handler 가 각 시도마다 ResetTimer
//     없음 — 표준 동작.
//   - PII 마스킹은 DocUtilClient 의 EnsureSuccessOrThrowKoreanAsync 가 담당.
// ────────────────────────────────────────────────────────────────────────────

// 공통 회복탄력성 정책 — Retry 3회 + Circuit Breaker(5/30s).
// 두 named client 가 같은 정책을 공유한다(timeout 만 다름).
static IAsyncPolicy<HttpResponseMessage> GetDocUtilRetryPolicy()
{
    // HandleTransientHttpError = 5xx + HttpRequestException. 4xx 는 retry 대상 외.
    return HttpPolicyExtensions
        .HandleTransientHttpError()
        .WaitAndRetryAsync(
            retryCount: 3,
            sleepDurationProvider: attempt => attempt switch
            {
                1 => TimeSpan.FromMilliseconds(200),
                2 => TimeSpan.FromMilliseconds(500),
                _ => TimeSpan.FromMilliseconds(1000),
            },
            onRetry: (outcome, delay, attempt, _) =>
            {
                // Polly Retry 는 ILogger 직접 주입이 어려우므로 콘솔 trace 만(LogInfo 대신).
                // 실제 운영 진단은 DocUtilClient 측의 LogError + status code 로 충분.
                Console.WriteLine(
                    $"[DocUtil HTTP retry] attempt={attempt}, delay={delay.TotalMilliseconds}ms, " +
                    $"status={(int?)outcome.Result?.StatusCode}, exception={outcome.Exception?.GetType().Name}");
            });
}

static IAsyncPolicy<HttpResponseMessage> GetDocUtilCircuitBreakerPolicy()
{
    // 5회 연속 실패 → 30초 차단(BrokenCircuitException 발생).
    // 차단 중 호출은 즉시 예외 → DocUtilClient 의 DocUtilUpstreamException 변환 → 502/503.
    //
    // Phase 10.x Task #9 (2026-05-15) 주석 보강:
    //   HandleTransientHttpError 는 5xx + HttpRequestException 만 처리 — 4xx(특히 401/403)
    //   는 CB 카운터에 집계되지 않는다. 따라서 토큰 갱신 실패로 인한 401 무한 사이클은
    //   본 CB 정책이 아니라 DocUtilTokenProvider 의 fail-fast 동작으로 차단된다:
    //     - 토큰 갱신 모든 경로 실패 → DocUtilTokenProvider 가 DocUtilUpstreamException
    //       (TOKEN_MISSING / TOKEN_FORBIDDEN) 을 즉시 throw → DocUtilClient 는 HTTP 호출
    //       자체를 시도하지 않음 → CB 카운터 영향 없음 → 운영자가 자격 정상화하면 즉시 회복.
    return HttpPolicyExtensions
        .HandleTransientHttpError()
        .CircuitBreakerAsync(
            handledEventsAllowedBeforeBreaking: 5,
            durationOfBreak: TimeSpan.FromSeconds(30),
            onBreak: (outcome, breakDelay) =>
            {
                Console.WriteLine(
                    $"[DocUtil HTTP circuit breaker] OPENED for {breakDelay.TotalSeconds}s — " +
                    $"status={(int?)outcome.Result?.StatusCode}, exception={outcome.Exception?.GetType().Name}");
            },
            onReset: () => Console.WriteLine("[DocUtil HTTP circuit breaker] RESET"),
            onHalfOpen: () => Console.WriteLine("[DocUtil HTTP circuit breaker] HALF-OPEN"));
}

builder.Services.AddHttpClient("docutil", client =>
{
    var docutilBaseUrl = builder.Configuration["DocUtil:BaseUrl"]
                         ?? "http://localhost:8000"; // DocUtil FastAPI 기본값
    client.BaseAddress = new Uri(docutilBaseUrl);
    client.Timeout = TimeSpan.FromSeconds(
        builder.Configuration.GetValue<int>("DocUtil:DefaultTimeoutSeconds", 60));
})
    .AddPolicyHandler(GetDocUtilRetryPolicy())
    .AddPolicyHandler(GetDocUtilCircuitBreakerPolicy());

// Long-running endpoint 전용 — Report 다운로드, Template preview, Documents V2 export 등.
// 5분 절대 timeout. Retry/CB 정책은 동일하게 적용(서버 5xx 시 재시도 가치 있음).
builder.Services.AddHttpClient("docutil-longrunning", client =>
{
    var docutilBaseUrl = builder.Configuration["DocUtil:BaseUrl"]
                         ?? "http://localhost:8000";
    client.BaseAddress = new Uri(docutilBaseUrl);
    client.Timeout = TimeSpan.FromMinutes(
        builder.Configuration.GetValue<int>("DocUtil:LongRunningTimeoutMinutes", 5));
})
    .AddPolicyHandler(GetDocUtilRetryPolicy())
    .AddPolicyHandler(GetDocUtilCircuitBreakerPolicy());

builder.Services.AddHttpClient(); // 기본 클라이언트 (기타 HTTP 호출용)

// HttpContextAccessor 추가 (PII 로깅용)
builder.Services.AddHttpContextAccessor();

// 서비스 등록
builder.Services.AddScoped<IAuthService, AuthService>();
builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddScoped<IAgentService, AgentService>();
builder.Services.AddScoped<IChatService, ChatService>();
builder.Services.AddScoped<IEmbeddingService, EmbeddingService>();
// ── Phase 8 (ADR-2): IDocumentIndexingService / IKnowledgeBaseService 는 자체 KB
// 제거와 함께 DI 등록을 삭제. RAG 단일 권위는 DocUtil 이며 RagService 가 위임한다.
builder.Services.AddScoped<IRagService, RagService>();
builder.Services.AddScoped<IQuotaService, QuotaService>();
builder.Services.AddScoped<INexusClient, NexusClient>(); // Phase 5.1 — Nexus 옵션 B 클라이언트
// DocUtil 토큰 자동 갱신 — 만료 5분 전 refresh / re-login. Singleton(인스턴스 캐시) 으로 등록
//   하여 모든 DocUtilClient 인스턴스(Scoped) 가 공통 토큰 캐시 공유.
builder.Services.AddSingleton<IDocUtilTokenProvider, DocUtilTokenProvider>();
builder.Services.AddScoped<IDocUtilClient, DocUtilClient>(); // Phase 6.1 — DocUtil RAG/문서 BFF 클라이언트 (ADR-2 RAG 단일 권위)
// RAG 응답 품질 개선 — query 다국어 정규화 (한국어↔영문) + RRF 결합.
// IServiceScopeFactory 로 IAiProxyService 를 lazy 해결(순환 의존 차단)하므로 Singleton 안전.
builder.Services.AddSingleton<IQueryRewriter, LlmQueryRewriter>();
// Phase 4 — RAG 운영 관측성. in-memory atomic 카운터(Interlocked) — captive 안전.
//   QueryRewriter(Singleton) / DocUtilClient(Scoped) / RagService(Scoped) 모두 동일 인스턴스 공유.
builder.Services.AddSingleton<IRagMetrics, RagMetrics>();
builder.Services.AddScoped<IHybridRouter, HybridRouter>(); // Phase 5.2 — Hybrid 라우팅 결정 엔진(PII/라벨/capability/cost)
builder.Services.AddScoped<IAiProxyService, AiProxyService>();
builder.Services.AddScoped<IAnalyticsService, AnalyticsService>();
// 트랙 #147 M1 (2026-06-01) — 운영자 보고서 정식 구현.
builder.Services.AddScoped<IReportsService, ReportsService>();
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
        catch (Npgsql.PostgresException pgEx)
        {
            // PostgreSQL 서버에서 보낸 표준 SQLSTATE 오류 (28P01 인증 실패, 42P01 테이블 없음 등)
            logger.LogError(pgEx, "=== PostgreSQL 오류 발생 ===");
            logger.LogError($"SQLSTATE: {pgEx.SqlState}");
            logger.LogError($"오류 메시지: {pgEx.Message}");
            logger.LogError($"심각도: {pgEx.Severity}");
            logger.LogError($"스키마: {pgEx.SchemaName ?? "(미지정)"}");
            logger.LogError($"테이블: {pgEx.TableName ?? "(미지정)"}");
            logger.LogError("애플리케이션은 계속 실행되지만 데이터베이스 기능은 작동하지 않을 수 있습니다.");
        }
        catch (Npgsql.NpgsqlException npgEx)
        {
            // 클라이언트측 연결 오류 (호스트 unreachable, 타임아웃 등) — PostgresException 의 부모 타입
            logger.LogError(npgEx, "=== Npgsql 연결 오류 발생 ===");
            logger.LogError($"오류 타입: {npgEx.GetType().Name}");
            logger.LogError($"오류 메시지: {npgEx.Message}");
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
            // 트랙 #112 (2026-05-27): SPA cache 정책 분리 (file name 기반).
            // - .html (index.html, SPA shell): no-cache → 사용자가 새 chunk hash reference
            //   를 즉시 받도록 강제 (브라우저 ETag/Last-Modified default 사용 시 stale 결함).
            // - .js/.css/이미지 (hashed asset): 1년 immutable → chunk hash 변경 시에만 재요청.
            //
            // 주의: Request.Path 가 아닌 ctx.File.Name 으로 판정 — MapFallbackToFile 이
            // /admin/docutil-projects 같은 SPA 경로에 index.html 응답 시 path 는 원본
            // 그대로 유지되어 path.EndsWith(".html") 매칭 실패. ctx.File.Name 은
            // 실제 응답 파일 이름이라 fallback 도 정확 판정.
            //
            // 결함 사례: 트랙 #111 axios cache-buster fix 가 새 chunk 에 포함됐으나, 사용자
            // 브라우저가 cached index.html (이전 chunk reference) 사용 → fix 코드 도달 안 함
            // → DELETE 2회 후 반영 결함 재발.
            var fileName = ctx.File?.Name ?? string.Empty;
            var isHtml = fileName.EndsWith(".html", StringComparison.OrdinalIgnoreCase);
            if (isHtml)
            {
                ctx.Context.Response.Headers["Cache-Control"] = "no-store, no-cache, must-revalidate";
                ctx.Context.Response.Headers["Pragma"] = "no-cache";
                ctx.Context.Response.Headers["Expires"] = "0";
            }
            else
            {
                // hashed asset (vite 가 파일명에 hash 부착) — 1년 immutable cache.
                ctx.Context.Response.Headers["Cache-Control"] = "public, max-age=31536000, immutable";
            }
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

// 트랙 #111 + #112 (2026-05-27): cache 정책 통합 middleware.
// /api/* + HTML 응답 (index.html / SPA fallback) → no-cache 강제 부착.
// hashed asset (.js/.css) 은 UseStaticFiles 의 OnPrepareResponse 가 immutable 처리.
//
// 핵심: MapFallbackToFile + UseDefaultFiles 는 StaticFiles 의 OnPrepareResponse 를
// 우회하는 경로 — Content-Type 기반으로 응답 직전 헤더 강제 부착이 정공법.
app.Use(async (ctx, next) =>
{
    ctx.Response.OnStarting(() =>
    {
        var path = ctx.Request.Path.Value;
        var isApi = path != null && path.StartsWith("/api/", StringComparison.OrdinalIgnoreCase);
        var contentType = ctx.Response.ContentType ?? string.Empty;
        var isHtml = contentType.Contains("text/html", StringComparison.OrdinalIgnoreCase);

        if (isApi || isHtml)
        {
            ctx.Response.Headers["Cache-Control"] = "no-store, no-cache, must-revalidate";
            ctx.Response.Headers["Pragma"] = "no-cache";
            ctx.Response.Headers["Expires"] = "0";
        }
        return Task.CompletedTask;
    });
    await next();
});

app.MapControllers();
app.MapHub<ChatHub>("/hubs/chat").RequireAuthorization();
app.MapHub<NotificationHub>("/hubs/notification").RequireAuthorization();

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

        // 트랙 #91 — 외부 LLM 키 풀 5분 주기 갱신.
        // DB 의 KeyType="Provider" 행과 appsettings 폴백을 합쳐 풀을 원자적으로 교체.
        recurringJobManager.AddOrUpdate<ApiKeyPoolRefreshJob>(
            "api-key-pool-refresh",
            j => j.RefreshAsync(),
            "*/5 * * * *");

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

// 트랙 #91 — 부팅 직후 1회 외부 LLM 키 풀 즉시 적재 (DB Provider 키 + appsettings 합산).
// Hangfire 5분 주기를 기다리지 않고 첫 요청부터 신규 키를 사용 가능하게 한다.
// 백그라운드 Task.Run 으로 격리 — 풀 로드 실패가 앱 기동 실패로 이어지지 않게 함 (P10 / anti-pattern #10 의도된 격리).
app.Lifetime.ApplicationStarted.Register(() => Task.Run(async () =>
{
    using var startupScope = app.Services.CreateScope();
    var pool = startupScope.ServiceProvider.GetRequiredService<IApiKeyPoolService>();
    var poolLogger = startupScope.ServiceProvider.GetRequiredService<ILogger<Program>>();
    try
    {
        await pool.RefreshAsync();
        poolLogger.LogInformation("[ApiKeyPool] 부팅 직후 초기 풀 로드 완료");
    }
    catch (Exception ex)
    {
        poolLogger.LogError(ex, "[ApiKeyPool] 부팅 직후 초기 풀 로드 실패 — 5분 후 Hangfire 잡이 재시도");
    }
}));

try
{
    app.Run();
}
catch (Exception ex)
{
    startupLogger.LogCritical(ex, "애플리케이션 시작 실패!");
    throw;
}
