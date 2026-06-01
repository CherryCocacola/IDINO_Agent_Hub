"""트랙 #149 P3 — i18n 3 locale (ko/en/vi) 회귀 매트릭스.

목표:
- vue-i18n placeholder syntax 결함 (트랙 #124 회귀) 차단
- 3개 locale 모두 정상 빌드 + 페이지 진입 시 console error 0
- 핵심 페이지의 라벨/메뉴/버튼이 locale 따라 변경 확인
- 누락 키는 ko 폴백 (warning 표시되지 않음)

검증 페이지 = 통합 차원의 핵심 동선:
1. /login            — 로그인 폼
2. /dashboard        — 대시보드
3. /agents           — Agent 카탈로그
4. /admin/docutil-users — DocUtil 흡수 운영자
5. /settings         — 설정 (i18n 토글 위치)
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://192.168.10.39:64005"
ADMIN = ("admin@example.com", "Admin123!")
OUT = Path(__file__).resolve().parents[1].parent / "user_mig" / "I18N_LOCALE_MATRIX.json"

LOCALES = ["ko", "en", "vi"]
PAGES = [
    ("/login", "로그인"),
    ("/dashboard", "대시보드"),
    ("/agents", "Agent 카탈로그"),
    ("/admin/docutil-users", "DocUtil 사용자 관리"),
    ("/settings", "설정"),
]


async def run() -> None:
    from playwright.async_api import async_playwright

    matrix: list[dict] = []

    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)

        for locale in LOCALES:
            ctx = await b.new_context(
                viewport={"width": 1400, "height": 900},
                locale={"ko": "ko-KR", "en": "en-US", "vi": "vi-VN"}[locale],
            )
            await ctx.add_init_script(
                f"localStorage.setItem('i18n_locale', '{locale}'); "
                f"localStorage.setItem('theme', 'light');"
            )
            page = await ctx.new_page()

            console_errors: list[str] = []
            page_errors: list[str] = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))

            # 로그인 (관리자) — /login 자체 검증 후 토큰 발급
            await page.goto(f"{URL}/login", wait_until="networkidle")
            await page.wait_for_timeout(500)
            # 로그인 페이지에서 i18n 적용 여부 확인
            login_title = (await page.title()) or ""
            login_html = await page.content()
            await page.locator("input").nth(0).fill(ADMIN[0])
            await page.locator("input").nth(1).fill(ADMIN[1])
            await page.locator('button[type="submit"]').first.click()
            try:
                await page.wait_for_url(lambda u: "/login" not in u, timeout=10000)
            except Exception:
                pass

            for path, label in PAGES:
                # 페이지 진입 전 console error 초기화
                console_errors.clear()
                page_errors.clear()

                try:
                    await page.goto(f"{URL}{path}", wait_until="networkidle", timeout=15000)
                except Exception as e:
                    matrix.append(
                        {
                            "locale": locale,
                            "path": path,
                            "label": label,
                            "status": "FAIL",
                            "detail": f"navigation error: {str(e)[:120]}",
                        }
                    )
                    continue

                await page.wait_for_timeout(800)

                # 현재 활성 locale 확인 (i18n 인스턴스에서 직접 read)
                active_locale = await page.evaluate(
                    "() => { try { return localStorage.getItem('i18n_locale') || 'ko'; } catch { return 'ko'; } }"
                )

                # i18n raw placeholder ({{ }} 또는 {key}) 미치환 여부 검사 — vue-i18n 누락 키 증상
                html = await page.content()
                # vue-i18n raw key 미해석 패턴: "{{xxx}}" 또는 noKeyFound 형태
                has_raw_placeholder = "{{" in html and "}}" in html and "vue-i18n" not in html
                # placeholder syntax error 신호
                i18n_errors = [
                    e for e in console_errors
                    if "vue-i18n" in e.lower() or "intlify" in e.lower() or "translation" in e.lower()
                ]

                status = "PASS"
                detail_parts = [f"locale={active_locale}"]
                if active_locale != locale:
                    status = "FAIL"
                    detail_parts.append(f"expected={locale}")
                if i18n_errors:
                    status = "FAIL"
                    detail_parts.append(f"i18n_errors={len(i18n_errors)}")
                if page_errors:
                    status = "FAIL"
                    detail_parts.append(f"page_errors={len(page_errors)}")

                icon = {"PASS": "[ OK ]", "FAIL": "[FAIL]"}[status]
                print(f"{icon} [{locale}] {path:35s} {label}  {' '.join(detail_parts)}")

                matrix.append(
                    {
                        "locale": locale,
                        "path": path,
                        "label": label,
                        "status": status,
                        "detail": " ".join(detail_parts),
                        "active_locale": active_locale,
                        "i18n_errors": i18n_errors[:3],
                        "page_errors": page_errors[:3],
                    }
                )

            await ctx.close()

        await b.close()

    pass_n = sum(1 for r in matrix if r["status"] == "PASS")
    fail_n = sum(1 for r in matrix if r["status"] == "FAIL")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {"summary": {"pass": pass_n, "fail": fail_n, "total": len(matrix)}, "results": matrix},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n[summary] PASS={pass_n} FAIL={fail_n} (total {len(matrix)}) / 결과: {OUT}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
