using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IAiProxyService
{
    Task<AiResponseDto> SendChatMessageAsync(int serviceId, string model, ChatMessageRequestDto request, CancellationToken cancellationToken = default);
    Task<Stream> SendChatMessageStreamAsync(int serviceId, string model, ChatMessageRequestDto request, CancellationToken cancellationToken = default);
    Task<decimal> CalculateCostAsync(int serviceId, string model, int promptTokens, int completionTokens);
    Task<List<string>> GetAvailableModelsAsync(int serviceId, CancellationToken cancellationToken = default);
    Task<bool> TestServiceConnectionAsync(int serviceId, CancellationToken cancellationToken = default);
    Task<ImageGenerationResponseDto> SendImageGenerationAsync(int serviceId, string model, ImageGenerationRequestDto request, CancellationToken cancellationToken = default);
    Task<decimal> CalculateImageGenerationCostAsync(int serviceId, string model, string size, string quality, int numberOfImages);

}
