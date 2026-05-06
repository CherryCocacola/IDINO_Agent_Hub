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
}
