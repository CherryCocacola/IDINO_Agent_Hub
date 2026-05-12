"""트랙 #75 — UI e2e 공통 유틸 (Playwright Python 1.58 sync API).

- AgentHub: http://192.168.10.39:64005 (Vue 3 SPA)
- DocUtil:  http://192.168.10.39:8041 (nginx → Next.js 3040)
- 운영 데이터 무영향이 절대 원칙 — 모든 mutation 은 자체 생성 → 자체 회수만 허용.

스크린샷 경로 규칙:
  screenshots/{시나리오ID}_{stepNN}_{설명}.png   (예: s1_01_login.png)

스크린샷 시 민감정보(평문 ApiKey) 노출되는 영역은 클리핑 / 마스킹 처리.
"""
from __future__ import annotations
import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

# --- 경로 ---
ROOT = Path(__file__).resolve().parent
SCREENSHOTS = ROOT / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)

# --- 운영 환경 상수 ---
AGENTHUB_BASE = "http://192.168.10.39:64005"
DOCUTIL_NGINX = "http://192.168.10.39:8041"
DOCUTIL_API = "http://192.168.10.39:8040"

# --- 자격증명 ---
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Admin123!"  # noqa: S105 (테스트 fixture; 운영 자격증명은 .env)

# --- 타임아웃 / 뷰포트 ---
DEFAULT_TIMEOUT_MS = 15_000
VIEWPORT = {"width": 1440, "height": 900}


@dataclass
class StepResult:
    """단일 UI 스텝 결과."""
    step_id: str  # 예: s1_01
    description: str
    result: str  # PASS / FAIL / SKIP
    duration_ms: int
    screenshot: str | None = None
    note: str = ""


@dataclass
class ScenarioResult:
    """시나리오 묶음 결과."""
    scenario_id: str
    scenario_name: str
    steps: list[StepResult] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""

    def summary(self) -> dict[str, int]:
        c = {"PASS": 0, "FAIL": 0, "SKIP": 0}
        for s in self.steps:
            c[s.result] = c.get(s.result, 0) + 1
        return c


def mask_apikey(plain: str) -> str:
    """평문 ApiKey 마스킹 — 앞 4 + 끝 4만 노출 + 길이."""
    if not plain:
        return "(empty)"
    if len(plain) <= 10:
        return f"{plain[:2]}***{plain[-2:]} (len={len(plain)})"
    return f"{plain[:4]}...{plain[-4:]} (len={len(plain)})"


def shot(page: Page, step_id: str, description: str) -> str:
    """스크린샷 저장 + 경로 반환."""
    safe = description.replace(" ", "_").replace("/", "_").replace("?", "")[:60]
    fname = f"{step_id}_{safe}.png"
    path = SCREENSHOTS / fname
    try:
        page.screenshot(path=str(path), full_page=False)
    except Exception as e:
        return f"(screenshot failed: {e})"
    return str(path.relative_to(ROOT.parent.parent)).replace("\\", "/")


@contextmanager
def chrome(
    *,
    headless: bool = True,
    storage_state: str | None = None,
    record_har: str | None = None,
) -> Iterator[tuple[Playwright, Browser, BrowserContext, Page]]:
    """Playwright Chromium 세션 컨텍스트 매니저."""
    with sync_playwright() as p:
        b = p.chromium.launch(headless=headless)
        ctx_kwargs: dict[str, Any] = {
            "viewport": VIEWPORT,
            "locale": "ko-KR",
            "ignore_https_errors": True,
        }
        if storage_state and os.path.exists(storage_state):
            ctx_kwargs["storage_state"] = storage_state
        if record_har:
            ctx_kwargs["record_har_path"] = record_har
        ctx = b.new_context(**ctx_kwargs)
        ctx.set_default_timeout(DEFAULT_TIMEOUT_MS)
        page = ctx.new_page()
        try:
            yield p, b, ctx, page
        finally:
            try:
                ctx.close()
            except Exception:
                pass
            try:
                b.close()
            except Exception:
                pass


def now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: str, data: dict[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
