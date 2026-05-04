"""프로젝트 파일을 Ubuntu 서버로 전송하는 스크립트."""
import paramiko
import tarfile
import io
import os

SERVER = "192.168.10.39"
USER = "idino"
PASS = "dkdlelsh@12"
LOCAL_PATH = r"D:\workspace\document_utilization"
REMOTE_DIR = "/home/idino/docutil"

# 제외할 디렉토리
EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".next", ".claude",
    "sample_templates", "test-results", "playwright-report",
    "e2e-screenshots",
}

# 제외할 파일 확장자 (user_mig 내)
EXCLUDE_USERMIG_EXT = {".png", ".pptx", ".pdf"}


def should_exclude(arcname):
    """전송에서 제외할 파일인지 판단한다."""
    if arcname.endswith(".pyc"):
        return True
    parts = arcname.replace("\\", "/").split("/")
    if "user_mig" in parts:
        _, ext = os.path.splitext(arcname)
        if ext.lower() in EXCLUDE_USERMIG_EXT:
            return True
    return False


def main():
    # 1. tar.gz 생성
    print("=== 1. 프로젝트 압축 중 ===")
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
    print("=== 2. 서버 접속 ===")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASS, timeout=15)
    print("  접속 성공")

    # 3. SFTP 전송
    print("=== 3. 파일 전송 ===")
    sftp = ssh.open_sftp()
    with sftp.file("/tmp/docutil_deploy.tar.gz", "wb") as f:
        f.write(data)
    sftp.close()
    print("  전송 완료")

    # 4. 압축 해제
    print("=== 4. 압축 해제 ===")
    _, stdout, _ = ssh.exec_command(
        f"mkdir -p {REMOTE_DIR} && cd {REMOTE_DIR} && tar xzf /tmp/docutil_deploy.tar.gz && echo EXTRACT_OK"
    )
    print(stdout.read().decode().strip())

    # 5. MinIO 이미지 수정 (서버 CPU 호환)
    print("=== 5. MinIO 이미지 수정 ===")
    _, stdout, _ = ssh.exec_command(
        f"cd {REMOTE_DIR} && sed -i "
        "'s|image: minio/minio:latest|image: quay.io/minio/minio:RELEASE.2023-09-04T19-57-37Z|' "
        "docker-compose.yml && echo MINIO_FIX_OK"
    )
    print(stdout.read().decode().strip())

    # 6. API + Celery 빌드
    print("=== 6. API + Celery 빌드 ===")
    _, stdout, stderr = ssh.exec_command(
        f"cd {REMOTE_DIR} && docker compose up -d --build api celery-worker 2>&1",
        timeout=600,
    )
    output = stdout.read().decode("utf-8", errors="replace")
    print(output[-300:] if len(output) > 300 else output)

    # 7. Nginx 재시작 (API upstream 연결 갱신)
    print("=== 7. Nginx 재시작 ===")
    _, stdout, _ = ssh.exec_command(
        f"cd {REMOTE_DIR} && docker compose restart nginx 2>&1",
        timeout=30,
    )
    print(stdout.read().decode("utf-8", errors="replace").strip())

    # 8. 헬스 체크
    print("=== 8. 헬스 체크 ===")
    import time
    for attempt in range(6):
        time.sleep(10)
        _, stdout, _ = ssh.exec_command(
            "docker exec docutil-api curl -sf http://localhost:8000/health 2>&1"
        )
        result = stdout.read().decode().strip()
        if result:
            print(f"  API healthy (attempt {attempt + 1})")
            break
    else:
        print("  WARNING: API health check failed after 60s")

    # 9. 파일 확인
    print("=== 9. 배포된 파일 ===")
    _, stdout, _ = ssh.exec_command(f"ls {REMOTE_DIR}/")
    print(stdout.read().decode().strip())

    ssh.close()
    print("=== 배포 완료 ===")


if __name__ == "__main__":
    main()
