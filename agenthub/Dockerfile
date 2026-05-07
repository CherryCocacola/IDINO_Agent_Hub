# =============================================================================
# AgentHub - Multi-stage Docker 빌드
# ---------------------------------------------------------------------------
# Stage 1 (build): .NET 8 SDK + Node.js 20 → dotnet publish 가
#   ClientApp 의 npm install + vite build 를 PublishRunWebpack target 으로
#   자동 수행하고 dist/ 산출물을 wwwroot/ 로 복사한다 (.csproj:55-66 참조).
# Stage 2 (runtime): ASP.NET 8 + curl(헬스체크용) — Kestrel 만으로 부팅.
#   IIS InProcess 호스팅 설정(.csproj:10) 은 Linux 환경에서 자동 무시됨.
# =============================================================================

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build

# Node.js 20 설치 (dotnet publish 가 npm install + vite build 를 호출)
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# .csproj 만 먼저 복사하여 dotnet restore 캐시 레이어 확보. 같은 디렉토리의
# .sln 파일이 함께 복사되면 dotnet 이 솔루션 빌드를 우선 선택해 NETSDK1194
# (--output 옵션 미지원) 경고가 발생하므로 .csproj 만 명시 복사 + 명시 빌드.
COPY AIAgentManagement.csproj ./
RUN dotnet restore AIAgentManagement.csproj

# 나머지 소스 복사 (.dockerignore 가 bin/obj/wwwroot/node_modules 제외)
COPY . ./

# Production 빌드 + publish (wwwroot 자동 생성). .csproj 명시로 .sln 우선 선택을
# 차단하여 NETSDK1194 경고 제거.
RUN dotnet publish AIAgentManagement.csproj -c Release -o /app/publish --no-restore /p:UseAppHost=false


FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime

# 헬스체크용 curl + CA 번들. LibreOffice/한글 폰트는 시연 범위 밖이라 미설치
# (PPTX↔PDF 변환을 사용하려면 별도 stage 또는 추가 apt 설치 필요).
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=build /app/publish ./

EXPOSE 8080
ENV ASPNETCORE_URLS=http://+:8080
ENV ASPNETCORE_ENVIRONMENT=Production
ENV DOTNET_RUNNING_IN_CONTAINER=true

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=5 \
    CMD curl -fsS http://localhost:8080/swagger >/dev/null || exit 1

ENTRYPOINT ["dotnet", "AIAgentManagement.dll"]
