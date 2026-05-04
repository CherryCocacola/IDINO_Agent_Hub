using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IBannedWordService
{
    Task<BannedWordCheckResult> CheckBannedWordsAsync(string message, int? agentId);
    Task<(List<BannedWordDto> Items, int TotalCount)> GetBannedWordsAsync(int? agentId, int page = 1, int pageSize = 20);
    Task<BannedWordDto> CreateBannedWordAsync(CreateBannedWordRequestDto request, int userId);
    Task<BannedWordDto?> UpdateBannedWordAsync(int id, UpdateBannedWordRequestDto request, int userId);
    Task<bool> DeleteBannedWordAsync(int id, int userId);
}
