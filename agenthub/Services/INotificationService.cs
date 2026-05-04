using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface INotificationService
{
    Task SendNotificationAsync(int userId, string title, string message, string? type = null);
    Task<List<NotificationDto>> GetNotificationsAsync(int userId, bool? isRead = null);
    Task MarkAsReadAsync(int notificationId, int userId);
    Task MarkAllAsReadAsync(int userId);
}
