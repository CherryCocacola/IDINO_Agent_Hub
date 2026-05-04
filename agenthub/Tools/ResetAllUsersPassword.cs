// 모든 사용자 비밀번호를 재설정하는 스크립트
// 이 파일을 Program.cs에 임시로 추가하거나, 별도의 콘솔 앱으로 실행하세요.

using AIAgentManagement.Data;
using AIAgentManagement.Models;
using BCrypt.Net;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace AIAgentManagement.Tools
{
    public static class ResetAllUsersPassword
    {
        public static async Task ResetPasswordsAsync(IServiceProvider serviceProvider, string newPassword = "Admin123!")
        {
            // IServiceProvider가 이미 scope인 경우를 대비해 scope를 생성하거나 직접 사용
            var context = serviceProvider.GetRequiredService<AIAgentManagementDbContext>();
            var loggerFactory = serviceProvider.GetRequiredService<ILoggerFactory>();
            var logger = loggerFactory.CreateLogger("ResetAllUsersPassword");

            try
            {
                logger.LogInformation("=== 모든 사용자 비밀번호 재설정 시작 ===");
                
                // 모든 활성 사용자 조회
                var users = await context.Users
                    .Where(u => !u.IsDeleted)
                    .ToListAsync();

                if (users.Count == 0)
                {
                    logger.LogWarning("재설정할 사용자가 없습니다.");
                    return;
                }

                logger.LogInformation($"총 {users.Count}명의 사용자 비밀번호를 재설정합니다.");

                // 비밀번호 해시 생성
                string passwordHash = BCrypt.Net.BCrypt.HashPassword(newPassword);
                logger.LogInformation($"새 비밀번호 해시 생성 완료: {passwordHash.Substring(0, 20)}...");

                // 각 사용자의 비밀번호 업데이트
                int updatedCount = 0;
                foreach (var user in users)
                {
                    user.PasswordHash = passwordHash;
                    user.UpdatedAt = DateTime.UtcNow;
                    updatedCount++;
                    
                    logger.LogInformation($"사용자 [{user.Email}] 비밀번호 업데이트 완료");
                }

                await context.SaveChangesAsync();

                logger.LogInformation($"=== 비밀번호 재설정 완료: {updatedCount}명 ===");
                
                // 검증 테스트
                bool isValid = BCrypt.Net.BCrypt.Verify(newPassword, passwordHash);
                logger.LogInformation($"해시 검증 테스트: {(isValid ? "성공" : "실패")}");
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "비밀번호 재설정 중 오류 발생");
                throw;
            }
        }

        // 특정 사용자만 비밀번호 재설정
        public static async Task ResetUserPasswordAsync(
            IServiceProvider serviceProvider, 
            string email, 
            string newPassword = "Admin123!")
        {
            var context = serviceProvider.GetRequiredService<AIAgentManagementDbContext>();
            var loggerFactory = serviceProvider.GetRequiredService<ILoggerFactory>();
            var logger = loggerFactory.CreateLogger("ResetAllUsersPassword");

            try
            {
                logger.LogInformation($"=== 사용자 [{email}] 비밀번호 재설정 시작 ===");

                var user = await context.Users
                    .FirstOrDefaultAsync(u => u.Email == email && !u.IsDeleted);

                if (user == null)
                {
                    logger.LogWarning($"사용자 [{email}]를 찾을 수 없습니다.");
                    return;
                }

                string passwordHash = BCrypt.Net.BCrypt.HashPassword(newPassword);
                user.PasswordHash = passwordHash;
                user.UpdatedAt = DateTime.UtcNow;

                await context.SaveChangesAsync();

                logger.LogInformation($"=== 사용자 [{email}] 비밀번호 재설정 완료 ===");
                
                // 검증 테스트
                bool isValid = BCrypt.Net.BCrypt.Verify(newPassword, passwordHash);
                logger.LogInformation($"해시 검증 테스트: {(isValid ? "성공" : "실패")}");
            }
            catch (Exception ex)
            {
                logger.LogError(ex, $"사용자 [{email}] 비밀번호 재설정 중 오류 발생");
                throw;
            }
        }
    }
}
