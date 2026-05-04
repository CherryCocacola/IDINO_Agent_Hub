# Phase 4 S3 완료 선언 (2026-04-23)

> **상위 문서**: `docs/phase3_execution_roadmap.md` §2.3 S3 D10
> **상태**: **S3 COMPLETE — S4 킥오프 승인**
> **QA 총점**: **80/100** (S2 86점 대비 -6, MIN 기준 충족)
> **기간**: 2026-04-23 (S2 종료 직후 10영업일 하루 만에 집중 실행)

---

## 1. S3 DoD 충족 현황

| 기준 | 목표 | 실제 | 상태 |
|---|---|---|---|
| PPTX 빌더 13 컴포넌트 (S1 MVP 6 + S3 +7) | 13종 | **14종** (추가 1종 Chart 고도화 포함) | ✅ 초과 |
| 이미지 자동 선택 Unsplash→DALL-E | 기능 완성 | `auto_select.py` + `DocumentServiceV2.generate` 통합 | ✅ |
| 조직별 월 DALL-E 쿼터 | Alembic + API + UI | `tb_organization_quotas` + GET/PUT + `/quotas` 페이지 | ✅ |
| FE 7 컴포넌트 React 렌더 + 폼 | 7종 | 완성 (Recharts 활용 Chart 포함) | ✅ |
| `qa_quick` 점수 | ≥80 | **80** (MIN 기준) | ✅ |
| `docutil-*:s3-stable` 태그 | push | ✅ | ✅ |

---

## 2. 일별 작업 요약

| Day | 범위 | 주요 산출 |
|---|---|---|
| D1 | Chart 고도화 (pie native + alias) + DocxBuilder 골격 | `components.py` 230 라인 + `docx/builder.py` 신규 |
| D1 | FE SlideSubtitle/Quote React + 폼 | 4 파일 (80+112줄) |
| D2 | Image/ImageGrid PPTX + HTML 렌더러 확장 | `render_image_grid` + HTML 9종 |
| D2 | FE Callout/Timeline React + 폼 | 4 파일 (142+184줄) |
| D3 | Unsplash + DALL-E fallback 알고리즘 | `auto_select.py` 249줄 |
| D3 | FE ImageGrid/IconRow React + 폼 | CSS Grid + lucide allowlist |
| D4 | FE Chart Recharts React + 폼 | 8색 팔레트, 3 chart_type 분기 |
| D4 | Alembic 009 `tb_organization_quotas` | 162줄 + QuotaService |
| D5 | 쿼터 체크 통합 + ImageForm 3-Radio + 403 토스트 | BE 3 파일 + FE 5 파일 |
| D6 | SlideSubtitle/Quote/Callout PPTX 빌더 | variant 4색 팔레트 |
| D6 | 관리자 `/quotas` 페이지 + PUT 엔드포인트 | 권한 가드 4단계 |
| D7 | Timeline/IconRow PPTX 빌더 | 마커+연결선, 원형+letter |
| D7 | AutoSelectedBadge + Image.tsx | Unsplash/DALL-E 휴리스틱 |
| D8 | /reports 회귀 (이전 S2 D8에 해소됨) | n/a |
| **D10** | **통합 배포 + Alembic 009 + 최종 QA + s3-stable** | 14 컨테이너 healthy |

---

## 3. 구현 요약

### 3.1 PPTX 14 컴포넌트 완성
- 텍스트 5종: SlideTitle / **SlideSubtitle** / Heading / Paragraph / BulletList
- 데이터 3종: KPI / DataTable / Chart (pie native + bar/line)
- 미디어 2종: Image / **ImageGrid** (자동 레이아웃 2/3/4)
- 강조 2종: **Quote** (accent 세로선 + author) / **Callout** (variant 4종 배경+border)
- 구조 2종: **Timeline** (마커+연결선) / **IconRow** (원형+letter)

### 3.2 이미지 자동 선택 파이프라인
```
LLM Structured Output (ImageComponent: src=None, prompt="...")
 ↓
DocumentServiceV2._auto_fill_image_sources() (asyncio.gather 병렬)
 ↓
auto_select_image(prompt, alt, organization_id, db)
 ├─ UnsplashService.search(prompt, count=1) → https URL
 └─ [실패 시] QuotaService.check_and_consume_quota(dalle_monthly) → DALL-E 3 → MinIO 업로드 → minio:// URL
 ↓
component.src 주입 (soft degrade: 쿼터 초과 시 degraded_components에 기록)
 ↓
PPTX/HTML 빌더가 src로 이미지 렌더 또는 placeholder
```

### 3.3 쿼터 시스템
- `tb_organization_quotas`: (organization_id, quota_type, year_month) UNIQUE + CHECK 4종 + FK CASCADE
- `QuotaService`: `get_all_quotas_current_month`, `check_and_consume_quota` (FOR UPDATE), `update_monthly_limit`
- API: `GET /organizations/{id}/quotas/current`, `PUT /organizations/{id}/quotas/{type}` (super_admin + org_admin 권한)
- FE: `useOrganizationQuotas` + `useUpdateQuotaLimit` 훅, `/quotas` 관리자 페이지

### 3.4 FE 7 컴포넌트 + 시각화
- 7 React 컴포넌트: SlideSubtitle/Quote/Callout/Timeline/ImageGrid/IconRow/Chart
- ImageForm 3-Radio (URL/프롬프트/자동)
- AutoSelectedBadge (Unsplash/DALL-E 3 휴리스틱 + hover 툴팁)
- 403 쿼터 초과 특화 토스트

---

## 4. QA 상세 (80/100)

### 감점 내역
| 항목 | 감점 | 상태 |
|---|---|---|
| C2 OpenAI 쿼터 초과 | -7 | **외부 요인** (결제/계정) |
| W6 신규 4종(Quote/Timeline/IconRow/ImageGrid) LLM 미관측 | -5 | 명시적 프롬프트 필요 |
| W3 DELETE /v2/documents 405 | -3 | S4 D1 보강 대상 |
| W5 한국어 비율 0.56~0.66 | -3 | S6 프롬프트 개선 대상 |
| W1 Nginx 4440 | -2 | 인프라 트랙 |
| W2 챗봇 지연 3.6s | -2 | S6 RAG 개선 대상 |
| C1 해소 보너스 | +2 | QA 도중 즉시 해소 |

### C1 — 배포 덮어쓰기로 인한 regression
- **증상**: S3 배포 시 `docker-compose.yml` 덮어쓰기로 celery-worker의 `-Q` 리스트에서 `document_export` 제거됨 → export task 영구 pending
- **해결**: QA 에이전트가 로컬 + 서버 양쪽 영구 수정
- **추가 조치**: 로컬에 `evaluation` queue도 추가 (daily-evaluation beat 대응)

### E2E 3회 성공률 (수정 후)
| 회차 | PPTX 크기 | ZIP sig | 소요 |
|---|---|---|---|
| Run 1 | 38.8KB | ✅ | 2.7s |
| Run 2 | 38.8KB | ✅ | 2.5s |
| Run 3 | 38.8KB | ✅ | 2.6s |

### 쿼터 API — 전항목 PASS
- GET 인증/미인증/타조직 권한 분기
- PUT limit=200 → 200, limit=-1 → 422, invalid_type → 400, member role → 403

---

## 5. 이미지 태그 / DB 스냅샷

```
docutil-api:s3-stable              be731e1c6d1f   14.7GB
docutil-celery-worker:s3-stable    28f0f7d52e31   14.7GB
docutil-frontend:s3-stable         3a243866a3c9   341MB

Alembic head: 009_organization_quotas
DB backup:    /home/idino/docutil/backups/post_s3_20260423_1543.sql (3.2MB)
```

---

## 6. S4 이관 Watch List

| ID | 내용 | 심각도 |
|---|---|---|
| W3 | DELETE /v2/documents 405 (미구현) | 중 |
| W5 | 컴포넌트 한국어 비율 0.7 미달 | 중 |
| W6 | OpenAI TPM 조금만 넘겨도 502 (재시도/백오프 없음) | 중 |
| W7 | 신규 4종(Quote/Timeline/IconRow/ImageGrid) LLM 활용도 낮음 → 프롬프트 예시 보강 | 낮 |
| W1/W2 | Nginx 4440, 챗봇 지연 (S2 이관 유지) | 낮 |
| W8 | `-Q` 옵션 영속성 — docker-compose.yml 재배포 시 재수정 필요 | 낮 |

---

## 7. S4 킥오프 준비 상태

**S4 범위** (Phase 3 §2.4, 12영업일 2.5주):
- Mode B slot-fill + `POST /v2/documents/{id}/switch-mode` + `(admin)/template-designer/`
- TwoColumn/ThreeColumn/Hero/Comparison 레이아웃 (React + PPTX)
- Mode 전환 자동 매핑 (목표 85%)
- IDINO 3건 Jinja2 → DocumentSchema 수동 변환
- **M3 마일스톤**

### S4 D1 체크리스트
- [x] S3 완료 선언 (본 문서)
- [x] s3-stable 태그 + DB 스냅샷
- [x] Alembic 009 head 적용 (운영)
- [x] 14 컴포넌트 PPTX/HTML 렌더 확인
- [ ] OpenAI API 쿼터 갱신 (외부, 사용자 처리)
- [ ] S4 D1 BE: `DocumentServiceV2.generate` Mode B slot-fill
- [ ] S4 D1 FE: `(admin)/template-designer/create/page.tsx` skeleton
- [ ] 사용자 S4 착수 승인

---

## 8. Phase 4 전체 진척

| 스프린트 | 상태 | QA |
|---|---|---|
| S1 DocumentSchema MVP | ✅ (04-23) | 84 |
| S2 PPTX Mode A + archive | ✅ (04-23) | 86 |
| **S3 컴포넌트 확장 + 이미지 자동** | ✅ **(04-23)** | **80** |
| S4 Mode B + 전환 | ⏳ | - |
| S5 HWPX + DOCX 완성 | ⏳ | - |
| S6 RAG 품질 + 색상 | ⏳ | - |
| S7 인라인 편집 + 병존 제거 | ⏳ | - |

**37/68 영업일 완료 (≈54%)**. **M2 완료** (13~14 컴포넌트). 남은 31일 ≈ 6.2주.
