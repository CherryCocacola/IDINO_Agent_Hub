"""S2 D1~D9 통합 배포: 파일 업로드 + api/celery/frontend 재빌드 (setsid).

deploy_to_server.py 의 1~5단계(압축·전송·해제·MinIO 이미지 수정) 수행 후,
빌드 단계는 setsid 백그라운드로 분리하여 paramiko PipeTimeout 회피.
완료 감지는 _poll_s2_build.py 로 polling.
"""
from __future__ import annotations

import io
import os
import sys
import tarfile
import time
from pathlib import Path

import paramiko

SERVER = "192.168.10.39"
USER = "idino"
PASS = os.environ.get("DOCUTIL_SERVER_PASS", "dkdlelsh@12")
LOCAL_PATH = Path(r"D:\workspace\document_utilization")
REMOTE_DIR = "/home/idino/docutil"

EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".next", ".claude",
    "sample_templates", "test-results", "playwright-report",
    "e2e-screenshots", "backups",
}
EXCLUDE_USERMIG_EXT = {".png", ".pptx", ".pdf"}


def should_exclude(arcname: str) -> bool:
    if arcname.endswith(".pyc"):
        return True
    parts = arcname.replace("\\", "/").split("/")
    if "user_mig" in parts:
        _, ext = os.path.splitext(arcname)
        if ext.lower() in EXCLUDE_USERMIG_EXT:
            return True
    return False


def main() -> int:
    # 1. 압축
    print("=== 1. 프로젝트 tar.gz 생성 ===")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for root, dirs, files in os.walk(LOCAL_PATH):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    arcname = os.path.relpath(fpath, LOCAL_PATH)
                except ValueError:
                    continue
                if should_exclude(arcname):
                    continue
                try:
                    fsize = os.path.getsize(fpath)
                except (OSError, ValueError):
                    continue
                if fsize > 10 * 1024 * 1024:
                    continue
                try:
                    tar.add(fpath, arcname=arcname)
                except (PermissionError, OSError):
                    pass
    buf.seek(0)
    data = buf.getvalue()
    print(f"  압축 크기: {len(data) / 1024:.0f}KB")

    # 2. SSH 접속
    print("\n=== 2. 서버 접속 ===")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)
    print("  접속 OK")

    # 3. SFTP 전송
    print("\n=== 3. 파일 전송 ===")
    sftp = ssh.open_sftp()
    with sftp.file("/tmp/docutil_s2_deploy.tar.gz", "wb") as f:
        f.write(data)
    sftp.close()
    print("  전송 완료")

    # 4. 압축 해제
    print("\n=== 4. 압축 해제 ===")
    _, so, _ = ssh.exec_command(
        f"mkdir -p {REMOTE_DIR} && cd {REMOTE_DIR} && tar xzf /tmp/docutil_s2_deploy.tar.gz && echo EXTRACT_OK",
        timeout=120,
    )
    print(" ", so.read().decode(errors="replace").strip())

    # 5. MinIO 이미지 버전 보정
    print("\n=== 5. MinIO 이미지 버전 보정 ===")
    _, so, _ = ssh.exec_command(
        f"cd {REMOTE_DIR} && sed -i "
        "'s|image: minio/minio:latest|image: quay.io/minio/minio:RELEASE.2023-09-04T19-57-37Z|' "
        "docker-compose.yml && echo MINIO_FIX_OK",
        timeout=10,
    )
    print(" ", so.read().decode(errors="replace").strip())

    # 6. setsid 백그라운드로 api+celery+frontend 빌드
    print("\n=== 6. 빌드 (setsid 백그라운드) ===")
    build_cmd = (
        f"cd {REMOTE_DIR} && "
        "( "
        "echo '=== s2 build start ===' && "
        "docker compose build api celery-worker frontend && "
        "echo '=== s2 build ok ===' && "
        "docker compose up -d --force-recreate api celery-worker frontend && "
        "echo '=== s2 up ok ===' && "
        "sleep 10 && "
        "docker compose restart nginx && "
        "echo S2_DEPLOY_DONE "
        ") || echo S2_DEPLOY_FAIL"
    )
    escaped = build_cmd.replace("'", "'\"'\"'")
    remote = (
        "rm -f /tmp/s2_build.log && "
        f"setsid bash -c '{escaped}' > /tmp/s2_build.log 2>&1 < /dev/null &"
    )
    ssh.exec_command(remote, timeout=10)
    time.sleep(3)
    _, so, _ = ssh.exec_command(
        "pgrep -af 'docker compose build api' | head -3",
        timeout=10,
    )
    print("  빌드 프로세스:", so.read().decode(errors="replace").strip() or "(시작 실패)")

    # 7. 로그 초기 확인
    _, so, _ = ssh.exec_command("head -5 /tmp/s2_build.log 2>&1", timeout=10)
    print("  로그 초기:\n", so.read().decode(errors="replace"))

    ssh.close()
    print("\n[detach 완료] polling: scripts/_poll_s2_build.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
