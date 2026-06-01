using AIAgentManagement.Models;
using BCrypt.Net;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace AIAgentManagement.Data;

public static class DatabaseInitializer
{
    /// <summary>
    /// AGENT_HUB 스키마(AIAgentManagement)에 baseline 마이그레이션을 적용하고
    /// 기본 시드 데이터(Roles / Admin / ApiServices / ApiServiceModels)를 멱등적으로 추가한다.
    /// PostgreSQL 마이그레이션(`MigrateAsync`)을 사용하므로 기존 EnsureCreatedAsync 가 만들었던
    /// 가짜 스키마와 마이그레이션 그래프 사이의 drift 위험은 본 시점에서 차단된다.
    /// </summary>
    /// <remarks>
    /// 외부 시그니처(`SeedAsync(AIAgentManagementDbContext)`)는 변경 금지 — Program.cs 호출 패턴 보존.
    /// 시드 단계별 try-catch 로 한 단계 실패가 전체를 막지 않게 한다 (Program.cs 의 의도된 swallow 와 동일 패턴).
    /// </remarks>
    public static async Task SeedAsync(AIAgentManagementDbContext context)
    {
        // ─── 1. 마이그레이션 적용 (EnsureCreatedAsync → MigrateAsync, TECHSPEC §16 C7) ───
        // 미적용 마이그레이션이 있으면 적용. 없으면 즉시 반환. baseline 부재 시(20260505131410_Init)
        // 자동으로 __EFMigrationsHistory 까지 함께 생성.
        try
        {
            await context.Database.MigrateAsync();
        }
        catch (Exception ex)
        {
            // 마이그레이션 실패는 전파해 상위 catch(Program.cs:417)가 SQL/PG 오류 분류하도록 둔다.
            // 시드만 실패한 경우와 구분되어야 함 (스키마 미존재면 시드는 의미 없음).
            Console.Error.WriteLine($"[DatabaseInitializer] MigrateAsync 실패: {ex.GetType().Name}: {ex.Message}");
            throw;
        }

        try
        {
            // Roles 시드
            if (!await context.Roles.AnyAsync())
            {
                var roles = new[]
                {
                    new Role { RoleName = "Admin", DisplayName = "관리자", Description = "시스템 전체 관리 권한", IsActive = true },
                    new Role { RoleName = "Developer", DisplayName = "개발자", Description = "Agent 생성 및 수정 권한", IsActive = true },
                    new Role { RoleName = "User", DisplayName = "사용자", Description = "기본 사용 권한", IsActive = true }
                };
                context.Roles.AddRange(roles);
                await context.SaveChangesAsync();
            }

            // Admin 사용자 생성 또는 업데이트
            var existingAdmin = await context.Users.FirstOrDefaultAsync(u => u.Email == "admin@example.com");
            if (existingAdmin == null)
            {
                // Admin 사용자가 없으면 생성
                var adminRole = await context.Roles.FirstOrDefaultAsync(r => r.RoleName == "Admin");
                if (adminRole != null)
                {
                    var adminUser = new User
                    {
                        Email = "admin@example.com",
                        PasswordHash = BCrypt.Net.BCrypt.HashPassword("Admin123!"),
                        FullName = "관리자",
                        Status = "Active",
                        IsEmailVerified = true,
                        IsDeleted = false,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    };
                    context.Users.Add(adminUser);
                    await context.SaveChangesAsync();

                    var userRole = new UserRole
                    {
                        UserId = adminUser.UserId,
                        RoleId = adminRole.RoleId,
                        AssignedAt = DateTime.UtcNow
                    };
                    context.UserRoles.Add(userRole);
                    await context.SaveChangesAsync();
                }
            }
            else
            {
                // Admin 사용자가 있으면 상태 확인 및 수정
                bool needsUpdate = false;
                
                if (existingAdmin.Status != "Active")
                {
                    existingAdmin.Status = "Active";
                    needsUpdate = true;
                }
                
                if (existingAdmin.IsDeleted)
                {
                    existingAdmin.IsDeleted = false;
                    needsUpdate = true;
                }
                
                if (!existingAdmin.IsEmailVerified)
                {
                    existingAdmin.IsEmailVerified = true;
                    needsUpdate = true;
                }
                
                // 비밀번호 해시가 비어있거나 잘못된 경우 재설정
                // BCrypt 해시는 항상 $2a$, $2b$, $2y$로 시작해야 함
                if (string.IsNullOrEmpty(existingAdmin.PasswordHash) || 
                    (!existingAdmin.PasswordHash.StartsWith("$2a$") && 
                     !existingAdmin.PasswordHash.StartsWith("$2b$") && 
                     !existingAdmin.PasswordHash.StartsWith("$2y$")))
                {
                    existingAdmin.PasswordHash = BCrypt.Net.BCrypt.HashPassword("Admin123!");
                    needsUpdate = true;
                }
                else
                {
                    // 비밀번호 검증 테스트 (Admin123!)
                    try
                    {
                        var testVerify = BCrypt.Net.BCrypt.Verify("Admin123!", existingAdmin.PasswordHash);
                        if (!testVerify)
                        {
                            // 비밀번호가 맞지 않으면 재설정
                            existingAdmin.PasswordHash = BCrypt.Net.BCrypt.HashPassword("Admin123!");
                            needsUpdate = true;
                        }
                    }
                    catch
                    {
                        // 해시 검증 실패 시 재설정
                        existingAdmin.PasswordHash = BCrypt.Net.BCrypt.HashPassword("Admin123!");
                        needsUpdate = true;
                    }
                }
                
                if (needsUpdate)
                {
                    existingAdmin.UpdatedAt = DateTime.UtcNow;
                    await context.SaveChangesAsync();
                }

                // 역할이 없으면 추가
                var hasAdminRole = await context.UserRoles
                    .Include(ur => ur.Role)
                    .AnyAsync(ur => ur.UserId == existingAdmin.UserId && ur.Role.RoleName == "Admin");
                
                if (!hasAdminRole)
                {
                    var adminRole = await context.Roles.FirstOrDefaultAsync(r => r.RoleName == "Admin");
                    if (adminRole != null)
                    {
                        context.UserRoles.Add(new UserRole
                        {
                            UserId = existingAdmin.UserId,
                            RoleId = adminRole.RoleId,
                            AssignedAt = DateTime.UtcNow
                        });
                        await context.SaveChangesAsync();
                    }
                }
            }

            // API Services 시드
            if (!await context.ApiServices.AnyAsync())
            {
                var services = new[]
                {
                    new ApiService
                    {
                        ServiceCode = "chatgpt",
                        ServiceName = "ChatGPT",
                        Description = "OpenAI ChatGPT API",
                        IconClass = "bi-chat-square-text",
                        ColorCode = "#00c9ff",
                        ApiEndpoint = "https://api.openai.com/v1",
                        DefaultModel = "gpt-4-turbo",
                        CostPerRequest = 0.03m,
                        ServiceType = "Chat",
                        IsActive = true,
                        SortOrder = 1,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    },
                    new ApiService
                    {
                        ServiceCode = "claude",
                        ServiceName = "Claude",
                        Description = "Anthropic Claude API",
                        IconClass = "bi-robot",
                        ColorCode = "#667eea",
                        ApiEndpoint = "https://api.anthropic.com/v1",
                        DefaultModel = "claude-3-sonnet",
                        CostPerRequest = 0.03m,
                        ServiceType = "Chat",
                        IsActive = true,
                        SortOrder = 2,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    },
                    new ApiService
                    {
                        ServiceCode = "cursor",
                        ServiceName = "Cursor",
                        Description = "Cursor AI",
                        IconClass = "bi-code-slash",
                        ColorCode = "#f093fb",
                        CostPerRequest = 0.02m,
                        ServiceType = "Chat",
                        IsActive = true,
                        SortOrder = 3,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    },
                    new ApiService
                    {
                        ServiceCode = "copilot",
                        ServiceName = "Microsoft Copilot",
                        Description = "Microsoft Copilot (Azure OpenAI)",
                        IconClass = "bi-microsoft",
                        ColorCode = "#00A4EF",
                        CostPerRequest = 0.02m,
                        ServiceType = "Chat",
                        IsActive = true,
                        SortOrder = 4,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    },
                    new ApiService
                    {
                        ServiceCode = "gemini",
                        ServiceName = "Gemini",
                        Description = "Google Gemini API",
                        IconClass = "bi-google",
                        ColorCode = "#4285f4",
                        ApiEndpoint = "https://generativelanguage.googleapis.com/v1beta",
                        DefaultModel = "gemini-1.5-flash",
                        CostPerRequest = 0.02m,
                        ServiceType = "Chat",
                        IsActive = true,
                        SortOrder = 5,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    },
                    new ApiService
                    {
                        ServiceCode = "mistral",
                        ServiceName = "Mistral",
                        Description = "Mistral AI API",
                        IconClass = "bi-stars",
                        ColorCode = "#FF6B35",
                        ApiEndpoint = "https://api.mistral.ai/v1",
                        DefaultModel = "mistral-large-latest",
                        CostPerRequest = 0.02m,
                        ServiceType = "Chat",
                        IsActive = true,
                        SortOrder = 6,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    }
                };
                context.ApiServices.AddRange(services);
                await context.SaveChangesAsync();
            }

            // Mistral 서비스가 없으면 추가
            var existingMistral = await context.ApiServices
                .FirstOrDefaultAsync(s => s.ServiceCode == "mistral");

            if (existingMistral == null)
            {
                var mistralService = new ApiService
                {
                    ServiceCode = "mistral",
                    ServiceName = "Mistral",
                    Description = "Mistral AI API",
                    IconClass = "bi-stars",
                    ColorCode = "#FF6B35",
                    ApiEndpoint = "https://api.mistral.ai/v1",
                    DefaultModel = "mistral-large-latest",
                    CostPerRequest = 0.02m,
                    ServiceType = "Chat",
                    IsActive = true,
                    SortOrder = 6,
                    CreatedAt = DateTime.UtcNow,
                    UpdatedAt = DateTime.UtcNow
                };
                context.ApiServices.Add(mistralService);
                await context.SaveChangesAsync();
            }

            // Nexus(사내 LAN-only LLM 게이트웨이) — Phase 5.1, ADR-1 옵션 B.
            // 외부망 배포에서는 IsActive=true 라도 Nexus 인스턴스 미가동 시 호출 자체가 실패하므로
            // 추가 환경 분리(IsActive 운영자 토글)가 필요하나 본 단계에서는 등록만 수행.
            var existingNexus = await context.ApiServices
                .FirstOrDefaultAsync(s => s.ServiceCode == "nexus");

            if (existingNexus == null)
            {
                var nexusService = new ApiService
                {
                    ServiceCode = "nexus",
                    ServiceName = "Project Nexus",
                    Description = "사내 LAN-only LLM 게이트웨이 (옵션 B 통합 — 세션/멀티테넌시 보존)",
                    IconClass = "bi-hdd-network",
                    ColorCode = "#10B981",
                    ApiEndpoint = "http://192.168.22.28:8001/v1/chat",
                    DefaultModel = "primary",
                    CostPerRequest = 0.0m,           // 사내 모델 — 비용 0
                    ServiceType = "Chat",
                    IsActive = true,
                    SortOrder = 8,                    // 기존 7개 Chat provider 다음
                    CreatedAt = DateTime.UtcNow,
                    UpdatedAt = DateTime.UtcNow
                };
                context.ApiServices.Add(nexusService);
                await context.SaveChangesAsync();
            }

            // Image Generation 서비스 추가
            var existingImageServices = await context.ApiServices
                .Where(s => s.ServiceType == "ImageGeneration")
                .AnyAsync();
            
            if (!existingImageServices)
            {
                var imageServices = new[]
                {
                    new ApiService
                    {
                        ServiceCode = "dalle",
                        ServiceName = "DALL-E 3",
                        Description = "OpenAI DALL-E 3 이미지 생성",
                        IconClass = "bi-image",
                        ColorCode = "#10a37f",
                        ApiEndpoint = "https://api.openai.com/v1",
                        DefaultModel = "dall-e-3",
                        CostPerRequest = 0.04m,
                        ServiceType = "ImageGeneration",
                        IsActive = true,
                        SortOrder = 10,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    },
                    new ApiService
                    {
                        ServiceCode = "gemini-image",
                        ServiceName = "Gemini 3 Pro Image",
                        Description = "Google Gemini 3 Pro Image 생성 (Nano banana Pro)",
                        IconClass = "bi-image",
                        ColorCode = "#4285f4",
                        ApiEndpoint = "https://generativelanguage.googleapis.com/v1beta",
                        DefaultModel = "gemini-3.0-pro-image",
                        CostPerRequest = 0.03m,
                        ServiceType = "ImageGeneration",
                        IsActive = true,
                        SortOrder = 11,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    },
                    new ApiService
                    {
                        ServiceCode = "imagen4",
                        ServiceName = "Imagen 4",
                        Description = "Google Imagen 4 이미지 생성",
                        IconClass = "bi-image",
                        ColorCode = "#34a853",
                        ApiEndpoint = "https://generativelanguage.googleapis.com/v1beta",
                        DefaultModel = "imagen-4.0-generate-001",
                        CostPerRequest = 0.04m,
                        ServiceType = "ImageGeneration",
                        IsActive = true,
                        SortOrder = 12,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    },
                    new ApiService
                    {
                        ServiceCode = "gen4-image",
                        ServiceName = "Gen4 Image",
                        Description = "Google Vertex AI Gen4 Image 생성",
                        IconClass = "bi-image",
                        ColorCode = "#ea4335",
                        ApiEndpoint = "https://us-central1-aiplatform.googleapis.com/v1",
                        DefaultModel = "imagegeneration@006",
                        CostPerRequest = 0.04m,
                        ServiceType = "ImageGeneration",
                        IsActive = true,
                        SortOrder = 13,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    },
                    new ApiService
                    {
                        ServiceCode = "flux2",
                        ServiceName = "Flux 2",
                        Description = "Stability AI Flux 2 이미지 생성",
                        IconClass = "bi-image",
                        ColorCode = "#6366f1",
                        ApiEndpoint = "https://api.stability.ai/v2beta",
                        DefaultModel = "flux-2",
                        CostPerRequest = 0.03m,
                        ServiceType = "ImageGeneration",
                        IsActive = true,
                        SortOrder = 14,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    }
                };
                context.ApiServices.AddRange(imageServices);
                await context.SaveChangesAsync();
            }

            // Video Generation 서비스 추가
            var existingVideoServices = await context.ApiServices
                .Where(s => s.ServiceType == "VideoGeneration")
                .AnyAsync();
            
            if (!existingVideoServices)
            {
                var videoServices = new[]
                {
                    new ApiService
                    {
                        ServiceCode = "gen4-video",
                        ServiceName = "Gen4 Video",
                        Description = "Google Vertex AI Gen4 영상 생성",
                        IconClass = "bi-camera-video",
                        ColorCode = "#ea4335",
                        ApiEndpoint = "https://us-central1-aiplatform.googleapis.com/v1",
                        DefaultModel = "videogeneration@006",
                        CostPerRequest = 0.10m,
                        ServiceType = "VideoGeneration",
                        IsActive = true,
                        SortOrder = 20,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    },
                    new ApiService
                    {
                        ServiceCode = "veo",
                        ServiceName = "Veo 3.1",
                        Description = "Google Veo 3.1 영상 생성",
                        IconClass = "bi-camera-video-fill",
                        ColorCode = "#4285f4",
                        ApiEndpoint = "https://generativelanguage.googleapis.com/v1beta",
                        DefaultModel = "veo-3.1",
                        CostPerRequest = 0.12m,
                        ServiceType = "VideoGeneration",
                        IsActive = true,
                        SortOrder = 21,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    },
                    new ApiService
                    {
                        ServiceCode = "openai-video",
                        ServiceName = "OpenAI Video",
                        Description = "OpenAI 비디오 생성 (Sora)",
                        IconClass = "bi-camera-reels",
                        ColorCode = "#10a37f",
                        ApiEndpoint = "https://api.openai.com/v1",
                        DefaultModel = "sora-2",
                        CostPerRequest = 0.15m,
                        ServiceType = "VideoGeneration",
                        IsActive = true,
                        SortOrder = 22,
                        CreatedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow
                    }
                };
                context.ApiServices.AddRange(videoServices);
                await context.SaveChangesAsync();
            }

            // API Service Models 시드 데이터 추가
            await SeedApiServiceModelsAsync(context);

            // 모델명 최신 업데이트 (기존 DB 레코드 갱신)
            await UpdateApiServiceModelsAsync(context);

            // ── Phase 7.1 — AI_INVENTORY.md §6 의 15개 신규 Agent 카탈로그 시드 ───
            // DocUtil(4) + career(8) + 공통(3). End-User 앱(DocUtil/career) 의 35곳 LLM
            // 직접 호출을 R2(단일 진입점)에 따라 AgentHub Agent API 호출로 교체할 때
            // 즉시 사용할 수 있도록 사전 등록한다.
            await SeedAgentsAsync(context);
        }
        catch (Exception ex)
        {
            // 시드 단계별 부분 실패는 swallow — 이미 동일 데이터가 있거나(중복 INSERT)
            // 단일 ApiService 한 건의 PG 제약 위반이 다른 시드 + 마이그레이션을 무력화하지 않도록.
            // 단, 디버깅을 위해 stderr 로 클래스명/메시지는 흘려둔다 (anti-patterns.md #10 의 의도된 swallow 패턴 일관성).
            Console.Error.WriteLine($"[DatabaseInitializer] Seed 일부 실패 (계속 진행): {ex.GetType().Name}: {ex.Message}");
        }
    }

    /// <summary>
    /// 기존 DB에 있는 모델 목록을 최신으로 업데이트합니다.
    /// 앱 시작 시마다 실행되어 outdated 모델을 갱신합니다.
    /// </summary>
    private static async Task UpdateApiServiceModelsAsync(AIAgentManagementDbContext context)
    {
        var now = DateTime.UtcNow;

        // ─── Gemini Chat 모델 갱신 ───────────────────────────────────────
        var geminiService = await context.ApiServices.FirstOrDefaultAsync(s => s.ServiceCode == "gemini");
        if (geminiService != null)
        {
            // 종료된 모델 비활성화
            var obsoleteGeminiModels = new[] { "gemini-3-pro-preview", "gemini-3-flash-preview",
                "gemini-3.0-pro-preview", "gemini-3.0-flash-preview" };
            var obsolete = await context.ApiServiceModels
                .Where(m => m.ServiceId == geminiService.ServiceId && obsoleteGeminiModels.Contains(m.ModelName))
                .ToListAsync();
            obsolete.ForEach(m => { m.IsActive = false; m.UpdatedAt = now; });

            // 지원 종료된 모델 비활성화
            var deprecatedGeminiModels = new[] { "gemini-1.5-pro", "gemini-1.5-flash", "gemini-3.1-flash-preview" };
            var deprecated = await context.ApiServiceModels
                .Where(m => m.ServiceId == geminiService.ServiceId && deprecatedGeminiModels.Contains(m.ModelName))
                .ToListAsync();
            deprecated.ForEach(m => { m.IsActive = false; m.UpdatedAt = now; });

            // 최신 모델 추가 (없는 것만)
            var latestGeminiModels = new[]
            {
                new { ModelName = "gemini-3.1-pro-preview",       Description = "Gemini 3.1 Pro Preview",       SortOrder = 1,  ModelType = "preview" },
                new { ModelName = "gemini-3.1-flash-lite-preview", Description = "Gemini 3.1 Flash Lite Preview", SortOrder = 2,  ModelType = "preview" },
                new { ModelName = "gemini-2.5-pro",               Description = "Gemini 2.5 Pro",               SortOrder = 3,  ModelType = "stable"  },
                new { ModelName = "gemini-2.5-flash",              Description = "Gemini 2.5 Flash",             SortOrder = 4,  ModelType = "stable"  },
                new { ModelName = "gemini-2.0-flash",              Description = "Gemini 2.0 Flash (2026-06 종료 예정)", SortOrder = 5,  ModelType = "stable"  },
            };
            var existingGeminiNames = await context.ApiServiceModels
                .Where(m => m.ServiceId == geminiService.ServiceId)
                .Select(m => m.ModelName).ToListAsync();
            foreach (var m in latestGeminiModels.Where(m => !existingGeminiNames.Contains(m.ModelName)))
            {
                context.ApiServiceModels.Add(new ApiServiceModel
                {
                    ServiceId = geminiService.ServiceId, ModelName = m.ModelName, Description = m.Description,
                    IsActive = true, SortOrder = m.SortOrder, ModelType = m.ModelType, CreatedAt = now, UpdatedAt = now
                });
            }
            // DefaultModel 최신화
            var outdatedDefaults = new[] { "gemini-1.5-flash", "gemini-1.5-pro", "gemini-3.1-flash-preview" };
            if (outdatedDefaults.Contains(geminiService.DefaultModel) || obsoleteGeminiModels.Contains(geminiService.DefaultModel ?? ""))
            {
                geminiService.DefaultModel = "gemini-3.1-pro-preview";
                geminiService.UpdatedAt = now;
            }
        }

        // ─── Gemini Image 모델 갱신 ──────────────────────────────────────
        var geminiImageService = await context.ApiServices.FirstOrDefaultAsync(s => s.ServiceCode == "gemini-image");
        if (geminiImageService != null)
        {
            var obsoleteImageModels = new[] { "gemini-3-pro-image-preview", "gemini-3.0-pro-image-preview" };
            var obsoleteImg = await context.ApiServiceModels
                .Where(m => m.ServiceId == geminiImageService.ServiceId && obsoleteImageModels.Contains(m.ModelName))
                .ToListAsync();
            obsoleteImg.ForEach(m => { m.IsActive = false; m.UpdatedAt = now; });

            var latestImageModels = new[]
            {
                new { ModelName = "gemini-3.1-pro-image-preview",   Description = "Gemini 3.1 Pro Image Preview",   SortOrder = 1, ModelType = "preview" },
                new { ModelName = "gemini-2.5-flash-image-preview", Description = "Gemini 2.5 Flash Image Preview", SortOrder = 2, ModelType = "preview" },
            };
            var existingImgNames = await context.ApiServiceModels
                .Where(m => m.ServiceId == geminiImageService.ServiceId)
                .Select(m => m.ModelName).ToListAsync();
            foreach (var m in latestImageModels.Where(m => !existingImgNames.Contains(m.ModelName)))
            {
                context.ApiServiceModels.Add(new ApiServiceModel
                {
                    ServiceId = geminiImageService.ServiceId, ModelName = m.ModelName, Description = m.Description,
                    IsActive = true, SortOrder = m.SortOrder, ModelType = m.ModelType, CreatedAt = now, UpdatedAt = now
                });
            }
            if (obsoleteImageModels.Contains(geminiImageService.DefaultModel ?? ""))
            {
                geminiImageService.DefaultModel = "gemini-3.1-pro-image-preview";
                geminiImageService.UpdatedAt = now;
            }
        }

        // ─── Claude 모델 갱신 ────────────────────────────────────────────
        var claudeService = await context.ApiServices.FirstOrDefaultAsync(s => s.ServiceCode == "claude");
        if (claudeService != null)
        {
            // Deprecated 모델 비활성화
            var deprecatedClaudeModels = new[] { "claude-3-sonnet-20240229" };
            var deprecatedClaude = await context.ApiServiceModels
                .Where(m => m.ServiceId == claudeService.ServiceId && deprecatedClaudeModels.Contains(m.ModelName))
                .ToListAsync();
            deprecatedClaude.ForEach(m => { m.IsActive = false; m.UpdatedAt = now; });

            var latestClaudeModels = new[]
            {
                new { ModelName = "claude-opus-4-6",           Description = "Claude Opus 4.6",      SortOrder = 1,  ModelType = "stable" },
                new { ModelName = "claude-sonnet-4-6",         Description = "Claude Sonnet 4.6",    SortOrder = 2,  ModelType = "stable" },
                new { ModelName = "claude-haiku-4-5-20251001", Description = "Claude Haiku 4.5",     SortOrder = 3,  ModelType = "stable" },
                new { ModelName = "claude-3-5-sonnet-20241022",Description = "Claude 3.5 Sonnet",    SortOrder = 10, ModelType = "stable" },
                new { ModelName = "claude-3-opus-20240229",    Description = "Claude 3 Opus",        SortOrder = 11, ModelType = "stable" },
                new { ModelName = "claude-3-haiku-20240307",   Description = "Claude 3 Haiku",       SortOrder = 12, ModelType = "stable" },
            };
            var existingClaudeNames = await context.ApiServiceModels
                .Where(m => m.ServiceId == claudeService.ServiceId)
                .Select(m => m.ModelName).ToListAsync();
            foreach (var m in latestClaudeModels.Where(m => !existingClaudeNames.Contains(m.ModelName)))
            {
                context.ApiServiceModels.Add(new ApiServiceModel
                {
                    ServiceId = claudeService.ServiceId, ModelName = m.ModelName, Description = m.Description,
                    IsActive = true, SortOrder = m.SortOrder, ModelType = m.ModelType, CreatedAt = now, UpdatedAt = now
                });
            }
            if (claudeService.DefaultModel == "claude-3-sonnet")
            {
                claudeService.DefaultModel = "claude-sonnet-4-6";
                claudeService.UpdatedAt = now;
            }
        }

        // ─── ChatGPT 모델 갱신 ──────────────────────────────────────────
        var chatgptService = await context.ApiServices.FirstOrDefaultAsync(s => s.ServiceCode == "chatgpt");
        if (chatgptService != null)
        {
            // Deprecated 모델 비활성화
            var deprecatedGptModels = new[] {
                "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo",   // legacy
                "gpt-5.2", "gpt-5.2-instant", "gpt-5.2-thinking", "gpt-5.2-pro"  // 구 버전
            };
            var deprecatedGpt = await context.ApiServiceModels
                .Where(m => m.ServiceId == chatgptService.ServiceId && deprecatedGptModels.Contains(m.ModelName))
                .ToListAsync();
            deprecatedGpt.ForEach(m => { m.IsActive = false; m.UpdatedAt = now; });

            // 현재 사용 가능한 모델 추가
            var latestGptModels = new[]
            {
                new { ModelName = "gpt-5",         Description = "GPT-5",           SortOrder = 1,  ModelType = "stable" },
                new { ModelName = "gpt-5-mini",    Description = "GPT-5 Mini",      SortOrder = 2,  ModelType = "stable" },
                new { ModelName = "gpt-5-nano",    Description = "GPT-5 Nano",      SortOrder = 3,  ModelType = "stable" },
                new { ModelName = "gpt-4o",        Description = "GPT-4o",          SortOrder = 4,  ModelType = "stable" },
                new { ModelName = "gpt-4o-mini",   Description = "GPT-4o Mini",     SortOrder = 5,  ModelType = "stable" },
                new { ModelName = "o3",            Description = "o3",              SortOrder = 6,  ModelType = "stable" },
                new { ModelName = "o3-mini",       Description = "o3 Mini",         SortOrder = 7,  ModelType = "stable" },
                new { ModelName = "o1",            Description = "o1",              SortOrder = 8,  ModelType = "stable" },
                new { ModelName = "o1-mini",       Description = "o1 Mini",         SortOrder = 9,  ModelType = "stable" },
            };
            var existingGptNames = await context.ApiServiceModels
                .Where(m => m.ServiceId == chatgptService.ServiceId)
                .Select(m => m.ModelName).ToListAsync();
            foreach (var m in latestGptModels.Where(m => !existingGptNames.Contains(m.ModelName)))
            {
                context.ApiServiceModels.Add(new ApiServiceModel
                {
                    ServiceId = chatgptService.ServiceId, ModelName = m.ModelName, Description = m.Description,
                    IsActive = true, SortOrder = m.SortOrder, ModelType = m.ModelType, CreatedAt = now, UpdatedAt = now
                });
            }
            // DefaultModel 최신화
            var outdatedGptDefaults = new[] { "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo" };
            if (outdatedGptDefaults.Contains(chatgptService.DefaultModel))
            {
                chatgptService.DefaultModel = "gpt-5";
                chatgptService.UpdatedAt = now;
            }
        }

        // ─── Cursor 모델 갱신 ────────────────────────────────────────────
        var cursorService = await context.ApiServices.FirstOrDefaultAsync(s => s.ServiceCode == "cursor");
        if (cursorService != null)
        {
            // 구식 모델 비활성화
            var deprecatedCursorModels = new[] { "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo" };
            var deprecatedCursor = await context.ApiServiceModels
                .Where(m => m.ServiceId == cursorService.ServiceId && deprecatedCursorModels.Contains(m.ModelName))
                .ToListAsync();
            deprecatedCursor.ForEach(m => { m.IsActive = false; m.UpdatedAt = now; });

            var latestCursorModels = new[]
            {
                new { ModelName = "claude-sonnet-4-6",          Description = "Claude Sonnet 4.6",  SortOrder = 1, ModelType = "stable" },
                new { ModelName = "claude-opus-4-6",            Description = "Claude Opus 4.6",    SortOrder = 2, ModelType = "stable" },
                new { ModelName = "claude-3-5-sonnet-20241022", Description = "Claude 3.5 Sonnet",  SortOrder = 3, ModelType = "stable" },
                new { ModelName = "gpt-4o",                    Description = "GPT-4o",             SortOrder = 4, ModelType = "stable" },
                new { ModelName = "gpt-4o-mini",               Description = "GPT-4o Mini",        SortOrder = 5, ModelType = "stable" },
                new { ModelName = "cursor-small",              Description = "Cursor Small",       SortOrder = 6, ModelType = "stable" },
            };
            var existingCursorNames = await context.ApiServiceModels
                .Where(m => m.ServiceId == cursorService.ServiceId)
                .Select(m => m.ModelName).ToListAsync();
            foreach (var m in latestCursorModels.Where(m => !existingCursorNames.Contains(m.ModelName)))
            {
                context.ApiServiceModels.Add(new ApiServiceModel
                {
                    ServiceId = cursorService.ServiceId, ModelName = m.ModelName, Description = m.Description,
                    IsActive = true, SortOrder = m.SortOrder, ModelType = m.ModelType, CreatedAt = now, UpdatedAt = now
                });
            }
        }

        // ─── Mistral 모델 갱신 ───────────────────────────────────────────
        var mistralService = await context.ApiServices.FirstOrDefaultAsync(s => s.ServiceCode == "mistral");
        if (mistralService != null)
        {
            // Deprecated / Legacy 모델 비활성화
            var deprecatedMistralModels = new[] {
                "mistral-medium-latest",  // Mistral medium 티어 2024 폐기
                "open-mixtral-8x7b",      // Legacy
                "open-mixtral-8x22b",     // Legacy
                "open-mistral-7b"         // Legacy
            };
            var deprecatedMistral = await context.ApiServiceModels
                .Where(m => m.ServiceId == mistralService.ServiceId && deprecatedMistralModels.Contains(m.ModelName))
                .ToListAsync();
            deprecatedMistral.ForEach(m => { m.IsActive = false; m.UpdatedAt = now; });

            // 최신 모델 추가 (없는 것만)
            var latestMistralModels = new[]
            {
                new { ModelName = "mistral-large-latest",   Description = "Mistral Large",          SortOrder = 1, ModelType = "stable" },
                new { ModelName = "mistral-small-latest",   Description = "Mistral Small",          SortOrder = 2, ModelType = "stable" },
                new { ModelName = "mistral-nemo",           Description = "Mistral Nemo",           SortOrder = 3, ModelType = "stable" },
                new { ModelName = "codestral-latest",       Description = "Codestral (코드 전용)",  SortOrder = 4, ModelType = "stable" },
                new { ModelName = "pixtral-large-latest",   Description = "Pixtral Large (멀티모달)", SortOrder = 5, ModelType = "stable" },
            };
            var existingMistralNames = await context.ApiServiceModels
                .Where(m => m.ServiceId == mistralService.ServiceId)
                .Select(m => m.ModelName).ToListAsync();
            foreach (var m in latestMistralModels.Where(m => !existingMistralNames.Contains(m.ModelName)))
            {
                context.ApiServiceModels.Add(new ApiServiceModel
                {
                    ServiceId = mistralService.ServiceId, ModelName = m.ModelName, Description = m.Description,
                    IsActive = true, SortOrder = m.SortOrder, ModelType = m.ModelType, CreatedAt = now, UpdatedAt = now
                });
            }
        }

        await context.SaveChangesAsync();
    }

    private static async Task SeedApiServiceModelsAsync(AIAgentManagementDbContext context)
    {
        var services = await context.ApiServices.ToListAsync();
        var now = DateTime.UtcNow;

        foreach (var service in services)
        {
            var serviceCode = service.ServiceCode.ToLower();
            var existingModels = await context.ApiServiceModels
                .Where(m => m.ServiceId == service.ServiceId)
                .AnyAsync();

            if (existingModels)
            {
                continue; // 이미 모델이 있으면 스킵
            }

            var models = new List<ApiServiceModel>();

            switch (serviceCode)
            {
                case "chatgpt":
                case "openai":
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gpt-5",         Description = "GPT-5",           IsActive = true, SortOrder = 1,  ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gpt-5-mini",    Description = "GPT-5 Mini",      IsActive = true, SortOrder = 2,  ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gpt-5-nano",    Description = "GPT-5 Nano",      IsActive = true, SortOrder = 3,  ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gpt-4o",        Description = "GPT-4o",          IsActive = true, SortOrder = 4,  ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gpt-4o-mini",   Description = "GPT-4o Mini",     IsActive = true, SortOrder = 5,  ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "o3",            Description = "o3",              IsActive = true, SortOrder = 6,  ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "o3-mini",       Description = "o3 Mini",         IsActive = true, SortOrder = 7,  ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "o1",            Description = "o1",              IsActive = true, SortOrder = 8,  ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "o1-mini",       Description = "o1 Mini",         IsActive = true, SortOrder = 9,  ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                    });
                    break;

                case "claude":
                case "anthropic":
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "claude-opus-4-6",            Description = "Claude Opus 4.6",      IsActive = true, SortOrder = 1,  ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "claude-sonnet-4-6",          Description = "Claude Sonnet 4.6",    IsActive = true, SortOrder = 2,  ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "claude-haiku-4-5-20251001",  Description = "Claude Haiku 4.5",     IsActive = true, SortOrder = 3,  ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "claude-3-5-sonnet-20241022", Description = "Claude 3.5 Sonnet",    IsActive = true, SortOrder = 10, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "claude-3-opus-20240229",     Description = "Claude 3 Opus",        IsActive = true, SortOrder = 11, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "claude-3-haiku-20240307",    Description = "Claude 3 Haiku",       IsActive = true, SortOrder = 12, ModelType = "stable", CreatedAt = now, UpdatedAt = now }
                    });
                    break;

                case "gemini":
                case "google":
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gemini-3.1-pro-preview",        Description = "Gemini 3.1 Pro Preview",          IsActive = true, SortOrder = 1, ModelType = "preview", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gemini-3.1-flash-lite-preview", Description = "Gemini 3.1 Flash Lite Preview",   IsActive = true, SortOrder = 2, ModelType = "preview", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gemini-2.5-pro",                Description = "Gemini 2.5 Pro",                  IsActive = true, SortOrder = 3, ModelType = "stable",  CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gemini-2.5-flash",              Description = "Gemini 2.5 Flash",                IsActive = true, SortOrder = 4, ModelType = "stable",  CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gemini-2.0-flash",              Description = "Gemini 2.0 Flash (2026-06 종료 예정)", IsActive = true, SortOrder = 5, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                    });
                    break;

                case "mistral":
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "mistral-large-latest",  Description = "Mistral Large",           IsActive = true, SortOrder = 1, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "mistral-small-latest",  Description = "Mistral Small",           IsActive = true, SortOrder = 2, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "mistral-nemo",          Description = "Mistral Nemo",            IsActive = true, SortOrder = 3, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "codestral-latest",      Description = "Codestral (코드 전용)",   IsActive = true, SortOrder = 4, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "pixtral-large-latest",  Description = "Pixtral Large (멀티모달)", IsActive = true, SortOrder = 5, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                    });
                    break;

                case "copilot":
                    // Microsoft Copilot (Azure OpenAI)
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gpt-4", Description = "GPT-4", IsActive = true, SortOrder = 1, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gpt-4-turbo", Description = "GPT-4 Turbo", IsActive = true, SortOrder = 2, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gpt-35-turbo", Description = "GPT-3.5 Turbo", IsActive = true, SortOrder = 3, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gpt-4o", Description = "GPT-4o", IsActive = true, SortOrder = 4, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gpt-4o-mini", Description = "GPT-4o Mini", IsActive = true, SortOrder = 5, ModelType = "stable", CreatedAt = now, UpdatedAt = now }
                    });
                    break;

                case "cursor":
                    // Cursor IDE AI 모델
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "claude-sonnet-4-6",          Description = "Claude Sonnet 4.6",    IsActive = true, SortOrder = 1, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "claude-opus-4-6",            Description = "Claude Opus 4.6",      IsActive = true, SortOrder = 2, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "claude-3-5-sonnet-20241022", Description = "Claude 3.5 Sonnet",    IsActive = true, SortOrder = 3, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gpt-4o",                    Description = "GPT-4o",               IsActive = true, SortOrder = 4, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gpt-4o-mini",               Description = "GPT-4o Mini",          IsActive = true, SortOrder = 5, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "cursor-small",              Description = "Cursor Small",         IsActive = true, SortOrder = 6, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                    });
                    break;

                case "perplexity":
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "sonar", Description = "Sonar", IsActive = true, SortOrder = 1, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "sonar-pro", Description = "Sonar Pro", IsActive = true, SortOrder = 2, ModelType = "stable", CreatedAt = now, UpdatedAt = now }
                    });
                    break;

                case "dalle":
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "dall-e-3", Description = "DALL-E 3", IsActive = true, SortOrder = 1, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "dall-e-2", Description = "DALL-E 2", IsActive = true, SortOrder = 2, ModelType = "stable", CreatedAt = now, UpdatedAt = now }
                    });
                    break;

                case "gemini-image":
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gemini-3.1-pro-image-preview",   Description = "Gemini 3.1 Pro Image Preview",   IsActive = true, SortOrder = 1, ModelType = "preview", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "gemini-2.5-flash-image-preview", Description = "Gemini 2.5 Flash Image Preview", IsActive = true, SortOrder = 2, ModelType = "preview", CreatedAt = now, UpdatedAt = now }
                    });
                    break;

                case "imagen4":
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "imagen-4.0-generate-001", Description = "Imagen 4.0 Generate", IsActive = true, SortOrder = 1, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "imagen-4.0-fast-generate-001", Description = "Imagen 4.0 Fast Generate", IsActive = true, SortOrder = 2, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "imagen-4.0-ultra-generate-001", Description = "Imagen 4.0 Ultra Generate", IsActive = true, SortOrder = 3, ModelType = "stable", CreatedAt = now, UpdatedAt = now }
                    });
                    break;

                case "gen4-image":
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "imagegeneration@006", Description = "Gen4 Image Generation", IsActive = true, SortOrder = 1, ModelType = "stable", CreatedAt = now, UpdatedAt = now }
                    });
                    break;

                case "flux2":
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "flux-2", Description = "Flux 2", IsActive = true, SortOrder = 1, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "flux-2.1", Description = "Flux 2.1", IsActive = true, SortOrder = 2, ModelType = "stable", CreatedAt = now, UpdatedAt = now }
                    });
                    break;

                case "gen4-video":
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "videogeneration@006", Description = "Gen4 Video Generation", IsActive = true, SortOrder = 1, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "videogeneration@006-hd", Description = "Gen4 Video Generation HD", IsActive = true, SortOrder = 2, ModelType = "stable", CreatedAt = now, UpdatedAt = now }
                    });
                    break;

                case "veo":
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "veo-3.1", Description = "Veo 3.1", IsActive = true, SortOrder = 1, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "veo-3.0", Description = "Veo 3.0", IsActive = true, SortOrder = 2, ModelType = "stable", CreatedAt = now, UpdatedAt = now }
                    });
                    break;

                case "openai-video":
                case "sora":
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "sora-2", Description = "Sora 2", IsActive = true, SortOrder = 1, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "sora-1.5", Description = "Sora 1.5", IsActive = true, SortOrder = 2, ModelType = "stable", CreatedAt = now, UpdatedAt = now }
                    });
                    break;

                case "nexus":
                    // Phase 5.2 — Nexus 사내 LLM 두 카테고리(primary/auxiliary).
                    // 모델 이름은 Nexus 의 model_loader 가 처리하는 카테고리 키이며,
                    // 실 모델(Qwen3 14B / ExaOne 7.8B 등)은 nexus_config.yaml 에서 매핑.
                    // AgentBuilder 의 모델 드롭다운 표시용으로만 사용된다.
                    models.AddRange(new[]
                    {
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "primary",   Description = "Nexus Primary (메인 모델)",    IsActive = true, SortOrder = 1, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                        new ApiServiceModel { ServiceId = service.ServiceId, ModelName = "auxiliary", Description = "Nexus Auxiliary (보조 모델)",  IsActive = true, SortOrder = 2, ModelType = "stable", CreatedAt = now, UpdatedAt = now },
                    });
                    break;
            }

            if (models.Any())
            {
                context.ApiServiceModels.AddRange(models);
                await context.SaveChangesAsync();
            }
        }
    }

    /// <summary>
    /// Phase 7.1 — AI_INVENTORY.md §6 의 15개 신규 Agent 카탈로그를 멱등적으로 시드한다.
    /// </summary>
    /// <remarks>
    /// 본 시드의 목적:
    ///   1) DocUtil/career 35곳의 LLM 직접 호출(R2 위반)을 AgentHub `/v1/chat/completions`
    ///      위임으로 교체할 때(Phase 7.3/7.4) 사전에 Agent 정의가 존재해야 한다.
    ///   2) AgentCode UNIQUE 식별자 + ConsumerSystems 화이트리스트 + LlmRouting 정책이
    ///      Phase 5.2(HybridRouter) + Phase 5.1(Agent 5컬럼) 위에서 즉시 동작하도록.
    ///
    /// 멱등 패턴:
    ///   - AgentCode 존재 검사 후 INSERT (R7: 시드 재실행 안전)
    ///   - ServiceCode 매핑 실패 시 LogWarning + skip (예: nexus 미등록 외부망 환경)
    ///   - 이미 존재하는 Agent 의 SystemPrompt/Temperature 등은 *덮어쓰지 않음* —
    ///     운영자가 UI 에서 수정한 값을 보존 (재기동 시 복원되면 운영 사고).
    ///
    /// CreatedBy 매핑:
    ///   - admin@example.com (DatabaseInitializer 자체가 생성하는 시스템 admin) FK 사용.
    ///   - admin 시드 부재 시 시드 전체 skip (Agents.CreatedBy 는 NOT NULL FK).
    /// </remarks>
    /// <summary>
    /// Phase 7 옵션 A:c (2026-06-01) — Hybrid 라우팅 표준 정책 JSON.
    /// OpenAI quota 초과 상태 우회 — dataLabels.public + modelCapability.vision/longContext
    /// + default 모두 internal 폴백. OpenAI 충전 완료 시 운영자가 vision/public/default 의
    /// 일부를 external 로 복원하거나 그대로 유지 가능 (운영 정책 결정).
    /// 트랙 #138 의 표준 정책에서 진화 — Phase 7 위임 호출이 OpenAI 의존 없이 Nexus 만으로
    /// 정상 작동하도록 보강 (DocUtil RAG / career coaching 모두 운영 검증 완료).
    /// </summary>
    private const string DefaultHybridRoutingPolicyJson =
        "{\"piiThreshold\":\"block\",\"piiAction\":\"internal\"," +
        "\"dataLabels\":{\"confidential\":\"internal\",\"internal\":\"internal\",\"public\":\"internal\"}," +
        "\"modelCapability\":{\"vision\":\"internal\",\"longContext\":\"internal\",\"longContextThreshold\":32000}," +
        "\"costThreshold\":{\"perRequest\":0.10,\"exceedAction\":\"internal\"}," +
        "\"default\":\"internal\"}";

    private static async Task SeedAgentsAsync(AIAgentManagementDbContext context)
    {
        var adminUser = await context.Users
            .AsNoTracking()
            .FirstOrDefaultAsync(u => u.Email == "admin@example.com");

        if (adminUser == null)
        {
            // admin 시드는 본 메서드 앞 단계에서 처리됨. 그럼에도 부재 시 시드 자체를 skip 한다.
            // (관리자 직접 운영 환경에서는 UI 의 Agent 빌더로 수동 등록 가능)
            Console.Error.WriteLine("[DatabaseInitializer] SeedAgentsAsync skip: admin@example.com 미존재");
            return;
        }

        var now = DateTime.UtcNow;

        // ── 시드 카탈로그 (AI_INVENTORY.md §6) ────────────────────────────────
        // 필드 의미:
        //   AgentCode          : UNIQUE 외부 식별자 (R5: kebab-case 영문)
        //   AgentName / Desc   : 한국어 사용자 노출 (R5)
        //   ServiceCode        : ApiServices.ServiceCode FK 매핑 키 (소문자)
        //   DefaultModel       : 첫 호출 시 모델 — 운영자가 UI 에서 추후 변경 가능
        //   Temperature        : 0~2 범위 (Agent 스키마 decimal(3,2))
        //   MaxTokens          : 응답 토큰 상한 — 0 은 임베딩 전용
        //   SystemPrompt       : Agent 인격 / 역할 / 제약 (R5 한국어, 200~500 자)
        //   EnableRag          : DocUtil collection 검색 활성화 여부
        //   PiiEnabled / Mode  : "Block" 강제 차단 / "Mask" 마스킹 후 진행
        //   LlmRouting         : "External"=ApiKeyPool 경유 / "Internal"=Nexus / "Hybrid"=정책 평가
        //   ConsumerSystems    : End-User App 화이트리스트 JSON 배열
        var seeds = new (
            string AgentCode,
            string AgentName,
            string Description,
            string ServiceCode,
            string DefaultModel,
            decimal Temperature,
            int MaxTokens,
            string SystemPrompt,
            bool EnableRag,
            bool PiiEnabled,
            string PiiMode,
            string LlmRouting,
            string ConsumerSystems
        )[]
        {
            // ── DocUtil 영역 (4개 — AI_INVENTORY §6.1) ─────────────────────────
            (
                "docutil-rag-chat",
                "DocUtil RAG 챗봇",
                "DocUtil 사용자 챗봇의 RAG 검색-증강 응답 Agent (DU-7, DU-8 통합)",
                "chatgpt", "gpt-4o", 0.5m, 4096,
                "당신은 사내 문서 검색-증강(RAG) 챗봇입니다. 사용자의 질문에 대해 제공된 문서 컨텍스트만을 근거로 정확한 답변을 합니다. " +
                "출처가 없는 추측이나 일반 지식으로 답변하지 마세요. 답변은 한국어로 친절하고 명확하게 작성하며, " +
                "근거가 된 문서/문단을 인용 표기하세요. 문서에서 답을 찾을 수 없으면 솔직히 모른다고 답합니다. " +
                "기밀 문서가 노출될 수 있는 질문이라면 사용자의 권한 범위를 우선 확인하세요.",
                true, true, "Mask", "Hybrid",
                "[\"docutil-user\"]"
            ),
            (
                "docutil-report-generator",
                "DocUtil 보고서 생성기",
                "DocUtil documents_v2 Mode A 보고서 생성 Agent (DU-9)",
                "chatgpt", "gpt-4o", 0.4m, 8192,
                "당신은 사내 보고서 작성 전문 AI 입니다. 사용자가 제공한 자료/메모/회의록을 바탕으로 구조적이고 일관된 한국어 보고서를 생성합니다. " +
                "응답은 1) 개요 2) 본문(섹션별 헤더) 3) 결론 4) 참고/출처 의 4단 구성을 기본으로 하며, 마크다운 헤더(##, ###)를 사용합니다. " +
                "사실 관계가 불분명한 부분은 추측하지 말고 '확인 필요' 로 표기합니다. 회사명/사람 이름은 입력에 명시된 표기를 그대로 따릅니다.",
                true, true, "Mask", "Hybrid",
                "[\"docutil-user\"]"
            ),
            (
                "docutil-evaluator",
                "DocUtil RAGAS 평가기",
                "RAG 응답 품질 평가용 LLM-as-judge Agent (DU-13). 정확도 우선 — External 강제",
                "chatgpt", "gpt-4o", 0.0m, 2048,
                "당신은 RAG 시스템의 응답 품질을 평가하는 심사 AI 입니다. " +
                "RAGAS 지표(faithfulness, answer_relevancy, context_precision, context_recall)에 따라 0~1 사이의 점수와 그 근거를 한국어로 제시합니다. " +
                "JSON 형식으로 {\"faithfulness\":0~1, \"relevancy\":0~1, \"precision\":0~1, \"recall\":0~1, \"reasoning\":\"...\"} 만 출력하며 추가 설명을 붙이지 않습니다. " +
                "주관적 호감이 아닌 검증 가능한 사실 일치 여부만 판단합니다.",
                false, false, "Block", "External",
                "[\"docutil-user\"]"
            ),
            (
                "docutil-image-generator",
                "DocUtil 이미지 생성기",
                "DocUtil 보고서/문서 자동 이미지 채움용 Agent (DU-14, DU-19, DU-20)",
                "dalle", "dall-e-3", 0.7m, 0,
                "당신은 한국어 보고서/문서에 들어갈 일러스트와 인포그래픽을 생성하는 이미지 AI 입니다. " +
                "요청된 주제를 적절한 비유와 색감으로 시각화하며, 텍스트는 가급적 포함하지 않습니다(언어 의존성 회피). " +
                "회사 로고, 실존 인물, 폭력적/선정적 요소는 생성하지 않습니다. 1024x1024 기본 해상도로 1장 생성합니다.",
                false, false, "Block", "External",
                "[\"docutil-user\"]"
            ),

            // ── career 영역 (8개 — AI_INVENTORY §6.2) ──────────────────────────
            (
                "career-actionboard-orchestrator",
                "career ActionBoard 추천 오케스트레이터",
                "ai-service Tool Calling + Structured Outputs strict 진입점 (CA-7, CA-8, CA-19)",
                "chatgpt", "gpt-4o-mini", 0.3m, 4096,
                "당신은 학생 진로 ActionBoard 추천 오케스트레이터입니다. " +
                "입력으로 학생 프로필/현재 학기/목표 직무 데이터를 받아, get_student_profile / get_competency_scores / search_alumni_patterns / check_constraints " +
                "4개 도구를 적절히 호출하여 데이터를 수집한 후, 학생에게 추천할 액션 리스트(JSON_SCHEMA_ACTIONBOARD strict) 를 생성합니다. " +
                "학사 위험(check_constraints) 이 발견되면 위험 완화 액션을 우선합니다. 응답은 반드시 사전 정의된 JSON 스키마에 정확히 맞춥니다 — 자유 텍스트 금지.",
                false, true, "Mask", "Hybrid",
                "[\"career-student\",\"career-coaching\"]"
            ),
            (
                "career-rag-actionboard",
                "career RAG ActionBoard 추천기",
                "ai-service /ai/recommendations/rag (CA-9, CA-10) — 동문 RAG 컨텍스트 prepend",
                "chatgpt", "gpt-4o-mini", 0.3m, 4096,
                "당신은 동문 진로 사례 RAG 컨텍스트를 활용하는 ActionBoard 추천기입니다. " +
                "주어진 동문 패턴/유사 학생 사례를 근거로 현재 학생에게 가장 효과적인 액션을 JSON_SCHEMA_ACTIONBOARD strict 로 응답합니다. " +
                "RAG 결과가 비어 있으면 일반 추천으로 폴백하되, 'rag_used': false 플래그를 응답에 포함합니다. " +
                "학생의 개인 정보(이름/학번/연락처)는 절대 응답 본문에 노출하지 않습니다.",
                true, true, "Mask", "Hybrid",
                "[\"career-student\",\"career-coaching\"]"
            ),
            (
                "career-competency-analyzer",
                "career 역량 분석기",
                "competency-service / ai-service /ai/analyze (CA-4, CA-18)",
                "chatgpt", "gpt-4o-mini", 0.4m, 4096,
                "당신은 학생 역량 분석 전문 AI 입니다. " +
                "주어진 학생 데이터(성적, 활동 이력, 자격증, 프로젝트)와 역량 점수, 목표 직무를 분석하여 " +
                "1) 강점 2) 약점 3) 격차 분석 4) 개선 제안 의 4단 구조 한국어 분석 결과를 작성합니다. " +
                "정량 점수는 1~5 척도로 일관되게 표기합니다. 학생의 성장 가능성을 긍정적으로 격려하되 사실에 기반합니다.",
                false, true, "Mask", "Hybrid",
                "[\"career-student\",\"career-coaching\"]"
            ),
            (
                "career-action-recommender",
                "career 액션 추천기",
                "ai-service /ai/actions/{id} (CA-3) — 단일 액션 상세 추천",
                "chatgpt", "gpt-4o-mini", 0.5m, 2048,
                "당신은 진로 액션 상세 추천 AI 입니다. " +
                "지정된 액션 ID에 대해 학생 맞춤형 실행 가이드(예상 소요 시간, 사전 요구 사항, 단계별 체크리스트, 성공 지표)를 한국어로 작성합니다. " +
                "현실적이고 구체적이어야 하며, 추상적인 동기 부여 문구만으로 채우지 않습니다.",
                false, true, "Mask", "Hybrid",
                "[\"career-student\",\"career-coaching\"]"
            ),
            (
                "career-chatbot",
                "career 코칭 챗봇",
                "coaching-service / ai-service /ai/chat (CA-5, CA-17). PII 위험 — Internal Nexus 강제",
                "nexus", "primary", 0.7m, 4096,
                "당신은 학생 진로 코칭 챗봇입니다. " +
                "학생의 진로 고민/감정/심리적 어려움을 경청하고 공감하는 어조로 한국어로 응답합니다. " +
                "다만 의료/법률/정신과적 진단을 내리지 않으며, 위기 신호(자해/극단적 불안)가 감지되면 즉시 학생 상담 센터 연결을 권유합니다. " +
                "학생의 이름·학번·연락처는 응답에 다시 표기하지 않습니다(개인정보 보호). " +
                "본 Agent 는 사내 LAN-only Nexus 로 라우팅되어 외부 LLM 으로 데이터가 유출되지 않습니다.",
                false, true, "Block", "Internal",
                "[\"career-coaching\"]"
            ),
            (
                "career-semester-planner",
                "career 학기 목표 플래너",
                "ai-service /ai/sprint/{id} (CA-6) — 학기 단위 목표/스프린트 생성",
                "chatgpt", "gpt-4o-mini", 0.4m, 4096,
                "당신은 학기 단위 진로 학습 목표 플래너입니다. " +
                "현재 학기/잔여 주차/학생 목표 직무를 입력받아 SMART 원칙에 따른 한 학기 목표 3~5개와 주차별 마일스톤을 한국어로 생성합니다. " +
                "각 목표에는 측정 가능한 산출물(포트폴리오/프로젝트/자격증 등)을 포함하며, 학사 일정과 충돌이 없는지 확인합니다.",
                false, true, "Mask", "Hybrid",
                "[\"career-student\"]"
            ),
            (
                "career-simulation-suggester",
                "career 시뮬레이션 추천기",
                "simulation-service _generate_ai_suggestions (CA-12) — 4개 시나리오 추천",
                "chatgpt", "gpt-4o-mini", 0.7m, 2000,
                "당신은 학생 진로 시뮬레이션 시나리오 생성 AI 입니다. " +
                "학생 현재 상태(전공/학년/관심분야) 기준으로 진로 가설 시나리오 4개를 한국어 JSON 배열로 추천합니다. " +
                "각 시나리오는 {\"title\":..., \"summary\":..., \"required_actions\":[...], \"expected_outcome\":...} 구조이며, " +
                "다양성을 위해 안전한 선택 1개 + 도전적 선택 2개 + 비전형 선택 1개를 균형 있게 포함합니다.",
                false, true, "Mask", "Hybrid",
                "[\"career-student\"]"
            ),
            (
                "career-simulation-analyzer",
                "career 시뮬레이션 분석기",
                "simulation-service _generate_ai_analysis (CA-13) — 선택 결과 분석",
                "chatgpt", "gpt-4o-mini", 0.7m, 1500,
                "당신은 학생이 선택한 진로 시뮬레이션 결과 분석 AI 입니다. " +
                "선택된 시나리오와 학생의 현재 데이터를 비교하여 1) 성공 가능성 (0~100%) 2) 주요 위험 요소 3) 보완 액션 의 3단 분석을 한국어로 제공합니다. " +
                "수치는 학생의 정량 데이터에 근거하여 산출하며, 근거가 부족하면 신뢰도(낮음/중간/높음)를 함께 표기합니다.",
                false, true, "Mask", "Hybrid",
                "[\"career-student\"]"
            ),

            // ── 공통 영역 (3개 — AI_INVENTORY §6.3) ────────────────────────────
            (
                "embedding-default",
                "기본 임베딩",
                "모든 시스템의 임베딩 위임 (DU-18, CA-14~16). 1536D 표준 (ADR-10)",
                "chatgpt", "text-embedding-3-small", 0.0m, 0,
                "(임베딩 전용 Agent — system prompt 미사용)",
                false, false, "Block", "External",
                "[\"docutil-user\",\"career-student\",\"career-coaching\"]"
            ),
            (
                "web-search-default",
                "기본 웹 검색",
                "Tavily 검색 위임 Agent (AH-14). EnableWebSearch=true 로 동작",
                "chatgpt", "gpt-4o-mini", 0.3m, 2048,
                "당신은 웹 검색 결과를 한국어로 요약하는 AI 입니다. " +
                "사용자의 질문에 대해 Tavily 검색으로 수집된 최신 결과를 바탕으로 객관적으로 요약하며, 출처(URL)를 함께 표기합니다. " +
                "검색 결과가 모순되면 양측 입장을 모두 제시하고, 단정적 주장은 피합니다. " +
                "광고/홍보성 콘텐츠는 사실과 분리하여 표기합니다.",
                false, false, "Block", "External",
                "[\"docutil-user\",\"career-student\"]"
            ),
            (
                "agentic-search",
                "DocUtil Agentic Search",
                "DocUtil agentic_search 모듈 (DU-16) — factory 우회 P1 위반 정리용",
                "chatgpt", "gpt-4o-mini", 0.4m, 4096,
                "당신은 다단계 에이전틱 검색 AI 입니다. " +
                "사용자의 복잡한 질문을 하위 질문으로 분해하고, 각 하위 질문에 대해 RAG 검색을 수행한 후 결과를 종합하여 한국어로 응답합니다. " +
                "각 단계의 추론 과정을 간결히 보여주며(Chain-of-Thought 요약), 최종 답변에는 사용된 문서 출처를 명시합니다. " +
                "검색 단계가 5회를 초과할 경우 자체 종료하고 부분 답변을 반환합니다.",
                true, true, "Mask", "Hybrid",
                "[\"docutil-user\"]"
            ),
        };

        var inserted = 0;
        var skipped = 0;

        foreach (var s in seeds)
        {
            // 멱등 가드: AgentCode 가 이미 있으면 운영자가 수정했을 가능성이 있으므로 skip.
            if (await context.Agents.AnyAsync(a => a.AgentCode == s.AgentCode))
            {
                skipped++;
                continue;
            }

            // ServiceCode 매핑 — nexus 외부망 미등록 환경에서는 해당 Agent skip.
            var service = await context.ApiServices
                .AsNoTracking()
                .FirstOrDefaultAsync(svc => svc.ServiceCode == s.ServiceCode);

            if (service == null)
            {
                Console.Error.WriteLine(
                    $"[DatabaseInitializer] SeedAgentsAsync skip {s.AgentCode}: ServiceCode '{s.ServiceCode}' 미등록 (외부망 환경에서 nexus skip 가능)");
                skipped++;
                continue;
            }

            context.Agents.Add(new Agent
            {
                AgentCode = s.AgentCode,
                AgentName = s.AgentName,
                Description = s.Description,
                ServiceId = service.ServiceId,
                DefaultModel = s.DefaultModel,
                SystemPrompt = s.SystemPrompt,
                Temperature = s.Temperature,
                MaxTokens = s.MaxTokens > 0 ? s.MaxTokens : (int?)null,
                EnableRag = s.EnableRag,
                PiiProtectionEnabled = s.PiiEnabled,
                PiiProtectionMode = s.PiiMode,
                LlmRouting = s.LlmRouting,
                // 트랙 #138 (2026-06-01): Hybrid 시드 Agent 가 정책 NULL 상태에서 빈 폴백
                // (Decision=external, Reason=empty_policy) → 운영자 의도(PII 보호 + 라벨 분기)
                // 미반영. domain-model.md 의 표준 정책 JSON 을 시드에 포함하여 재배포 시
                // 회귀 차단. External/Internal 은 정책 불필요 → NULL 유지.
                RoutingPolicyJson = s.LlmRouting == "Hybrid" ? DefaultHybridRoutingPolicyJson : null,
                KnowledgeBaseSource = s.EnableRag ? "DocUtil" : "AgentHub", // ADR-2: RAG 활성 시 DocUtil 위임
                KnowledgeBaseRef = null,                                   // Phase 6 KB 마이그레이션 시 collection ID 매핑
                ConsumerSystems = s.ConsumerSystems,
                IsActive = true,
                IsPublic = false,                                          // 시스템 시드는 운영자 콘솔 한정 — 게스트 노출 금지
                CreatedBy = adminUser.UserId,
                SortOrder = 100,                                            // 사용자 생성 Agent(0~99) 보다 뒤로
                IconClass = "bi-robot",
                ColorCode = "#6366f1",
                CreatedAt = now,
                UpdatedAt = now
            });
            inserted++;
        }

        if (inserted > 0)
        {
            await context.SaveChangesAsync();
        }

        Console.Out.WriteLine(
            $"[DatabaseInitializer] SeedAgentsAsync 완료: inserted={inserted} skipped={skipped} (총 {seeds.Length})");
    }
}
