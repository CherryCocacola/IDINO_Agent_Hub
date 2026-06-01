using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;

namespace AIAgentManagement.Controllers;

/// <summary>
/// 트랙 #147 M1 (2026-06-01) — 운영자 보고서 정식 endpoint.
/// </summary>
[ApiController]
[Route("api/[controller]")]
[Authorize]
public class ReportsController : ControllerBase
{
    private readonly IReportsService _reportsService;
    private readonly ILogger<ReportsController> _logger;

    public ReportsController(IReportsService reportsService, ILogger<ReportsController> logger)
    {
        _reportsService = reportsService;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<List<GeneratedReportDto>>> List(CancellationToken ct = default)
    {
        var (userId, isAdmin) = GetCaller();
        if (userId is null) return Unauthorized(ErrorResponseDto.Unauthorized());
        var list = await _reportsService.ListAsync(userId.Value, isAdmin, ct);
        return Ok(list);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<GeneratedReportDto>> Get(int id, CancellationToken ct = default)
    {
        var (userId, isAdmin) = GetCaller();
        if (userId is null) return Unauthorized(ErrorResponseDto.Unauthorized());
        var dto = await _reportsService.GetAsync(id, userId.Value, isAdmin, ct);
        if (dto is null) return NotFound(ErrorResponseDto.NotFound("보고서를 찾을 수 없습니다."));
        return Ok(dto);
    }

    [HttpPost]
    public async Task<ActionResult<GeneratedReportDto>> Create([FromBody] CreateReportRequestDto request, CancellationToken ct = default)
    {
        var (userId, _) = GetCaller();
        if (userId is null) return Unauthorized(ErrorResponseDto.Unauthorized());
        try
        {
            var dto = await _reportsService.CreateAsync(request, userId.Value, ct);
            return CreatedAtAction(nameof(Get), new { id = dto.ReportId }, dto);
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ErrorResponseDto.BadRequest(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "보고서 생성 실패");
            return StatusCode(500, new ErrorResponseDto(
                "보고서 생성에 실패했습니다.", "REPORT_CREATE_ERROR", new { error = ex.Message }));
        }
    }

    [HttpGet("{id}/download")]
    public async Task<IActionResult> Download(int id, CancellationToken ct = default)
    {
        var (userId, isAdmin) = GetCaller();
        if (userId is null) return Unauthorized(ErrorResponseDto.Unauthorized());
        var result = await _reportsService.DownloadAsync(id, userId.Value, isAdmin, ct);
        if (result is null) return NotFound(ErrorResponseDto.NotFound("보고서 파일을 찾을 수 없습니다."));
        var (bytes, fileName, contentType) = result.Value;
        Response.Headers["Content-Disposition"] =
            $"attachment; filename=\"report.xlsx\"; filename*=UTF-8''{Uri.EscapeDataString(fileName)}";
        return File(bytes, contentType);
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id, CancellationToken ct = default)
    {
        var (userId, isAdmin) = GetCaller();
        if (userId is null) return Unauthorized(ErrorResponseDto.Unauthorized());
        var ok = await _reportsService.DeleteAsync(id, userId.Value, isAdmin, ct);
        if (!ok) return NotFound(ErrorResponseDto.NotFound("보고서를 찾을 수 없습니다."));
        return NoContent();
    }

    private (int? UserId, bool IsAdmin) GetCaller()
    {
        var claim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        var ok = int.TryParse(claim, out var uid);
        return (ok ? uid : null, User.IsInRole("Admin"));
    }
}
