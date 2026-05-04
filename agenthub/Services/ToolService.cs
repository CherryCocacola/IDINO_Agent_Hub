using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

public class ToolService : IToolService
{
    private readonly AIAgentManagementDbContext _context;

    public ToolService(AIAgentManagementDbContext context)
    {
        _context = context;
    }

    public async Task<List<ToolDto>> GetToolsAsync(int? userId = null, bool? isPublic = null, string? toolType = null, string? search = null)
    {
        try
        {
            var query = _context.Tools
                .AsNoTracking()
                .Where(t => t.IsActive)
                .AsQueryable();

            if (userId.HasValue)
            {
                query = query.Where(t => t.CreatedBy == userId.Value || t.IsPublic);
            }

            if (isPublic.HasValue)
            {
                query = query.Where(t => t.IsPublic == isPublic.Value);
            }

            if (!string.IsNullOrEmpty(toolType))
            {
                query = query.Where(t => t.ToolType == toolType);
            }

            if (!string.IsNullOrEmpty(search))
            {
                query = query.Where(t =>
                    t.ToolName.Contains(search) ||
                    (t.Description != null && t.Description.Contains(search)));
            }

            var toolsList = await query
                .OrderByDescending(t => t.CreatedAt)
                .ToListAsync();

            var userIds = toolsList.Select(t => t.CreatedBy).Distinct().ToList();
            var users = await _context.Users
                .AsNoTracking()
                .Where(u => userIds.Contains(u.UserId))
                .ToDictionaryAsync(u => u.UserId, u => u);

            var toolIds = toolsList.Select(t => t.ToolId).ToList();
            var activeVersions = await _context.ToolVersions
                .AsNoTracking()
                .Where(v => toolIds.Contains(v.ToolId) && v.IsActive)
                .ToDictionaryAsync(v => v.ToolId, v => v);

            var tools = toolsList.Select(t => new ToolDto
            {
                ToolId = t.ToolId,
                ToolCode = t.ToolCode,
                ToolName = t.ToolName,
                Description = t.Description,
                ToolType = t.ToolType,
                Category = t.Category,
                IconClass = t.IconClass,
                ColorCode = t.ColorCode,
                CreatedBy = t.CreatedBy,
                CreatedByName = users.TryGetValue(t.CreatedBy, out var user) ? (user.FullName ?? "Unknown") : "Unknown",
                IsPublic = t.IsPublic,
                IsActive = t.IsActive,
                CreatedAt = t.CreatedAt,
                UpdatedAt = t.UpdatedAt,
                ActiveVersion = activeVersions.TryGetValue(t.ToolId, out var version) ? new ToolVersionDto
                {
                    VersionId = version.VersionId,
                    ToolId = version.ToolId,
                    Version = version.Version,
                    Code = version.Code,
                    Config = version.Config,
                    IsActive = version.IsActive,
                    CreatedAt = version.CreatedAt
                } : null
            }).ToList();

            return tools;
        }
        catch (Exception ex)
        {
            throw new Exception($"Error in GetToolsAsync: {ex.Message}", ex);
        }
    }

    public async Task<ToolDto?> GetToolByIdAsync(int toolId)
    {
        var tool = await _context.Tools
            .AsNoTracking()
            .Where(t => t.ToolId == toolId && t.IsActive)
            .Select(t => new ToolDto
            {
                ToolId = t.ToolId,
                ToolCode = t.ToolCode,
                ToolName = t.ToolName,
                Description = t.Description,
                ToolType = t.ToolType,
                Category = t.Category,
                IconClass = t.IconClass,
                ColorCode = t.ColorCode,
                CreatedBy = t.CreatedBy,
                CreatedByName = t.Creator.FullName ?? "Unknown",
                IsPublic = t.IsPublic,
                IsActive = t.IsActive,
                CreatedAt = t.CreatedAt,
                UpdatedAt = t.UpdatedAt,
                ActiveVersion = t.ToolVersions
                    .Where(v => v.IsActive)
                    .OrderByDescending(v => v.CreatedAt)
                    .Select(v => new ToolVersionDto
                    {
                        VersionId = v.VersionId,
                        ToolId = v.ToolId,
                        Version = v.Version,
                        Code = v.Code,
                        Config = v.Config,
                        IsActive = v.IsActive,
                        CreatedAt = v.CreatedAt
                    })
                    .FirstOrDefault()
            })
            .FirstOrDefaultAsync();

        return tool;
    }

    public async Task<ToolDto> CreateToolAsync(CreateToolRequestDto request, int createdBy)
    {
        var toolCode = request.ToolCode ?? GenerateToolCode(request.ToolName);

        // 중복 체크
        if (await _context.Tools.AnyAsync(t => t.ToolCode == toolCode))
        {
            throw new InvalidOperationException($"Tool with code '{toolCode}' already exists");
        }

        var tool = new Tool
        {
            ToolCode = toolCode,
            ToolName = request.ToolName,
            Description = request.Description,
            ToolType = request.ToolType,
            Category = request.Category,
            IconClass = request.IconClass,
            ColorCode = request.ColorCode,
            CreatedBy = createdBy,
            IsPublic = request.IsPublic ?? false,
            IsActive = true,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };

        _context.Tools.Add(tool);
        await _context.SaveChangesAsync();

        // 첫 버전 생성
        if (!string.IsNullOrEmpty(request.Code) || !string.IsNullOrEmpty(request.Config))
        {
            var version = request.Version ?? "1.0.0";
            await CreateToolVersionAsync(tool.ToolId, version, request.Code, request.Config);
        }

        return (await GetToolByIdAsync(tool.ToolId))!;
    }

    public async Task<ToolDto?> UpdateToolAsync(int toolId, UpdateToolRequestDto request, int userId)
    {
        var tool = await _context.Tools
            .FirstOrDefaultAsync(t => t.ToolId == toolId && t.IsActive);

        if (tool == null)
        {
            return null;
        }

        // 권한 체크
        if (tool.CreatedBy != userId)
        {
            throw new UnauthorizedAccessException("You don't have permission to update this tool");
        }

        if (!string.IsNullOrEmpty(request.ToolName))
        {
            tool.ToolName = request.ToolName;
        }

        if (request.Description != null)
        {
            tool.Description = request.Description;
        }

        if (request.Category != null)
        {
            tool.Category = request.Category;
        }

        if (request.IconClass != null)
        {
            tool.IconClass = request.IconClass;
        }

        if (request.ColorCode != null)
        {
            tool.ColorCode = request.ColorCode;
        }

        if (request.IsPublic.HasValue)
        {
            tool.IsPublic = request.IsPublic.Value;
        }

        if (request.IsActive.HasValue)
        {
            tool.IsActive = request.IsActive.Value;
        }

        tool.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync();

        return await GetToolByIdAsync(toolId);
    }

    public async Task<bool> DeleteToolAsync(int toolId, int userId)
    {
        var tool = await _context.Tools
            .FirstOrDefaultAsync(t => t.ToolId == toolId && t.IsActive);

        if (tool == null)
        {
            return false;
        }

        // 권한 체크
        if (tool.CreatedBy != userId)
        {
            throw new UnauthorizedAccessException("You don't have permission to delete this tool");
        }

        tool.IsActive = false;
        tool.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync();

        return true;
    }

    public async Task<ToolVersionDto> CreateToolVersionAsync(int toolId, string version, string? code, string? config)
    {
        var tool = await _context.Tools.FindAsync(toolId);
        if (tool == null || !tool.IsActive)
        {
            throw new InvalidOperationException($"Tool {toolId} not found or inactive");
        }

        // 기존 활성 버전 비활성화
        var activeVersions = await _context.ToolVersions
            .Where(v => v.ToolId == toolId && v.IsActive)
            .ToListAsync();

        foreach (var activeVersion in activeVersions)
        {
            activeVersion.IsActive = false;
        }

        var toolVersion = new ToolVersion
        {
            ToolId = toolId,
            Version = version,
            Code = code,
            Config = config,
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        _context.ToolVersions.Add(toolVersion);
        await _context.SaveChangesAsync();

        return new ToolVersionDto
        {
            VersionId = toolVersion.VersionId,
            ToolId = toolVersion.ToolId,
            Version = toolVersion.Version,
            Code = toolVersion.Code,
            Config = toolVersion.Config,
            IsActive = toolVersion.IsActive,
            CreatedAt = toolVersion.CreatedAt
        };
    }

    public async Task<List<ToolVersionDto>> GetToolVersionsAsync(int toolId)
    {
        var versions = await _context.ToolVersions
            .AsNoTracking()
            .Where(v => v.ToolId == toolId)
            .OrderByDescending(v => v.CreatedAt)
            .Select(v => new ToolVersionDto
            {
                VersionId = v.VersionId,
                ToolId = v.ToolId,
                Version = v.Version,
                Code = v.Code,
                Config = v.Config,
                IsActive = v.IsActive,
                CreatedAt = v.CreatedAt
            })
            .ToListAsync();

        return versions;
    }

    public async Task<bool> SetActiveVersionAsync(int toolId, int versionId)
    {
        var tool = await _context.Tools.FindAsync(toolId);
        if (tool == null || !tool.IsActive)
        {
            return false;
        }

        var version = await _context.ToolVersions.FindAsync(versionId);
        if (version == null || version.ToolId != toolId)
        {
            return false;
        }

        // 기존 활성 버전 비활성화
        var activeVersions = await _context.ToolVersions
            .Where(v => v.ToolId == toolId && v.IsActive && v.VersionId != versionId)
            .ToListAsync();

        foreach (var activeVersion in activeVersions)
        {
            activeVersion.IsActive = false;
        }

        version.IsActive = true;
        await _context.SaveChangesAsync();

        return true;
    }

    private string GenerateToolCode(string toolName)
    {
        var code = toolName
            .Replace(" ", "-")
            .Replace("_", "-")
            .ToLowerInvariant();

        // 특수문자 제거
        code = System.Text.RegularExpressions.Regex.Replace(code, @"[^a-z0-9-]", "");

        // 중복 체크 및 숫자 추가
        var baseCode = code;
        var counter = 1;
        while (_context.Tools.Any(t => t.ToolCode == code))
        {
            code = $"{baseCode}-{counter}";
            counter++;
        }

        return code;
    }
}
