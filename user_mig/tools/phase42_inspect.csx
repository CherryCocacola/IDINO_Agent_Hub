// =============================================================================
// Phase 4.2 사전 점검 스크립트 — career idino_career schema 현재 상태 확인
// =============================================================================
// 목적: Phase 3.6 에서 idino_career 빈 schema 가 이미 생성되었는지 확인.
// DDL 적용 전 read-only 점검 (확장/스키마/테이블 수).
// =============================================================================

#r "nuget: Npgsql, 8.0.6"
using Npgsql;
using System;
using System.Threading.Tasks;

async Task RunAsync()
{
    var cs = "Host=192.168.10.39;Port=5440;Database=AGENT_HUB;Username=AGENT_HUB;Password=idino!@#$;Timeout=60";

    using var conn = new NpgsqlConnection(cs);
    await conn.OpenAsync();
    Console.WriteLine($"[OK] connected to AGENT_HUB DB ({conn.ServerVersion})");

    // 1. 스키마 목록
    Console.WriteLine("\n=== Schemas ===");
    using (var cmd = new NpgsqlCommand(
        @"SELECT schema_name FROM information_schema.schemata
          WHERE schema_name NOT LIKE 'pg_%' AND schema_name <> 'information_schema'
          ORDER BY schema_name", conn))
    using (var r = await cmd.ExecuteReaderAsync())
        while (await r.ReadAsync()) Console.WriteLine($"  {r.GetString(0)}");

    // 2. 확장 (uuid-ossp / pgcrypto / vector)
    Console.WriteLine("\n=== Extensions ===");
    using (var cmd = new NpgsqlCommand(
        "SELECT extname, extversion FROM pg_extension ORDER BY extname", conn))
    using (var r = await cmd.ExecuteReaderAsync())
        while (await r.ReadAsync()) Console.WriteLine($"  {r.GetString(0)} v{r.GetString(1)}");

    // 3. idino_career schema 의 현재 테이블 수
    Console.WriteLine("\n=== idino_career schema tables ===");
    using (var cmd = new NpgsqlCommand(
        @"SELECT COUNT(*) FROM information_schema.tables
          WHERE table_schema = 'idino_career' AND table_type = 'BASE TABLE'", conn))
    {
        var n = await cmd.ExecuteScalarAsync();
        Console.WriteLine($"  TOTAL: {n}");
    }
    using (var cmd = new NpgsqlCommand(
        @"SELECT table_name FROM information_schema.tables
          WHERE table_schema = 'idino_career' AND table_type = 'BASE TABLE'
          ORDER BY table_name", conn))
    using (var r = await cmd.ExecuteReaderAsync())
        while (await r.ReadAsync()) Console.WriteLine($"    - {r.GetString(0)}");

    // 4. R3 스키마 격리 사전 검증 — 다른 schema 에 tb_* 누설 여부
    Console.WriteLine("\n=== Cross-schema tb_* leakage check (pre) ===");
    using (var cmd = new NpgsqlCommand(
        @"SELECT table_schema, COUNT(*) FROM information_schema.tables
          WHERE table_name LIKE 'tb_%' AND table_type = 'BASE TABLE'
          GROUP BY table_schema ORDER BY table_schema", conn))
    using (var r = await cmd.ExecuteReaderAsync())
        while (await r.ReadAsync())
            Console.WriteLine($"  {r.GetString(0)}: {r.GetInt64(1)} tb_*");

    await conn.CloseAsync();
    Console.WriteLine("\n[DONE]");
}

await RunAsync();
