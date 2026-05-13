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
    private readonly IUserService _userService;
    private readonly ILogger<AuthController> _logger;

    public AuthController(IAuthService authService, IUserService userService, ILogger<AuthController> logger)
    {
        _authService = authService;
        _userService = userService;
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
                return Unauthorized(ErrorResponseDto.Unauthorized("이메일 또는 비밀번호가 올바르지 않습니다."));
            }

            _logger.LogInformation($"Login successful for email: {request.Email}, UserId: {response.User.UserId}");
            return Ok(response);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, $"Error during login for email: {request.Email}");
            return StatusCode(500, ErrorResponseDto.InternalError("로그인 처리 중 오류가 발생했습니다."));
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
                return BadRequest(ErrorResponseDto.BadRequest("이미 등록된 이메일이거나 회원가입에 실패했습니다."));
            }

            return Ok(new { message = "회원가입이 완료되었습니다. 관리자 승인을 기다려 주세요." });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during registration");
            return StatusCode(500, ErrorResponseDto.InternalError("회원가입 처리 중 오류가 발생했습니다."));
        }
    }

    [HttpPost("logout")]
    [Authorize]
    public async Task<ActionResult> Logout([FromBody] RefreshTokenRequestDto request)
    {
        try
        {
            await _authService.LogoutAsync(request.RefreshToken);
            return Ok(new { message = "로그아웃되었습니다." });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during logout");
            return StatusCode(500, ErrorResponseDto.InternalError("로그아웃 처리 중 오류가 발생했습니다."));
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
                return Unauthorized(ErrorResponseDto.Unauthorized("세션이 만료되었습니다. 다시 로그인해 주세요."));
            }

            return Ok(response);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during token refresh");
            return StatusCode(500, ErrorResponseDto.InternalError("토큰 갱신 처리 중 오류가 발생했습니다."));
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

    /// <summary>
    /// 현재 로그인 사용자 정보 조회.
    ///
    /// 트랙 #88 H7 (2026-05-13): UserService 위임으로 정식 구현.
    /// 이전 stub("...UserService 에서 구현 예정입니다.") 응답을 UserDto 정상 응답으로 교체.
    /// 대체 endpoint 인 GET /api/users/me 와 동일한 결과를 반환하므로 양쪽 모두 사용 가능.
    /// </summary>
    [HttpGet("me")]
    [Authorize]
    public async Task<ActionResult<UserDto>> GetCurrentUser()
    {
        try
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized(ErrorResponseDto.Unauthorized());
            }

            var user = await _userService.GetCurrentUserAsync(userId);
            if (user == null)
            {
                return NotFound(ErrorResponseDto.NotFound());
            }

            return Ok(user);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting current user");
            return StatusCode(500, ErrorResponseDto.InternalError("처리 중 오류가 발생했습니다."));
        }
    }
}
