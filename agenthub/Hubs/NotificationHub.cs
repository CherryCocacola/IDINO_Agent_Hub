using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.SignalR;

namespace AIAgentManagement.Hubs;

/// <summary>
/// 사용자별 알림을 실시간으로 전송하는 SignalR Hub.
/// 인증된 사용자만 접속 가능하며, 그룹 가입은 서버 측에서 토큰 클레임으로 결정한다.
/// </summary>
[Authorize]
public class NotificationHub : Hub
{
    private readonly ILogger<NotificationHub> _logger;

    public NotificationHub(ILogger<NotificationHub> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// 인증된 사용자의 알림 그룹("user_{userId}")에 가입한다.
    /// 클라이언트가 userId를 전달할 수 없으며, 항상 토큰 클레임에서 추출한다.
    /// 사용자 식별이 불가능하면 그룹 가입 없이 조용히 종료한다.
    /// </summary>
    public async Task JoinUserNotifications()
    {
        var userId = ResolveUserId();
        if (userId is null)
        {
            _logger.LogWarning("알림 그룹 가입 실패: 사용자 식별자를 확인할 수 없습니다. ConnectionId={ConnectionId}", Context.ConnectionId);
            return;
        }

        await Groups.AddToGroupAsync(Context.ConnectionId, $"user_{userId}");
        _logger.LogInformation("사용자 {UserId}가 알림 그룹에 가입했습니다.", userId);
    }

    /// <summary>
    /// 인증된 사용자의 알림 그룹에서 탈퇴한다.
    /// 클라이언트는 userId를 전달하지 않으며, 토큰 클레임으로 결정한다.
    /// </summary>
    public async Task LeaveUserNotifications()
    {
        var userId = ResolveUserId();
        if (userId is null)
        {
            return;
        }

        await Groups.RemoveFromGroupAsync(Context.ConnectionId, $"user_{userId}");
        _logger.LogInformation("사용자 {UserId}가 알림 그룹에서 탈퇴했습니다.", userId);
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        _logger.LogInformation("알림 허브 연결 종료: ConnectionId={ConnectionId}", Context.ConnectionId);
        await base.OnDisconnectedAsync(exception);
    }

    /// <summary>
    /// 토큰에서 사용자 ID를 추출한다.
    /// SignalR의 <see cref="HubCallerContext.UserIdentifier"/>를 우선 사용하고,
    /// 없으면 NameIdentifier 클레임을 폴백으로 사용한다. 모두 실패하면 null.
    /// </summary>
    private int? ResolveUserId()
    {
        var raw = Context.UserIdentifier
                  ?? Context.User?.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        if (int.TryParse(raw, out var userId))
        {
            return userId;
        }
        return null;
    }
}
