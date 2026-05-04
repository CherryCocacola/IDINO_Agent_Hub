using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IPresentationService
{
    Task<PresentationDto> GeneratePresentationAsync(PresentationGenerationRequestDto request, CancellationToken cancellationToken = default);
    Task<PresentationDto> GetPresentationAsync(int presentationId, int userId);
    Task<PresentationDto> UpdatePresentationAsync(int presentationId, int userId, PresentationDto presentation);
    Task<PresentationDto> AddSlideAsync(int presentationId, int userId, SlideDto slide);
    Task<PresentationDto> UpdateSlideAsync(int presentationId, int userId, string slideId, SlideDto slide);
    Task<PresentationDto> DeleteSlideAsync(int presentationId, int userId, string slideId);
    Task<PresentationDto> ReorderSlidesAsync(int presentationId, int userId, List<string> slideIds);
    Task<Stream> ExportToPptxAsync(int presentationId, int userId, string? themeIdOverride = null);
    Task<Stream> ExportToPdfAsync(int presentationId, int userId, string? themeIdOverride = null);
    Task<Stream> ExportToPptxFromDtoAsync(PresentationDto presentation);
    Task<Stream> ExportToPdfFromDtoAsync(PresentationDto presentation);
    Task<PresentationDto> UpdateThemeAsync(int presentationId, int userId, string themeId);
}
