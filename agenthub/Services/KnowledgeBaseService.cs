using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

// ── Phase 6.4 (ADR-2): 자체 KB CRUD 구현체는 deprecate ────────────────
// IDocUtilClient (Phase 6.1) 가 DocUtil 의 운영자 API 를 통해 동일 책임 대체.
// 본 클래스는 Phase 5+ 호환을 위해 유지. 본문 변경 없음 — 신규 사용만 차단.
// Phase 8+ 에서 KnowledgeBaseDocument/DocumentChunk DB drop 시 함께 제거.
// ----------------------------------------------------------------------
[Obsolete("ADR-2: AgentHub 자체 KB CRUD 구현체는 deprecate. 신규 코드는 IDocUtilClient (Phase 6.1) 사용. Phase 8+ 에서 제거 예정.", error: false)]
public class KnowledgeBaseService : IKnowledgeBaseService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly IDocumentIndexingService _documentIndexingService;
    private readonly ILogger<KnowledgeBaseService> _logger;

    public KnowledgeBaseService(
        AIAgentManagementDbContext context,
        IDocumentIndexingService documentIndexingService,
        ILogger<KnowledgeBaseService> logger)
    {
        _context = context;
        _documentIndexingService = documentIndexingService;
        _logger = logger;
    }

    public async Task<List<KnowledgeBaseDocumentListDto>> GetDocumentsAsync(int userId, string? search = null, bool? isIndexed = null)
    {
        var query = _context.KnowledgeBaseDocuments
            .AsNoTracking()
            .Include(d => d.User)
            .Include(d => d.Chunks)
            .Where(d => d.UserId == userId)
            .AsQueryable();

        if (!string.IsNullOrEmpty(search))
        {
            query = query.Where(d => 
                d.Title.Contains(search) || 
                d.Content.Contains(search));
        }

        if (isIndexed.HasValue)
        {
            query = query.Where(d => d.IsIndexed == isIndexed.Value);
        }

        var documents = await query
            .OrderByDescending(d => d.UpdatedAt)
            .Select(d => new KnowledgeBaseDocumentListDto
            {
                DocumentId = d.DocumentId,
                UserId = d.UserId,
                UserName = d.User != null ? d.User.FullName ?? "Unknown" : "Unknown",
                Title = d.Title,
                SourceType = d.SourceType,
                SourceId = d.SourceId,
                IsIndexed = d.IsIndexed,
                IndexedAt = d.IndexedAt,
                ChunkCount = d.Chunks.Count,
                CreatedAt = d.CreatedAt,
                UpdatedAt = d.UpdatedAt
            })
            .ToListAsync();

        return documents;
    }

    public async Task<KnowledgeBaseDocumentDto?> GetDocumentByIdAsync(int documentId, int userId)
    {
        var document = await _context.KnowledgeBaseDocuments
            .AsNoTracking()
            .Include(d => d.User)
            .Include(d => d.Chunks)
            .Where(d => d.DocumentId == documentId && d.UserId == userId)
            .Select(d => new KnowledgeBaseDocumentDto
            {
                DocumentId = d.DocumentId,
                UserId = d.UserId,
                UserName = d.User != null ? d.User.FullName ?? "Unknown" : "Unknown",
                Title = d.Title,
                Content = d.Content,
                SourceType = d.SourceType,
                SourceId = d.SourceId,
                IsIndexed = d.IsIndexed,
                IndexedAt = d.IndexedAt,
                ChunkCount = d.Chunks.Count,
                CreatedAt = d.CreatedAt,
                UpdatedAt = d.UpdatedAt
            })
            .FirstOrDefaultAsync();

        return document;
    }

    public async Task<KnowledgeBaseDocumentDto> CreateDocumentAsync(CreateKnowledgeBaseDocumentRequestDto request, int userId)
    {
        var document = new KnowledgeBaseDocument
        {
            UserId = userId,
            Title = request.Title,
            Content = request.Content,
            SourceType = request.SourceType,
            SourceId = request.SourceId,
            IsIndexed = false,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };

        _context.KnowledgeBaseDocuments.Add(document);
        await _context.SaveChangesAsync();

        // 즉시 인덱싱이 요청된 경우
        if (request.IndexImmediately)
        {
            try
            {
                await _documentIndexingService.IndexDocumentAsync(document.DocumentId);
                _logger.LogInformation("Document {DocumentId} indexed immediately after creation", document.DocumentId);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to index document {DocumentId} immediately after creation", document.DocumentId);
                // 인덱싱 실패해도 문서는 생성됨 (나중에 수동으로 인덱싱 가능)
            }
        }

        // DTO 반환을 위해 다시 조회
        var result = await GetDocumentByIdAsync(document.DocumentId, userId);
        if (result == null)
        {
            throw new InvalidOperationException("Failed to retrieve created document");
        }

        return result;
    }

    public async Task<KnowledgeBaseDocumentDto?> UpdateDocumentAsync(int documentId, UpdateKnowledgeBaseDocumentRequestDto request, int userId)
    {
        var document = await _context.KnowledgeBaseDocuments
            .FirstOrDefaultAsync(d => d.DocumentId == documentId && d.UserId == userId);

        if (document == null)
        {
            return null;
        }

        bool contentChanged = false;

        if (!string.IsNullOrEmpty(request.Title))
        {
            document.Title = request.Title;
        }

        if (!string.IsNullOrEmpty(request.Content))
        {
            document.Content = request.Content;
            contentChanged = true;
        }

        if (!string.IsNullOrEmpty(request.SourceType))
        {
            document.SourceType = request.SourceType;
        }

        if (request.SourceId != null)
        {
            document.SourceId = request.SourceId;
        }

        document.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync();

        // 내용이 변경되고 재인덱싱이 요청된 경우
        if (contentChanged && request.Reindex == true)
        {
            try
            {
                await _documentIndexingService.ReindexDocumentAsync(documentId);
                _logger.LogInformation("Document {DocumentId} reindexed after update", documentId);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to reindex document {DocumentId} after update", documentId);
                // 재인덱싱 실패해도 업데이트는 성공
            }
        }

        return await GetDocumentByIdAsync(documentId, userId);
    }

    public async Task<bool> DeleteDocumentAsync(int documentId, int userId)
    {
        var document = await _context.KnowledgeBaseDocuments
            .Include(d => d.Chunks)
            .FirstOrDefaultAsync(d => d.DocumentId == documentId && d.UserId == userId);

        if (document == null)
        {
            return false;
        }

        // 청크는 CASCADE DELETE로 자동 삭제됨
        _context.KnowledgeBaseDocuments.Remove(document);
        await _context.SaveChangesAsync();

        _logger.LogInformation("Document {DocumentId} deleted by user {UserId}", documentId, userId);
        return true;
    }

    public async Task<bool> IndexDocumentAsync(int documentId, int userId)
    {
        var document = await _context.KnowledgeBaseDocuments
            .FirstOrDefaultAsync(d => d.DocumentId == documentId && d.UserId == userId);

        if (document == null)
        {
            return false;
        }

        try
        {
            await _documentIndexingService.IndexDocumentAsync(documentId);
            _logger.LogInformation("Document {DocumentId} indexed by user {UserId}", documentId, userId);
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to index document {DocumentId}", documentId);
            return false;
        }
    }

    public async Task<bool> ReindexDocumentAsync(int documentId, int userId)
    {
        var document = await _context.KnowledgeBaseDocuments
            .FirstOrDefaultAsync(d => d.DocumentId == documentId && d.UserId == userId);

        if (document == null)
        {
            return false;
        }

        try
        {
            await _documentIndexingService.ReindexDocumentAsync(documentId);
            _logger.LogInformation("Document {DocumentId} reindexed by user {UserId}", documentId, userId);
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to reindex document {DocumentId}", documentId);
            return false;
        }
    }
}
