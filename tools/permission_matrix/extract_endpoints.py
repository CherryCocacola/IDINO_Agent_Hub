"""트랙 #105 Phase B.1 — DocUtil + AgentHub endpoint 카탈로그 자동 추출.

산출물:
- user_mig/track105_endpoint_catalog.json : 모든 endpoint × 허용 role 목록
- user_mig/track105_endpoint_catalog.md   : 사람이 읽을 수 있는 요약

DocUtil:
- `docutil/backend/app/modules/*/router.py` 전 18 파일
- Python AST 로 함수별 `@router.{method}(path)` 데코레이터 + `Depends(...)` 추적
- 헬퍼 변수 (`_require_member = require_role([...])`) 매핑 후 화이트리스트 해석

AgentHub:
- `agenthub/Controllers/*.cs` 전 41 파일
- 정규식으로 클래스 레벨 [Authorize(Roles=...)] / [AllowAnonymous] + 메서드 레벨 [Http*] + [Route] 추출
- 클래스 [Route] 의 prefix 도 결합
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DOCUTIL_MODULES = ROOT / "docutil" / "backend" / "app" / "modules"
AGENTHUB_CONTROLLERS = ROOT / "agenthub" / "Controllers"
OUT_JSON = ROOT / "user_mig" / "track105_endpoint_catalog.json"
OUT_MD = ROOT / "user_mig" / "track105_endpoint_catalog.md"

# DocUtil 의 router prefix (app/main.py 또는 application factory 참조)
# 기본 mount 는 /api/v1 + module-specific prefix 일 가능성. 일단 router 내부 path 만 추출하고 prefix 는 별도 메타로 보관.
DOCUTIL_PREFIX = "/api/v1"


# ---------------------------------------------------------------------------
# DocUtil — Python AST 추출
# ---------------------------------------------------------------------------


def _node_to_list_of_str(node: ast.AST | None) -> list[str]:
    """ast.List of ast.Constant(str) → list[str]. 아니면 빈 리스트."""
    if not isinstance(node, ast.List):
        return []
    out: list[str] = []
    for elt in node.elts:
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
            out.append(elt.value)
    return out


def _extract_require_role_helpers(tree: ast.Module) -> dict[str, list[str]]:
    """모듈 레벨 `_require_xxx = require_role([...])` 추출.

    반환: helper_name → 허용 role 리스트
    """
    helpers: dict[str, list[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        if not name.startswith("_require"):
            continue
        if not (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "require_role"
        ):
            continue
        if node.value.args:
            helpers[name] = _node_to_list_of_str(node.value.args[0])
    return helpers


def _resolve_depends(default_value: ast.AST, helpers: dict[str, list[str]]) -> list[str] | None:
    """함수 인자의 기본값이 `Depends(...)` 형태일 때, 안의 require_role 화이트리스트 해석.

    매칭 패턴:
    - `Depends(_require_member)` → helpers["_require_member"]
    - `Depends(require_role(["super_admin","admin"]))` → 즉시 해석
    - `Depends(require_role([...]))` 인자가 다른 형태 → []
    - 그 외 → None (require_role 미사용)
    """
    if not (
        isinstance(default_value, ast.Call)
        and isinstance(default_value.func, ast.Name)
        and default_value.func.id == "Depends"
    ):
        return None
    if not default_value.args:
        return None
    arg = default_value.args[0]
    # Depends(_require_xxx)
    if isinstance(arg, ast.Name) and arg.id in helpers:
        return helpers[arg.id]
    # Depends(require_role([...]))
    if (
        isinstance(arg, ast.Call)
        and isinstance(arg.func, ast.Name)
        and arg.func.id == "require_role"
        and arg.args
    ):
        return _node_to_list_of_str(arg.args[0])
    return None


def extract_docutil_router(path: Path) -> list[dict[str, Any]]:
    """단일 router.py 에서 endpoint 추출."""
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        print(f"  [WARN] parse 실패: {path} — {e}", file=sys.stderr)
        return []
    helpers = _extract_require_role_helpers(tree)
    module = path.parent.name

    endpoints: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # 데코레이터에서 method + path 추출
        for deco in node.decorator_list:
            if not isinstance(deco, ast.Call):
                continue
            # @router.get("/path") / @router.post(...) ...
            if not (
                isinstance(deco.func, ast.Attribute)
                and isinstance(deco.func.value, ast.Name)
                and deco.func.value.id == "router"
            ):
                continue
            method = deco.func.attr.upper()
            if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue
            if not deco.args or not isinstance(deco.args[0], ast.Constant):
                continue
            path_str = deco.args[0].value
            if not isinstance(path_str, str):
                continue

            # 함수 인자에서 Depends(require_role(...)) 또는 Depends(_require_xxx) 추적
            roles: list[str] | None = None
            helper_name: str | None = None
            args_all = list(node.args.args) + list(node.args.kwonlyargs)
            defaults_all = list(node.args.defaults) + list(node.args.kw_defaults)
            # zip 가 정렬되지 않으므로 인자별로 default 매칭. FastAPI 는 보통 kwonly 가 아닌 default 만 사용.
            # 단순화: 함수 본체와 인자 default 둘 다 훑어 require_role 호출 detect.
            for default in node.args.defaults + node.args.kw_defaults:
                if default is None:
                    continue
                resolved = _resolve_depends(default, helpers)
                if resolved is not None:
                    roles = resolved
                    if isinstance(default, ast.Call) and isinstance(default.args[0], ast.Name):
                        helper_name = default.args[0].id
                    break

            endpoints.append(
                {
                    "system": "docutil",
                    "module": module,
                    "function": node.name,
                    "method": method,
                    "path": path_str,
                    "full_path": DOCUTIL_PREFIX + path_str,
                    "roles": roles,  # None = 인증만 (require_role 미사용)
                    "helper": helper_name,
                    "source_file": str(path.relative_to(ROOT)),
                    "line": node.lineno,
                }
            )
    return endpoints


# ---------------------------------------------------------------------------
# AgentHub — 정규식 추출
# ---------------------------------------------------------------------------

# 클래스 레벨 어트리뷰트 + class 선언
CLASS_RE = re.compile(
    r"((?:\[[^\]]+\]\s*)*)public\s+(?:partial\s+)?class\s+(\w+)\s*:\s*\w+",
    re.MULTILINE,
)
# 메서드 어트리뷰트 + method 선언 (public, async/non-async, ActionResult 등)
METHOD_RE = re.compile(
    r"((?:\[[^\]]+\]\s*)+)\s*public\s+(?:async\s+)?(?:[\w<>,\s\?]+?)\s+(\w+)\s*\(",
    re.MULTILINE,
)
ROUTE_RE = re.compile(r"\[Route\(\s*\"([^\"]*)\"\s*\)\]")
HTTP_METHOD_RE = re.compile(r"\[Http(Get|Post|Put|Patch|Delete)(?:\(\s*\"([^\"]*)\"\s*\))?\]")
AUTHORIZE_RE = re.compile(r"\[Authorize(?:\(\s*([^)]*)\s*\))?\]")
ALLOW_ANON_RE = re.compile(r"\[AllowAnonymous\]")
ROLES_PARAM_RE = re.compile(r"Roles\s*=\s*\"([^\"]+)\"")
POLICY_PARAM_RE = re.compile(r"Policy\s*=\s*\"([^\"]+)\"")


def _normalize_route(prefix: str | None, route: str | None, controller: str) -> str:
    """class [Route(prefix)] + method [Http*("/sub")] 또는 [Route(...)] 결합."""

    def expand(r: str | None) -> str:
        if r is None:
            return ""
        r = r.strip()
        # [controller] 토큰 → 클래스명에서 'Controller' 제거
        ctrl_name = controller
        if ctrl_name.endswith("Controller"):
            ctrl_name = ctrl_name[: -len("Controller")]
        r = r.replace("[controller]", ctrl_name.lower())
        r = r.replace("[action]", "")
        return r

    p = expand(prefix)
    r = expand(route)
    if not p and not r:
        return "/" + (controller.replace("Controller", "").lower())
    if not p:
        return "/" + r.lstrip("/")
    if not r:
        return "/" + p.lstrip("/")
    if r.startswith("/") or r.startswith("~"):
        return "/" + r.lstrip("~/")
    return "/" + p.lstrip("/").rstrip("/") + "/" + r.lstrip("/")


def _parse_authorize(class_attrs: str, method_attrs: str) -> dict[str, Any]:
    """[Authorize] / [AllowAnonymous] / Roles="..." 해석."""
    # 메서드 레벨이 우선
    if ALLOW_ANON_RE.search(method_attrs):
        return {"auth": "anonymous", "roles": [], "policy": None}

    auth = "none"
    roles: list[str] = []
    policy: str | None = None
    auth_match = AUTHORIZE_RE.search(method_attrs) or AUTHORIZE_RE.search(class_attrs)
    if auth_match:
        auth = "authenticated"
        inner = auth_match.group(1) or ""
        rm = ROLES_PARAM_RE.search(inner)
        if rm:
            roles = [r.strip() for r in rm.group(1).split(",") if r.strip()]
        pm = POLICY_PARAM_RE.search(inner)
        if pm:
            policy = pm.group(1).strip()
    # 클래스 [AllowAnonymous] (드물지만 가능)
    if auth == "none" and ALLOW_ANON_RE.search(class_attrs):
        auth = "anonymous"
    return {"auth": auth, "roles": roles, "policy": policy}


def extract_agenthub_controller(path: Path) -> list[dict[str, Any]]:
    src = path.read_text(encoding="utf-8", errors="replace")
    cm = CLASS_RE.search(src)
    if not cm:
        return []
    class_attrs = cm.group(1) or ""
    controller = cm.group(2)
    class_route_m = ROUTE_RE.search(class_attrs)
    class_route = class_route_m.group(1) if class_route_m else None
    endpoints: list[dict[str, Any]] = []

    for mm in METHOD_RE.finditer(src):
        method_attrs = mm.group(1)
        method_name = mm.group(2)
        # constructor 제외
        if method_name == controller:
            continue
        http_match = HTTP_METHOD_RE.search(method_attrs)
        if not http_match:
            continue
        http_method = http_match.group(1).upper()
        route_in_http = http_match.group(2)
        # 메서드의 [Route("...")] (드물지만 있음)
        route_m = ROUTE_RE.search(method_attrs)
        method_route = route_m.group(1) if route_m else route_in_http

        full_path = _normalize_route(class_route, method_route, controller)
        auth = _parse_authorize(class_attrs, method_attrs)
        endpoints.append(
            {
                "system": "agenthub",
                "controller": controller,
                "method": method_name,
                "http_method": http_method,
                "path": full_path,
                "auth": auth["auth"],
                "roles": auth["roles"],
                "policy": auth["policy"],
                "source_file": str(path.relative_to(ROOT)),
                "line": src[: mm.start()].count("\n") + 1,
            }
        )
    return endpoints


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

    docutil_endpoints: list[dict[str, Any]] = []
    for router_file in sorted(DOCUTIL_MODULES.glob("*/router.py")):
        eps = extract_docutil_router(router_file)
        docutil_endpoints.extend(eps)
        print(f"  [docutil] {router_file.parent.name:20s} {len(eps):3d} endpoints")

    agenthub_endpoints: list[dict[str, Any]] = []
    for ctrl_file in sorted(AGENTHUB_CONTROLLERS.glob("*.cs")):
        eps = extract_agenthub_controller(ctrl_file)
        agenthub_endpoints.extend(eps)
        print(f"  [agenthub] {ctrl_file.stem:40s} {len(eps):3d} endpoints")

    catalog = {
        "extracted_at": "2026-05-20",
        "track": "#105 Phase B.1",
        "docutil": {
            "total": len(docutil_endpoints),
            "endpoints": docutil_endpoints,
        },
        "agenthub": {
            "total": len(agenthub_endpoints),
            "endpoints": agenthub_endpoints,
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[JSON] {OUT_JSON.relative_to(ROOT)} ({OUT_JSON.stat().st_size:,} bytes)")

    # 사람용 요약
    lines: list[str] = []
    lines.append("# 트랙 #105 Phase B.1 — endpoint 카탈로그 자동 추출 결과\n")
    lines.append(f"**추출일**: {catalog['extracted_at']}\n")
    lines.append(f"**DocUtil 총 endpoint**: {catalog['docutil']['total']}\n")
    lines.append(f"**AgentHub 총 endpoint**: {catalog['agenthub']['total']}\n\n---\n\n")

    # DocUtil module 별 요약 + 'user' 누락 잠재 결함 표시
    lines.append("## DocUtil endpoint (module 별)\n\n")
    by_module: dict[str, list[dict[str, Any]]] = {}
    for ep in docutil_endpoints:
        by_module.setdefault(ep["module"], []).append(ep)
    lines.append("| Module | endpoint 수 | require_role 미사용 | 'user' 포함 (member 기준) | 결함 후보 |\n")
    lines.append("|---|---|---|---|---|\n")
    for module in sorted(by_module):
        eps = by_module[module]
        no_role = sum(1 for e in eps if e["roles"] is None)
        # _require_member 헬퍼를 사용하는 endpoint 가 있는데 'user' 가 빠진 케이스
        member_eps = [e for e in eps if e.get("helper") and "member" in e["helper"]]
        if member_eps:
            has_user = "user" in (member_eps[0]["roles"] or [])
            user_status = "✓" if has_user else "✗ (결함 후보)"
        else:
            has_user = None
            user_status = "—"
        defect = "⚠️" if (member_eps and not has_user) else ""
        lines.append(
            f"| {module} | {len(eps)} | {no_role} | {user_status} | {defect} |\n"
        )
    lines.append("\n")

    # AgentHub controller 별 요약
    lines.append("## AgentHub endpoint (controller 별)\n\n")
    by_controller: dict[str, list[dict[str, Any]]] = {}
    for ep in agenthub_endpoints:
        by_controller.setdefault(ep["controller"], []).append(ep)
    lines.append("| Controller | endpoint 수 | auth | Roles |\n")
    lines.append("|---|---|---|---|\n")
    for ctrl in sorted(by_controller):
        eps = by_controller[ctrl]
        auths = set(e["auth"] for e in eps)
        roles_set = set()
        for e in eps:
            for r in e["roles"]:
                roles_set.add(r)
        lines.append(
            f"| {ctrl} | {len(eps)} | {','.join(sorted(auths))} | {','.join(sorted(roles_set)) or '—'} |\n"
        )
    lines.append("\n")

    # 'user' 누락 잠재 결함 상세 목록
    lines.append("## 'user' role 누락 잠재 결함 (DocUtil)\n\n")
    lines.append(
        "트랙 #104 fix 패턴 ('member' 가 있는 helper 에는 'user' 도 함께 포함되어야 함) 기준.\n"
        "본 트랙 #105 Phase A 진단으로 projects/reports/search_scopes/templates 4 router fix 완료.\n\n"
    )
    lines.append("| Module | helper | roles | 'user' 포함? | 비고 |\n")
    lines.append("|---|---|---|---|---|\n")
    seen_helpers: set[tuple[str, str]] = set()
    for ep in docutil_endpoints:
        helper = ep.get("helper")
        if not helper:
            continue
        if "member" not in helper and "reader" not in helper:
            continue
        key = (ep["module"], helper)
        if key in seen_helpers:
            continue
        seen_helpers.add(key)
        roles = ep["roles"] or []
        has_user = "user" in roles
        note = "✓ fix 완료" if has_user else "⚠️ 결함 후보"
        lines.append(
            f"| {ep['module']} | {helper} | {','.join(roles)} | {'✓' if has_user else '✗'} | {note} |\n"
        )
    lines.append("\n")

    OUT_MD.write_text("".join(lines), encoding="utf-8")
    print(f"[MD]   {OUT_MD.relative_to(ROOT)} ({OUT_MD.stat().st_size:,} bytes)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
