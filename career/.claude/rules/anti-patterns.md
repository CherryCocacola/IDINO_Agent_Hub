# IDINO Career Forbidden Patterns

이 패턴들은 IDINO Career 프로젝트에서 절대 허용되지 않는다. 발견 시 즉시 리팩터링 또는 거부.

## 1. 직접 OpenAI SDK Import

```python
# BAD — AI 서비스 외부에서 직접 OpenAI SDK 호출
from openai import AsyncOpenAI
client = AsyncOpenAI(api_key="...")

# GOOD — ai-service의 LLMService를 거쳐서만 호출
# 다른 서비스는 Kong을 경유해 ai-service의 엔드포인트를 호출
async with httpx.AsyncClient(base_url=settings.kong_gateway_url) as c:
    resp = await c.post("/api/v1/ai/recommend", json={...})
```

**Why**: LLM 호출 정책(모델 선택, 캐싱, Tool Calling, 비용 추적)을 한 곳에서만 관리.

## 2. 다른 서비스의 SQLAlchemy 모델 직접 Import

```python
# BAD — competency-service가 student-service의 ORM 모델을 직접 import
from services.student_service.app.models.student import Student

# GOOD (a) — Kong 경유 REST 호출
async with httpx.AsyncClient(base_url=settings.kong_gateway_url) as c:
    student = (await c.get(f"/api/v1/students/{student_id}")).json()

# GOOD (b) — Kafka 이벤트 구독
@consumer.on("student.created")
async def handle_student_created(event: StudentCreatedEvent):
    ...
```

**Why**: 서비스 경계를 강제. DB 스키마 변경이 다른 서비스를 깨뜨리지 않게 하려는 것.

## 3. 하드코딩된 URL/포트/시크릿

```python
# BAD
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/idino"
KONG_URL = "http://localhost:8000"
JWT_SECRET = "my-secret"

# GOOD
from app.config import settings
settings.database_url
settings.kong_gateway_url
settings.jwt_secret
```

`app/config.py`는 `pydantic.BaseSettings`로 환경변수에서만 로드한다.

## 4. 프론트엔드에서 직접 fetch / axios 인스턴스 생성

```typescript
// BAD
const res = await fetch("http://localhost:8011/api/v1/auth/login", {...})
const myAxios = axios.create({ baseURL: "..." })

// GOOD
import { authApi } from "@/lib/api/client"
const res = await authApi.post("/login", { email, password })
```

**Why**: 토큰 갱신, 에러 처리, 로깅 등이 단일 인스턴스에 통합되어 있음.

## 5. 테이블 명명 규칙 / 감사열 미준수

```python
# BAD
class StudentCompetency(Base):
    __tablename__ = "student_competency"  # tb_ 접두사 누락
    id = Column(UUID, primary_key=True)
    score = Column(Float)
    # 감사열 없음

# GOOD
class StudentCompetency(Base):
    __tablename__ = "tb_student_competency"
    id = Column(UUID, primary_key=True, default=uuid4)
    student_id = Column(String, ForeignKey("tb_student.student_id"))
    competency_cd = Column(String, ForeignKey("tb_competency.competency_cd"))
    score = Column(Float)
    ins_dt = Column(DateTime, default=datetime.utcnow, nullable=False)
    upd_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ins_user_id = Column(String, nullable=False)
```

테이블: `tb_*` 접두사. PK: `*_id`(UUID/문자열) 또는 `*_cd`(코드 문자열). 감사열 3종(`ins_dt`, `upd_dt`, `ins_user_id`)은 신규 테이블에 의무.

## 6. Bare except — 모든 예외를 삼키는 코드

```python
# BAD
try:
    result = await competency_service.calculate(student_id)
except:
    return None

# GOOD
try:
    result = await competency_service.calculate(student_id)
except CompetencyNotFoundError as e:
    logger.warning("competency not found", student_id=student_id)
    raise HTTPException(status_code=404, detail="역량 정보를 찾을 수 없습니다")
except DatabaseError as e:
    logger.error("DB error during calculation", error=str(e))
    raise HTTPException(status_code=500, detail="역량 계산 중 오류가 발생했습니다")
```

비즈니스 에러는 `HTTPException` + 한글 detail. 외부 의존 에러는 로그 + 사용자 친화 한글 메시지.

## 7. 한글 파일명 Latin-1 인코딩

```python
# BAD — Content-Disposition에서 한글 깨짐
filename = "역량평가서.pdf".encode("latin-1")
headers["Content-Disposition"] = f'attachment; filename="{filename}"'

# GOOD — RFC 5987 표준
from urllib.parse import quote
headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(filename)}"
```

## 8. snake_case / camelCase 혼용

```python
# BAD — 백엔드 코드에 camelCase
class StudentResponse(BaseModel):
    studentId: str       # 잘못됨
    careerGoal: str      # 잘못됨

# GOOD — 백엔드는 snake_case, 경계에서 alias
class StudentResponse(BaseModel):
    student_id: str = Field(alias="studentId")
    career_goal: str = Field(alias="careerGoal")
    model_config = ConfigDict(populate_by_name=True)
```

```typescript
// BAD — 프론트엔드 코드에 snake_case
const { student_id, career_goal } = data

// GOOD — 프론트엔드는 camelCase
const { studentId, careerGoal } = data
```

## 9. Alembic 마이그레이션 없는 스키마 변경

```python
# BAD — models.py만 수정하고 끝냄
class Student(Base):
    new_field = Column(String)  # 마이그레이션 없음

# GOOD — database/scripts/ 또는 Alembic 마이그레이션 추가
# 1. database/scripts/61_add_student_new_field.sql 작성
# 2. database/scripts/00_run_all.sql 에 추가
# 3. 또는 Alembic revision 생성
```

## 10. Kong 게이트웨이 우회 호출

```python
# BAD — 서비스 직접 호출 (게이트웨이 우회)
async with httpx.AsyncClient(base_url="http://student-service:8002") as c:
    ...

# GOOD — 항상 Kong 경유
async with httpx.AsyncClient(base_url=settings.kong_gateway_url) as c:
    await c.get("/api/v1/students/...")
```

**Why**: 인증, 라우팅, 레이트 리밋, 로깅이 Kong에 집중되어 있음.

## 11. Relative Import

```python
# BAD
from .service import StudentService
from ..schemas.student import StudentResponse

# GOOD
from app.services.student_service import StudentService
from app.schemas.student import StudentResponse
```

## 12. Kafka 이벤트 스키마를 서비스 내부에 정의

```python
# BAD — services/competency-service/app/schemas/events.py
class CompetencyCalculatedEvent(BaseModel):
    ...

# GOOD — shared/schemas/events.py
class CompetencyCalculatedEvent(BaseModel):
    student_id: str
    competency_cd: str
    score: float
    calculated_at: datetime
```

**Why**: 발행자와 구독자가 같은 스키마를 import해야 계약이 깨지지 않음. shared에만 정의.
