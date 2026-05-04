namespace AIAgentManagement.Services;

public interface IFileService
{
    Task<string> SaveFileAsync(Stream fileStream, string fileName, string? folder = null);
    Task<bool> DeleteFileAsync(string filePath);
    Task<Stream?> GetFileAsync(string filePath);
    Task<FileInfoDto> UploadAndParseFileAsync(IFormFile file, string? folder = null);
    Task<string> SaveImageAsync(Stream imageStream, string fileName, string? folder = null);
    Task<string> SaveAudioAsync(Stream audioStream, string fileName, string? folder = null);
    string GetContentType(string filePath);
    string GetOriginalFileName(string filePath);
}

public class FileInfoDto
{
    public string FilePath { get; set; } = string.Empty;
    public string FileName { get; set; } = string.Empty;
    public string FileType { get; set; } = string.Empty;
    public long FileSize { get; set; }
    public string? ParsedContent { get; set; }
    public List<string>? Images { get; set; }
    public Dictionary<string, object>? Metadata { get; set; }
    public bool IsParsed { get; set; }
}
