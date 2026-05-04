using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;
using System.Text.Json;

namespace AIAgentManagement.Services;

public class WorkflowService : IWorkflowService
{
    private readonly AIAgentManagementDbContext _context;

    public WorkflowService(AIAgentManagementDbContext context)
    {
        _context = context;
    }

    public async Task<List<WorkflowDto>> GetWorkflowsAsync(int? userId = null, bool? isPublic = null, string? search = null)
    {
        try
        {
            var query = _context.Workflows
                .AsNoTracking()
                .Where(w => w.IsActive)
                .AsQueryable();

            if (userId.HasValue)
            {
                query = query.Where(w => w.CreatedBy == userId.Value || w.IsPublic);
            }

            if (isPublic.HasValue)
            {
                query = query.Where(w => w.IsPublic == isPublic.Value);
            }

            if (!string.IsNullOrEmpty(search))
            {
                query = query.Where(w =>
                    w.WorkflowName.Contains(search) ||
                    (w.Description != null && w.Description.Contains(search)));
            }

            var workflowsList = await query
                .OrderByDescending(w => w.CreatedAt)
                .ToListAsync();

            var userIds = workflowsList.Select(w => w.CreatedBy).Distinct().ToList();
            var users = await _context.Users
                .AsNoTracking()
                .Where(u => userIds.Contains(u.UserId))
                .ToDictionaryAsync(u => u.UserId, u => u);

            var workflowIds = workflowsList.Select(w => w.WorkflowId).ToList();
            var nodes = await _context.WorkflowNodes
                .AsNoTracking()
                .Where(n => workflowIds.Contains(n.WorkflowId))
                .ToListAsync();

            var nodesByWorkflow = nodes.GroupBy(n => n.WorkflowId)
                .ToDictionary(g => g.Key, g => g.ToList());

            var workflows = workflowsList.Select(w => new WorkflowDto
            {
                WorkflowId = w.WorkflowId,
                WorkflowCode = w.WorkflowCode,
                WorkflowName = w.WorkflowName,
                Description = w.Description,
                WorkflowDefinition = w.WorkflowDefinition,
                IconClass = w.IconClass,
                ColorCode = w.ColorCode,
                CreatedBy = w.CreatedBy,
                CreatedByName = users.TryGetValue(w.CreatedBy, out var user) ? (user.FullName ?? "Unknown") : "Unknown",
                IsPublic = w.IsPublic,
                IsActive = w.IsActive,
                CreatedAt = w.CreatedAt,
                UpdatedAt = w.UpdatedAt,
                Nodes = nodesByWorkflow.TryGetValue(w.WorkflowId, out var workflowNodes)
                    ? workflowNodes.Select(n => new WorkflowNodeDto
                    {
                        NodeId = n.NodeId,
                        WorkflowId = n.WorkflowId,
                        NodeCode = n.NodeCode,
                        NodeType = n.NodeType,
                        NodeConfig = n.NodeConfig,
                        PositionX = n.PositionX,
                        PositionY = n.PositionY,
                        Connections = n.Connections,
                        SortOrder = n.SortOrder
                    }).ToList()
                    : new List<WorkflowNodeDto>()
            }).ToList();

            return workflows;
        }
        catch (Exception ex)
        {
            throw new Exception($"Error in GetWorkflowsAsync: {ex.Message}", ex);
        }
    }

    public async Task<WorkflowDto?> GetWorkflowByIdAsync(int workflowId)
    {
        var workflow = await _context.Workflows
            .AsNoTracking()
            .Where(w => w.WorkflowId == workflowId && w.IsActive)
            .Select(w => new WorkflowDto
            {
                WorkflowId = w.WorkflowId,
                WorkflowCode = w.WorkflowCode,
                WorkflowName = w.WorkflowName,
                Description = w.Description,
                WorkflowDefinition = w.WorkflowDefinition,
                IconClass = w.IconClass,
                ColorCode = w.ColorCode,
                CreatedBy = w.CreatedBy,
                CreatedByName = w.Creator.FullName ?? "Unknown",
                IsPublic = w.IsPublic,
                IsActive = w.IsActive,
                CreatedAt = w.CreatedAt,
                UpdatedAt = w.UpdatedAt,
                Nodes = w.WorkflowNodes.Select(n => new WorkflowNodeDto
                {
                    NodeId = n.NodeId,
                    WorkflowId = n.WorkflowId,
                    NodeCode = n.NodeCode,
                    NodeType = n.NodeType,
                    NodeConfig = n.NodeConfig,
                    PositionX = n.PositionX,
                    PositionY = n.PositionY,
                    Connections = n.Connections,
                    SortOrder = n.SortOrder
                }).ToList()
            })
            .FirstOrDefaultAsync();

        return workflow;
    }

    public async Task<WorkflowDto> CreateWorkflowAsync(CreateWorkflowRequestDto request, int createdBy)
    {
        var workflowCode = request.WorkflowCode ?? GenerateWorkflowCode(request.WorkflowName);

        // 중복 체크
        if (await _context.Workflows.AnyAsync(w => w.WorkflowCode == workflowCode))
        {
            throw new InvalidOperationException($"Workflow with code '{workflowCode}' already exists");
        }

        var workflow = new Workflow
        {
            WorkflowCode = workflowCode,
            WorkflowName = request.WorkflowName,
            Description = request.Description,
            WorkflowDefinition = request.WorkflowDefinition,
            IconClass = request.IconClass,
            ColorCode = request.ColorCode,
            CreatedBy = createdBy,
            IsPublic = request.IsPublic ?? false,
            IsActive = true,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };

        _context.Workflows.Add(workflow);
        await _context.SaveChangesAsync();

        // 노드 추가
        if (request.Nodes != null && request.Nodes.Any())
        {
            foreach (var nodeDto in request.Nodes)
            {
                var node = new WorkflowNode
                {
                    WorkflowId = workflow.WorkflowId,
                    NodeCode = nodeDto.NodeCode,
                    NodeType = nodeDto.NodeType,
                    NodeConfig = nodeDto.NodeConfig,
                    PositionX = nodeDto.PositionX,
                    PositionY = nodeDto.PositionY,
                    Connections = nodeDto.Connections,
                    SortOrder = nodeDto.SortOrder,
                    CreatedAt = DateTime.UtcNow,
                    UpdatedAt = DateTime.UtcNow
                };

                _context.WorkflowNodes.Add(node);
            }

            await _context.SaveChangesAsync();
        }

        return (await GetWorkflowByIdAsync(workflow.WorkflowId))!;
    }

    public async Task<WorkflowDto?> UpdateWorkflowAsync(int workflowId, UpdateWorkflowRequestDto request, int userId)
    {
        var workflow = await _context.Workflows
            .Include(w => w.WorkflowNodes)
            .FirstOrDefaultAsync(w => w.WorkflowId == workflowId && w.IsActive);

        if (workflow == null)
        {
            return null;
        }

        // 권한 체크
        if (workflow.CreatedBy != userId)
        {
            throw new UnauthorizedAccessException("You don't have permission to update this workflow");
        }

        if (!string.IsNullOrEmpty(request.WorkflowName))
        {
            workflow.WorkflowName = request.WorkflowName;
        }

        if (request.Description != null)
        {
            workflow.Description = request.Description;
        }

        if (request.WorkflowDefinition != null)
        {
            workflow.WorkflowDefinition = request.WorkflowDefinition;
        }

        if (request.IconClass != null)
        {
            workflow.IconClass = request.IconClass;
        }

        if (request.ColorCode != null)
        {
            workflow.ColorCode = request.ColorCode;
        }

        if (request.IsPublic.HasValue)
        {
            workflow.IsPublic = request.IsPublic.Value;
        }

        if (request.IsActive.HasValue)
        {
            workflow.IsActive = request.IsActive.Value;
        }

        // 노드 업데이트
        if (request.Nodes != null)
        {
            // 기존 노드 삭제
            _context.WorkflowNodes.RemoveRange(workflow.WorkflowNodes);

            // 새 노드 추가
            foreach (var nodeDto in request.Nodes)
            {
                var node = new WorkflowNode
                {
                    WorkflowId = workflowId,
                    NodeCode = nodeDto.NodeCode,
                    NodeType = nodeDto.NodeType,
                    NodeConfig = nodeDto.NodeConfig,
                    PositionX = nodeDto.PositionX,
                    PositionY = nodeDto.PositionY,
                    Connections = nodeDto.Connections,
                    SortOrder = nodeDto.SortOrder,
                    CreatedAt = DateTime.UtcNow,
                    UpdatedAt = DateTime.UtcNow
                };

                _context.WorkflowNodes.Add(node);
            }
        }

        workflow.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync();

        return await GetWorkflowByIdAsync(workflowId);
    }

    public async Task<bool> DeleteWorkflowAsync(int workflowId, int userId)
    {
        var workflow = await _context.Workflows
            .FirstOrDefaultAsync(w => w.WorkflowId == workflowId && w.IsActive);

        if (workflow == null)
        {
            return false;
        }

        // 권한 체크
        if (workflow.CreatedBy != userId)
        {
            throw new UnauthorizedAccessException("You don't have permission to delete this workflow");
        }

        workflow.IsActive = false;
        workflow.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync();

        return true;
    }

    private string GenerateWorkflowCode(string workflowName)
    {
        var code = workflowName
            .Replace(" ", "-")
            .Replace("_", "-")
            .ToLowerInvariant();

        // 특수문자 제거
        code = System.Text.RegularExpressions.Regex.Replace(code, @"[^a-z0-9-]", "");

        // 중복 체크 및 숫자 추가
        var baseCode = code;
        var counter = 1;
        while (_context.Workflows.Any(w => w.WorkflowCode == code))
        {
            code = $"{baseCode}-{counter}";
            counter++;
        }

        return code;
    }
}
