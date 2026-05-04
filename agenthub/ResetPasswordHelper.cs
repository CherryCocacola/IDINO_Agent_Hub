// 모든 사용자 비밀번호를 재설정하는 헬퍼 코드
// 이 코드를 실행하여 실제 해시 값을 생성한 후 SQL에 사용하세요.

using BCrypt.Net;
using System;

namespace AIAgentManagement.Tools
{
    public class ResetPasswordHelper
    {
        public static void GeneratePasswordHash()
        {
            // 새 비밀번호 설정
            string newPassword = "Admin123!";
            
            // BCrypt 해시 생성
            string hash = BCrypt.Net.BCrypt.HashPassword(newPassword);
            
            Console.WriteLine("=== 비밀번호 해시 생성 ===");
            Console.WriteLine($"비밀번호: {newPassword}");
            Console.WriteLine($"해시 값: {hash}");
            Console.WriteLine();
            Console.WriteLine("=== SQL UPDATE 문 ===");
            Console.WriteLine($"UPDATE Users");
            Console.WriteLine($"SET PasswordHash = '{hash}',");
            Console.WriteLine($"    UpdatedAt = GETUTCDATE()");
            Console.WriteLine($"WHERE IsDeleted = 0;");
            Console.WriteLine();
            Console.WriteLine("=== 특정 사용자만 업데이트 ===");
            Console.WriteLine($"UPDATE Users");
            Console.WriteLine($"SET PasswordHash = '{hash}',");
            Console.WriteLine($"    UpdatedAt = GETUTCDATE()");
            Console.WriteLine($"WHERE Email = 'admin@example.com'");
            Console.WriteLine($"  AND IsDeleted = 0;");
            
            // 해시 검증 테스트
            bool isValid = BCrypt.Net.BCrypt.Verify(newPassword, hash);
            Console.WriteLine();
            Console.WriteLine($"=== 해시 검증 테스트 ===");
            Console.WriteLine($"검증 결과: {(isValid ? "성공" : "실패")}");
        }
        
        // 여러 사용자의 비밀번호를 개별적으로 설정하는 경우
        public static void GenerateMultiplePasswordHashes()
        {
            string[] passwords = { "Admin123!", "User123!", "Test123!" };
            
            Console.WriteLine("=== 여러 비밀번호 해시 생성 ===");
            foreach (var password in passwords)
            {
                string hash = BCrypt.Net.BCrypt.HashPassword(password);
                Console.WriteLine($"비밀번호: {password}");
                Console.WriteLine($"해시: {hash}");
                Console.WriteLine();
            }
        }
    }
}

// 사용 방법:
// 1. Program.cs의 Main 메서드에서 또는 별도의 콘솔 앱에서 호출:
//    ResetPasswordHelper.GeneratePasswordHash();
// 2. 출력된 SQL 문을 복사하여 SQL Server에서 실행
