using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;
using BCrypt.Net;
using Microsoft.EntityFrameworkCore;
using System.Security.Cryptography;

namespace AIAgentManagement.Services;

public class AuthService : IAuthService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly IJwtService _jwtService;
    private readonly ILogger<AuthService> _logger;

    private readonly IEmailService _emailService;

    public AuthService(AIAgentManagementDbContext context, IJwtService jwtService, ILogger<AuthService> logger, IEmailService emailService)
    {
        _context = context;
        _jwtService = jwtService;
        _logger = logger;
        _emailService = emailService;
    }

    public async Task<LoginResponseDto?> LoginAsync(LoginRequestDto request)
    {
        _logger.LogInformation($"[AuthService] Login attempt for email: {request.Email}");
        
        var user = await _context.Users
            .Include(u => u.UserRoles)
                .ThenInclude(ur => ur.Role)
            .FirstOrDefaultAsync(u => u.Email == request.Email && !u.IsDeleted);

        if (user == null)
        {
            _logger.LogWarning($"[AuthService] User not found for email: {request.Email}");
            return null;
        }

        _logger.LogInformation($"[AuthService] User found: {user.Email}, Status: {user.Status}, IsDeleted: {user.IsDeleted}");

        // 비밀번호 검증
        try
        {
            var isPasswordValid = BCrypt.Net.BCrypt.Verify(request.Password, user.PasswordHash);
            if (!isPasswordValid)
            {
                _logger.LogWarning($"[AuthService] Invalid password for email: {request.Email}");
                return null;
            }
            _logger.LogInformation($"[AuthService] Password verified successfully for email: {request.Email}");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, $"[AuthService] Error verifying password for email: {request.Email}");
            return null;
        }

        if (!user.Status.Equals("Active", StringComparison.OrdinalIgnoreCase))
        {
            _logger.LogWarning($"[AuthService] User status is not Active for email: {request.Email}, Status: {user.Status}");
            return null;
        }

        // Update last login
        user.LastLoginAt = DateTime.UtcNow;
        await _context.SaveChangesAsync();

        // Create session
        var sessionToken = _jwtService.GenerateRefreshToken();
        var session = new UserSession
        {
            UserId = user.UserId,
            SessionToken = sessionToken,
            DeviceInfo = request.DeviceInfo,
            IpAddress = request.IpAddress,
            UserAgent = request.UserAgent,
            LoginAt = DateTime.UtcNow,
            LastActivityAt = DateTime.UtcNow,
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };
        _context.UserSessions.Add(session);
        await _context.SaveChangesAsync();

        // Get roles
        var roles = user.UserRoles.Select(ur => ur.Role.RoleName).ToList();

        // Generate JWT token
        var jwtToken = _jwtService.GenerateToken(user.UserId, user.Email, roles);

        return new LoginResponseDto
        {
            Token = jwtToken,
            RefreshToken = sessionToken,
            User = new UserDto
            {
                UserId = user.UserId,
                Email = user.Email,
                FullName = user.FullName,
                Roles = roles
            }
        };
    }

    public async Task<bool> RegisterAsync(RegisterRequestDto request)
    {
        if (await _context.Users.AnyAsync(u => u.Email == request.Email))
        {
            return false;
        }

        var user = new User
        {
            Email = request.Email,
            PasswordHash = BCrypt.Net.BCrypt.HashPassword(request.Password),
            FullName = request.FullName,
            PhoneNumber = request.PhoneNumber,
            Department = request.Department,
            Status = "Pending",
            IsEmailVerified = false,
            IsDeleted = false,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };

        _context.Users.Add(user);
        await _context.SaveChangesAsync();

        // Assign default User role
        var userRole = await _context.Roles.FirstOrDefaultAsync(r => r.RoleName == "User");
        if (userRole != null)
        {
            _context.UserRoles.Add(new UserRole
            {
                UserId = user.UserId,
                RoleId = userRole.RoleId,
                AssignedAt = DateTime.UtcNow
            });
            await _context.SaveChangesAsync();
        }

        return true;
    }

    public async Task<bool> LogoutAsync(string token)
    {
        var session = await _context.UserSessions
            .FirstOrDefaultAsync(s => s.SessionToken == token && s.IsActive);

        if (session != null)
        {
            session.IsActive = false;
            session.LogoutAt = DateTime.UtcNow;
            await _context.SaveChangesAsync();
            return true;
        }

        return false;
    }

    public async Task<RefreshTokenResponseDto?> RefreshTokenAsync(string refreshToken)
    {
        var session = await _context.UserSessions
            .Include(s => s.User)
                .ThenInclude(u => u.UserRoles)
                    .ThenInclude(ur => ur.Role)
            .FirstOrDefaultAsync(s => s.SessionToken == refreshToken && s.IsActive);

        if (session == null || !session.User.Status.Equals("Active", StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }

        // Update last activity
        session.LastActivityAt = DateTime.UtcNow;
        await _context.SaveChangesAsync();

        var roles = session.User.UserRoles.Select(ur => ur.Role.RoleName).ToList();
        var newToken = _jwtService.GenerateToken(session.User.UserId, session.User.Email, roles);

        return new RefreshTokenResponseDto
        {
            Token = newToken
        };
    }

    public async Task<bool> ForgotPasswordAsync(ForgotPasswordRequestDto request, string baseUrl)
    {
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Email == request.Email && !u.IsDeleted && u.Status == "Active");

        // 보안상 사용자가 없어도 성공처럼 반환 (이메일 열거 방지)
        if (user == null)
            return true;

        // 토큰 생성 (URL-safe Base64)
        var tokenBytes = RandomNumberGenerator.GetBytes(32);
        var token = Convert.ToBase64String(tokenBytes)
            .Replace("+", "-").Replace("/", "_").Replace("=", "");

        user.PasswordResetToken = BCrypt.Net.BCrypt.HashPassword(token);
        user.PasswordResetTokenExpiry = DateTime.UtcNow.AddHours(2);
        user.UpdatedAt = DateTime.UtcNow;
        await _context.SaveChangesAsync();

        var resetLink = $"{baseUrl}/reset-password?email={Uri.EscapeDataString(user.Email)}&token={Uri.EscapeDataString(token)}";
        var body = $@"
<div style=""font-family:sans-serif;max-width:480px;margin:0 auto"">
  <h2 style=""color:#4f46e5"">비밀번호 재설정</h2>
  <p>안녕하세요, {user.FullName}님.</p>
  <p>아래 버튼을 클릭하여 비밀번호를 재설정하세요. 이 링크는 <strong>2시간</strong> 동안 유효합니다.</p>
  <a href=""{resetLink}"" style=""display:inline-block;padding:12px 28px;background:#4f46e5;color:#fff;border-radius:8px;text-decoration:none;font-weight:600"">
    비밀번호 재설정하기
  </a>
  <p style=""margin-top:20px;color:#6b7280;font-size:0.875rem"">
    이 이메일을 요청하지 않으셨다면 무시하셔도 됩니다.
  </p>
</div>";

        try
        {
            await _emailService.SendEmailAsync(user.Email, "[AIAgent] 비밀번호 재설정 안내", body);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to send password reset email to {Email}", user.Email);
        }

        return true;
    }

    public async Task<bool> ResetPasswordAsync(ResetPasswordRequestDto request)
    {
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Email == request.Email && !u.IsDeleted);

        if (user == null
            || string.IsNullOrEmpty(user.PasswordResetToken)
            || user.PasswordResetTokenExpiry == null
            || user.PasswordResetTokenExpiry < DateTime.UtcNow)
            return false;

        if (!BCrypt.Net.BCrypt.Verify(request.Token, user.PasswordResetToken))
            return false;

        user.PasswordHash = BCrypt.Net.BCrypt.HashPassword(request.NewPassword);
        user.PasswordResetToken = null;
        user.PasswordResetTokenExpiry = null;
        user.UpdatedAt = DateTime.UtcNow;
        await _context.SaveChangesAsync();

        return true;
    }
}
