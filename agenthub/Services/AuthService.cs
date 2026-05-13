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
    private readonly IConfiguration _configuration;

    public AuthService(
        AIAgentManagementDbContext context,
        IJwtService jwtService,
        ILogger<AuthService> logger,
        IEmailService emailService,
        IConfiguration configuration)
    {
        _context = context;
        _jwtService = jwtService;
        _logger = logger;
        _emailService = emailService;
        _configuration = configuration;
    }

    /// <summary>
    /// JWT (access token) 만료 분. JwtSettings:ExpirationInMinutes (default 60).
    /// </summary>
    private int AccessTokenExpirationMinutes
        => _configuration.GetValue<int>("JwtSettings:ExpirationInMinutes", 60);

    /// <summary>
    /// Refresh token (UserSession.ExpiresAt) 만료 일. JwtSettings:RefreshTokenExpirationInDays (default 7).
    /// </summary>
    private int RefreshTokenExpirationDays
        => _configuration.GetValue<int>("JwtSettings:RefreshTokenExpirationInDays", 7);

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

        // Create session — 트랙 #89 C2: ExpiresAt 설정으로 60분 무알림 강제 로그아웃 결함 해소
        var now = DateTime.UtcNow;
        var refreshTokenExpiresAt = now.AddDays(RefreshTokenExpirationDays);
        var sessionToken = _jwtService.GenerateRefreshToken();
        var session = new UserSession
        {
            UserId = user.UserId,
            SessionToken = sessionToken,
            DeviceInfo = request.DeviceInfo,
            IpAddress = request.IpAddress,
            UserAgent = request.UserAgent,
            LoginAt = now,
            LastActivityAt = now,
            ExpiresAt = refreshTokenExpiresAt,
            IsActive = true,
            CreatedAt = now
        };
        _context.UserSessions.Add(session);
        await _context.SaveChangesAsync();

        // Get roles
        var roles = user.UserRoles.Select(ur => ur.Role.RoleName).ToList();

        // Generate JWT token
        var jwtToken = _jwtService.GenerateToken(user.UserId, user.Email, roles);
        var accessTokenExpiresAt = now.AddMinutes(AccessTokenExpirationMinutes);

        return new LoginResponseDto
        {
            Token = jwtToken,
            RefreshToken = sessionToken,
            TokenExpiresAt = new DateTimeOffset(accessTokenExpiresAt, TimeSpan.Zero),
            RefreshTokenExpiresAt = new DateTimeOffset(refreshTokenExpiresAt, TimeSpan.Zero),
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
        // 트랙 #89 C2 — Refresh token 만료 검사 + 회전(rotation):
        // 1) 만료된 세션은 자동 비활성화하고 null 반환 → 클라이언트는 재로그인 유도
        // 2) 유효한 세션이면 새 SessionToken 발급 + 기존 세션 비활성화 + 새 UserSession row 생성
        // 3) 새 access/refresh token 의 만료 시각을 응답에 포함하여 클라이언트 사전 갱신 지원
        var session = await _context.UserSessions
            .Include(s => s.User)
                .ThenInclude(u => u.UserRoles)
                    .ThenInclude(ur => ur.Role)
            .FirstOrDefaultAsync(s => s.SessionToken == refreshToken && s.IsActive);

        if (session == null)
        {
            _logger.LogWarning("[AuthService] RefreshToken 실패 — 세션을 찾을 수 없거나 이미 비활성화됨");
            return null;
        }

        if (!session.User.Status.Equals("Active", StringComparison.OrdinalIgnoreCase) || session.User.IsDeleted)
        {
            _logger.LogWarning("[AuthService] RefreshToken 실패 — 사용자 비활성/삭제 상태 (UserId={UserId})", session.UserId);
            session.IsActive = false;
            session.LogoutAt = DateTime.UtcNow;
            await _context.SaveChangesAsync();
            return null;
        }

        var now = DateTime.UtcNow;
        if (session.ExpiresAt < now)
        {
            _logger.LogInformation(
                "[AuthService] RefreshToken 실패 — 세션 만료 (UserId={UserId}, ExpiresAt={ExpiresAt:o})",
                session.UserId, session.ExpiresAt);
            session.IsActive = false;
            session.LogoutAt = now;
            await _context.SaveChangesAsync();
            return null;
        }

        // 기존 세션 비활성화 (회전)
        session.IsActive = false;
        session.LogoutAt = now;
        session.LastActivityAt = now;

        // 새 세션 생성 — 동일 디바이스 정보 승계
        var newSessionToken = _jwtService.GenerateRefreshToken();
        var newRefreshExpiresAt = now.AddDays(RefreshTokenExpirationDays);
        var newSession = new UserSession
        {
            UserId = session.UserId,
            SessionToken = newSessionToken,
            DeviceInfo = session.DeviceInfo,
            IpAddress = session.IpAddress,
            UserAgent = session.UserAgent,
            LoginAt = session.LoginAt,        // 최초 로그인 시각 유지
            LastActivityAt = now,
            ExpiresAt = newRefreshExpiresAt,
            IsActive = true,
            CreatedAt = now
        };
        _context.UserSessions.Add(newSession);
        await _context.SaveChangesAsync();

        var roles = session.User.UserRoles.Select(ur => ur.Role.RoleName).ToList();
        var newAccessToken = _jwtService.GenerateToken(session.User.UserId, session.User.Email, roles);
        var newAccessExpiresAt = now.AddMinutes(AccessTokenExpirationMinutes);

        return new RefreshTokenResponseDto
        {
            Token = newAccessToken,
            RefreshToken = newSessionToken,
            TokenExpiresAt = new DateTimeOffset(newAccessExpiresAt, TimeSpan.Zero),
            RefreshTokenExpiresAt = new DateTimeOffset(newRefreshExpiresAt, TimeSpan.Zero)
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
