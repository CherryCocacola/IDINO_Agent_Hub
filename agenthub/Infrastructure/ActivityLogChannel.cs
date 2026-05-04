using System.Threading.Channels;
using AIAgentManagement.Models;

namespace AIAgentManagement.Infrastructure;

/// <summary>
/// ActivityLog를 비동기로 처리하기 위한 Bounded Channel 래퍼.
/// Singleton으로 등록하여 미들웨어(Producer)와 BackgroundWorker(Consumer)가 공유합니다.
/// </summary>
public class ActivityLogChannel
{
    private readonly Channel<ActivityLog> _channel;

    public ActivityLogChannel()
    {
        // capacity 1000: 초당 1000건 이상 몰려도 DropOldest로 최신 로그 우선 보존
        var options = new BoundedChannelOptions(1000)
        {
            FullMode = BoundedChannelFullMode.DropOldest,
            SingleReader = true,
            SingleWriter = false
        };
        _channel = Channel.CreateBounded<ActivityLog>(options);
    }

    /// <summary>채널에 로그를 추가합니다. 실패 시 false 반환(채널 꽉 찬 경우 DropOldest 동작).</summary>
    public bool TryWrite(ActivityLog log) => _channel.Writer.TryWrite(log);

    public ChannelReader<ActivityLog> Reader => _channel.Reader;
}
