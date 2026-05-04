# LibreOffice 설치 가이드

HWP/HWPX 파일을 PDF로 변환하여 파싱하기 위해 LibreOffice가 필요합니다.

## Windows 설치 방법

### 방법 1: 공식 웹사이트에서 다운로드 (권장)

1. **LibreOffice 다운로드**
   - 공식 웹사이트: https://www.libreoffice.org/download/
   - Windows 64-bit 버전 다운로드
   - 또는 직접 링크: https://www.libreoffice.org/download/download/

2. **설치**
   - 다운로드한 설치 파일(`LibreOffice_*.msi`) 실행
   - 설치 마법사 따라가기 (기본 설치 경로: `C:\Program Files\LibreOffice\`)
   - 설치 완료 후 재시작 권장

3. **설정 확인**
   - 기본 설치 경로: `C:\Program Files\LibreOffice\program\soffice.exe`
   - 또는: `C:\Program Files (x86)\LibreOffice\program\soffice.exe` (32-bit 시스템)

4. **appsettings.json 설정 (선택사항)**
   ```json
   {
     "FileUploadSettings": {
       "LibreOfficePath": "C:\\Program Files\\LibreOffice\\program\\soffice.exe"
     }
   }
   ```
   - 경로를 설정하지 않으면 자동으로 찾습니다.
   - 설치 경로가 다르면 위 설정에 경로를 지정하세요.

### 방법 2: Chocolatey 사용 (개발자용)

```powershell
# Chocolatey가 설치되어 있는 경우
choco install libreoffice
```

## Linux 설치 방법

### Ubuntu/Debian

```bash
# 패키지 업데이트
sudo apt update

# LibreOffice 설치
sudo apt install libreoffice

# 설치 확인
which libreoffice
# 출력: /usr/bin/libreoffice
```

### CentOS/RHEL/Fedora

```bash
# Fedora
sudo dnf install libreoffice

# CentOS/RHEL (EPEL 저장소 필요)
sudo yum install epel-release
sudo yum install libreoffice
```

### 설치 확인

```bash
# 버전 확인
libreoffice --version

# Headless 모드 테스트
libreoffice --headless --help
```

## macOS 설치 방법

### 방법 1: 공식 웹사이트

1. https://www.libreoffice.org/download/ 에서 macOS 버전 다운로드
2. `.dmg` 파일 실행 및 설치
3. Applications 폴더로 드래그

### 방법 2: Homebrew

```bash
brew install --cask libreoffice
```

## 설치 확인 및 테스트

### Windows (PowerShell)

```powershell
# 경로 확인
Test-Path "C:\Program Files\LibreOffice\program\soffice.exe"

# 버전 확인
& "C:\Program Files\LibreOffice\program\soffice.exe" --version

# Headless 모드 테스트
& "C:\Program Files\LibreOffice\program\soffice.exe" --headless --help
```

### Linux/Mac

```bash
# 버전 확인
libreoffice --version

# Headless 모드 테스트
libreoffice --headless --help
```

## 문제 해결

### LibreOffice를 찾을 수 없는 경우

1. **설치 확인**
   - LibreOffice가 실제로 설치되어 있는지 확인
   - 프로그램 목록에서 "LibreOffice" 검색

2. **경로 확인**
   - Windows: `C:\Program Files\LibreOffice\program\soffice.exe` 존재 여부 확인
   - Linux: `which libreoffice` 명령으로 경로 확인

3. **수동 경로 설정**
   - `appsettings.json`에 `LibreOfficePath` 설정
   - 예: `"LibreOfficePath": "C:\\Program Files\\LibreOffice\\program\\soffice.exe"`

### 변환 실패 시

1. **로그 확인**
   - 애플리케이션 로그에서 LibreOffice 오류 메시지 확인
   - `_logger.LogError` 메시지 확인

2. **권한 확인**
   - 임시 파일 생성 권한 확인
   - LibreOffice 실행 권한 확인

3. **파일 형식 확인**
   - HWP/HWPX 파일이 손상되지 않았는지 확인
   - 다른 HWP 파일로 테스트

## 성능 최적화

- **대용량 파일**: 변환에는 시간이 소요될 수 있습니다 (파일 크기에 따라 다름)
- **동시 변환**: 여러 파일을 동시에 변환하는 경우 리소스 고려
- **타임아웃**: 큰 파일의 경우 변환 시간이 오래 걸릴 수 있음

## 참고 사항

- LibreOffice는 무료 오픈소스 소프트웨어입니다
- HWP 파일 변환 품질은 파일의 복잡도에 따라 달라질 수 있습니다
- HWPX 파일은 일반적으로 더 나은 변환 품질을 제공합니다
