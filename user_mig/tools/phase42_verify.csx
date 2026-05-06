// =============================================================================
// Phase 4.2 검증 스크립트 — DDL 적용 후 idino_career schema 상태 + R3 격리 검증
// =============================================================================

#r "nuget: Npgsql, 8.0.6"
using Npgsql;
using System;
using System.Threading.Tasks;
using System.Collections.Generic;

async Task RunAsync()
{
    var cs = "Host=192.168.10.39;Port=5440;Database=AGENT_HUB;Username=AGENT_HUB;Password=idino!@#$;Timeout=60";

    using var conn = new NpgsqlConnection(cs);
    await conn.OpenAsync();

    // 1. idino_career schema 의 테이블 수
    Console.WriteLine("=== idino_career schema tables ===");
    int totalTables = 0, tbStarTables = 0;
    var tableNames = new List<string>();
    using (var cmd = new NpgsqlCommand(
        @"SELECT table_name FROM information_schema.tables
          WHERE table_schema = 'idino_career' AND table_type = 'BASE TABLE'
          ORDER BY table_name", conn))
    using (var r = await cmd.ExecuteReaderAsync())
        while (await r.ReadAsync())
        {
            var name = r.GetString(0);
            tableNames.Add(name);
            totalTables++;
            if (name.StartsWith("tb_")) tbStarTables++;
        }
    Console.WriteLine($"  TOTAL: {totalTables} tables");
    Console.WriteLine($"  tb_* tables: {tbStarTables}");
    foreach (var n in tableNames) Console.WriteLine($"    - {n}");

    // 2. R3 스키마 격리 검증 — 어디에 tb_* 가 있는지
    Console.WriteLine("\n=== Cross-schema tb_* leakage check ===");
    using (var cmd = new NpgsqlCommand(
        @"SELECT table_schema, COUNT(*) FROM information_schema.tables
          WHERE table_name LIKE 'tb_%' AND table_type = 'BASE TABLE'
          GROUP BY table_schema ORDER BY table_schema", conn))
    using (var r = await cmd.ExecuteReaderAsync())
        while (await r.ReadAsync())
            Console.WriteLine($"  {r.GetString(0)}: {r.GetInt64(1)} tb_*");

    // 3. 인덱스 수
    Console.WriteLine("\n=== idino_career indexes ===");
    using (var cmd = new NpgsqlCommand(
        @"SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'idino_career'", conn))
        Console.WriteLine($"  TOTAL: {await cmd.ExecuteScalarAsync()}");

    // 4. FK 제약 수
    Console.WriteLine("\n=== idino_career foreign keys ===");
    using (var cmd = new NpgsqlCommand(
        @"SELECT COUNT(*) FROM information_schema.table_constraints
          WHERE table_schema = 'idino_career' AND constraint_type = 'FOREIGN KEY'", conn))
        Console.WriteLine($"  TOTAL: {await cmd.ExecuteScalarAsync()}");

    // 5. 행 수 (Q-A — 빈 schema only 검증, 모든 테이블 0행이어야 함)
    Console.WriteLine("\n=== Row counts (Q-A: 모두 0 이어야 함) ===");
    int totalRows = 0;
    foreach (var t in tableNames)
    {
        using var cmd = new NpgsqlCommand($"SELECT COUNT(*) FROM idino_career.{t}", conn);
        var n = (long)(await cmd.ExecuteScalarAsync());
        if (n > 0)
        {
            Console.WriteLine($"  [WARN] {t}: {n} rows");
            totalRows += (int)n;
        }
    }
    Console.WriteLine($"  Total non-zero tables: 0 (expected)");
    if (totalRows > 0)
        Console.WriteLine($"  [WARN] Total rows: {totalRows} (Q-A 위반 가능)");
    else
        Console.WriteLine($"  [OK] 모든 테이블 0행 — Q-A 빈 schema 원칙 준수");

    // 6. 다른 schema 의 테이블 분포 (참고)
    Console.WriteLine("\n=== All schemas table count ===");
    using (var cmd = new NpgsqlCommand(
        @"SELECT table_schema, COUNT(*) FROM information_schema.tables
          WHERE table_schema NOT LIKE 'pg_%' AND table_schema <> 'information_schema'
          GROUP BY table_schema ORDER BY table_schema", conn))
    using (var r = await cmd.ExecuteReaderAsync())
        while (await r.ReadAsync())
            Console.WriteLine($"  {r.GetString(0)}: {r.GetInt64(1)} tables");

    Console.WriteLine("\n[DONE]");
}

await RunAsync();
