using System.Net;
using System.Net.Mail;
using AIAgentManagement.Data;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Services;

public class EmailService : IEmailService
{
    private readonly IConfiguration _configuration;
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<EmailService> _logger;

    public EmailService(
        IConfiguration configuration,
        AIAgentManagementDbContext context,
        ILogger<EmailService> logger)
    {
        _configuration = configuration;
        _context = context;
        _logger = logger;
    }

    public async Task SendEmailAsync(string to, string subject, string body, bool isHtml = true)
    {
        try
        {
            var emailSettings = _configuration.GetSection("EmailSettings");
            var smtpServer = emailSettings["SmtpServer"];
            var smtpPort = emailSettings.GetValue<int>("SmtpPort", 587);
            var smtpUsername = emailSettings["SmtpUsername"];
            var smtpPassword = emailSettings["SmtpPassword"];
            var fromEmail = emailSettings["FromEmail"] ?? "noreply@aiagent.com";
            var fromName = emailSettings["FromName"] ?? "AI Agent Management";

            if (string.IsNullOrEmpty(smtpServer) || string.IsNullOrEmpty(smtpUsername))
            {
                _logger.LogWarning("Email settings not configured, skipping email send");
                return;
            }

            using var message = new MailMessage();
            message.From = new MailAddress(fromEmail, fromName);
            message.To.Add(new MailAddress(to));
            message.Subject = subject;
            message.Body = body;
            message.IsBodyHtml = isHtml;

            using var client = new SmtpClient(smtpServer, smtpPort);
            client.EnableSsl = smtpPort == 465 || smtpPort == 587;
            client.UseDefaultCredentials = false;
            client.Credentials = new NetworkCredential(smtpUsername, smtpPassword);
            
            await client.SendMailAsync(message);

            _logger.LogInformation("Email sent successfully to {To}", to);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error sending email to {To}", to);
            throw;
        }
    }

    public async Task SendQuotaAlertEmailAsync(int userId, int serviceId, decimal currentUsage, decimal limit)
    {
        var user = await _context.Users.FindAsync(userId);
        var service = await _context.ApiServices.FindAsync(serviceId);

        if (user == null || service == null) return;

        var usagePercentage = (currentUsage / limit) * 100;
        var subject = $"Quota Alert: {service.ServiceName} usage at {usagePercentage:F1}%";
        var body = $@"
<h2>Quota Alert</h2>
<p>Hello {user.FullName},</p>
<p>You have reached {usagePercentage:F1}% of your quota limit for <strong>{service.ServiceName}</strong>.</p>
<p><strong>Current Usage:</strong> ${currentUsage:F2} / ${limit:F2}</p>
<p>Please monitor your usage to avoid service interruption.</p>
";

        await SendEmailAsync(user.Email, subject, body);
    }
}
