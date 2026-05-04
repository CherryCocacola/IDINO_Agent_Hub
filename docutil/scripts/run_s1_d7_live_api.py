"""Phase 4 S1 D7 Part 2 — 서버 docutil-api 컨테이너에서 실 LLM API 검증 실행.

동작:
    1. 로컬의 신규 파일 2개 (test_llm_live_providers.py, pyproject.toml) 와
       router/schemas/main 변경분을 컨테이너에 복사.
    2. docker exec 로 pytest 실행 (-m live_api, LIVE_API_ENABLED=1).
    3. 결과 로그 + qa_reports/20260419_s1_d7_live_api_*.{json,md} 를
       로컬로 회수한다.

사전 조건:
    - 서버 192.168.10.39 docutil-api 컨테이너에 프로바이더별 API 키
      환경변수가 이미 주입되어 있어야 한다 (.env 파일).
"""

from __future__ import annotations

import io
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

FILES_TO_SYNC = [
    # Part 1 변경분
    "backend/app/main.py",
    "backend/app/modules/documents_v2/__init__.py",
    "backend/app/modules/documents_v2/constants.py",
    "backend/app/modules/documents_v2/exceptions.py",
    "backend/app/modules/documents_v2/models.py",
    "backend/app/modules/documents_v2/router.py",
    "backend/app/modules/documents_v2/schemas.py",
    "backend/app/modules/documents_v2/service.py",
    "backend/app/modules/documents_v2/utils.py",
    # LLM integration 레이어도 동기화 (D5 완성본이 서버에 없을 수 있음)
    "backend/app/integrations/llm/__init__.py",
    "backend/app/integrations/llm/azure_client.py",
    "backend/app/integrations/llm/claude_client.py",
    "backend/app/integrations/llm/client.py",
    "backend/app/integrations/llm/factory.py",
    "backend/app/integrations/llm/gemini_client.py",
    "backend/app/integrations/llm/schema_adapter.py",
    "backend/pyproject.toml",
    # Part 2 신규 파일
    "backend/tests/test_llm_live_providers.py",
]


def main() -> int:
    print("=== Phase 4 S1 D7 Part 2: 서버 실 API 검증 ===")
    print(f"- 서버: {USER}@{SERVER}")
    print(f"- 로컬 루트: {LOCAL_ROOT}")
    print()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("[1/5] SSH 접속 중...")
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)
    print("  OK")

    # ------------------------------------------------------------------
    # 2) 파일 업로드 (호스트) + 컨테이너 내부로 복사
    # ------------------------------------------------------------------
    print("[2/5] 파일 업로드...")
    sftp = ssh.open_sftp()
    for rel in FILES_TO_SYNC:
        local = LOCAL_ROOT / rel.replace("/", os.sep)
        if not local.exists():
            print(f"  SKIP (not found): {rel}")
            continue
        remote_host_path = f"{REMOTE_DIR}/{rel}"
        # 원격 디렉토리 생성 보장
        remote_dir = os.path.dirname(remote_host_path)
        _mkdir_p_ssh(ssh, remote_dir)
        sftp.put(str(local), remote_host_path)
        print(f"  UPLOADED: {rel}")
    sftp.close()

    # 컨테이너 내 /app 으로 복사
    print("[3/5] 컨테이너로 복사 (docker cp)...")

    # 컨테이너에 tests 디렉토리 없으므로 먼저 생성.
    _run_and_log(ssh, "docker exec docutil-api mkdir -p /app/tests/qa_reports")

    # 각 업로드 파일을 동일 경로로 컨테이너에 복사.
    _run_and_log(
        ssh, "docker exec docutil-api mkdir -p /app/app/modules/documents_v2"
    )
    _run_and_log(
        ssh, "docker exec docutil-api mkdir -p /app/app/integrations/llm"
    )
    for rel in FILES_TO_SYNC:
        src = f"{REMOTE_DIR}/{rel}"
        # backend/ prefix 를 벗겨 /app/... 경로로 매핑. pyproject.toml 은 /app/pyproject.toml.
        if rel == "backend/pyproject.toml":
            container_path = "/app/pyproject.toml"
        elif rel.startswith("backend/"):
            container_path = "/app/" + rel[len("backend/"):]
        else:
            container_path = "/app/" + rel
        cmd = f"docker cp {src} docutil-api:{container_path}"
        _run_and_log(ssh, cmd)

    # tests/__init__.py 빈 파일 생성 (패키지 인식).
    _run_and_log(ssh, "docker exec docutil-api touch /app/tests/__init__.py")

    # ------------------------------------------------------------------
    # 4) pytest 실행 (live_api)
    # ------------------------------------------------------------------
    print("[4/5] 컨테이너에서 pytest 실행...")
    pytest_cmd = (
        "docker exec -w /app "
        "-e PYTHONIOENCODING=utf-8 "
        "-e LIVE_API_ENABLED=1 "
        "docutil-api "
        "pytest tests/test_llm_live_providers.py -m live_api -rs --tb=short -v"
    )
    rc, out = _run_and_log(ssh, pytest_cmd, capture=True, timeout_s=1800)
    print(f"  pytest exit code: {rc}")

    # ------------------------------------------------------------------
    # 5) 리포트 회수
    # ------------------------------------------------------------------
    print("[5/5] 리포트 회수...")
    date_tag = time.strftime("%Y%m%d")

    # 컨테이너 내부 qa_reports 를 호스트로 복사 후 sftp 로 로컬 이동.
    reports_to_fetch = [
        f"/app/tests/qa_reports/{date_tag}_s1_d7_live_api_metrics.json",
        f"/app/tests/qa_reports/{date_tag}_s1_d7_live_api_report.md",
    ]
    local_reports_dir = LOCAL_ROOT / "backend" / "tests" / "qa_reports"
    local_reports_dir.mkdir(parents=True, exist_ok=True)
    # pytest 로그 자체도 로컬에 저장
    log_path = local_reports_dir / f"{date_tag}_s1_d7_live_api_pytest.log"
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
        local_path = local_reports_dir / Path(container_path).name
        try:
            sftp.get(remote_host_path, str(local_path))
            print(f"  FETCHED: {local_path}")
        except Exception as exc:  # noqa: BLE001
            print(f"  FETCH FAIL: {container_path} ({exc})")
    sftp.close()

    ssh.close()
    print("\n=== 완료 ===")
    return rc


# ---------------------------------------------------------------------------
# SSH 헬퍼
# ---------------------------------------------------------------------------


def _safe_write(s: str) -> None:
    """CP949 등 제한된 스트림에서도 안전하게 출력한다."""
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
