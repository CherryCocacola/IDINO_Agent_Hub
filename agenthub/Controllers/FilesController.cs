using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.Services;
using AIAgentManagement.DTOs;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class FilesController : ControllerBase
{
    private readonly IFileService _fileService;
    private readonly ILogger<FilesController> _logger;

    public FilesController(
        IFileService fileService,
        ILogger<FilesController> logger)
    {
        _fileService = fileService;
        _logger = logger;
    }

    [HttpPost("upload")]
    [DisableRequestSizeLimit]
    public async Task<ActionResult> UploadFile(IFormFile file, [FromQuery] string? folder, [FromQuery] bool parse = false)
    {
        try
        {
            if (file == null || file.Length == 0)
            {
                return BadRequest(ErrorResponseDto.BadRequest("No file uploaded"));
            }

            if (parse)
            {
                var fileInfo = await _fileService.UploadAndParseFileAsync(file, folder);
                return Ok(fileInfo);
            }
            else
            {
                using var stream = file.OpenReadStream();
                var filePath = await _fileService.SaveFileAsync(stream, file.FileName, folder);
                return Ok(new { path = filePath, fileName = file.FileName });
            }
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ErrorResponseDto.BadRequest(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error uploading file");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred while uploading file"));
        }
    }

    [HttpPost("upload/image")]
    [DisableRequestSizeLimit]
    public async Task<ActionResult> UploadImage(IFormFile file, [FromQuery] string? folder)
    {
        try
        {
            if (file == null || file.Length == 0)
            {
                return BadRequest(ErrorResponseDto.BadRequest("No image uploaded"));
            }

            using var stream = file.OpenReadStream();
            var imagePath = await _fileService.SaveImageAsync(stream, file.FileName, folder);

            return Ok(new { path = imagePath, fileName = file.FileName, type = "image" });
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ErrorResponseDto.BadRequest(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error uploading image");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred while uploading image"));
        }
    }

    [HttpPost("upload/audio")]
    [DisableRequestSizeLimit]
    public async Task<ActionResult> UploadAudio(IFormFile file, [FromQuery] string? folder)
    {
        try
        {
            if (file == null || file.Length == 0)
            {
                return BadRequest(ErrorResponseDto.BadRequest("No audio uploaded"));
            }

            using var stream = file.OpenReadStream();
            var audioPath = await _fileService.SaveAudioAsync(stream, file.FileName, folder);

            return Ok(new { path = audioPath, fileName = file.FileName, type = "audio" });
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ErrorResponseDto.BadRequest(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error uploading audio");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred while uploading audio"));
        }
    }

    [HttpGet("download/{*filePath}")]
    public async Task<ActionResult> DownloadFile(string filePath)
    {
        try
        {
            if (string.IsNullOrEmpty(filePath))
            {
                return BadRequest(ErrorResponseDto.BadRequest("File path is required"));
            }

            // URL 디코딩
            filePath = Uri.UnescapeDataString(filePath);
            
            var fileStream = await _fileService.GetFileAsync(filePath);
            if (fileStream == null)
            {
                _logger.LogWarning("File not found: {FilePath}", filePath);
                return NotFound(ErrorResponseDto.NotFound("File not found"));
            }

            // 원본 파일명 가져오기 (메타데이터에서)
            var originalFileName = _fileService.GetOriginalFileName(filePath);
            
            // Content-Type 설정
            var contentType = _fileService.GetContentType(filePath);
            
            // 파일 스트림을 메모리에 복사 (Response가 dispose되면 스트림도 닫히므로)
            using var memoryStream = new MemoryStream();
            await fileStream.CopyToAsync(memoryStream);
            memoryStream.Position = 0;
            
            fileStream.Dispose();

            // 파일 다운로드로 처리
            return File(memoryStream.ToArray(), contentType, originalFileName);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error downloading file {FilePath}", filePath);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred while downloading file"));
        }
    }

    [HttpDelete("{*filePath}")]
    public async Task<ActionResult> DeleteFile(string filePath)
    {
        try
        {
            var result = await _fileService.DeleteFileAsync(filePath);
            if (!result)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(new { message = "File deleted successfully" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting file {FilePath}", filePath);
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    // ── Phase 8 (ADR-2): 자체 KB 업로드 엔드포인트 제거 ──────────────────
    // /api/files/upload/knowledgebase 라우트는 자체 KB 테이블(KnowledgeBaseDocuments
    // / DocumentChunks) 에 직접 INSERT 하던 흐름이었다. ADR-2 의 단일 권위 정책에
    // 따라 자체 KB 코드/스키마가 모두 제거되었으므로 본 라우트는 410 Gone 으로
    // 응답한다. 운영자는 AgentHub Vue UI 의 `/admin/knowledge-base/upload` (Phase
    // 6.3) 또는 BFF 라우트 `/api/admin/knowledge-base/documents/upload` 를 사용해
    // DocUtil 로 위임 업로드한다.
    // ----------------------------------------------------------------------
    [HttpPost("upload/knowledgebase")]
    [DisableRequestSizeLimit]
    public ActionResult UploadFileToKnowledgeBase()
    {
        _logger.LogWarning(
            "Deprecated route /api/files/upload/knowledgebase 호출됨 — ADR-2 에 따라 410 Gone 으로 응답");
        return StatusCode(StatusCodes.Status410Gone, new ErrorResponseDto(
            "자체 지식베이스 업로드 엔드포인트는 제거되었습니다. AgentHub 운영자 콘솔(/admin/knowledge-base/upload) 을 사용해 DocUtil 로 업로드하세요.",
            "ENDPOINT_REMOVED",
            null));
    }
}
