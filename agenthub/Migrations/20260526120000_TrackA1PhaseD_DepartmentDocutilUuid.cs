using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace AIAgentManagement.Migrations
{
    /// <inheritdoc />
    /// <summary>
    /// 트랙 A1 Phase D (2026-05-26) — Departments 테이블에 OriginalDocutilUuid 컬럼 추가.
    ///
    /// 목적: DocUtil tb_departments (9건, uuid PK) 를 AgentHub.Departments (32건, int PK)
    /// 와 매핑하여, tb_departments 를 VIEW + INSTEAD OF TRIGGER 로 통합하기 위한 사전 작업.
    /// tb_users 패턴 (트랙 #88 + #98 phase 3) 그대로 재사용.
    ///
    /// 트랙 #88 (UserDepartmentFK) 와 동일한 IF NOT EXISTS 가드 패턴 — 운영 DB 에 raw SQL
    /// 로 이미 적용된 경우 ALTER 가 skip 되고 __EFMigrationsHistory 만 기록.
    /// </summary>
    public partial class TrackA1PhaseD_DepartmentDocutilUuid : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                DO $$
                BEGIN
                    -- 1) OriginalDocutilUuid 컬럼 추가
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema='AIAgentManagement'
                          AND table_name='Departments'
                          AND column_name='OriginalDocutilUuid'
                    ) THEN
                        ALTER TABLE ""AIAgentManagement"".""Departments""
                          ADD COLUMN ""OriginalDocutilUuid"" uuid NULL;
                    END IF;

                    -- 2) UNIQUE 제약 (NULL 허용) — 한 DocUtil uuid 는 한 Department 에만
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints
                        WHERE table_schema='AIAgentManagement'
                          AND table_name='Departments'
                          AND constraint_name='UQ_Departments_OriginalDocutilUuid'
                    ) THEN
                        ALTER TABLE ""AIAgentManagement"".""Departments""
                          ADD CONSTRAINT ""UQ_Departments_OriginalDocutilUuid""
                          UNIQUE (""OriginalDocutilUuid"");
                    END IF;
                END $$;
            ");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                ALTER TABLE ""AIAgentManagement"".""Departments""
                  DROP CONSTRAINT IF EXISTS ""UQ_Departments_OriginalDocutilUuid"";
                ALTER TABLE ""AIAgentManagement"".""Departments""
                  DROP COLUMN IF EXISTS ""OriginalDocutilUuid"";
            ");
        }
    }
}
