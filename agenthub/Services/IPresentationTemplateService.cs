using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IPresentationTemplateService
{
    Task<PresentationTemplateDto> UploadTemplateAsync(int userId, IFormFile templateFile, TemplateUploadRequestDto request, CancellationToken cancellationToken = default);
    Task<List<PresentationTemplateDto>> GetTemplatesAsync(int? userId = null, string? category = null, bool? isPublic = null);
    Task<PresentationTemplateDto> GetTemplateAsync(int templateId);
    /// <summary>Returns the template file stream and suggested file name, or null if not found.</summary>
    Task<(Stream Stream, string FileName)?> GetTemplateFileAsync(int templateId);
    Task<bool> DeleteTemplateAsync(int templateId, int userId);
    Task<PresentationDto> GenerateFromTemplateAsync(int templateId, PresentationGenerationRequestDto request, CancellationToken cancellationToken = default);
}
