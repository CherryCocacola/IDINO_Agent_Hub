#r "nuget: Npgsql, 8.0.4"
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Npgsql;

// Phase 4.5 — 4 schema 통합 검증 (검증 only, 데이터 무수정)
const string CONN = "Host=192.168.10.39;Port=5440;Database=AGENT_HUB;Username=AGENT_HUB;Password=idino!@#$;Include Error Detail=true;Timeout=30";

async Task<List<Dictionary<string, object>>> Q(NpgsqlConnection conn, string sql, params (string n, object v)[] ps)
{
    using var cmd = new NpgsqlCommand(sql, conn);
    foreach (var p in ps) cmd.Parameters.AddWithValue(p.n, p.v);
    using var r = await cmd.ExecuteReaderAsync();
    var rows = new List<Dictionary<string, object>>();
    while (await r.ReadAsync())
    {
        var row = new Dictionary<string, object>();
        for (int i = 0; i < r.FieldCount; i++) row[r.GetName(i)] = r.IsDBNull(i) ? null : r.GetValue(i);
        rows.Add(row);
    }
    return rows;
}

void H(string title) { Console.WriteLine(); Console.WriteLine($"=== {title} ==="); }

var conn = new NpgsqlConnection(CONN);
await conn.OpenAsync();
Console.WriteLine($"Connected: {conn.Host}:{conn.Port}/{conn.Database} (PG {conn.PostgreSqlVersion})");

// 1) schema 별 테이블 수
H("1. Schema 별 BASE TABLE 수");
var t1 = await Q(conn, @"
SELECT table_schema, COUNT(*) AS cnt
FROM information_schema.tables
WHERE table_schema IN ('AIAgentManagement','document_utilization','idino_career','hangfire')
  AND table_type='BASE TABLE'
GROUP BY table_schema ORDER BY table_schema");
foreach (var r in t1) Console.WriteLine($"  {r["table_schema"],-22} : {r["cnt"]}");

// 2) Cross-schema FK 검증
H("2. Cross-schema FK (R3 격리 — 0행이어야 함)");
var t2 = await Q(conn, @"
SELECT conname,
       pgn1.nspname || '.' || pgc1.relname AS source,
       pgn2.nspname || '.' || pgc2.relname AS target
FROM pg_constraint con
JOIN pg_class pgc1 ON con.conrelid = pgc1.oid
JOIN pg_namespace pgn1 ON pgc1.relnamespace = pgn1.oid
JOIN pg_class pgc2 ON con.confrelid = pgc2.oid
JOIN pg_namespace pgn2 ON pgc2.relnamespace = pgn2.oid
WHERE con.contype='f'
  AND pgn1.nspname IN ('AIAgentManagement','document_utilization','idino_career','hangfire')
  AND pgn2.nspname <> pgn1.nspname
  AND pgn1.nspname <> 'public' AND pgn2.nspname <> 'public'");
Console.WriteLine($"  cross-schema FK 수: {t2.Count} {(t2.Count == 0 ? "[PASS]" : "[FAIL]")}");
foreach (var r in t2) Console.WriteLine($"   - {r["conname"]}: {r["source"]} -> {r["target"]}");

// 3) FK ON DELETE 정책 분포
H("3. FK ON DELETE 정책 분포 (schema 별)");
var t3 = await Q(conn, @"
SELECT pgn.nspname AS schema_name,
       CASE confdeltype
         WHEN 'c' THEN 'CASCADE' WHEN 'r' THEN 'RESTRICT'
         WHEN 'n' THEN 'SET NULL' WHEN 'd' THEN 'SET DEFAULT'
         WHEN 'a' THEN 'NO ACTION' END AS on_delete,
       COUNT(*) AS cnt
FROM pg_constraint con
JOIN pg_class pgc ON con.conrelid = pgc.oid
JOIN pg_namespace pgn ON pgc.relnamespace = pgn.oid
WHERE con.contype='f'
  AND pgn.nspname IN ('AIAgentManagement','document_utilization','idino_career')
GROUP BY pgn.nspname, confdeltype
ORDER BY pgn.nspname, on_delete");
foreach (var r in t3) Console.WriteLine($"  {r["schema_name"],-22} {r["on_delete"],-12} {r["cnt"]}");

// 4) FK 총수 schema 별
H("4. FK 총수 (schema 별)");
var t4 = await Q(conn, @"
SELECT pgn.nspname AS schema_name, COUNT(*) AS fk_count
FROM pg_constraint con
JOIN pg_class pgc ON con.conrelid = pgc.oid
JOIN pg_namespace pgn ON pgc.relnamespace = pgn.oid
WHERE con.contype='f'
  AND pgn.nspname IN ('AIAgentManagement','document_utilization','idino_career')
GROUP BY pgn.nspname ORDER BY pgn.nspname");
foreach (var r in t4) Console.WriteLine($"  {r["schema_name"],-22} : {r["fk_count"]}");

// 5) audit 컬럼 분포
H("5. Audit 컬럼 분포");
var t5 = await Q(conn, @"
SELECT table_schema, column_name, COUNT(*) AS table_count
FROM information_schema.columns
WHERE table_schema IN ('AIAgentManagement','document_utilization','idino_career')
  AND column_name IN (
    'CreatedAt','UpdatedAt','CreatedBy','UpdatedBy',
    'created_at','updated_at','created_by','updated_by',
    'ins_user_id','ins_dt','upd_user_id','upd_dt')
GROUP BY table_schema, column_name
ORDER BY table_schema, column_name");
foreach (var r in t5) Console.WriteLine($"  {r["table_schema"],-22} {r["column_name"],-15} {r["table_count"]}");

// 6) audit 누락 테이블 (각 schema 별 표준 컬럼 체크)
H("6. Audit 누락 가능성 점검 (테이블 수 vs audit 보유 테이블 수)");
var t6 = await Q(conn, @"
WITH tables_all AS (
  SELECT table_schema, table_name
  FROM information_schema.tables
  WHERE table_schema IN ('AIAgentManagement','document_utilization','idino_career')
    AND table_type='BASE TABLE'
),
created_at_holders AS (
  SELECT DISTINCT table_schema, table_name
  FROM information_schema.columns
  WHERE table_schema IN ('AIAgentManagement','document_utilization','idino_career')
    AND column_name IN ('CreatedAt','created_at','ins_dt')
)
SELECT t.table_schema,
       COUNT(*) AS total_tables,
       COUNT(c.table_name) AS with_created
FROM tables_all t
LEFT JOIN created_at_holders c
  ON c.table_schema = t.table_schema AND c.table_name = t.table_name
GROUP BY t.table_schema
ORDER BY t.table_schema");
foreach (var r in t6) Console.WriteLine($"  {r["table_schema"],-22} total={r["total_tables"]} with_created_at={r["with_created"]}");

// 6b) audit 누락 테이블 목록
H("6b. created_at 컬럼 누락 테이블 (sampling, 각 schema 최대 10개)");
foreach (var schema in new[] { "AIAgentManagement", "document_utilization", "idino_career" })
{
    var cols = schema == "idino_career" ? "ins_dt" : (schema == "AIAgentManagement" ? "CreatedAt" : "created_at");
    var miss = await Q(conn, $@"
SELECT t.table_name FROM information_schema.tables t
WHERE t.table_schema=@s AND t.table_type='BASE TABLE'
  AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns c
    WHERE c.table_schema=t.table_schema AND c.table_name=t.table_name
      AND c.column_name=@col)
ORDER BY t.table_name LIMIT 10", ("s", schema), ("col", cols));
    Console.WriteLine($"  [{schema}] (체크 컬럼: {cols}) 누락: {miss.Count}");
    foreach (var r in miss) Console.WriteLine($"    - {r["table_name"]}");
}

// 7) 인덱스 통계
H("7. 인덱스 통계 (schema 별)");
var t7 = await Q(conn, @"
SELECT schemaname,
       COUNT(*) AS total_indexes,
       SUM(CASE WHEN indexdef LIKE '%UNIQUE%' THEN 1 ELSE 0 END) AS unique_indexes,
       SUM(CASE WHEN indexdef LIKE '%vector_cosine_ops%' THEN 1 ELSE 0 END) AS vector_indexes
FROM pg_indexes
WHERE schemaname IN ('AIAgentManagement','document_utilization','idino_career')
GROUP BY schemaname ORDER BY schemaname");
foreach (var r in t7)
    Console.WriteLine($"  {r["schemaname"],-22} total={r["total_indexes"]} unique={r["unique_indexes"]} vector={r["vector_indexes"]}");

// 8) Phase 5 Nexus 등록
H("8. Phase 5 — Nexus ApiService 등록");
var t8 = await Q(conn, @"
SELECT ""ServiceCode"", ""ServiceName"", ""ServiceType""
FROM ""AIAgentManagement"".""ApiServices""
WHERE ""ServiceCode""='nexus'");
Console.WriteLine($"  nexus 시드: {t8.Count}");
foreach (var r in t8) Console.WriteLine($"    code={r["ServiceCode"]}  name={r["ServiceName"]}  type={r["ServiceType"]}");

// 9) Phase 7.1 Agent 시드
H("9. Phase 7.1 — Agent 시드 (15개 신규)");
var t9 = await Q(conn, @"
SELECT ""AgentCode"", ""ServiceId"", ""LlmRouting""
FROM ""AIAgentManagement"".""Agents""
WHERE ""AgentCode"" LIKE 'docutil-%' OR ""AgentCode"" LIKE 'career-%'
   OR ""AgentCode"" LIKE 'common-%' OR ""AgentCode"" LIKE 'embedding-%'
   OR ""AgentCode"" LIKE 'web-search-%' OR ""AgentCode"" LIKE 'agentic-%'
ORDER BY ""AgentCode""");
Console.WriteLine($"  Phase 7.1 Agent 수: {t9.Count}");
foreach (var r in t9)
    Console.WriteLine($"    {r["AgentCode"],-40} service={r["ServiceId"]} routing={r["LlmRouting"]}");

// 10) Phase 7.2 ApiKey
H("10. Phase 7.2 — ApiKey 발급");
var t10 = await Q(conn, @"
SELECT ""ApiKeyId"", ""KeyName"", ""Scopes"", ""IsActive""
FROM ""AIAgentManagement"".""ApiKeys""
ORDER BY ""ApiKeyId""");
Console.WriteLine($"  ApiKey 수: {t10.Count}");
foreach (var r in t10)
    Console.WriteLine($"    id={r["ApiKeyId"]} name={r["KeyName"],-25} scopes={r["Scopes"],-30} active={r["IsActive"]}");

// 11) Tenants + Departments (Phase 4.3)
H("11. Phase 4.3 — Tenants / Departments");
var t11a = await Q(conn, @"SELECT COUNT(*) AS c FROM ""AIAgentManagement"".""Tenants""");
var t11b = await Q(conn, @"SELECT COUNT(*) AS c FROM ""AIAgentManagement"".""Departments""");
Console.WriteLine($"  Tenants={t11a[0]["c"]}  Departments={t11b[0]["c"]}");

// 12) idino_career pgvector 검증 (Phase 4.4)
H("12. Phase 4.4 — idino_career vector 컬럼");
var t12 = await Q(conn, @"
SELECT table_name, column_name, udt_name
FROM information_schema.columns
WHERE table_schema='idino_career' AND udt_name='vector'
ORDER BY table_name");
Console.WriteLine($"  vector 컬럼 수: {t12.Count}");
foreach (var r in t12) Console.WriteLine($"    {r["table_name"]}.{r["column_name"]} ({r["udt_name"]})");

// 13) R3 격리 시뮬레이션 — 3개 connection (search_path 별)
H("13. R3 격리 시뮬레이션 — 3개 connection");
async Task SimulateConn(string label, string searchPath)
{
    var c = new NpgsqlConnection(CONN);
    await c.OpenAsync();
    using (var setCmd = new NpgsqlCommand($"SET search_path TO {searchPath}", c))
        await setCmd.ExecuteNonQueryAsync();
    Console.WriteLine($"  [{label}] search_path={searchPath}");
    // search_path 첫 번째 schema 가 자기 schema, 다른 schema 의 테이블은 unqualified 로 접근 불가해야 함
    // AIAgentManagement.Users / document_utilization.tb_documents / idino_career.tb_student
    var probes = new (string sql, string desc)[] {
        ("SELECT 1 FROM \"Users\" LIMIT 1",        "Users (AgentHub)"),
        ("SELECT 1 FROM tb_documents LIMIT 1",      "tb_documents (DocUtil)"),
        ("SELECT 1 FROM tb_student LIMIT 1",        "tb_student (career)")
    };
    foreach (var p in probes)
    {
        try
        {
            using var cmd = new NpgsqlCommand(p.sql, c);
            using var r = await cmd.ExecuteReaderAsync();
            await r.ReadAsync();
            Console.WriteLine($"    OK    {p.desc}");
        }
        catch (Exception ex)
        {
            var msg = ex.Message.Length > 80 ? ex.Message.Substring(0, 80) + "..." : ex.Message;
            Console.WriteLine($"    FAIL  {p.desc} : {msg}");
        }
    }
}
await SimulateConn("agenthub", "\"AIAgentManagement\",public");
await SimulateConn("docutil", "document_utilization,public");
await SimulateConn("career", "idino_career,public");

// 14) UNIQUE 제약 분포
H("14. UNIQUE 제약 분포");
var t14 = await Q(conn, @"
SELECT pgn.nspname AS schema_name, COUNT(*) AS uq_count
FROM pg_constraint con
JOIN pg_class pgc ON con.conrelid = pgc.oid
JOIN pg_namespace pgn ON pgc.relnamespace = pgn.oid
WHERE con.contype='u'
  AND pgn.nspname IN ('AIAgentManagement','document_utilization','idino_career')
GROUP BY pgn.nspname ORDER BY pgn.nspname");
foreach (var r in t14) Console.WriteLine($"  {r["schema_name"],-22} : {r["uq_count"]}");

// 15) PK 누락 테이블
H("15. PK 누락 BASE TABLE");
var t15 = await Q(conn, @"
SELECT t.table_schema, t.table_name FROM information_schema.tables t
WHERE t.table_schema IN ('AIAgentManagement','document_utilization','idino_career')
  AND t.table_type='BASE TABLE'
  AND NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints c
    WHERE c.table_schema=t.table_schema AND c.table_name=t.table_name AND c.constraint_type='PRIMARY KEY')
ORDER BY t.table_schema, t.table_name LIMIT 30");
Console.WriteLine($"  PK 누락 수: {t15.Count}");
foreach (var r in t15) Console.WriteLine($"    {r["table_schema"]}.{r["table_name"]}");

Console.WriteLine();
Console.WriteLine("=== Phase 4.5 검증 완료 ===");
