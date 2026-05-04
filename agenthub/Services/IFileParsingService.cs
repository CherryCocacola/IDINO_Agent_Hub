namespace AIAgentManagement.Services;

public interface IFileParsingService
{
    Task<FileParseResult> ParseFileAsync(Stream fileStream, string fileName, string mimeType);
    bool CanParse(string fileName, string mimeType);
}

public class FileParseResult
{
    public string Content { get; set; } = string.Empty;
    public List<string>? Images { get; set; } // Base64 encoded images from PDF, DOCX, etc.
    public Dictionary<string, object>? Metadata { get; set; } // File metadata
    public string FileType { get; set; } = string.Empty;
    public bool IsSuccess { get; set; }
    public string? ErrorMessage { get; set; }
}
