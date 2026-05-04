using Microsoft.Data.SqlClient;
using System;

namespace AIAgentManagement;

public class TestDbConnection
{
    public static void TestConnection(string connectionString)
    {
        try
        {
            Console.WriteLine("=== 데이터베이스 연결 테스트 시작 ===");
            Console.WriteLine($"연결 문자열: {connectionString.Replace("Password=rnehrwhgdk20@^", "Password=***")}");
            Console.WriteLine();

            using (var connection = new SqlConnection(connectionString))
            {
                Console.WriteLine("1. SqlConnection 객체 생성 성공");
                
                connection.Open();
                Console.WriteLine("2. 데이터베이스 연결 성공!");
                
                using (var command = new SqlCommand("SELECT @@VERSION AS Version, DB_NAME() AS CurrentDB, USER_NAME() AS CurrentUser", connection))
                {
                    using (var reader = command.ExecuteReader())
                    {
                        if (reader.Read())
                        {
                            Console.WriteLine($"3. SQL Server 버전: {reader["Version"]}");
                            Console.WriteLine($"4. 현재 데이터베이스: {reader["CurrentDB"]}");
                            Console.WriteLine($"5. 현재 사용자: {reader["CurrentUser"]}");
                        }
                    }
                }
                
                using (var command = new SqlCommand("SELECT COUNT(*) AS TableCount FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'", connection))
                {
                    var tableCount = command.ExecuteScalar();
                    Console.WriteLine($"6. 테이블 개수: {tableCount}");
                }
                
                Console.WriteLine();
                Console.WriteLine("=== 모든 테스트 통과 ===");
            }
        }
        catch (SqlException ex)
        {
            Console.WriteLine();
            Console.WriteLine("=== SQL 오류 발생 ===");
            Console.WriteLine($"오류 번호: {ex.Number}");
            Console.WriteLine($"오류 메시지: {ex.Message}");
            Console.WriteLine($"서버: {ex.Server}");
            Console.WriteLine($"상태: {ex.State}");
            Console.WriteLine($"심각도: {ex.Class}");
            Console.WriteLine($"프로시저: {ex.Procedure}");
            Console.WriteLine($"줄 번호: {ex.LineNumber}");
            throw;
        }
        catch (Exception ex)
        {
            Console.WriteLine();
            Console.WriteLine("=== 일반 오류 발생 ===");
            Console.WriteLine($"오류 타입: {ex.GetType().Name}");
            Console.WriteLine($"오류 메시지: {ex.Message}");
            Console.WriteLine($"스택 트레이스:");
            Console.WriteLine(ex.StackTrace);
            throw;
        }
    }
}
