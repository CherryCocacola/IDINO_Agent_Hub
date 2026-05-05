using System.Security.Claims;
using AIAgentManagement.Data;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Hubs;

/// <summary>
/// 대화별 실시간 메시지 푸시를 위한 SignalR Hub.
/// 인증된 사용자만 접속 가능하며, 대화 그룹 가입 시 소유권을 서버가 직접 검증한다.
/// </summary>
[Authorize]
public class ChatHub : Hub
{
    private readonly ILogger<ChatHub> _logger;
    private readonly AIAgentManagementDbContext _dbContext;

    public ChatHub(ILogger<ChatHub> logger, AIAgentManagementDbContext dbContext)
    {
        _logger = logger;
        _dbContext = dbContext;
    }

    /// <summary>
    /// 지정한 대화 그룹("conversation_{conversationId}")에 가입한다.
    /// 본인이 소유한 대화에만 가입할 수 있으며, 그렇지 않으면 <see cref="HubException"/>으로 거부한다.
    /// </summary>
    public async Task JoinConversation(int conversationId)
    {
        var userId = ResolveUserId();

        var isOwner = await _dbContext.ChatConversations
            .AsNoTracking()
            .AnyAsync(c => c.ConversationId == conversationId && c.UserId == userId);

        if (!isOwner)
        {
            _logger.LogWarning(
                "대화 가입 거부: 소유권 없음. UserId={UserId}, ConversationId={ConversationId}, ConnectionId={ConnectionId}",
                userId, conversationId, Context.ConnectionId);
            throw new HubException("권한 없음");
        }

        await Groups.AddToGroupAsync(Context.ConnectionId, $"conversation_{conversationId}");
        _logger.LogInformation(
            "사용자 {UserId}가 대화 {ConversationId} 그룹에 가입했습니다.",
            userId, conversationId);
    }

    /// <summary>
    /// 대화 그룹에서 탈퇴한다. 탈퇴는 본인 그룹에 한정되므로 별도 소유권 검증은 생략한다.
    /// (가입이 이미 서버측 소유권 검증을 통과했어야 함)
    /// </summary>
    public async Task LeaveConversation(int conversationId)
    {
        await Groups.RemoveFromGroupAsync(Context.ConnectionId, $"conversation_{conversationId}");
        _logger.LogInformation(
            "ConnectionId={ConnectionId}가 대화 {ConversationId} 그룹에서 탈퇴했습니다.",
            Context.ConnectionId, conversationId);
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        _logger.LogInformation("채팅 허브 연결 종료: ConnectionId={ConnectionId}", Context.ConnectionId);
        await base.OnDisconnectedAsync(exception);
    }

    /// <summary>
    /// 토큰에서 사용자 ID를 추출한다.
    /// <see cref="HubCallerContext.UserIdentifier"/>를 우선 사용하고, 없으면 NameIdentifier 클레임을 폴백으로 사용한다.
    /// 둘 다 없거나 정수 변환이 실패하면 <see cref="HubException"/>을 던진다.
    /// </summary>
    private int ResolveUserId()
    {
        var raw = Context.UserIdentifier
                  ?? Context.User?.FindFirst(ClaimTypes.NameIdentifier)?.Value;

        if (!int.TryParse(raw, out var userId))
        {
            throw new HubException("인증 정보가 없습니다");
        }

        return userId;
    }
}
