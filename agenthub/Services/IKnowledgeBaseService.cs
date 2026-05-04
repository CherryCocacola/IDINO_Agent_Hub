using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IKnowledgeBaseService
{
    Task<List<KnowledgeBaseDocumentListDto>> GetDocumentsAsync(int userId, string? search = null, bool? isIndexed = null);
    Task<KnowledgeBaseDocumentDto?> GetDocumentByIdAsync(int documentId, int userId);
    Task<KnowledgeBaseDocumentDto> CreateDocumentAsync(CreateKnowledgeBaseDocumentRequestDto request, int userId);
    Task<KnowledgeBaseDocumentDto?> UpdateDocumentAsync(int documentId, UpdateKnowledgeBaseDocumentRequestDto request, int userId);
    Task<bool> DeleteDocumentAsync(int documentId, int userId);
    Task<bool> IndexDocumentAsync(int documentId, int userId);
    Task<bool> ReindexDocumentAsync(int documentId, int userId);
}
