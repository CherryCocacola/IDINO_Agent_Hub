// Phase 4.3 FK ON DELETE / 인덱스 정밀 검증
#r "nuget: Npgsql, 8.0.6"
using System;
using System.Threading.Tasks;
using Npgsql;

const string ConnStr =
    "Host=192.168.10.39;Port=5440;Database=AGENT_HUB;Username=AGENT_HUB;Password=idino!@#$;Search Path=AIAgentManagement,public";

await Run();

async Task Run()
{
    await using var cn = new NpgsqlConnection(ConnStr);
    await cn.OpenAsync();

    // FK 상세
    await using (var cmd = new NpgsqlCommand(@"
        SELECT tc.constraint_name, tc.table_name, rc.delete_rule, rc.update_rule
        FROM information_schema.table_constraints tc
        JOIN information_schema.referential_constraints rc ON rc.constraint_name=tc.constraint_name
        WHERE tc.table_schema='AIAgentManagement'
          AND tc.constraint_type='FOREIGN KEY'
          AND tc.table_name IN ('Tenants','Departments')
        ORDER BY tc.table_name, tc.constraint_name", cn))
    await using (var r = await cmd.ExecuteReaderAsync())
    {
        Console.WriteLine("[FK 상세]");
        while (await r.ReadAsync())
            Console.WriteLine($"  {r.GetString(1)}.{r.GetString(0)} → ON DELETE {r.GetString(2)}, ON UPDATE {r.GetString(3)}");
    }

    // 인덱스 상세
    await using (var cmd = new NpgsqlCommand(@"
        SELECT indexname, indexdef FROM pg_indexes
        WHERE schemaname='AIAgentManagement'
          AND tablename IN ('Tenants','Departments')
        ORDER BY tablename, indexname", cn))
    await using (var r = await cmd.ExecuteReaderAsync())
    {
        Console.WriteLine("[인덱스 상세]");
        while (await r.ReadAsync())
            Console.WriteLine($"  {r.GetString(0)} :: {r.GetString(1)}");
    }

    // UNIQUE 위반 시뮬레이션 (rollback)
    Console.WriteLine("[UNIQUE 위반 시험 — 'idino-default' 중복 INSERT]");
    try
    {
        await using var cmd = new NpgsqlCommand(@"
            INSERT INTO ""AIAgentManagement"".""Tenants""
                (""TenantCode"",""TenantName"",""IsActive"",""CreatedAt"")
            VALUES ('idino-default','중복 테스트', true, NOW() AT TIME ZONE 'UTC')", cn);
        await cmd.ExecuteNonQueryAsync();
        Console.WriteLine("  ❌ 중복 INSERT 성공해서는 안 됨!");
    }
    catch (PostgresException ex)
    {
        Console.WriteLine($"  ✓ 중복 INSERT 차단됨: {ex.SqlState} ({ex.MessageText.Substring(0, Math.Min(80, ex.MessageText.Length))}...)");
    }
}
