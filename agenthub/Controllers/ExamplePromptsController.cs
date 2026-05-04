using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class ExamplePromptsController : ControllerBase
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<ExamplePromptsController> _logger;

    public ExamplePromptsController(AIAgentManagementDbContext context, ILogger<ExamplePromptsController> logger)
    {
        _context = context;
        _logger = logger;
    }

    // GET: api/exampleprompts (비로그인 접근 허용 — 채팅 화면 예시 프롬프트 조회)
    [HttpGet]
    [AllowAnonymous]
    public async Task<ActionResult<List<ExamplePromptDto>>> GetExamplePrompts(
        [FromQuery] string? serviceCode,
        [FromQuery] string? model,
        [FromQuery] string? category,
        [FromQuery] bool? isActive)
    {
        try
        {
            var query = _context.ExamplePrompts.AsQueryable();

            if (!string.IsNullOrEmpty(serviceCode))
            {
                // ServiceCode가 일치하거나 null인 것 (null은 모든 서비스에 적용)
                query = query.Where(e => e.ServiceCode == serviceCode || e.ServiceCode == null);
            }

            if (!string.IsNullOrEmpty(model))
            {
                // Model이 null이거나 일치하는 것 (null은 모든 모델에 적용)
                query = query.Where(e => e.Model == null || e.Model == model);
            }

            if (!string.IsNullOrEmpty(category))
            {
                query = query.Where(e => e.Category == category);
            }

            if (isActive.HasValue)
            {
                query = query.Where(e => e.IsActive == isActive.Value);
            }

            var examplePrompts = await query
                .OrderBy(e => e.SortOrder)
                .ThenBy(e => e.ExamplePromptId)
                .Select(e => new ExamplePromptDto
                {
                    ExamplePromptId = e.ExamplePromptId,
                    Title = e.Title,
                    Prompt = e.Prompt,
                    Description = e.Description,
                    ServiceCode = e.ServiceCode,
                    Model = e.Model,
                    Category = e.Category,
                    IconClass = e.IconClass,
                    SortOrder = e.SortOrder,
                    IsActive = e.IsActive,
                    CreatedAt = e.CreatedAt,
                    UpdatedAt = e.UpdatedAt
                })
                .ToListAsync();

            return Ok(examplePrompts);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting example prompts");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    // GET: api/exampleprompts/{id} (비로그인 접근 허용)
    [HttpGet("{id}")]
    [AllowAnonymous]
    public async Task<ActionResult<ExamplePromptDto>> GetExamplePrompt(int id)
    {
        try
        {
            var examplePrompt = await _context.ExamplePrompts.FindAsync(id);
            if (examplePrompt == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            var examplePromptDto = new ExamplePromptDto
            {
                ExamplePromptId = examplePrompt.ExamplePromptId,
                Title = examplePrompt.Title,
                Prompt = examplePrompt.Prompt,
                Description = examplePrompt.Description,
                ServiceCode = examplePrompt.ServiceCode,
                Model = examplePrompt.Model,
                Category = examplePrompt.Category,
                IconClass = examplePrompt.IconClass,
                SortOrder = examplePrompt.SortOrder,
                IsActive = examplePrompt.IsActive,
                CreatedAt = examplePrompt.CreatedAt,
                UpdatedAt = examplePrompt.UpdatedAt
            };

            return Ok(examplePromptDto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting example prompt {Id}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    // POST: api/exampleprompts
    [HttpPost]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<ExamplePromptDto>> CreateExamplePrompt([FromBody] CreateExamplePromptRequestDto request)
    {
        try
        {
            var examplePrompt = new Models.ExamplePrompt
            {
                Title = request.Title,
                Prompt = request.Prompt,
                Description = request.Description,
                ServiceCode = request.ServiceCode,
                Model = request.Model,
                Category = request.Category,
                IconClass = request.IconClass,
                SortOrder = request.SortOrder,
                IsActive = request.IsActive,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            };

            _context.ExamplePrompts.Add(examplePrompt);
            await _context.SaveChangesAsync();

            var examplePromptDto = new ExamplePromptDto
            {
                ExamplePromptId = examplePrompt.ExamplePromptId,
                Title = examplePrompt.Title,
                Prompt = examplePrompt.Prompt,
                Description = examplePrompt.Description,
                ServiceCode = examplePrompt.ServiceCode,
                Model = examplePrompt.Model,
                Category = examplePrompt.Category,
                IconClass = examplePrompt.IconClass,
                SortOrder = examplePrompt.SortOrder,
                IsActive = examplePrompt.IsActive,
                CreatedAt = examplePrompt.CreatedAt,
                UpdatedAt = examplePrompt.UpdatedAt
            };

            return CreatedAtAction(nameof(GetExamplePrompt), new { id = examplePrompt.ExamplePromptId }, examplePromptDto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating example prompt");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    // PUT: api/exampleprompts/{id}
    [HttpPut("{id}")]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> UpdateExamplePrompt(int id, [FromBody] UpdateExamplePromptRequestDto request)
    {
        try
        {
            var examplePrompt = await _context.ExamplePrompts.FindAsync(id);
            if (examplePrompt == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            if (request.Title != null)
            {
                examplePrompt.Title = request.Title;
            }

            if (request.Prompt != null)
            {
                examplePrompt.Prompt = request.Prompt;
            }

            if (request.Description != null)
            {
                examplePrompt.Description = request.Description;
            }

            if (request.ServiceCode != null)
            {
                examplePrompt.ServiceCode = request.ServiceCode;
            }

            if (request.Model != null)
            {
                examplePrompt.Model = request.Model;
            }

            if (request.Category != null)
            {
                examplePrompt.Category = request.Category;
            }

            if (request.IconClass != null)
            {
                examplePrompt.IconClass = request.IconClass;
            }

            if (request.SortOrder.HasValue)
            {
                examplePrompt.SortOrder = request.SortOrder.Value;
            }

            if (request.IsActive.HasValue)
            {
                examplePrompt.IsActive = request.IsActive.Value;
            }

            examplePrompt.UpdatedAt = DateTime.UtcNow;

            await _context.SaveChangesAsync();

            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating example prompt {Id}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    // DELETE: api/exampleprompts/{id}
    [HttpDelete("{id}")]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> DeleteExamplePrompt(int id)
    {
        try
        {
            var examplePrompt = await _context.ExamplePrompts.FindAsync(id);
            if (examplePrompt == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            _context.ExamplePrompts.Remove(examplePrompt);
            await _context.SaveChangesAsync();

            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting example prompt {Id}", id);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }
}
