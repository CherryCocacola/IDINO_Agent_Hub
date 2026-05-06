using System.Text;
using System.Text.Json;
using AIAgentManagement.Data;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

// ── Phase 6.4 (ADR-2): 자체 문서 인덱싱 구현체는 deprecate ────────────
// 청크 분할(SplitIntoChunks) + 임베딩(IEmbeddingService) + DocumentChunks INSERT 흐름
// 전체가 DocUtil 워커로 이전. 본 클래스는 Phase 5+ 호환을 위해 유지 — 본문 변경 없음.
// Phase 8+ 에서 KnowledgeBaseDocument/DocumentChunk DB drop 과 함께 제거.
// ----------------------------------------------------------------------
[Obsolete("ADR-2: AgentHub 자체 문서 인덱싱 구현체는 deprecate. 신규 코드는 IDocUtilClient.UploadDocumentAsync 사용. Phase 8+ 에서 제거 예정.", error: false)]
public class DocumentIndexingService : IDocumentIndexingService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly IEmbeddingService _embeddingService;
    private readonly ILogger<DocumentIndexingService> _logger;
    private readonly IConfiguration _configuration;
    private readonly int _chunkSize;
    private readonly int _chunkOverlap;

    public DocumentIndexingService(
        AIAgentManagementDbContext context,
        IEmbeddingService embeddingService,
        ILogger<DocumentIndexingService> logger,
        IConfiguration configuration)
    {
        _context = context;
        _embeddingService = embeddingService;
        _logger = logger;
        _configuration = configuration;
        _chunkSize = _configuration.GetValue<int>("RagSettings:ChunkSize", 1000);
        _chunkOverlap = _configuration.GetValue<int>("RagSettings:ChunkOverlap", 200);
    }

    public async Task IndexDocumentAsync(int documentId, CancellationToken cancellationToken = default)
    {
        var document = await _context.KnowledgeBaseDocuments
            .FirstOrDefaultAsync(d => d.DocumentId == documentId, cancellationToken);

        if (document == null)
        {
            throw new InvalidOperationException($"Document {documentId} not found");
        }

        // 이미 인덱싱된 경우 스킵 (재인덱싱을 원하면 ReindexDocumentAsync 사용)
        if (document.IsIndexed)
        {
            _logger.LogInformation("Document {DocumentId} is already indexed", documentId);
            return;
        }

        try
        {
            // 기존 청크 삭제 (재인덱싱 시)
            await DeleteDocumentChunksAsync(documentId, cancellationToken);

            // 텍스트를 청크로 분할
            var chunks = SplitIntoChunks(document.Content, _chunkSize, _chunkOverlap);

            if (!chunks.Any())
            {
                _logger.LogWarning("No chunks generated for document {DocumentId}", documentId);
                return;
            }

            // 각 청크에 대한 임베딩 생성 (배치 처리)
            _logger.LogInformation("Generating embeddings for {ChunkCount} chunks of document {DocumentId}", chunks.Count, documentId);
            var embeddings = await _embeddingService.GetEmbeddingsAsync(chunks, cancellationToken);

            if (embeddings.Count != chunks.Count)
            {
                throw new InvalidOperationException($"Embedding count ({embeddings.Count}) does not match chunk count ({chunks.Count})");
            }

            // DocumentChunks 테이블에 저장
            var documentChunks = new List<DocumentChunk>();
            for (int i = 0; i < chunks.Count; i++)
            {
                var chunk = new DocumentChunk
                {
                    DocumentId = documentId,
                    ChunkIndex = i,
                    Content = chunks[i],
                    Embedding = _embeddingService.SerializeEmbedding(embeddings[i]),
                    Metadata = JsonSerializer.Serialize(new
                    {
                        chunkSize = chunks[i].Length,
                        chunkIndex = i,
                        totalChunks = chunks.Count
                    }),
                    CreatedAt = DateTime.UtcNow
                };
                documentChunks.Add(chunk);
            }

            _context.DocumentChunks.AddRange(documentChunks);

            // 문서 인덱싱 상태 업데이트
            document.IsIndexed = true;
            document.IndexedAt = DateTime.UtcNow;
            document.UpdatedAt = DateTime.UtcNow;

            await _context.SaveChangesAsync(cancellationToken);

            _logger.LogInformation("Successfully indexed document {DocumentId} with {ChunkCount} chunks", documentId, chunks.Count);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error indexing document {DocumentId}", documentId);
            throw;
        }
    }

    public async Task ReindexDocumentAsync(int documentId, CancellationToken cancellationToken = default)
    {
        var document = await _context.KnowledgeBaseDocuments
            .FirstOrDefaultAsync(d => d.DocumentId == documentId, cancellationToken);

        if (document == null)
        {
            throw new InvalidOperationException($"Document {documentId} not found");
        }

        // 인덱싱 상태 초기화
        document.IsIndexed = false;
        document.IndexedAt = null;

        // 재인덱싱
        await IndexDocumentAsync(documentId, cancellationToken);
    }

    public async Task DeleteDocumentChunksAsync(int documentId, CancellationToken cancellationToken = default)
    {
        var chunks = await _context.DocumentChunks
            .Where(c => c.DocumentId == documentId)
            .ToListAsync(cancellationToken);

        if (chunks.Any())
        {
            _context.DocumentChunks.RemoveRange(chunks);
            await _context.SaveChangesAsync(cancellationToken);
            _logger.LogInformation("Deleted {ChunkCount} chunks for document {DocumentId}", chunks.Count, documentId);
        }
    }

    public List<string> SplitIntoChunks(string text, int chunkSize = 1000, int chunkOverlap = 200)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            return new List<string>();
        }

        var chunks = new List<string>();

        // 문장 단위로 분할 (마침표, 느낌표, 물음표 기준)
        var sentences = System.Text.RegularExpressions.Regex.Split(text, @"(?<=[.!?])\s+")
            .Where(s => !string.IsNullOrWhiteSpace(s))
            .ToList();

        if (!sentences.Any())
        {
            // 문장 분할이 안 되는 경우 공백 기준으로 분할
            sentences = text.Split(new[] { ' ', '\n', '\r', '\t' }, StringSplitOptions.RemoveEmptyEntries).ToList();
        }

        var currentChunk = new StringBuilder();
        var currentLength = 0;
        var lastChunkEnd = 0;

        for (int i = 0; i < sentences.Count; i++)
        {
            var sentence = sentences[i];
            var sentenceLength = sentence.Length + 1; // 공백 포함

            if (currentLength + sentenceLength > chunkSize && currentChunk.Length > 0)
            {
                // 현재 청크 저장
                chunks.Add(currentChunk.ToString().Trim());

                // 오버랩 처리: 이전 청크의 마지막 부분을 포함
                if (chunkOverlap > 0 && lastChunkEnd < sentences.Count)
                {
                    var overlapStart = Math.Max(0, lastChunkEnd - (chunkOverlap / 20)); // 대략적인 문장 수
                    var overlapSentences = sentences.Skip(overlapStart).Take(lastChunkEnd - overlapStart);
                    currentChunk = new StringBuilder(string.Join(" ", overlapSentences));
                    currentLength = currentChunk.Length;
                }
                else
                {
                    currentChunk = new StringBuilder();
                    currentLength = 0;
                }

                lastChunkEnd = i;
            }

            if (currentChunk.Length > 0)
            {
                currentChunk.Append(" ");
            }
            currentChunk.Append(sentence);
            currentLength += sentenceLength;
        }

        // 마지막 청크 추가
        if (currentChunk.Length > 0)
        {
            chunks.Add(currentChunk.ToString().Trim());
        }

        // 빈 청크 제거
        return chunks.Where(c => !string.IsNullOrWhiteSpace(c)).ToList();
    }
}
