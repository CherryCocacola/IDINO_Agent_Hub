using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class FaqsController : ControllerBase
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<FaqsController> _logger;

    public FaqsController(AIAgentManagementDbContext context, ILogger<FaqsController> logger)
    {
        _context = context;
        _logger = logger;
    }

    // GET: api/faqs (비로그인 접근 허용 — Help 페이지 공개 조회)
    [HttpGet]
    [AllowAnonymous]
    public async Task<ActionResult<List<FaqDto>>> GetFaqs([FromQuery] string? category, [FromQuery] bool? isActive)
    {
        try
        {
            var query = _context.Faqs.AsQueryable();

            if (category != null)
            {
                query = query.Where(f => f.Category == category);
            }

            if (isActive.HasValue)
            {
                query = query.Where(f => f.IsActive == isActive.Value);
            }

            var faqs = await query
                .OrderBy(f => f.SortOrder)
                .ThenBy(f => f.FaqId)
                .Select(f => new FaqDto
                {
                    FaqId = f.FaqId,
                    Question = f.Question,
                    Answer = f.Answer,
                    Category = f.Category,
                    SortOrder = f.SortOrder,
                    IsActive = f.IsActive,
                    CreatedAt = f.CreatedAt,
                    UpdatedAt = f.UpdatedAt
                })
                .ToListAsync();

            return Ok(faqs);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting FAQs");
            return StatusCode(500, ErrorResponseDto.InternalError());
        }
    }

    // GET: api/faqs/{id} (비로그인 접근 허용)
    [HttpGet("{id}")]
    [AllowAnonymous]
    public async Task<ActionResult<FaqDto>> GetFaq(int id)
    {
        try
        {
            var faq = await _context.Faqs.FindAsync(id);
            if (faq == null)
            {
                return NotFound();
            }

            var faqDto = new FaqDto
            {
                FaqId = faq.FaqId,
                Question = faq.Question,
                Answer = faq.Answer,
                Category = faq.Category,
                SortOrder = faq.SortOrder,
                IsActive = faq.IsActive,
                CreatedAt = faq.CreatedAt,
                UpdatedAt = faq.UpdatedAt
            };

            return Ok(faqDto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting FAQ {Id}", id);
            return StatusCode(500, ErrorResponseDto.InternalError());
        }
    }

    // POST: api/faqs
    [HttpPost]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<FaqDto>> CreateFaq([FromBody] CreateFaqRequestDto request)
    {
        try
        {
            var faq = new Models.Faq
            {
                Question = request.Question,
                Answer = request.Answer,
                Category = request.Category,
                SortOrder = request.SortOrder,
                IsActive = request.IsActive,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            };

            _context.Faqs.Add(faq);
            await _context.SaveChangesAsync();

            var faqDto = new FaqDto
            {
                FaqId = faq.FaqId,
                Question = faq.Question,
                Answer = faq.Answer,
                Category = faq.Category,
                SortOrder = faq.SortOrder,
                IsActive = faq.IsActive,
                CreatedAt = faq.CreatedAt,
                UpdatedAt = faq.UpdatedAt
            };

            return CreatedAtAction(nameof(GetFaq), new { id = faq.FaqId }, faqDto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating FAQ");
            return StatusCode(500, ErrorResponseDto.InternalError());
        }
    }

    // PUT: api/faqs/{id}
    [HttpPut("{id}")]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> UpdateFaq(int id, [FromBody] UpdateFaqRequestDto request)
    {
        try
        {
            var faq = await _context.Faqs.FindAsync(id);
            if (faq == null)
            {
                return NotFound();
            }

            if (request.Question != null)
            {
                faq.Question = request.Question;
            }

            if (request.Answer != null)
            {
                faq.Answer = request.Answer;
            }

            if (request.Category != null)
            {
                faq.Category = request.Category;
            }

            if (request.SortOrder.HasValue)
            {
                faq.SortOrder = request.SortOrder.Value;
            }

            if (request.IsActive.HasValue)
            {
                faq.IsActive = request.IsActive.Value;
            }

            faq.UpdatedAt = DateTime.UtcNow;

            await _context.SaveChangesAsync();

            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating FAQ {Id}", id);
            return StatusCode(500, ErrorResponseDto.InternalError());
        }
    }

    // DELETE: api/faqs/{id}
    [HttpDelete("{id}")]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> DeleteFaq(int id)
    {
        try
        {
            var faq = await _context.Faqs.FindAsync(id);
            if (faq == null)
            {
                return NotFound();
            }

            _context.Faqs.Remove(faq);
            await _context.SaveChangesAsync();

            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting FAQ {Id}", id);
            return StatusCode(500, ErrorResponseDto.InternalError());
        }
    }
}
