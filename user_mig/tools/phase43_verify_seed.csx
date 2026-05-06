// Phase 4.3 검증 + 시드 — Tenants + Departments
// 1) 운영 PG 의 Tenants/Departments 테이블 + UNIQUE 인덱스 + FK 검증
// 2) idino-default Tenant + general Department 멱등 시드
// 사용: dotnet script user_mig/tools/phase43_verify_seed.csx
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

    // 검증 1: Tenants/Departments 테이블 존재
    var tenantsExists = (bool)(await Scalar(cn,
        "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='AIAgentManagement' AND table_name='Tenants')"));
    var deptExists = (bool)(await Scalar(cn,
        "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='AIAgentManagement' AND table_name='Departments')"));
    Console.WriteLine($"[검증1] Tenants 테이블: {tenantsExists} / Departments 테이블: {deptExists}");

    // 검증 2: UNIQUE 인덱스 존재
    var uniqIdx = Convert.ToInt64(await Scalar(cn, @"
        SELECT count(*) FROM pg_indexes
        WHERE schemaname='AIAgentManagement'
          AND indexname IN ('IX_Tenants_TenantCode','IX_Departments_DepartmentCode')"));
    Console.WriteLine($"[검증2] UNIQUE 인덱스 (TenantCode + DepartmentCode): {uniqIdx}/2");

    // 검증 3: FK 제약 존재 (3개 기대)
    var fkCount = Convert.ToInt64(await Scalar(cn, @"
        SELECT count(*) FROM information_schema.table_constraints tc
        WHERE tc.table_schema='AIAgentManagement'
          AND tc.constraint_type='FOREIGN KEY'
          AND tc.table_name IN ('Tenants','Departments')"));
    Console.WriteLine($"[검증3] FK 제약 (Tenants.CreatedBy + Departments.TenantId + Departments.ParentDepartmentId): {fkCount}/3");

    // 검증 4: 컬럼 수
    var tenCols = Convert.ToInt64(await Scalar(cn,
        "SELECT count(*) FROM information_schema.columns WHERE table_schema='AIAgentManagement' AND table_name='Tenants'"));
    var depCols = Convert.ToInt64(await Scalar(cn,
        "SELECT count(*) FROM information_schema.columns WHERE table_schema='AIAgentManagement' AND table_name='Departments'"));
    Console.WriteLine($"[검증4] Tenants 컬럼={tenCols}/8, Departments 컬럼={depCols}/9");

    // 검증 5: 마이그레이션 히스토리
    var migApplied = (bool)(await Scalar(cn,
        "SELECT EXISTS(SELECT 1 FROM \"__EFMigrationsHistory\" WHERE \"MigrationId\" = '20260506085522_AddTenantsAndDepartments')"));
    Console.WriteLine($"[검증5] 마이그레이션 적용 기록: {migApplied}");

    // 시드 1: idino-default Tenant
    var tenantExistsCnt = Convert.ToInt64(await Scalar(cn,
        "SELECT count(*) FROM \"AIAgentManagement\".\"Tenants\" WHERE \"TenantCode\"='idino-default'"));
    if (tenantExistsCnt == 0)
    {
        await Exec(cn, @"
            INSERT INTO ""AIAgentManagement"".""Tenants""
                (""TenantCode"",""TenantName"",""Description"",""IsActive"",""CreatedAt"")
            VALUES
                ('idino-default','IDINO 기본 테넌트',
                 '통합 멀티테넌시 단일 권위 (ADR-8) — 기본 시연 테넌트',
                 true, NOW() AT TIME ZONE 'UTC')");
        Console.WriteLine("[시드1] idino-default Tenant — 신규 INSERT");
    }
    else
    {
        Console.WriteLine("[시드1] idino-default Tenant — 이미 존재 (skip)");
    }

    var tenantId = Convert.ToInt32(await Scalar(cn,
        "SELECT \"TenantId\" FROM \"AIAgentManagement\".\"Tenants\" WHERE \"TenantCode\"='idino-default'"));
    Console.WriteLine($"  → TenantId={tenantId}");

    // 시드 2: general Department
    var deptExistsCnt = Convert.ToInt64(await Scalar(cn,
        "SELECT count(*) FROM \"AIAgentManagement\".\"Departments\" WHERE \"DepartmentCode\"='general'"));
    if (deptExistsCnt == 0)
    {
        await using (var cmd = new NpgsqlCommand(@"
            INSERT INTO ""AIAgentManagement"".""Departments""
                (""DepartmentCode"",""DepartmentName"",""TenantId"",""ParentDepartmentId"",
                 ""Description"",""IsActive"",""CreatedAt"")
            VALUES
                ('general','공용 부서',@tid, NULL,
                 '테넌트 기본 부서 — career.tb_department 통합 매핑 베이스',
                 true, NOW() AT TIME ZONE 'UTC')", cn))
        {
            cmd.Parameters.AddWithValue("tid", tenantId);
            await cmd.ExecuteNonQueryAsync();
        }
        Console.WriteLine("[시드2] general Department — 신규 INSERT");
    }
    else
    {
        Console.WriteLine("[시드2] general Department — 이미 존재 (skip)");
    }

    // 검증 6: 시드 조인 조회
    var seedRows = Convert.ToInt64(await Scalar(cn, @"
        SELECT count(*) FROM ""AIAgentManagement"".""Departments"" d
        JOIN ""AIAgentManagement"".""Tenants"" t ON t.""TenantId""=d.""TenantId""
        WHERE t.""TenantCode""='idino-default' AND d.""DepartmentCode""='general'"));
    Console.WriteLine($"[검증6] 조인 시드 행수: {seedRows} (1 기대)");

    // 검증 7: AIAgentManagement schema 의 총 테이블 수
    var totalTables = Convert.ToInt64(await Scalar(cn,
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='AIAgentManagement' AND table_type='BASE TABLE'"));
    Console.WriteLine($"[검증7] AIAgentManagement schema 총 BASE TABLE: {totalTables} (이전 35 → 37 + __EFMigrationsHistory 기대)");

    Console.WriteLine("[Phase 4.3] 검증 + 시드 완료");
}

async Task<object> Scalar(NpgsqlConnection cn, string sql)
{
    await using var cmd = new NpgsqlCommand(sql, cn);
    return await cmd.ExecuteScalarAsync();
}

async Task Exec(NpgsqlConnection cn, string sql)
{
    await using var cmd = new NpgsqlCommand(sql, cn);
    await cmd.ExecuteNonQueryAsync();
}
