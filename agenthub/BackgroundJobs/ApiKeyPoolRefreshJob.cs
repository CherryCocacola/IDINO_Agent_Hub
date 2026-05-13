using Hangfire;
using AIAgentManagement.Services;

namespace AIAgentManagement.BackgroundJobs;

/// <summary>
/// 외부 LLM 키 풀 5분 주기 갱신 — 트랙 #91 (ApiKeyPoolService DB 통합).
///
/// Hangfire `*/5 * * * *` 스케줄로 등록되어 `IApiKeyPoolService.RefreshAsync()` 를 호출한다.
/// 운영자가 콘솔에서 키를 등록하면 `ApiKeyService` 가 즉시 `RefreshAsync()` 를 트리거하지만,
/// 다른 인스턴스 / 직접 SQL 변경 / 만료 시점 자동 처리 등을 위해 폴링 갱신을 함께 유지한다.
///
/// `DisableConcurrentExecution` — 동일 잡이 60초 안에 겹쳐 시작되지 않도록 잠금. 단일 인스턴스 가정이지만
/// 다중 큐 워커가 같은 잡을 중복 실행하는 사고를 방지한다.
/// </summary>
public class ApiKeyPoolRefreshJob
{
    private readonly IApiKeyPoolService _pool;
    private readonly ILogger<ApiKeyPoolRefreshJob> _logger;

    public ApiKeyPoolRefreshJob(IApiKeyPoolService pool, ILogger<ApiKeyPoolRefreshJob> logger)
    {
        _pool = pool;
        _logger = logger;
    }

    [DisableConcurrentExecution(timeoutInSeconds: 60)]
    public async Task RefreshAsync()
    {
        try
        {
            await _pool.RefreshAsync();
        }
        catch (Exception ex)
        {
            // 단일 실행 실패가 다음 주기를 막으면 안 됨 — Hangfire 의 자동 retry 도 옵트인하지 않는다.
            _logger.LogError(ex, "[ApiKeyPool] 5분 주기 갱신 실패");
        }
    }
}
