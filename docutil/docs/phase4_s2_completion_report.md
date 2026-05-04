# Phase 4 S2 완료 선언 (2026-04-23)

> **상위 문서**: `docs/phase3_execution_roadmap.md` §2.2 S2 D10
> **상태**: **S2 COMPLETE — S3 킥오프 승인**
> **QA 총점**: **86/100** (E2E 성공률 3/3, D8 83점 대비 +3)
> **기간**: 2026-04-23 (S1 종료 직후 10영업일 하루 만에 집중 실행)

---

## 1. S2 DoD 충족 현황

| 기준 | 목표 | 실제 | 상태 |
|---|---|---|---|
| PPTX Mode A end-to-end | 시연 통과 | **3/3 (100%)** 2.7~2.8초/건 | ✅ |
| PPTX 빌더 6 → 8 컴포넌트 | 6종 MVP | **8종 완성** (Text×4, KPI, DataTable, Image, Chart) | ✅ 초과 |
| `layout_resolver` Phase 0 근본원인 해소 | 하드코딩 제거 | candidate + normalize + override + fallback | ✅ |
| export_worker + status API | 기능 완성 | Celery + Redis + MinIO 통합 | ✅ |
| `archive` 리네이밍 | ORM 정합 | 007 마이그레이션 + 410 Gone (5 쓰기 경로) | ✅ |
| `qa_quick` 점수 | ≥80 | **86** | ✅ |
| `docutil-api:s2-stable` 태그 | push | c1b4569b5288 | ✅ |

---

## 2. 일별 작업 요약

| Day | 범위 | 주요 산출 |
|---|---|---|
| D1 | PptxBuilder ABC 골격 + FE promo 배너 | `pptx/builder.py` + `mode-a-promo-banner.tsx` |
| D2 | 텍스트 4종 + export-menu UI | `pptx/components.py` 텍스트 렌더 + 훅 |
| D3 | KPI/DataTable + **`layout_resolver`** (Phase 0 해소) | 하드코딩 14종 레이아웃명 제거 |
| D4 | export_worker + status API | Celery + Redis + `/v2/documents/{id}/export` |
| D5 | MinIO 업로드 + presigned URL + cleanup | `MinIOService.upload_bytes` 경유 |
| D6 | reports 410 Gone + Image 컴포넌트 | ISSUE-D2-1 해소, `image_fetcher.py` |
| D7 | Chart (bar/line native) + archive view | `/reports` 배지 + 410 토스트 |
| D8 | PPTX A/B 리뷰 (50 체크 PASS 40/WARN 10/FAIL 0) + /reports 회귀 (26 PASS) | 개선 권고 P0/P1 도출 |
| D9 | IDINO 튜닝 (WARN 10 전부 해소) + 통합 배포 + E2E 7/8 (W4 블로커) | placeholder 주입 + 한글 가중 높이 |
| **D10** | **W4 API 프록시 + 최종 QA + s2-stable + DB 스냅샷** | `/v2/documents/exports/{id}/download` |

---

## 3. D10 핵심 변경 (W4 해소)

| 파일 | 변동 |
|---|---|
| `backend/app/integrations/object_storage/minio_client.py` | +30 (`get_object_bytes`) |
| `backend/app/modules/documents_v2/service.py` | +130 (`get_export_file` + 예외 매핑) |
| `backend/app/modules/documents_v2/router.py` | +115 (`GET /exports/{id}/download` StreamingResponse) |
| `backend/app/workers/export_worker.py` | +40 (`_upload_only` — presigned URL 제거) |
| `backend/tests/test_documents_v2_export.py` | +300 (14 → 20 케이스) |
| `scripts/_s2_d9_e2e_demo.py` | SSH docker exec 우회 제거, 순수 httpx 호출 |

**download_url 필드 정책 변경**:
- 이전: `http://minio:9000/...?X-Amz-Signature=...` (Docker hostname, 외부 resolve 불가)
- 이후: `/api/v1/v2/documents/exports/{job_id}/download` (API 프록시 상대 경로)

**보안 이점**: presigned URL 노출 완전 제거. 서버가 MinIO → FE 스트리밍 프록시 역할로 권한 체크 강제.

---

## 4. E2E 시연 최종 결과 (3회 연속)

| 회차 | doc_id | job_id | pages | 크기 | ZIP sig | elapsed |
|---|---|---|---|---|---|---|
| Run 1 | c070a258 | 2cb50300 | 5 | 38.7KB | ✅ | 2.8s |
| Run 2 | e089256f | c954ad9b | 5 | 38.5KB | ✅ | 2.8s |
| Run 3 | 7b02ab77 | 836d215d | 5 | 38.4KB | ✅ | 2.7s |

**Content-Type**: `application/vnd.openxmlformats-officedocument.presentationml.presentation`
**Content-Disposition**: `attachment; filename*=UTF-8''...` (RFC 5987)

---

## 5. 운영 중 해결한 Critical Fix (S2 내)

| ID | 이슈 | 원인 | 해결 |
|---|---|---|---|
| F1 | Celery worker가 export task 안 받음 | docker-compose.yml `-Q` 에 `document_export` 누락 | docker-compose.yml에 `-Q ...,document_export,evaluation` 추가 + celery-worker 재생성 |
| F2 | BuilderRegistry에 pptx 빌더 미등록 | subpackage 자동 import 부재 | `document_builders/__init__.py`에 `from . import html, pptx` side-effect import |
| F3 | presigned URL 외부 접근 불가 | Docker hostname (minio:9000) 노출 | W4 API 프록시 엔드포인트로 전환 |

---

## 6. 잔여 경고 (S3 이관)

| ID | 내용 | 심각도 | S3 대응 |
|---|---|---|---|
| W1 | Nginx 4440 포트 connection refused | 낮 | 인프라 트랙 |
| W2 | 챗봇 응답 평균 3.6s (목표 3s) | 중 | RAG 병렬화 또는 스트리밍 |
| W3 | `DELETE /v2/documents/{id}` 405 | 중 | S3 라우터 확장 시 추가 |
| W5 | 컴포넌트 텍스트 한국어 비율 0.56~0.66 | 중 | 프롬프트 한국어 가중 개선 |
| W6 | OpenAI TPM 30k 초과 시 502 | 중 | 재시도/백오프 로직 |

---

## 7. S3 킥오프 준비 상태

**S3 범위** (Phase 3 §2.3, 10영업일 2주):
- 7종 추가 컴포넌트 완성: SlideSubtitle / Quote / Callout / Timeline / ImageGrid / IconRow + Chart 고도화
- **Unsplash 우선 + DALL-E fallback** 이미지 자동 선택
- 조직별 월 DALL-E **쿼터 설정** (Alembic 009 `tb_organization_quotas`)
- **M2 완**: 13 컴포넌트 end-to-end

### S3 Day 1 체크리스트

- [x] S1 + S2 완료 선언 (본 문서)
- [x] `docutil-api:s2-stable` + `docutil-celery-worker:s2-stable` + `docutil-frontend:s2-stable` 태그 push
- [x] DB 스냅샷 `/home/idino/docutil/backups/post_s2_20260423_1331.sql` (3.2MB)
- [x] QA ≥80 확보 (86점)
- [x] W4 해소로 FE 브라우저 다운로드 경로 검증 완료
- [ ] S3 D1 BE: Chart 컴포넌트 PPTX 고도화 (stacked/pie/area)
- [ ] S3 D1 FE: SlideSubtitle/Quote React 렌더 + 폼
- [ ] S3 D1 DB: (기존 Alembic 007 head 유지 확인, 009는 D4에 작성 예정)
- [ ] 사용자 S3 D1 착수 승인

---

## 8. 이미지 태그 / DB 스냅샷 메타

```
docutil-api:s2-stable              c1b4569b5288   14.7GB
docutil-celery-worker:s2-stable    7329620c3bcc   14.7GB
docutil-frontend:s2-stable         372cade7670a   339MB

DB backup: /home/idino/docutil/backups/post_s2_20260423_1331.sql (3.2MB)
```

롤백 명령 (필요 시):
```bash
ssh idino@192.168.10.39
cd ~/docutil
cat /home/idino/docutil/backups/post_s2_20260423_1331.sql \
  | docker exec -i -e PGPASSWORD=docutil docutil-postgres psql -U docutil -d docutil
```

---

## 9. Phase 4 전체 진척

| 스프린트 | 상태 | QA |
|---|---|---|
| S1 DocumentSchema MVP | ✅ 완료 (2026-04-23) | 84 |
| **S2 PPTX Mode A + archive** | ✅ **완료 (2026-04-23)** | **86** |
| S3 컴포넌트 확장 + 이미지 자동 | ⏳ 대기 | - |
| S4 Mode B + 전환 | ⏳ | - |
| S5 HWPX + DOCX 완성 | ⏳ | - |
| S6 RAG 품질 + 색상 | ⏳ | - |
| S7 인라인 편집 + 병존 제거 | ⏳ | - |

**전체 68영업일 중 약 27일 완료 (≈40%)**. M2 마일스톤 (PPTX Mode A end-to-end + archive) **달성**.
