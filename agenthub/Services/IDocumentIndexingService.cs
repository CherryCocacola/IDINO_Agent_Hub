namespace AIAgentManagement.Services;

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
