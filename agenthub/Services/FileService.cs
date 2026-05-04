using AIAgentManagement.Models;
using Microsoft.AspNetCore.Http;

namespace AIAgentManagement.Services;

public class FileService : IFileService
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<FileService> _logger;
    private readonly IFileParsingService _fileParsingService;
    private readonly string _uploadPath;
    private readonly string _imagePath;
    private readonly string _audioPath;

    public FileService(IConfiguration configuration, ILogger<FileService> logger, IFileParsingService fileParsingService)
    {
        _configuration = configuration;
        _logger = logger;
        _fileParsingService = fileParsingService;
        _uploadPath = _configuration["FileUploadSettings:UploadPath"] ?? "wwwroot/uploads";
        _imagePath = Path.Combine(_uploadPath, "images");
        _audioPath = Path.Combine(_uploadPath, "audio");
        
        if (!Directory.Exists(_uploadPath))
        {
            Directory.CreateDirectory(_uploadPath);
        }
        if (!Directory.Exists(_imagePath))
        {
            Directory.CreateDirectory(_imagePath);
        }
        if (!Directory.Exists(_audioPath))
        {
            Directory.CreateDirectory(_audioPath);
        }
    }

    public async Task<string> SaveFileAsync(Stream fileStream, string fileName, string? folder = null)
    {
        try
        {
            var allowedExtensions = _configuration.GetSection("FileUploadSettings:AllowedExtensions").Get<string[]>() 
                ?? new[] { ".jpg", ".jpeg", ".png", ".pdf", ".txt", ".doc", ".docx" };
            
            var extension = Path.GetExtension(fileName).ToLowerInvariant();
            if (!allowedExtensions.Contains(extension))
            {
                throw new InvalidOperationException($"File extension {extension} is not allowed");
            }

            var maxFileSize = _configuration.GetValue<long>("FileUploadSettings:MaxFileSize", 10485760);
            if (fileStream.Length > maxFileSize)
            {
                throw new InvalidOperationException($"File size exceeds maximum allowed size of {maxFileSize} bytes");
            }

            var folderPath = string.IsNullOrEmpty(folder) ? _uploadPath : Path.Combine(_uploadPath, folder);
            if (!Directory.Exists(folderPath))
            {
                Directory.CreateDirectory(folderPath);
            }

            var uniqueFileName = $"{Guid.NewGuid()}{extension}";
            var filePath = Path.Combine(folderPath, uniqueFileName);

            using (var file = new FileStream(filePath, FileMode.Create))
            {
                await fileStream.CopyToAsync(file);
            }

            // 원본 파일명 메타데이터 저장
            try
            {
                var metadataPath = filePath + ".metadata.json";
                var metadata = new
                {
                    originalFileName = fileName,
                    uploadedAt = DateTime.UtcNow
                };
                var metadataJson = System.Text.Json.JsonSerializer.Serialize(metadata);
                await System.IO.File.WriteAllTextAsync(metadataPath, metadataJson);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to save metadata for file {FileName}", fileName);
            }

            var relativePath = Path.GetRelativePath(_uploadPath, filePath).Replace('\\', '/');
            return $"/uploads/{relativePath}";
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error saving file {FileName}", fileName);
            throw;
        }
    }

    public async Task<bool> DeleteFileAsync(string filePath)
    {
        try
        {
            // Remove leading slash and ensure it's within uploads directory
            var cleanPath = filePath.TrimStart('/');
            if (!cleanPath.StartsWith("uploads/"))
            {
                return false;
            }

            var fullPath = Path.Combine(_uploadPath, cleanPath.Replace("uploads/", ""));
            
            if (File.Exists(fullPath))
            {
                File.Delete(fullPath);
                return true;
            }

            return false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting file {FilePath}", filePath);
            return false;
        }
    }

    public async Task<Stream?> GetFileAsync(string filePath)
    {
        try
        {
            var cleanPath = filePath.TrimStart('/');
            if (!cleanPath.StartsWith("uploads/"))
            {
                return null;
            }

            var fullPath = Path.Combine(_uploadPath, cleanPath.Replace("uploads/", ""));
            
            if (File.Exists(fullPath))
            {
                return File.OpenRead(fullPath);
            }

            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting file {FilePath}", filePath);
            return null;
        }
    }

    public async Task<FileInfoDto> UploadAndParseFileAsync(IFormFile file, string? folder = null)
    {
        if (file == null || file.Length == 0)
        {
            throw new InvalidOperationException("No file uploaded");
        }

        var filePath = await SaveFileAsync(file.OpenReadStream(), file.FileName, folder);
        
        var fileInfo = new FileInfoDto
        {
            FilePath = filePath,
            FileName = file.FileName,
            FileSize = file.Length,
            FileType = Path.GetExtension(file.FileName).ToLowerInvariant().TrimStart('.')
        };

        // 파일 파싱 시도
        if (_fileParsingService.CanParse(file.FileName, file.ContentType))
        {
            try
            {
                file.OpenReadStream().Position = 0;
                var parseResult = await _fileParsingService.ParseFileAsync(file.OpenReadStream(), file.FileName, file.ContentType);
                
                if (parseResult.IsSuccess)
                {
                    fileInfo.ParsedContent = parseResult.Content;
                    fileInfo.Images = parseResult.Images;
                    fileInfo.Metadata = parseResult.Metadata;
                    fileInfo.IsParsed = true;
                }
                else
                {
                    _logger.LogWarning("File parsing failed: {ErrorMessage}", parseResult.ErrorMessage);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error parsing file {FileName}", file.FileName);
            }
        }

        return fileInfo;
    }

    public async Task<string> SaveImageAsync(Stream imageStream, string fileName, string? folder = null)
    {
        var imageExtensions = new[] { ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp" };
        var extension = Path.GetExtension(fileName).ToLowerInvariant();
        
        if (!imageExtensions.Contains(extension))
        {
            throw new InvalidOperationException($"Invalid image file extension: {extension}");
        }

        var targetFolder = string.IsNullOrEmpty(folder) ? _imagePath : Path.Combine(_imagePath, folder);
        if (!Directory.Exists(targetFolder))
        {
            Directory.CreateDirectory(targetFolder);
        }

        return await SaveFileToFolderAsync(imageStream, fileName, targetFolder);
    }

    public async Task<string> SaveAudioAsync(Stream audioStream, string fileName, string? folder = null)
    {
        var audioExtensions = new[] { ".mp3", ".wav", ".m4a", ".ogg", ".mp4", ".mov", ".avi" };
        var extension = Path.GetExtension(fileName).ToLowerInvariant();
        
        if (!audioExtensions.Contains(extension))
        {
            throw new InvalidOperationException($"Invalid audio file extension: {extension}");
        }

        var targetFolder = string.IsNullOrEmpty(folder) ? _audioPath : Path.Combine(_audioPath, folder);
        if (!Directory.Exists(targetFolder))
        {
            Directory.CreateDirectory(targetFolder);
        }

        return await SaveFileToFolderAsync(audioStream, fileName, targetFolder);
    }

    private async Task<string> SaveFileToFolderAsync(Stream fileStream, string fileName, string targetFolder)
    {
        var extension = Path.GetExtension(fileName).ToLowerInvariant();
        var uniqueFileName = $"{Guid.NewGuid()}{extension}";
        var filePath = Path.Combine(targetFolder, uniqueFileName);

        using (var file = new FileStream(filePath, FileMode.Create))
        {
            await fileStream.CopyToAsync(file);
        }

        // 원본 파일명 메타데이터 저장 (이미지, 오디오 파일 포함)
        try
        {
            var metadataPath = filePath + ".metadata.json";
            var metadata = new
            {
                originalFileName = fileName,
                uploadedAt = DateTime.UtcNow
            };
            var metadataJson = System.Text.Json.JsonSerializer.Serialize(metadata);
            await System.IO.File.WriteAllTextAsync(metadataPath, metadataJson);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to save metadata for file {FileName}", fileName);
        }

        var relativePath = Path.GetRelativePath(_uploadPath, filePath).Replace('\\', '/');
        return $"/uploads/{relativePath}";
    }

    public string GetContentType(string filePath)
    {
        var extension = Path.GetExtension(filePath).ToLowerInvariant();
        return extension switch
        {
            ".pdf" => "application/pdf",
            ".txt" => "text/plain",
            ".doc" => "application/msword",
            ".docx" => "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls" => "application/vnd.ms-excel",
            ".xlsx" => "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".csv" => "text/csv",
            ".jpg" or ".jpeg" => "image/jpeg",
            ".png" => "image/png",
            ".gif" => "image/gif",
            ".bmp" => "image/bmp",
            ".webp" => "image/webp",
            ".mp3" => "audio/mpeg",
            ".wav" => "audio/wav",
            ".m4a" => "audio/mp4",
            ".ogg" => "audio/ogg",
            ".mp4" => "video/mp4",
            ".mov" => "video/quicktime",
            ".avi" => "video/x-msvideo",
            ".hwp" => "application/x-hwp",
            _ => "application/octet-stream"
        };
    }

    public string GetOriginalFileName(string filePath)
    {
        try
        {
            var cleanPath = filePath.TrimStart('/');
            if (!cleanPath.StartsWith("uploads/"))
            {
                return Path.GetFileName(filePath);
            }

            var fullPath = Path.Combine(_uploadPath, cleanPath.Replace("uploads/", ""));
            
            // 메타데이터 파일에서 원본 파일명 가져오기 (있는 경우)
            var metadataPath = fullPath + ".metadata.json";
            if (File.Exists(metadataPath))
            {
                try
                {
                    // 동기 메서드 사용 (메타데이터 파일은 작으므로 문제없음)
                    var metadataJson = File.ReadAllText(metadataPath);
                    var metadata = System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, object>>(metadataJson);
                    if (metadata != null && metadata.ContainsKey("originalFileName"))
                    {
                        return metadata["originalFileName"]?.ToString() ?? Path.GetFileName(filePath);
                    }
                }
                catch
                {
                    // 메타데이터 읽기 실패 시 무시
                }
            }

            return Path.GetFileName(filePath);
        }
        catch
        {
            return Path.GetFileName(filePath);
        }
    }
}
