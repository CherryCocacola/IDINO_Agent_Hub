using AIAgentManagement.Data;
using AIAgentManagement.Infrastructure;
using AIAgentManagement.Models;

namespace AIAgentManagement.BackgroundJobs;

/// <summary>
/// ActivityLogChannel에서 로그를 읽어 배치로 DB에 저장하는 BackgroundService.
/// 3초마다 또는 50건이 모이면 한 번에 INSERT하여 DB 부하를 최소화합니다.
/// </summary>
public class ActivityLogWorker : BackgroundService
{
    private readonly ActivityLogChannel _channel;
    private readonly IServiceScopeFactory _scopeFactory;
    private readonly ILogger<ActivityLogWorker> _logger;

    private const int BatchSize = 50;
    private static readonly TimeSpan FlushInterval = TimeSpan.FromSeconds(3);

    public ActivityLogWorker(
        ActivityLogChannel channel,
        IServiceScopeFactory scopeFactory,
        ILogger<ActivityLogWorker> logger)
    {
        _channel = channel;
        _scopeFactory = scopeFactory;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var batch = new List<ActivityLog>(BatchSize);

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                // FlushInterval(3초) 동안 또는 BatchSize만큼 수집
                using var cts = CancellationTokenSource.CreateLinkedTokenSource(stoppingToken);
                cts.CancelAfter(FlushInterval);

                try
                {
                    await foreach (var log in _channel.Reader.ReadAllAsync(cts.Token))
                    {
                        batch.Add(log);
                        if (batch.Count >= BatchSize) break;
                    }
                }
                catch (OperationCanceledException)
                {
                    // FlushInterval 타임아웃 or 앱 종료 — 수집된 것만 flush
                }

                if (batch.Count > 0)
                {
                    await FlushBatchAsync(batch, stoppingToken);
                    batch.Clear();
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "ActivityLogWorker: 배치 처리 중 오류 발생");
                await Task.Delay(TimeSpan.FromSeconds(5), stoppingToken);
            }
        }
    }

    private async Task FlushBatchAsync(List<ActivityLog> batch, CancellationToken ct)
    {
        // BackgroundService는 Singleton이므로 Scoped DbContext를 매번 새로 생성
        await using var scope = _scopeFactory.CreateAsyncScope();
        var db = scope.ServiceProvider.GetRequiredService<AIAgentManagementDbContext>();

        db.ActivityLogs.AddRange(batch);
        await db.SaveChangesAsync(ct);

        _logger.LogDebug("ActivityLogWorker: {Count}건 저장 완료", batch.Count);
    }
}
