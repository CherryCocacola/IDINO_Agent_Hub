"""Phase 4 S1 D7 후속 — H11 + D6 프롬프트 개선 후 재검증.

수정본 (schema_adapter.py / constants.py) 을 서버에 업로드 후
docutil-api 컨테이너에서 pytest 로 실 OpenAI API 를 호출하여
H11 (strict 결함) 및 D6 (프롬프트 개선) 효과를 검증한다.

본 스크립트는 ``run_s1_d7_live_api.py`` 의 축소판이다.

변경점:
    - FILES_TO_SYNC 최소화 (schema_adapter.py + constants.py 만)
    - pytest -k 로 ``openai and (minutes or proposal)`` 만 선택 (5 호출)
    - 리포트 파일명에 ``revalidation`` 접미사
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import paramiko

SERVER = "192.168.10.39"
USER = "idino"
PASS = os.environ.get("DOCUTIL_SERVER_PASS", "dkdlelsh@12")

LOCAL_ROOT = Path(r"D:\workspace\document_utilization")
REMOTE_DIR = "/home/idino/docutil"

# H11 + D6 수정 대상 파일만. live 테스트 자체는 서버에 이미 올라가 있다고 가정하되,
# 안전을 위해 함께 동기화한다.
FILES_TO_SYNC = [
    "backend/app/integrations/llm/schema_adapter.py",
    "backend/app/modules/documents_v2/constants.py",
    "backend/tests/test_llm_live_providers.py",
    "backend/tests/test_llm_structured_cross_provider.py",
]


def main() -> int:
    print("=== Phase 4 S1 D7 후속: H11 + D6 재검증 ===")
    print(f"- 서버: {USER}@{SERVER}")
    print()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("[1/5] SSH 접속 중...")
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)
    print("  OK")

    # ------------------------------------------------------------------
    # 2) 파일 업로드 (호스트)
    # ------------------------------------------------------------------
    print("[2/5] 파일 업로드...")
    sftp = ssh.open_sftp()
    for rel in FILES_TO_SYNC:
        local = LOCAL_ROOT / rel.replace("/", os.sep)
        if not local.exists():
            print(f"  SKIP (not found): {rel}")
            continue
        remote_host_path = f"{REMOTE_DIR}/{rel}"
        remote_dir = os.path.dirname(remote_host_path)
        _mkdir_p_ssh(ssh, remote_dir)
        sftp.put(str(local), remote_host_path)
        print(f"  UPLOADED: {rel}")
    sftp.close()

    # ------------------------------------------------------------------
    # 3) 컨테이너 내 /app 으로 복사 + 서비스 재시작
    # ------------------------------------------------------------------
    print("[3/5] 컨테이너로 복사 + API 재시작...")
    for rel in FILES_TO_SYNC:
        src = f"{REMOTE_DIR}/{rel}"
        if rel.startswith("backend/"):
            container_path = "/app/" + rel[len("backend/") :]
        else:
            container_path = "/app/" + rel
        cmd = f"docker cp {src} docutil-api:{container_path}"
        _run_and_log(ssh, cmd)
        # celery 워커도 같은 코드베이스를 사용
        cmd2 = f"docker cp {src} docutil-celery-worker:{container_path} 2>/dev/null || true"
        _run_and_log(ssh, cmd2)

    # API 재시작 (schema_adapter 변경은 import 시점에 로드되므로 필요)
    _run_and_log(ssh, "docker exec docutil-api pkill -HUP -f uvicorn 2>/dev/null || true")

    # ------------------------------------------------------------------
    # 4) pytest 실행 (live_api, openai + minutes/proposal 만)
    # ------------------------------------------------------------------
    print("[4/5] 컨테이너에서 pytest 실행 (OpenAI minutes+proposal 만, 최대 5 호출)...")
    # 5 호출 재검증: minutes × 3 + proposal × 2 = 5 (상한).
    # openai 만 활성, 그 외는 env 미설정으로 자동 skip.
    pytest_cmd = (
        "docker exec -w /app "
        "-e PYTHONIOENCODING=utf-8 "
        "-e LIVE_API_ENABLED=1 "
        "docutil-api "
        "pytest tests/test_llm_live_providers.py -m live_api "
        "-k \"openai and (minutes or proposal)\" "
        "-rs --tb=short -v"
    )
    rc, out = _run_and_log(ssh, pytest_cmd, capture=True, timeout_s=1800)
    print(f"  pytest exit code: {rc}")

    # ------------------------------------------------------------------
    # 5) 리포트 회수
    # ------------------------------------------------------------------
    print("[5/5] 리포트 회수...")
    date_tag = time.strftime("%Y%m%d")

    reports_to_fetch = [
        f"/app/tests/qa_reports/{date_tag}_s1_d7_live_api_metrics.json",
        f"/app/tests/qa_reports/{date_tag}_s1_d7_live_api_report.md",
    ]
    local_reports_dir = LOCAL_ROOT / "backend" / "tests" / "qa_reports"
    local_reports_dir.mkdir(parents=True, exist_ok=True)
    log_path = local_reports_dir / f"{date_tag}_s1_d7_revalidation_pytest.log"
    log_path.write_text(out or "", encoding="utf-8")
    print(f"  pytest 로그 저장: {log_path}")

    sftp = ssh.open_sftp()
    for container_path in reports_to_fetch:
        remote_host_path = f"/tmp/{Path(container_path).name}"
        cp_cmd = f"docker cp docutil-api:{container_path} {remote_host_path}"
        rc2, _ = _run_and_log(ssh, cp_cmd)
        if rc2 != 0:
            print(f"  SKIP (not produced): {container_path}")
            continue
        # 재검증 리포트임을 알 수 있도록 revalidation 접미사로 로컬 저장.
        local_name = Path(container_path).name.replace(
            "_live_api_", "_revalidation_"
        )
        local_path = local_reports_dir / local_name
        try:
            sftp.get(remote_host_path, str(local_path))
            print(f"  FETCHED: {local_path}")
        except Exception as exc:  # noqa: BLE001
            print(f"  FETCH FAIL: {container_path} ({exc})")
    sftp.close()

    ssh.close()
    print("\n=== 완료 ===")
    return rc


def _safe_write(s: str) -> None:
    try:
        sys.stdout.write(s)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "ascii"
        sys.stdout.write(s.encode(enc, errors="replace").decode(enc, errors="replace"))


def _run_and_log(
    ssh: paramiko.SSHClient,
    cmd: str,
    *,
    capture: bool = False,
    timeout_s: int = 120,
) -> tuple[int, str]:
    print(f"  $ {cmd}")
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout_s)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if out:
        _safe_write(out)
    if err:
        _safe_write(err)
    if capture:
        return exit_code, out + ("\n--- STDERR ---\n" + err if err else "")
    return exit_code, ""


def _mkdir_p_ssh(ssh: paramiko.SSHClient, remote_dir: str) -> None:
    cmd = f"mkdir -p {remote_dir}"
    ssh.exec_command(cmd)


if __name__ == "__main__":
    sys.exit(main())
