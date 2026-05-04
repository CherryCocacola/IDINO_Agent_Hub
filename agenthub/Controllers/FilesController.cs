using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using AIAgentManagement.Services;
using AIAgentManagement.DTOs;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class FilesController : ControllerBase
{
    private readonly IFileService _fileService;
    private readonly IKnowledgeBaseService _knowledgeBaseService;
    private readonly ILogger<FilesController> _logger;

    public FilesController(
        IFileService fileService,
        IKnowledgeBaseService knowledgeBaseService,
        ILogger<FilesController> logger)
    {
        _fileService = fileService;
        _knowledgeBaseService = knowledgeBaseService;
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

    [HttpPost("upload/knowledgebase")]
    [DisableRequestSizeLimit]
    public async Task<ActionResult> UploadFileToKnowledgeBase(
        IFormFile file,
        [FromQuery] string? title = null,
        [FromQuery] bool indexImmediately = true)
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            if (file == null || file.Length == 0)
            {
                return BadRequest(ErrorResponseDto.BadRequest("No file uploaded"));
            }

            // 파일 파싱
            var fileInfo = await _fileService.UploadAndParseFileAsync(file, "knowledgebase");
            
            if (!fileInfo.IsParsed || string.IsNullOrEmpty(fileInfo.ParsedContent))
            {
                return BadRequest(ErrorResponseDto.BadRequest("Failed to parse file or file content is empty"));
            }

            // KnowledgeBaseDocument 생성
            var createRequest = new CreateKnowledgeBaseDocumentRequestDto
            {
                Title = title ?? file.FileName,
                Content = fileInfo.ParsedContent,
                SourceType = "UploadedFile",
                SourceId = fileInfo.FilePath,
                IndexImmediately = indexImmediately
            };

            var document = await _knowledgeBaseService.CreateDocumentAsync(createRequest, userId);

            return Ok(new
            {
                documentId = document.DocumentId,
                title = document.Title,
                filePath = fileInfo.FilePath,
                fileName = file.FileName,
                isIndexed = document.IsIndexed,
                chunkCount = document.ChunkCount,
                message = indexImmediately && document.IsIndexed 
                    ? "File uploaded and indexed successfully" 
                    : "File uploaded successfully. Indexing may be in progress."
            });
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ErrorResponseDto.BadRequest(ex.Message));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error uploading file to knowledge base");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred while uploading file to knowledge base"));
        }
    }
}
