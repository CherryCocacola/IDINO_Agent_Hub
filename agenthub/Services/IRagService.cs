using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IRagService
{
    /// <summary>
    /// 사용자 질문과 관련된 문서 청크 검색 (RAG)
    /// </summary>
    Task<List<RagSearchResultDto>> RetrieveAsync(string query, int topK = 5, int? userId = null, int? agentId = null, List<int>? documentIds = null, CancellationToken cancellationToken = default);
}
