using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace AIAgentManagement.Migrations
{
    /// <inheritdoc />
    public partial class Track088_UserDepartmentFK : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            // 트랙 #88 — 이 마이그레이션은 운영 DB 에 이미 raw SQL 로 적용된 상태.
            // 빈 DB / 신규 dev 환경에서 적용 시에만 ALTER 실행되도록 IF NOT EXISTS 가드.
            // 운영 DB 에서는 모든 ALTER 가 skip → 변경 없이 __EFMigrationsHistory 만 추가.
            migrationBuilder.Sql(@"
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema='AIAgentManagement' AND table_name='Users' AND column_name='DepartmentId'
                    ) THEN
                        ALTER TABLE ""AIAgentManagement"".""Users"" ADD COLUMN ""DepartmentId"" integer NULL;
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema='AIAgentManagement' AND table_name='Users' AND column_name='OriginalDocutilUuid'
                    ) THEN
                        ALTER TABLE ""AIAgentManagement"".""Users"" ADD COLUMN ""OriginalDocutilUuid"" uuid NULL;
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes
                        WHERE schemaname='AIAgentManagement' AND indexname='IX_Users_DepartmentId'
                    ) THEN
                        CREATE INDEX ""IX_Users_DepartmentId"" ON ""AIAgentManagement"".""Users"" (""DepartmentId"");
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints
                        WHERE table_schema='AIAgentManagement' AND table_name='Users'
                          AND constraint_name='FK_Users_Departments_DepartmentId'
                    ) THEN
                        ALTER TABLE ""AIAgentManagement"".""Users""
                          ADD CONSTRAINT ""FK_Users_Departments_DepartmentId""
                          FOREIGN KEY (""DepartmentId"")
                          REFERENCES ""AIAgentManagement"".""Departments""(""DepartmentId"")
                          ON DELETE SET NULL;
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints
                        WHERE table_schema='AIAgentManagement' AND table_name='Users'
                          AND constraint_name='UQ_Users_OriginalDocutilUuid'
                    ) THEN
                        ALTER TABLE ""AIAgentManagement"".""Users""
                          ADD CONSTRAINT ""UQ_Users_OriginalDocutilUuid""
                          UNIQUE (""OriginalDocutilUuid"");
                    END IF;
                END $$;
            ");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                ALTER TABLE ""AIAgentManagement"".""Users"" DROP CONSTRAINT IF EXISTS ""FK_Users_Departments_DepartmentId"";
                ALTER TABLE ""AIAgentManagement"".""Users"" DROP CONSTRAINT IF EXISTS ""UQ_Users_OriginalDocutilUuid"";
                DROP INDEX IF EXISTS ""AIAgentManagement"".""IX_Users_DepartmentId"";
                ALTER TABLE ""AIAgentManagement"".""Users"" DROP COLUMN IF EXISTS ""DepartmentId"";
                ALTER TABLE ""AIAgentManagement"".""Users"" DROP COLUMN IF EXISTS ""OriginalDocutilUuid"";
            ");
        }
    }
}
