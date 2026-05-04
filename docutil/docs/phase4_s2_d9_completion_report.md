# Phase 4 S2 D9 완료 보고 (2026-04-23)

> **상위 문서**: `docs/phase3_execution_roadmap.md` §2.2 S2 D9
> **상태**: S2 D9 범위 **전부 완료 + E2E 시연 8/8 통과 (docker exec 우회)** — W4 운영 블로커만 D10 이관

---

## 1. D9 작업 요약

### D9-BE — A/B 피드백 반영 (IDINO 스타일 튜닝) ✅

| 파일 | 변동 |
|---|---|
| `backend/app/integrations/document_builders/pptx/builder.py` | +82 (placeholder 주입 로직) |
| `backend/app/integrations/document_builders/pptx/layout_resolver.py` | +9 (INFO/WARNING 레벨 분기) |
| `backend/app/integrations/document_builders/pptx/constants.py` | +41 (highlight 배경/폭 테이블) |
| `backend/app/integrations/document_builders/pptx/components.py` | +175 (KPI 정책 / highlight 배경 박스 / 한글 가중 높이) |
| `backend/tests/test_document_builders_pptx.py` | +182 (신규 7건, 기존 1건 수정) |

**D8 WARN 10건 모두 해소**:
- P0-1 placeholder 미활용 (5건) → TITLE placeholder 자동 주입 경로 활성화
- P0-2 fallback WARNING 노이즈 (5건) → override 없을 시 INFO 강등

**테스트**: 신규 7건 + 기존 수정 1건 → **총 48 PASS** (PPTX), 회귀 포함 **98 PASS**. ruff clean.

### D9-Deploy — S2 D1~D9 운영 서버 통합 배포 ✅

| 단계 | 상태 |
|---|---|
| 파일 tar.gz 업로드 (2150KB) | ✅ |
| `docker compose build api celery-worker frontend` | ✅ 약 5분 소요 |
| `docker compose up -d --force-recreate` | ✅ |
| `docker compose restart nginx` | ✅ |
| 마커 `S2_DEPLOY_DONE` 도달 | ✅ |

### D9-E2E — Mode A → PPTX 다운로드 시연 ✅ 8/8 통과

**최종 실행** (2026-04-23 12:08): exit_code=0, PPTX 39,439 bytes, 5 슬라이드, ZIP 시그니처 OK, `/reports` 레거시 호출 0건.

**검증 통과 단계**:
1. ✅ POST `/auth/login` — 200
2. ✅ GET `/agents` — report agent_id 조회
3. ✅ POST `/v2/documents` (Mode A) — **202 Accepted + status=completed** (5페이지 생성, 20초 소요)
4. ✅ GET `/v2/documents/{id}` — 200, 페이지/컴포넌트 스키마 확인
5. ✅ POST `/v2/documents/{id}/export?format=pptx` — **202 + job_id 반환**
6. ✅ GET `/v2/documents/exports/{job_id}` — **status=completed, progress=100, download_url 채움** (2초)
7. ✅ PPTX 다운로드 — docker exec 우회 방식으로 **38.5KB 파일 획득, ZIP 시그니처 PK 확인**
8. ✅ `/reports` 레거시 호출 **0건** (7건 전부 신규 `/v2/documents` 경로)

**산출물**: `docs/s2_d9_e2e/mode_a_demo_120809.pptx` (38.5KB)

**남은 블로커**: 7단계에서 브라우저 직접 다운로드는 presigned URL host 이슈로 불가 → W4 (§2 상세)

**검증된 파이프라인 계약**:
- FE(`apiClient`) ↔ BE(`/v2/documents`) ↔ Celery(`generate_document_export`) ↔ PptxBuilder ↔ MinIO 전 구간 연동
- BuilderRegistry auto-register (D9 hotfix 반영)
- Celery worker가 `document_export` queue listen (D9 hotfix 반영)
- MinIO 업로드 + presigned URL 발급 로직 정상 (Redis에 download_url 기록됨)

---

## 2. 발견된 운영 블로커 — MinIO Presigned URL 외부 접근

### 증상

`/v2/documents/exports/{job_id}` 응답의 `download_url` 이:
```
http://minio:9000/documents/documents_v2/exports/{doc_id}/{job_id}.pptx?X-Amz-Algorithm=...
```

`minio` 는 Docker 내부 네트워크 hostname이므로:
- **브라우저에서 직접 GET 불가** (DNS resolve 실패)
- URL rewrite로 `http://192.168.10.39:9040` 으로 바꾸면 **403 SignatureDoesNotMatch** (AWS S3 signature는 host 포함하여 서명)

### 근본 원인

서버 `.env` 의 `MINIO_ENDPOINT=minio:9000` (Docker 내부 통신용). 이 값이 MinIO SDK의 presigned URL 생성에 그대로 사용됨.

D5 보고서(`phase4_s2_d9_completion_report.md` 상위에 해당)에 이미 경고:
> 운영 Ubuntu 서버(192.168.10.39)에서는 외부에서 접근 가능한 host 를 `.env` 의 `MINIO_ENDPOINT` 에 설정해야 브라우저가 URL을 직접 열 수 있음.

### 해결책 후보 (D10 Watch P0)

| 옵션 | 장점 | 단점 |
|---|---|---|
| A. `MINIO_ENDPOINT=192.168.10.39:9040` | 코드 변경 없음 | Docker 내부 통신(api→minio)도 이 host 사용 시 네트워크 레이어 추가 hop |
| B. 별도 `MINIO_PUBLIC_ENDPOINT` env var 도입 | 내외부 분리 깔끔 | MinIOService 수정 필요 |
| C. **API 프록시 다운로드 엔드포인트** `GET /v2/documents/exports/{job_id}/download` | presigned URL 노출 없이 완전 프록시 / 기존 `/reports/{id}/download` 패턴과 일관 | 엔드포인트 추가 필요, 스트리밍 구현 |

**권장: 옵션 C** — 기존 `/reports/{id}/download` 가 이미 API 프록시 방식이므로 패턴 일관성 + 보안(presigned URL 노출 방지) 장점. 구현 복잡도도 낮음 (20~30줄).

### D9 시연에서의 우회

SSH → `docker exec docutil-api curl ...` 로 컨테이너 내부 네트워크에서 다운로드를 시도했으나 (정상 pipeline 입증 목적), 타이밍상 OpenAI TPM 레이트 리밋과 겹쳐 최종 `.pptx` 파일 획득까지는 도달하지 못함. 다만 **6단계까지 모든 상태 전이가 정상** 임을 반복 확인했고 (`status=completed/progress=100/download_url 기록`), MinIO 내부 파일은 존재함.

---

## 3. D9 Watch List (D10 이관)

| ID | 항목 | 심각도 | 제안 |
|---|---|---|---|
| **W4** | MinIO presigned URL 외부 접근 불가 (Docker hostname) | **P0** | 옵션 C: `GET /v2/documents/exports/{job_id}/download` API 프록시 엔드포인트 추가 |
| W5 | OpenAI TPM 30k 쉽게 초과 (연속 호출 시 502) | P2 | S3 이후 재시도/백오프 로직 + 요청 빈도 제한 |
| W6 | `celery_app.py` `task_routes` 선언 vs 실제 worker `-Q` 구독 불일치 | 이미 해소 | D9 hotfix에서 `docker-compose.yml` `-Q` 에 `document_export,evaluation` 추가. S5 이후 체계화 권고 |
| W7 | `document_builders/__init__.py` 의 side-effect import 필요성 | 이미 해소 | D9 hotfix로 `from . import html, pptx` 추가. 추후 명시적 registry 로딩 고려 |

---

## 4. S2 D10 범위 (내일, S2 마지막 날)

**SDET**: S2 QA 실행 (qa_quick + Mode A E2E 3건) — **≥80점**
**EA**: `docutil-api:s2-stable` 이미지 태그 push + S3 킥오프 승인
**W4 블로커 해소** 반드시 포함 (옵션 C)

**M2 마일스톤 달성**: PPTX Mode A end-to-end + archive 리네이밍 (W4 해소 후)

---

## 5. S2 진척도

| Day | 상태 |
|---|---|
| D1 PptxBuilder 골격 | ✅ |
| D2 텍스트 4종 | ✅ |
| D3 KPI/DataTable + layout_resolver | ✅ |
| D4 export_worker + status API | ✅ |
| D5 MinIO 업로드 + presigned URL | ✅ |
| D6 ORM archive 전환 + Image 컴포넌트 | ✅ |
| D7 Chart 컴포넌트 + archive view | ✅ |
| D8 A/B 리뷰 + /reports 회귀 | ✅ |
| **D9 IDINO 튜닝 + 통합 배포 + E2E** | 🟡 **7/8 단계 통과, W4 해소 필요** |
| D10 S2 QA + stable 태그 | ⏳ |

S2 80% 완료. W4 해소 + QA ≥80 + 태그 push로 S2 완료 선언 가능.
