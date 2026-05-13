using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace AIAgentManagement.Migrations
{
    /// <inheritdoc />
    /// <remarks>
    /// 트랙 #91 — ApiKeyPoolService DB 통합.
    /// 외부 노출용 키(<c>"External"</c>, 기본값)와 외부 LLM 풀 키(<c>"Provider"</c>)를 같은 `ApiKeys` 테이블에서
    /// 격리하기 위한 `KeyType` 컬럼 + `(KeyType, IsActive, ServiceCode)` 복합 인덱스 추가.
    ///
    /// 기존 행 처리:
    /// - 운영 DB 의 기존 1건(들)은 모두 외부 노출용 ak- 키 또는 agent-api 키이므로 `'External'` 백필.
    /// - 신규 운영자 등록 키는 `ApiKeyService.CreateProviderApiKeyAsync` 가 `'Provider'` 강제 지정.
    ///
    /// idempotent SQL 패턴은 트랙 #89 `Track089_UserSessionExpiresAt` 답습:
    /// - <c>information_schema.columns IF NOT EXISTS</c> 가드로 운영 DB 수동 선적용 케이스 흡수.
    /// - 인덱스도 <c>pg_indexes</c> 가드 + <c>CREATE INDEX IF NOT EXISTS</c> 이중 안전.
    /// - Down 은 <c>DROP IF EXISTS</c> 로 롤백 친화적.
    /// </remarks>
    public partial class Track091_ApiKeyKeyType : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                DO $$
                BEGIN
                    -- 1) KeyType 컬럼 추가 (멱등 가드).
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema='AIAgentManagement'
                          AND table_name='ApiKeys'
                          AND column_name='KeyType'
                    ) THEN
                        -- 1-1) NULL 허용으로 컬럼 추가
                        ALTER TABLE ""AIAgentManagement"".""ApiKeys""
                          ADD COLUMN ""KeyType"" character varying(20) NULL;

                        -- 1-2) 기존 행 백필: 모두 외부 노출 키이므로 'External'.
                        UPDATE ""AIAgentManagement"".""ApiKeys""
                           SET ""KeyType"" = 'External'
                         WHERE ""KeyType"" IS NULL;

                        -- 1-3) NOT NULL + DEFAULT 'External' 제약 부여.
                        --      (DEFAULT 는 향후 신규 row INSERT 시 KeyType 누락 안전망.)
                        ALTER TABLE ""AIAgentManagement"".""ApiKeys""
                          ALTER COLUMN ""KeyType"" SET NOT NULL;

                        ALTER TABLE ""AIAgentManagement"".""ApiKeys""
                          ALTER COLUMN ""KeyType"" SET DEFAULT 'External';
                    END IF;

                    -- 2) 복합 인덱스 추가 (멱등 가드).
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes
                        WHERE schemaname='AIAgentManagement'
                          AND tablename='ApiKeys'
                          AND indexname='IX_ApiKeys_KeyType_IsActive_ServiceCode'
                    ) THEN
                        CREATE INDEX IF NOT EXISTS ""IX_ApiKeys_KeyType_IsActive_ServiceCode""
                          ON ""AIAgentManagement"".""ApiKeys"" (""KeyType"", ""IsActive"", ""ServiceCode"");
                    END IF;
                END $$;
            ");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                DROP INDEX IF EXISTS ""AIAgentManagement"".""IX_ApiKeys_KeyType_IsActive_ServiceCode"";

                ALTER TABLE ""AIAgentManagement"".""ApiKeys""
                  DROP COLUMN IF EXISTS ""KeyType"";
            ");
        }
    }
}
