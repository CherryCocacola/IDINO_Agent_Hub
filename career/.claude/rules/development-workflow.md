# IDINO Career Development Workflow

마이크로서비스 신규 추가/변경 시 표준 절차.

## 새 마이크로서비스 추가 체크리스트

새 서비스를 추가할 때 아래 순서대로 작업한다. enterprise-architect와 backend-specialist 에이전트에 위임 권장.

1. **포트 할당**: `8001~8020` 범위 내 미사용 포트 선택. `infrastructure/docker/docker-compose.yml`의 모든 포트를 확인.
2. **디렉토리 생성**: `services/{service-name}/` (kebab-case)
3. **표준 파일 작성** (architecture.md P2 참조):
   - [ ] `app/__init__.py`
   - [ ] `app/main.py` — FastAPI 앱 + lifespan + 라우터 등록 + Prometheus 메트릭
   - [ ] `app/config.py` — pydantic Settings, env에서 로드
   - [ ] `app/database.py` — `shared/database/connection.py`의 세션 의존성 재export (DB 사용 시)
   - [ ] `app/routers/` — 엔드포인트 정의
   - [ ] `app/schemas/` — Pydantic 모델
   - [ ] `app/services/` — 비즈니스 로직
   - [ ] `app/models/` — SQLAlchemy ORM (DB 사용 시)
   - [ ] `app/exceptions.py` — 서비스 고유 예외
4. **인프라 등록**:
   - [ ] `infrastructure/docker/docker-compose.yml`에 서비스 정의 추가 (이미지, 포트, env, depends_on)
   - [ ] `gateway/kong.yml`에 라우팅 추가 (`/api/v1/{service-prefix}` → `service-name:port`)
   - [ ] `Dockerfile` 작성 (다른 서비스 패턴 복사)
5. **DB 변경**: 새 테이블이 필요하면 `database/scripts/{nn}_seed_*.sql` 또는 마이그레이션 파일 추가, `00_run_all.sql`에 등록
6. **테스트**: `services/{service-name}/tests/` 디렉토리 생성 후 단위 테스트 1건 이상 작성
7. **프론트엔드 통합** (필요 시):
   - [ ] `frontend/lib/api/{service}.ts` 생성
   - [ ] `frontend/lib/api/client.ts`에 새 axios 인스턴스 추가
   - [ ] `frontend/types/`에 TypeScript 타입 정의

## 기능 추가 (기존 서비스 내)

1. 작업할 서비스 이름 식별 → CLAUDE.md §2의 backend-specialist 에이전트에 위임
2. 수정할 파일 미리 읽기 (Read 도구)
3. 의존성 방향 확인 — Router → Service → Repository/Client
4. 스키마 먼저 정의: `schemas/`에 요청/응답 Pydantic 모델
5. 라우터 → 서비스 → (필요 시) 리포지토리/클라이언트 순으로 구현
6. **한글 주석 작성** (CLAUDE.md §3 의무)
7. sdet-agent 호출하여 테스트 작성
8. `ruff check . && ruff format .`
9. 변경 요약을 한글로 보고

## DB 스키마 변경

```
1. database/scripts/{nn}_{description}.sql 작성
   - 새 번호는 마지막 파일 번호 + 1
2. database/scripts/00_run_all.sql에 등록
3. 영향받는 서비스의 models/와 schemas/ 동기화
4. 변경된 모델에 의존하는 다른 서비스가 있는지 grep으로 점검
5. (선택) Alembic 마이그레이션 사용 시 backend/alembic 패턴 따라 revision 생성
6. tests/integration에 마이그레이션 검증 테스트 추가
```

database-architect 에이전트에 위임 권장.

## Kafka 이벤트 추가

```
1. shared/schemas/events.py에 Pydantic 이벤트 모델 정의
   class ResourceActionEvent(BaseModel):
       resource_id: str
       triggered_at: datetime
       ...
2. 발행 측 서비스: services/{publisher}/app/services/에서
   producer = KafkaProducer.get_instance()
   await producer.send("resource.action", event)
3. 구독 측 서비스: services/{consumer}/app/main.py의 lifespan에서
   consumer.subscribe("resource.action", handler)
4. 이벤트 스키마 호환성 정책: 신규 필드는 Optional, 필드 삭제 금지(deprecate)
```

## 프론트엔드 기능 추가

frontend-specialist 에이전트에 위임.

```
1. types/{service}.ts에 응답 타입 정의 (백엔드 스키마와 1:1)
2. lib/api/{service}.ts에 API 함수 추가 — apiClient 사용
3. hooks/use{Feature}.ts에 React Query 훅 (필요 시)
4. components/sections/{FeatureSection}.tsx에 섹션 컴포넌트
5. components/ui/는 UI 원자만 (도메인 로직 금지)
6. 백엔드 snake_case ↔ 프론트 camelCase 매핑은 lib/api/{service}.ts에서 수행
7. e2e/{feature}.spec.ts에 Playwright 테스트
```

## 코드 리뷰 기준

### 필수 통과 (MUST)
- [ ] architecture.md P2 모듈 구조 준수
- [ ] architecture.md P3 의존성 방향 위반 없음
- [ ] anti-patterns.md 12가지 금지 패턴 위반 없음
- [ ] 한글 주석 작성됨 (함수/클래스/복잡한 로직)
- [ ] 테스트 통과 (관련 모듈)
- [ ] `ruff check` / `ruff format` 통과
- [ ] 시크릿/하드코딩된 URL 없음
- [ ] DB 스키마 변경 시 마이그레이션 동반

### 권장 (SHOULD)
- [ ] Pydantic v2 모델 사용 (`model_config = ConfigDict(...)`)
- [ ] 비동기 일관성 (`async def` 함수에서 동기 IO 차단 호출 회피)
- [ ] 에러 메시지가 한글이며 사용자 친화적
- [ ] 새 엔드포인트에 OpenAPI tags/summary 작성
- [ ] 프론트 boundary에서 snake_case ↔ camelCase 매핑 명시적

## 세션 간 일관성 유지

- 진행 중인 큰 작업은 `EnterPlanMode`로 한글 계획서를 작성해 사용자 승인을 받는다
- 미완성 코드에는 `# TODO(idino): 설명` 주석을 남겨 다음 세션이 이어받을 수 있게 한다
- 설계 결정의 이유(why)를 주석 또는 커밋 메시지에 기록
- 도메인 용어는 `domain-model.md`의 정의를 정확히 따른다 (동의어 혼용 금지)

## 빠른 명령어 모음

```powershell
# 전체 환경 기동 (Windows)
docker compose -f infrastructure/docker/docker-compose.yml up -d

# 특정 서비스 재시작
docker compose -f infrastructure/docker/docker-compose.yml restart auth-service

# 서비스 로그 확인
docker compose -f infrastructure/docker/docker-compose.yml logs -f competency-service

# 백엔드 린트 (서비스별)
cd services/auth-service; ruff check .; ruff format .

# 프론트엔드 빌드 검증
cd frontend; npx tsc --noEmit; npm run build

# DB 시드 재실행
psql -h localhost -U postgres -d idino_career -f database/scripts/00_run_all.sql
```
