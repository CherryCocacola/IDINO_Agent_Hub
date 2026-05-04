using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

public class AgentService : IAgentService
{
    private readonly AIAgentManagementDbContext _context;

    public AgentService(AIAgentManagementDbContext context)
    {
        _context = context;
    }

    public async Task<List<AgentDto>> GetAgentsAsync(int? userId = null, bool? isPublic = null, string? search = null)
    {
        try
        {
            var query = _context.Agents
                .AsNoTracking()
                .Where(a => a.IsActive)
                .AsQueryable();

            if (userId.HasValue)
            {
                query = query.Where(a => a.CreatedBy == userId.Value || a.IsPublic);
            }

            if (isPublic.HasValue)
            {
                query = query.Where(a => a.IsPublic == isPublic.Value);
            }

            if (!string.IsNullOrEmpty(search))
            {
                query = query.Where(a => 
                    a.AgentName.Contains(search) || 
                    (a.Description != null && a.Description.Contains(search)));
            }

            var agentsList = await query
                .OrderBy(a => a.SortOrder)
                .ThenByDescending(a => a.CreatedAt)
                .ToListAsync();

            // ServiceId·CreatedBy 목록으로 서비스·사용자 일괄 조회 (INNER JOIN 없이 Agent는 모두 반환)
            var serviceIds = agentsList.Select(a => a.ServiceId).Distinct().ToList();
            var userIds = agentsList.Select(a => a.CreatedBy).Distinct().ToList();

            var services = await _context.ApiServices
                .AsNoTracking()
                .Where(s => serviceIds.Contains(s.ServiceId))
                .ToDictionaryAsync(s => s.ServiceId, s => s);

            var users = await _context.Users
                .AsNoTracking()
                .Where(u => userIds.Contains(u.UserId))
                .ToDictionaryAsync(u => u.UserId, u => u);

            // DTO 매핑
            var agents = agentsList.Select(a => new AgentDto
            {
                AgentId = a.AgentId,
                AgentCode = a.AgentCode,
                AgentName = a.AgentName,
                Description = a.Description,
                ServiceId = a.ServiceId,
                ServiceName = services.TryGetValue(a.ServiceId, out var service) ? service.ServiceName : "Unknown",
                SystemPrompt = a.SystemPrompt,
                IconClass = a.IconClass,
                ColorCode = a.ColorCode,
                Temperature = a.Temperature,
                MaxTokens = a.MaxTokens,
                DefaultModel = a.DefaultModel ?? (services.TryGetValue(a.ServiceId, out var svc) ? svc.DefaultModel : null),
                IsPublic = a.IsPublic,
                EnableRag = a.EnableRag,
                PiiProtectionEnabled = a.PiiProtectionEnabled,
                PiiProtectionMode = a.PiiProtectionMode,
                WelcomeMessage = a.WelcomeMessage,
                PlaceholderText = a.PlaceholderText,
                ChatTheme = a.ChatTheme,
                AllowGuestChat = a.AllowGuestChat,
                AllowedEmbedDomains = a.AllowedEmbedDomains,
                CreatedBy = a.CreatedBy,
                CreatedByName = users.TryGetValue(a.CreatedBy, out var user) ? (user.FullName ?? "Unknown") : "Unknown",
                IsActive = a.IsActive,
                CreatedAt = a.CreatedAt,
                UpdatedAt = a.UpdatedAt
            }).ToList();

            return agents;
        }
        catch (Exception ex)
        {
            throw new Exception($"Error in GetAgentsAsync: {ex.Message}", ex);
        }
    }

    public async Task<AgentDto?> GetAgentByIdAsync(int agentId)
    {
        // 프로젝션을 쿼리 레벨에서 수행
        var agent = await _context.Agents
            .AsNoTracking() // 변경 추적 비활성화
            .Where(a => a.AgentId == agentId && a.IsActive)
            .Select(a => new AgentDto
            {
                AgentId = a.AgentId,
                AgentCode = a.AgentCode,
                AgentName = a.AgentName,
                Description = a.Description,
                ServiceId = a.ServiceId,
                ServiceName = a.ApiService.ServiceName,
                SystemPrompt = a.SystemPrompt,
                IconClass = a.IconClass,
                ColorCode = a.ColorCode,
                Temperature = a.Temperature,
                MaxTokens = a.MaxTokens,
                DefaultModel = a.DefaultModel ?? (a.ApiService != null ? a.ApiService.DefaultModel : null),
                IsPublic = a.IsPublic,
                EnableRag = a.EnableRag,
                PiiProtectionEnabled = a.PiiProtectionEnabled,
                PiiProtectionMode = a.PiiProtectionMode,
                WelcomeMessage = a.WelcomeMessage,
                PlaceholderText = a.PlaceholderText,
                ChatTheme = a.ChatTheme,
                AllowGuestChat = a.AllowGuestChat,
                AllowedEmbedDomains = a.AllowedEmbedDomains,
                CreatedBy = a.CreatedBy,
                CreatedByName = a.Creator.FullName,
                IsActive = a.IsActive,
                CreatedAt = a.CreatedAt,
                UpdatedAt = a.UpdatedAt,
                Documents = a.AgentDocuments
                    .Select(ad => new KnowledgeBaseDocumentListDto
                    {
                        DocumentId = ad.Document.DocumentId,
                        UserId = ad.Document.UserId,
                        UserName = ad.Document.User != null ? ad.Document.User.FullName ?? "Unknown" : "Unknown",
                        Title = ad.Document.Title,
                        SourceType = ad.Document.SourceType,
                        SourceId = ad.Document.SourceId,
                        IsIndexed = ad.Document.IsIndexed,
                        IndexedAt = ad.Document.IndexedAt,
                        ChunkCount = ad.Document.Chunks.Count,
                        CreatedAt = ad.Document.CreatedAt,
                        UpdatedAt = ad.Document.UpdatedAt
                    })
                    .ToList()
            })
            .FirstOrDefaultAsync();

        return agent;
    }

    public async Task<AgentDto> CreateAgentAsync(CreateAgentRequestDto request, int createdBy)
    {
        var agentCode = request.AgentCode ?? GenerateAgentCode(request.AgentName);
        
        // Ensure unique agent code
        var existingCode = await _context.Agents.AnyAsync(a => a.AgentCode == agentCode);
        if (existingCode)
        {
            agentCode = $"{agentCode}_{DateTime.UtcNow.Ticks}";
        }

        var agent = new Models.Agent
        {
            AgentCode = agentCode,
            AgentName = request.AgentName,
            Description = request.Description,
            ServiceId = request.ServiceId,
            SystemPrompt = request.SystemPrompt,
            IconClass = request.IconClass,
            ColorCode = SanitizeColorCode(request.ColorCode) ?? "#0d6efd",
            Temperature = request.Temperature ?? 0.7m,
            MaxTokens = request.MaxTokens ?? 2000,
            DefaultModel = request.DefaultModel,
            IsPublic = request.IsPublic ?? false,
            EnableRag = request.EnableRag,
            PiiProtectionEnabled = request.PiiProtectionEnabled ?? true,
            PiiProtectionMode = request.PiiProtectionMode,
            WelcomeMessage = request.WelcomeMessage,
            PlaceholderText = request.PlaceholderText,
            ChatTheme = request.ChatTheme ?? "light",
            AllowGuestChat = request.AllowGuestChat,
            AllowedEmbedDomains = request.AllowedEmbedDomains,
            CreatedBy = createdBy,
            IsActive = true,
            SortOrder = request.SortOrder ?? 0,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };

        _context.Agents.Add(agent);
        await _context.SaveChangesAsync();

        // RAG 문서 연결
        if (request.EnableRag && request.SelectedDocumentIds != null && request.SelectedDocumentIds.Count > 0)
        {
            // 문서가 해당 사용자의 것인지 확인
            var validDocuments = await _context.KnowledgeBaseDocuments
                .Where(d => request.SelectedDocumentIds.Contains(d.DocumentId) && d.UserId == createdBy && d.IsIndexed)
                .Select(d => d.DocumentId)
                .ToListAsync();

            foreach (var documentId in validDocuments)
            {
                _context.AgentDocuments.Add(new Models.AgentDocument
                {
                    AgentId = agent.AgentId,
                    DocumentId = documentId,
                    CreatedAt = DateTime.UtcNow
                });
            }

            await _context.SaveChangesAsync();
        }

        return await GetAgentByIdAsync(agent.AgentId) ?? throw new InvalidOperationException("Failed to create agent");
    }

    public async Task<AgentDto?> UpdateAgentAsync(int agentId, UpdateAgentRequestDto request, int userId, bool isAdmin = false)
    {
        var agent = await _context.Agents.FirstOrDefaultAsync(a => a.AgentId == agentId && a.IsActive);
        if (agent == null) return null;

        // Admin은 모든 Agent 수정 가능, 일반 사용자는 본인이 만든 Agent만 수정 가능
        if (!isAdmin && agent.CreatedBy != userId)
        {
            throw new UnauthorizedAccessException("수정 권한이 없습니다.");
        }

        agent.AgentName = request.AgentName ?? agent.AgentName;
        agent.Description = request.Description ?? agent.Description;
        agent.ServiceId = request.ServiceId ?? agent.ServiceId;
        agent.SystemPrompt = request.SystemPrompt ?? agent.SystemPrompt;
        agent.IconClass = request.IconClass ?? agent.IconClass;
        agent.ColorCode = SanitizeColorCode(request.ColorCode ?? agent.ColorCode) ?? agent.ColorCode;
        agent.Temperature = request.Temperature ?? agent.Temperature;
        agent.MaxTokens = request.MaxTokens ?? agent.MaxTokens;
        if (request.DefaultModel != null)
        {
            agent.DefaultModel = request.DefaultModel;
        }
        agent.IsPublic = request.IsPublic ?? agent.IsPublic;
        agent.SortOrder = request.SortOrder ?? agent.SortOrder;
        if (request.PiiProtectionEnabled.HasValue)
        {
            agent.PiiProtectionEnabled = request.PiiProtectionEnabled.Value;
        }
        if (request.PiiProtectionMode != null)
        {
            agent.PiiProtectionMode = request.PiiProtectionMode;
        }
        if (request.WelcomeMessage != null) agent.WelcomeMessage = request.WelcomeMessage;
        if (request.PlaceholderText != null) agent.PlaceholderText = request.PlaceholderText;
        if (request.ChatTheme != null) agent.ChatTheme = request.ChatTheme;
        if (request.AllowGuestChat.HasValue) agent.AllowGuestChat = request.AllowGuestChat.Value;
        if (request.AllowedEmbedDomains != null) agent.AllowedEmbedDomains = string.IsNullOrWhiteSpace(request.AllowedEmbedDomains) ? null : request.AllowedEmbedDomains;
        agent.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync();
        return await GetAgentByIdAsync(agentId);
    }

    public async Task<bool> DeleteAgentAsync(int agentId, int userId, bool isAdmin = false)
    {
        var agent = await _context.Agents.FirstOrDefaultAsync(a => a.AgentId == agentId && a.IsActive);
        if (agent == null) return false;

        // Admin은 모든 Agent 삭제 가능, 일반 사용자는 본인이 만든 Agent만 삭제 가능
        if (!isAdmin && agent.CreatedBy != userId)
        {
            throw new UnauthorizedAccessException("삭제 권한이 없습니다.");
        }

        agent.IsActive = false;
        agent.UpdatedAt = DateTime.UtcNow;
        await _context.SaveChangesAsync();

        return true;
    }

    private string GenerateAgentCode(string agentName)
    {
        return agentName
            .Replace(" ", "-")
            .ToLowerInvariant()
            .Replace("--", "-")
            .Trim('-');
    }

    /// <summary>흰색 계열 colorCode는 저장하지 않고 기본값으로 대체</summary>
    private static string? SanitizeColorCode(string? colorCode)
    {
        if (string.IsNullOrWhiteSpace(colorCode)) return colorCode;
        var normalized = colorCode.Trim().ToLowerInvariant();
        if (normalized is "#fff" or "#ffffff" or "white") return "#0d6efd";
        return colorCode;
    }
}
