namespace AIAgentManagement.Services;

// ── Phase 6.4 (ADR-2): 자체 문서 인덱싱은 deprecate ───────────────────
// 청크 분할 + 임베딩 + DB 저장은 DocUtil 워커(`docutil/backend/app/workers/embedding_generator.py`)
// 가 권위 시스템. AgentHub 는 IDocUtilClient.UploadDocumentAsync 로 위임만 한다.
// Phase 8+ 에서 KnowledgeBaseDocument/DocumentChunk DB drop 과 함께 제거.
// ----------------------------------------------------------------------
[Obsolete("ADR-2: AgentHub 자체 문서 인덱싱은 deprecate. 신규 코드는 IDocUtilClient.UploadDocumentAsync 사용. Phase 8+ 에서 제거 예정.", error: false)]
public interface IDocumentIndexingService
{
    /// <summary>
    /// 문서를 인덱싱 (청크 분할 및 임베딩 생성)
    /// </summary>
    Task IndexDocumentAsync(int documentId, CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서 재인덱싱 (기존 청크 삭제 후 재생성)
    /// </summary>
    Task ReindexDocumentAsync(int documentId, CancellationToken cancellationToken = default);

    /// <summary>
    /// 문서의 청크를 모두 삭제
    /// </summary>
    Task DeleteDocumentChunksAsync(int documentId, CancellationToken cancellationToken = default);

    /// <summary>
    /// 텍스트를 청크로 분할
    /// </summary>
    List<string> SplitIntoChunks(string text, int chunkSize = 1000, int chunkOverlap = 200);
}
