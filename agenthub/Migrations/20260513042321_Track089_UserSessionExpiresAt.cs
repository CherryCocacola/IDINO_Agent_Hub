using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace AIAgentManagement.Migrations
{
    /// <inheritdoc />
    /// <remarks>
    /// 트랙 #89 C2 — UserSessions.ExpiresAt 컬럼 추가.
    /// 60분 무알림 강제 로그아웃 + "자동 로그인" 미동작 결함 해소를 위한 refresh token 만료 시점 컬럼.
    /// AuthService.LoginAsync 가 LoginAt + JwtSettings:RefreshTokenExpirationInDays (default 7일) 로 채운다.
    /// AuthService.RefreshTokenAsync 가 ExpiresAt 검사로 만료된 세션은 거부하여 재로그인 유도.
    ///
    /// 기존 행(운영 DB) 처리:
    /// - 이미 비활성화된 세션(IsActive=FALSE)은 LoginAt 기준 default 부여 (조회만 가능, 갱신 불가)
    /// - 활성 세션(IsActive=TRUE)은 LoginAt + 7일 적용. 7일 이전 로그인은 즉시 만료로 자연스러운 재로그인 유도
    /// </remarks>
    public partial class Track089_UserSessionExpiresAt : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            // 빈 DB / 신규 dev 환경: 컬럼 추가 (NULL 허용 임시) → 기존 행 채우기 → NOT NULL 전환.
            // 운영 DB 에 raw SQL 로 선적용된 경우엔 IF NOT EXISTS 가드로 skip.
            migrationBuilder.Sql(@"
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema='AIAgentManagement'
                          AND table_name='UserSessions'
                          AND column_name='ExpiresAt'
                    ) THEN
                        -- 1) NULL 허용으로 컬럼 추가
                        ALTER TABLE ""AIAgentManagement"".""UserSessions""
                          ADD COLUMN ""ExpiresAt"" timestamp with time zone NULL;

                        -- 2) 기존 행 채우기: LoginAt + 7일 (JwtSettings:RefreshTokenExpirationInDays default)
                        UPDATE ""AIAgentManagement"".""UserSessions""
                           SET ""ExpiresAt"" = ""LoginAt"" + INTERVAL '7 days'
                         WHERE ""ExpiresAt"" IS NULL;

                        -- 3) NOT NULL 제약 부여
                        ALTER TABLE ""AIAgentManagement"".""UserSessions""
                          ALTER COLUMN ""ExpiresAt"" SET NOT NULL;
                    END IF;
                END $$;
            ");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                ALTER TABLE ""AIAgentManagement"".""UserSessions""
                  DROP COLUMN IF EXISTS ""ExpiresAt"";
            ");
        }
    }
}
