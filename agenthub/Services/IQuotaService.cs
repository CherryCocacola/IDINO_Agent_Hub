using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IQuotaService
{
    Task<List<QuotaDto>> GetQuotasAsync(int? userId = null, int? serviceId = null);
    Task<QuotaDto?> GetQuotaAsync(int userId, int serviceId);
    Task<QuotaDto> SetQuotaAsync(int userId, int serviceId, SetQuotaRequestDto request);
    Task<QuotaCheckResult> CheckQuotaAsync(int userId, int serviceId);
    Task RecordUsageAsync(int userId, int serviceId, int tokens, decimal cost);
    Task<int> GetTodayUsageAsync(int userId, int serviceId);
}
