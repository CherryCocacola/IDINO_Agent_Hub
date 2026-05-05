// 본 파일은 SQL Server 시점에 작성된 일회성 dev 도구 (사용처 0건, Phase 3.4 grep 결과 자기 정의 외 참조 없음).
// PostgreSQL 전환(Phase 3.1) 이후 본 코드는 더 이상 동작하지 않는다 (SqlConnection / @@VERSION / DB_NAME() 등 PG 비호환).
// Phase 5+ 별도 트랙에서 완전 제거 또는 PG 호환(Npgsql) 으로 재작성한다.
// 본 단계(Phase 3.4)는 `Microsoft.Data.SqlClient` 직접 의존을 제거하기 위해 코드 본문을 비활성화한다.
//
// 현재 DB 연결 점검은 다음을 사용한다:
//   1. Program.cs 의 부팅 시점 `context.Database.CanConnectAsync()` 로그
//   2. Hangfire Dashboard `/hangfire` (PG 연결 실패 시 시작 안 됨)
//   3. 외부 도구 (psql / DBeaver / pgAdmin)
//
// 별도 의존성을 묶지 않기 위해 클래스 자체는 보존하되, 호출 시 NotSupportedException 을 발생시킨다.

using System;

namespace AIAgentManagement;

[Obsolete("Phase 3.1 PostgreSQL 전환 후 deprecated. Phase 5+ 에서 제거 또는 Npgsql 호환으로 재작성 예정.")]
public class TestDbConnection
{
    public static void TestConnection(string connectionString)
    {
        throw new NotSupportedException(
            "TestDbConnection 은 PostgreSQL 전환 후 사용 불가합니다. " +
            "Program.cs 의 CanConnectAsync 로그 또는 외부 도구(psql/pgAdmin)를 사용하세요.");
    }
}
