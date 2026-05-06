// =============================================================================
// Phase 4.2 적용 스크립트 — career DDL 3개 파일 → AGENT_HUB.idino_career schema
// =============================================================================
// 사용자 결정 (Q-A/Q-B/Q-C/Q-D 확정):
//   Q-A: 빈 schema only (DDL only) — 시연용 monorepo COPY
//   Q-B: 옵션 C (래퍼 — SQL 파일 무변경 + SET search_path 주입 + 런타임 필터)
//   Q-C: 00_run_all.sql 의 \i 순서 따라가되 DDL 3개 파일만
//   Q-D: dotnet-script + Npgsql 직접 실행
//
// 적용 대상:
//   1. career/database/01_schema_create.sql   (핵심 14 테이블)
//   2. career/database/02_techspec_tables.sql (TechSpec 25 테이블)
//   3. career/database/10_p1_p2_extensions.sql(P1/P2 확장 24 테이블)
//
// 처리 사항:
//   - 디스크 SQL 파일은 *무변경* (Q-B 옵션 C 원칙)
//   - 런타임 메모리 상에서 다음 변환 수행 (한국어 인코딩 손상 우회):
//     * UTF-8 BOM 제거
//     * COMMENT ON ... ; 라인 제거 — 깨진 한글 문자열 리터럴이 unterminated quote 유발
//   - 한 파일 = 한 트랜잭션 (실패 시 부분 적용 방지)
// =============================================================================

#r "nuget: Npgsql, 8.0.6"
using Npgsql;
using System;
using System.IO;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using System.Text;

async Task<int> RunAsync()
{
    var cs = "Host=192.168.10.39;Port=5440;Database=AGENT_HUB;Username=AGENT_HUB;Password=idino!@#$;Timeout=120";

    var sqlFiles = new[]
    {
        "career/database/01_schema_create.sql",
        "career/database/02_techspec_tables.sql",
        "career/database/10_p1_p2_extensions.sql",
    };

    // COMMENT ON 라인 제거 정규식 — 한국어 인코딩 손상 우회
    // 멀티라인 모드: 각 라인 시작 (^M) 의 COMMENT ON ... ; 까지 제거
    // 한국어 깨진 문자열 안에는 인용부호 짝이 깨졌을 가능성이 높아 안전하게 라인 단위로 처리
    var commentLineRegex = new Regex(
        @"^\s*COMMENT\s+ON\s+[^;]*;.*$",
        RegexOptions.Multiline | RegexOptions.IgnoreCase);

    // SET search_path 보정 — 파일 내 `SET search_path TO idino_career;` 가 public 을 누락
    //   uuid_generate_v4 / gen_random_uuid (extension public 스키마) 호출 실패 유발
    //   → idino_career, public 으로 치환
    var searchPathRegex = new Regex(
        @"^\s*SET\s+search_path\s+TO\s+idino_career\s*;",
        RegexOptions.Multiline | RegexOptions.IgnoreCase);

    // 라인 주석 + DDL 키워드 같은 라인 분리 — 한국어 인코딩 손상 시 newline 사라진 패턴
    //   예: `-- ?ы듃?대━??CREATE TABLE IF NOT EXISTS tb_portfolio (`
    //   → DDL 키워드 앞에 줄바꿈 삽입
    var inlineCommentDdlRegex = new Regex(
        @"(--[^\r\n]*?)\s*(CREATE\s+(TABLE|INDEX|UNIQUE|VIEW|FUNCTION|TRIGGER)\s)",
        RegexOptions.IgnoreCase);

    // CREATE INDEX → CREATE INDEX IF NOT EXISTS (멱등성 — 재실행 안전)
    var createIndexRegex = new Regex(
        @"\bCREATE\s+INDEX\s+(?!IF\s+NOT\s+EXISTS)",
        RegexOptions.IgnoreCase);

    // tb_user FK 제거 — file 10 의 advisor_user_id UUID REFERENCES tb_user(user_id)
    //   tb_user 는 별도 auth 스키마 파일에 정의 (현재 적용 대상 X)
    //   FK 제약만 제거, 컬럼은 보존 (애플리케이션 코드가 의존)
    var stripTbUserFkRegex = new Regex(
        @"\s+REFERENCES\s+tb_user\s*\(\s*user_id\s*\)",
        RegexOptions.IgnoreCase);

    // DML 제거 (Q-A 빈 schema only — DDL only)
    //   INSERT/UPDATE/DELETE/MERGE 통째로 제거 — 한국어 손상 시드 데이터 우회
    //   세미콜론 단위 매칭: INSERT ... ; (라인 가로지름 가능, multiline DOTALL 모드)
    //   주의: 안에 다중 row VALUES 줄바꿈 포함 → \s+\(...\),\s*\(... 패턴
    //   가장 단순: 라인 첫 토큰이 INSERT|UPDATE|DELETE 인 라인부터 다음 ; 까지
    var dmlRegex = new Regex(
        @"^\s*(INSERT|UPDATE|DELETE|MERGE)\s+[\s\S]*?;\s*$",
        RegexOptions.Multiline | RegexOptions.IgnoreCase);

    var results = new List<(string file, bool ok, string err, int commentsStripped)>();

    foreach (var rel in sqlFiles)
    {
        var abs = Path.GetFullPath(rel);
        Console.WriteLine($"\n=== Applying {Path.GetFileName(abs)} ===");

        if (!File.Exists(abs))
        {
            Console.WriteLine($"[SKIP] file not found: {abs}");
            results.Add((rel, false, "file not found", 0));
            continue;
        }

        // UTF-8 (.NET ReadAllText with Encoding.UTF8 strips BOM)
        var sql = File.ReadAllText(abs, Encoding.UTF8);

        // COMMENT ON 라인 제거 카운트
        var matches = commentLineRegex.Matches(sql);
        int strippedCount = matches.Count;
        sql = commentLineRegex.Replace(sql, "-- [STRIPPED COMMENT ON]");
        Console.WriteLine($"  [INFO] COMMENT ON lines stripped: {strippedCount}");

        // SET search_path 치환 (idino_career → idino_career, public)
        var spMatches = searchPathRegex.Matches(sql);
        sql = searchPathRegex.Replace(sql, "SET search_path TO idino_career, public;");
        Console.WriteLine($"  [INFO] search_path lines patched: {spMatches.Count}");

        // 인라인 주석+DDL 분리 (`-- ?? CREATE TABLE ...` → `-- ??\nCREATE TABLE ...`)
        var inlineMatches = inlineCommentDdlRegex.Matches(sql);
        sql = inlineCommentDdlRegex.Replace(sql, "$1\n$2");
        Console.WriteLine($"  [INFO] inline comment+DDL split: {inlineMatches.Count}");

        // CREATE INDEX → CREATE INDEX IF NOT EXISTS (멱등성)
        var ciMatches = createIndexRegex.Matches(sql);
        sql = createIndexRegex.Replace(sql, "CREATE INDEX IF NOT EXISTS ");
        Console.WriteLine($"  [INFO] CREATE INDEX → IF NOT EXISTS: {ciMatches.Count}");

        // tb_user FK 제거 (별도 auth 파일에 정의됨)
        var fkMatches = stripTbUserFkRegex.Matches(sql);
        sql = stripTbUserFkRegex.Replace(sql, "");
        if (fkMatches.Count > 0)
            Console.WriteLine($"  [INFO] tb_user FK references stripped: {fkMatches.Count}");

        // DML 제거 (Q-A — 빈 schema only)
        var dmlMatches = dmlRegex.Matches(sql);
        sql = dmlRegex.Replace(sql, "-- [STRIPPED DML]");
        if (dmlMatches.Count > 0)
            Console.WriteLine($"  [INFO] DML statements stripped: {dmlMatches.Count}");

        // 옵션 C: 파일 무변경 + 연결 단위로 search_path 강제
        try
        {
            using var conn = new NpgsqlConnection(cs);
            await conn.OpenAsync();

            using (var setCmd = new NpgsqlCommand("SET search_path TO idino_career, public;", conn))
                await setCmd.ExecuteNonQueryAsync();

            using var tx = await conn.BeginTransactionAsync();
            try
            {
                using var cmd = new NpgsqlCommand(sql, conn, tx);
                cmd.CommandTimeout = 180;
                await cmd.ExecuteNonQueryAsync();
                await tx.CommitAsync();

                Console.WriteLine($"[OK] {Path.GetFileName(abs)}");
                results.Add((rel, true, "", strippedCount));
            }
            catch (Exception)
            {
                await tx.RollbackAsync();
                throw;
            }
        }
        catch (Exception ex)
        {
            var msg = ex.Message;
            if (msg.Length > 250) msg = msg.Substring(0, 250) + "...";
            Console.WriteLine($"[FAIL] {Path.GetFileName(abs)}: {msg}");
            results.Add((rel, false, msg, strippedCount));
        }
    }

    // 요약
    Console.WriteLine("\n=== SUMMARY ===");
    int ok = 0, fail = 0;
    foreach (var (file, success, err, sc) in results)
    {
        var tag = success ? "OK  " : "FAIL";
        Console.WriteLine($"  [{tag}] {Path.GetFileName(file)} (COMMENT lines stripped: {sc})");
        if (success) ok++; else fail++;
    }
    Console.WriteLine($"\n  Total: {ok} OK / {fail} FAIL");

    return fail == 0 ? 0 : 1;
}

return await RunAsync();
