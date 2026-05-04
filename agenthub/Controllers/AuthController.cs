using Microsoft.AspNetCore.Mvc;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;
using Microsoft.AspNetCore.Authorization;
using System.Security.Claims;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    private readonly IAuthService _authService;
    private readonly ILogger<AuthController> _logger;

    public AuthController(IAuthService authService, ILogger<AuthController> logger)
    {
        _authService = authService;
        _logger = logger;
    }

    [HttpPost("login")]
    [AllowAnonymous]
    public async Task<ActionResult<LoginResponseDto>> Login([FromBody] LoginRequestDto request)
    {
        try
        {
            _logger.LogInformation($"Login attempt for email: {request.Email}");
            
            request.IpAddress = HttpContext.Connection.RemoteIpAddress?.ToString();
            request.UserAgent = Request.Headers["User-Agent"].ToString();

            var response = await _authService.LoginAsync(request);
            if (response == null)
            {
                _logger.LogWarning($"Login failed for email: {request.Email} - Invalid credentials or inactive user");
                return Unauthorized(ErrorResponseDto.Unauthorized("Invalid email or password"));
            }

            _logger.LogInformation($"Login successful for email: {request.Email}, UserId: {response.User.UserId}");
            return Ok(response);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, $"Error during login for email: {request.Email}");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred during login"));
        }
    }

    [HttpPost("register")]
    [AllowAnonymous]
    public async Task<ActionResult> Register([FromBody] RegisterRequestDto request)
    {
        try
        {
            var result = await _authService.RegisterAsync(request);
            if (!result)
            {
                return BadRequest(ErrorResponseDto.BadRequest("Email already exists or registration failed"));
            }

            return Ok(new { message = "Registration successful. Please wait for admin approval." });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during registration");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred during registration"));
        }
    }

    [HttpPost("logout")]
    [Authorize]
    public async Task<ActionResult> Logout([FromBody] RefreshTokenRequestDto request)
    {
        try
        {
            await _authService.LogoutAsync(request.RefreshToken);
            return Ok(new { message = "Logout successful" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during logout");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred during logout"));
        }
    }

    [HttpPost("refresh")]
    [AllowAnonymous]
    public async Task<ActionResult<RefreshTokenResponseDto>> RefreshToken([FromBody] RefreshTokenRequestDto request)
    {
        try
        {
            var response = await _authService.RefreshTokenAsync(request.RefreshToken);
            if (response == null)
            {
                return Unauthorized(ErrorResponseDto.Unauthorized("Invalid refresh token"));
            }

            return Ok(response);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during token refresh");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred during token refresh"));
        }
    }

    [HttpPost("forgot-password")]
    [AllowAnonymous]
    public async Task<ActionResult> ForgotPassword([FromBody] ForgotPasswordRequestDto request)
    {
        try
        {
            var baseUrl = $"{Request.Scheme}://{Request.Host}";
            await _authService.ForgotPasswordAsync(request, baseUrl);
            // 항상 200 반환 (이메일 열거 방지)
            return Ok(new { message = "비밀번호 재설정 이메일을 발송했습니다." });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during forgot password for email: {Email}", request.Email);
            return StatusCode(500, ErrorResponseDto.InternalError("오류가 발생했습니다."));
        }
    }

    [HttpPost("reset-password")]
    [AllowAnonymous]
    public async Task<ActionResult> ResetPassword([FromBody] ResetPasswordRequestDto request)
    {
        try
        {
            var result = await _authService.ResetPasswordAsync(request);
            if (!result)
                return BadRequest(ErrorResponseDto.BadRequest("유효하지 않거나 만료된 토큰입니다."));

            return Ok(new { message = "비밀번호가 성공적으로 변경되었습니다." });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during reset password");
            return StatusCode(500, ErrorResponseDto.InternalError("오류가 발생했습니다."));
        }
    }

    [HttpGet("me")]
    [Authorize]
    public async Task<ActionResult<UserDto>> GetCurrentUser()
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized();
            }

            // This will be implemented in UserService
            return Ok(new { message = "Get current user - to be implemented in UserService" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting current user");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }
}
