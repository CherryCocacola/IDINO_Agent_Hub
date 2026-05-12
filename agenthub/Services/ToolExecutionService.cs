using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Exceptions;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

public class ToolExecutionService : IToolExecutionService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ICSharpToolExecutor _csharpExecutor;
    private readonly IScriptToolExecutor _scriptExecutor;
    private readonly IApiToolExecutor _apiExecutor;
    private readonly ILogger<ToolExecutionService> _logger;

    public ToolExecutionService(
        AIAgentManagementDbContext context,
        ICSharpToolExecutor csharpExecutor,
        IScriptToolExecutor scriptExecutor,
        IApiToolExecutor apiExecutor,
        ILogger<ToolExecutionService> logger)
    {
        _context = context;
        _csharpExecutor = csharpExecutor;
        _scriptExecutor = scriptExecutor;
        _apiExecutor = apiExecutor;
        _logger = logger;
    }

    public async Task<ToolExecutionDto> ExecuteToolAsync(int toolId, ExecuteToolRequestDto request, int? userId = null)
    {
        var tool = await _context.Tools
            .Include(t => t.ToolVersions)
            .FirstOrDefaultAsync(t => t.ToolId == toolId && t.IsActive);

        if (tool == null)
        {
            // 도메인 예외로 분리하여 컨트롤러가 404 로 매핑하도록 한다.
            // (기존 InvalidOperationException → catch (Exception) → 500 흐름 방지)
            throw new ToolNotFoundException(toolId);
        }

        // 활성 버전 가져오기
        var version = request.VersionId.HasValue
            ? await _context.ToolVersions.FindAsync(request.VersionId.Value)
            : tool.ToolVersions.FirstOrDefault(v => v.IsActive);

        if (version == null)
        {
            // 활성 ToolVersion 미등록 = 운영 데이터 결손. 500 이 아니라 400 으로 안내한다.
            // 운영자가 /api/tools/{id}/versions POST + activate 를 먼저 호출해야 한다.
            throw new ToolVersionNotActiveException(toolId);
        }

        // 실행 기록 생성
        var execution = new ToolExecution
        {
            ToolId = toolId,
            VersionId = version.VersionId,
            UserId = userId,
            InputData = request.InputData,
            Status = "Running",
            CreatedAt = DateTime.UtcNow
        };

        _context.ToolExecutions.Add(execution);
        await _context.SaveChangesAsync();

        var startTime = DateTime.UtcNow;
        var memoryBefore = GC.GetTotalMemory(false);

        try
        {
            string? outputData = null;

            // Tool 타입에 따라 실행기 선택
            switch (tool.ToolType.ToLower())
            {
                case "csharp":
                    outputData = await _csharpExecutor.ExecuteAsync(version.Code ?? "", request.InputData);
                    break;

                case "python":
                case "javascript":
                    outputData = await _scriptExecutor.ExecuteAsync(tool.ToolType, version.Code ?? "", request.InputData);
                    break;

                case "api":
                    outputData = await _apiExecutor.ExecuteAsync(version.Config ?? "", request.InputData);
                    break;

                default:
                    throw new NotSupportedException($"Tool type '{tool.ToolType}' is not supported");
            }

            var executionTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
            var memoryAfter = GC.GetTotalMemory(false);
            var memoryUsage = memoryAfter - memoryBefore;

            execution.OutputData = outputData;
            execution.Status = "Completed";
            execution.ExecutionTime = executionTime;
            execution.MemoryUsage = memoryUsage > 0 ? memoryUsage : null;

            await _context.SaveChangesAsync();

            return MapToDto(execution, tool);
        }
        catch (Exception ex)
        {
            var executionTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;

            execution.Status = "Failed";
            execution.ErrorMessage = ex.Message;
            execution.ExecutionTime = executionTime;

            await _context.SaveChangesAsync();

            _logger.LogError(ex, "Error executing tool {ToolId}", toolId);

            return MapToDto(execution, tool);
        }
    }

    public async Task<ToolExecutionDto?> GetExecutionByIdAsync(long executionId)
    {
        var execution = await _context.ToolExecutions
            .AsNoTracking()
            .Include(e => e.Tool)
            .Include(e => e.ToolVersion)
            .FirstOrDefaultAsync(e => e.ExecutionId == executionId);

        if (execution == null)
        {
            return null;
        }

        return MapToDto(execution, execution.Tool);
    }

    public async Task<List<ToolExecutionDto>> GetExecutionsAsync(int? toolId = null, int? userId = null, string? status = null, int skip = 0, int take = 50)
    {
        var query = _context.ToolExecutions
            .AsNoTracking()
            .Include(e => e.Tool)
            .Include(e => e.ToolVersion)
            .AsQueryable();

        if (toolId.HasValue)
        {
            query = query.Where(e => e.ToolId == toolId.Value);
        }

        if (userId.HasValue)
        {
            query = query.Where(e => e.UserId == userId.Value);
        }

        if (!string.IsNullOrEmpty(status))
        {
            query = query.Where(e => e.Status == status);
        }

        var executions = await query
            .OrderByDescending(e => e.CreatedAt)
            .Skip(skip)
            .Take(take)
            .ToListAsync();

        return executions.Select(e => MapToDto(e, e.Tool)).ToList();
    }

    private ToolExecutionDto MapToDto(ToolExecution execution, Tool tool)
    {
        return new ToolExecutionDto
        {
            ExecutionId = execution.ExecutionId,
            ToolId = execution.ToolId,
            ToolName = tool.ToolName,
            VersionId = execution.VersionId,
            Version = execution.ToolVersion?.Version,
            UserId = execution.UserId,
            InputData = execution.InputData,
            OutputData = execution.OutputData,
            Status = execution.Status,
            ErrorMessage = execution.ErrorMessage,
            ExecutionTime = execution.ExecutionTime,
            MemoryUsage = execution.MemoryUsage,
            CreatedAt = execution.CreatedAt
        };
    }
}
