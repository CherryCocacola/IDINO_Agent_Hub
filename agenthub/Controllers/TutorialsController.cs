using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class TutorialsController : ControllerBase
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<TutorialsController> _logger;

    public TutorialsController(AIAgentManagementDbContext context, ILogger<TutorialsController> logger)
    {
        _context = context;
        _logger = logger;
    }

    // GET: api/tutorials (비로그인 접근 허용 — Help 페이지 공개 조회)
    [HttpGet]
    [AllowAnonymous]
    public async Task<ActionResult<List<TutorialDto>>> GetTutorials([FromQuery] string? category, [FromQuery] bool? isActive)
    {
        try
        {
            var query = _context.Tutorials.AsQueryable();

            if (category != null)
            {
                query = query.Where(t => t.Category == category);
            }

            if (isActive.HasValue)
            {
                query = query.Where(t => t.IsActive == isActive.Value);
            }

            var tutorials = await query
                .OrderBy(t => t.SortOrder)
                .ThenBy(t => t.TutorialId)
                .Select(t => new TutorialDto
                {
                    TutorialId = t.TutorialId,
                    Title = t.Title,
                    Description = t.Description,
                    VideoUrl = t.VideoUrl,
                    ThumbnailUrl = t.ThumbnailUrl,
                    Duration = t.Duration,
                    Category = t.Category,
                    SortOrder = t.SortOrder,
                    IsActive = t.IsActive,
                    ViewCount = t.ViewCount,
                    CreatedAt = t.CreatedAt,
                    UpdatedAt = t.UpdatedAt
                })
                .ToListAsync();

            return Ok(tutorials);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting tutorials");
            return StatusCode(500, ErrorResponseDto.InternalError());
        }
    }

    // GET: api/tutorials/{id} (비로그인 접근 허용)
    [HttpGet("{id}")]
    [AllowAnonymous]
    public async Task<ActionResult<TutorialDto>> GetTutorial(int id)
    {
        try
        {
            var tutorial = await _context.Tutorials.FindAsync(id);
            if (tutorial == null)
            {
                return NotFound();
            }

            // 조회수 증가
            tutorial.ViewCount++;
            await _context.SaveChangesAsync();

            var tutorialDto = new TutorialDto
            {
                TutorialId = tutorial.TutorialId,
                Title = tutorial.Title,
                Description = tutorial.Description,
                VideoUrl = tutorial.VideoUrl,
                ThumbnailUrl = tutorial.ThumbnailUrl,
                Duration = tutorial.Duration,
                Category = tutorial.Category,
                SortOrder = tutorial.SortOrder,
                IsActive = tutorial.IsActive,
                ViewCount = tutorial.ViewCount,
                CreatedAt = tutorial.CreatedAt,
                UpdatedAt = tutorial.UpdatedAt
            };

            return Ok(tutorialDto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting tutorial {Id}", id);
            return StatusCode(500, ErrorResponseDto.InternalError());
        }
    }

    // POST: api/tutorials
    [HttpPost]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<TutorialDto>> CreateTutorial([FromBody] CreateTutorialRequestDto request)
    {
        try
        {
            var tutorial = new Models.Tutorial
            {
                Title = request.Title,
                Description = request.Description,
                VideoUrl = request.VideoUrl,
                ThumbnailUrl = request.ThumbnailUrl,
                Duration = request.Duration,
                Category = request.Category,
                SortOrder = request.SortOrder,
                IsActive = request.IsActive,
                ViewCount = 0,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            };

            _context.Tutorials.Add(tutorial);
            await _context.SaveChangesAsync();

            var tutorialDto = new TutorialDto
            {
                TutorialId = tutorial.TutorialId,
                Title = tutorial.Title,
                Description = tutorial.Description,
                VideoUrl = tutorial.VideoUrl,
                ThumbnailUrl = tutorial.ThumbnailUrl,
                Duration = tutorial.Duration,
                Category = tutorial.Category,
                SortOrder = tutorial.SortOrder,
                IsActive = tutorial.IsActive,
                ViewCount = tutorial.ViewCount,
                CreatedAt = tutorial.CreatedAt,
                UpdatedAt = tutorial.UpdatedAt
            };

            return CreatedAtAction(nameof(GetTutorial), new { id = tutorial.TutorialId }, tutorialDto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating tutorial");
            return StatusCode(500, ErrorResponseDto.InternalError());
        }
    }

    // PUT: api/tutorials/{id}
    [HttpPut("{id}")]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> UpdateTutorial(int id, [FromBody] UpdateTutorialRequestDto request)
    {
        try
        {
            var tutorial = await _context.Tutorials.FindAsync(id);
            if (tutorial == null)
            {
                return NotFound();
            }

            if (request.Title != null)
            {
                tutorial.Title = request.Title;
            }

            if (request.Description != null)
            {
                tutorial.Description = request.Description;
            }

            if (request.VideoUrl != null)
            {
                tutorial.VideoUrl = request.VideoUrl;
            }

            if (request.ThumbnailUrl != null)
            {
                tutorial.ThumbnailUrl = request.ThumbnailUrl;
            }

            if (request.Duration != null)
            {
                tutorial.Duration = request.Duration;
            }

            if (request.Category != null)
            {
                tutorial.Category = request.Category;
            }

            if (request.SortOrder.HasValue)
            {
                tutorial.SortOrder = request.SortOrder.Value;
            }

            if (request.IsActive.HasValue)
            {
                tutorial.IsActive = request.IsActive.Value;
            }

            tutorial.UpdatedAt = DateTime.UtcNow;

            await _context.SaveChangesAsync();

            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating tutorial {Id}", id);
            return StatusCode(500, ErrorResponseDto.InternalError());
        }
    }

    // DELETE: api/tutorials/{id}
    [HttpDelete("{id}")]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> DeleteTutorial(int id)
    {
        try
        {
            var tutorial = await _context.Tutorials.FindAsync(id);
            if (tutorial == null)
            {
                return NotFound();
            }

            _context.Tutorials.Remove(tutorial);
            await _context.SaveChangesAsync();

            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting tutorial {Id}", id);
            return StatusCode(500, ErrorResponseDto.InternalError());
        }
    }
}
