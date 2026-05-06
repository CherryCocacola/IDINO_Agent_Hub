using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

// ── Phase 6.4 (ADR-2): 자체 KB CRUD 서비스는 deprecate ────────────────
// 신규 코드는 IDocUtilClient (Phase 6.1) 경유로 DocUtil 의 운영자 API
// (`/api/v1/documents`, `/api/v1/search`) 를 호출한다. 본 인터페이스는
// FilesController/KnowledgeBaseController 호환을 위해 Phase 5+ 까지 유지.
// 참고: .claude/rules/anti-patterns.md §7
// ----------------------------------------------------------------------
[Obsolete("ADR-2: AgentHub 자체 KB CRUD 는 deprecate. 신규 코드는 IDocUtilClient (Phase 6.1) 사용. Phase 8+ 에서 제거 예정.", error: false)]
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
