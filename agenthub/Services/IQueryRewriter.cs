namespace AIAgentManagement.Services;

/// <summary>
/// RAG 검색 직전에 사용자 query 를 다국어/동의어 정규화하는 단일 진입점.
/// <para>
/// 동작:
///   - 한국어 query → 자연스러운 영문 번역 1건 추가
///   - 영문 query → 자연스러운 한국어 번역 1건 추가
///   - 핵심 엔터티(프로젝트명/지명/기술용어) 보존
/// </para>
/// <para>
/// 결과는 IMemoryCache 60분 TTL 캐시. 동일 query 재호출 시 LLM 미호출.
/// 호출 실패 시 원본 query 만 반환(graceful — RAG 검색 자체는 계속 동작).
/// </para>
/// </summary>
public interface IQueryRewriter
{
    /// <summary>
    /// 원본 query + 추가 정규화 query 목록을 반환. 첫 항목은 항상 원본.
    /// </summary>
    Task<IReadOnlyList<string>> RewriteAsync(string query, CancellationToken cancellationToken = default);
}
