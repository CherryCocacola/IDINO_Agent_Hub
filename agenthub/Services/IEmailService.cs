namespace AIAgentManagement.Services;

public interface IEmailService
{
    Task SendEmailAsync(string to, string subject, string body, bool isHtml = true);
    Task SendQuotaAlertEmailAsync(int userId, int serviceId, decimal currentUsage, decimal limit);
}
