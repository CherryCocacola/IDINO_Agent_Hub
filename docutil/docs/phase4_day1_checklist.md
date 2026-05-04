# Phase 4 Day 1 체크리스트 — 2026-04-21 착수 예정

> **상위 문서**: `docs/phase3_execution_roadmap.md` §6
> **사용법**: Phase 4 S1 D1 아침 팀 점검용. 14항목 모두 체크 완료 시 S1 D1 작업 즉시 착수 가능.
> **통과 기준**: 14/14. 누락 1건이라도 있으면 해당 항목 해소 후 재검토.

---

## 준비 상태 확인 (문서·환경·데이터)

- [ ] **1. S0 조사 결과 이해**
  - `docs/s0_inventory_report.md` §0 핵심 발견 8건 숙지
  - 조직 1건(아이디노), 템플릿 3건, `tb_report_templates` 0건, MinIO 0 파일, Alembic head=006_evaluation

- [ ] **2. Phase 1~3 최신 버전 확인**
  - `phase1_decisions.md` **v1.2**
  - `phase2_transition_plan.md` **v1.1**
  - `phase1_architecture.md` **v1.6**
  - `phase3_execution_roadmap.md` **v1.0**

- [ ] **3. 개발 환경 정상 구동 (Windows)**
  ```bash
  cd D:\workspace\document_utilization
  docker compose up -d
  docker compose ps  # 14 컨테이너 정상 확인
  curl http://localhost:8040/api/v1/health  # 200 응답 확인
  ```

- [ ] **4. Ubuntu 서버 접속 확인**
  ```bash
  ssh idino@192.168.10.39 "docker ps --format 'table {{.Names}}\t{{.Status}}'"
  # 14 컨테이너 Up 상태 확인
  ```

- [ ] **5. MinIO 템플릿 3건 재업로드 완료**
  - 운영팀 별도 트랙으로 완료 여부 확인
  - 파일 3건: `보고서_양식.docx`, `회의록_양식.docx`, `ppt_제안서_가로양식.pptx`
  - 확인: `docker exec docutil-minio mc ls docutil/documents/templates/`

## 팀·계획·의사결정

- [ ] **6. 에이전트 분담 확정**
  - BE (backend-specialist): S1/S2/S4/S5/S6/S7 주담당
  - FE (frontend-specialist): S1/S3/S4/S7 주담당
  - DB (database-architect): S1/S4 주담당
  - RA (research-assistant): S5 주담당
  - SDET (sdet-agent): 전 스프린트 말 QA
  - EA (enterprise-architect): 전체 조율

- [ ] **7. Q1~Q10 결정 + v1.2 조정 요지 숙지**
  - **Q3** Mode 전환 Phase 1 범위 포함 (소프트 체크 + switch-mode API)
  - **Q4** 조직별 템플릿은 향후 로드맵 성격 (단일 조직 가정, 다조직 설계 유지)
  - **Q8** MVP 6종 (SlideTitle/Heading/Paragraph/BulletList/KPI/DataTable)
  - Q1, Q2, Q5~Q7, Q9, Q10 확인

- [ ] **8. S1 D1 작업 즉시 착수 준비**
  - BE: DocumentSchema Pydantic 6종 discriminated union 검증 테스트 작성
  - FE: SlideTitle/Heading/Paragraph React 렌더 시작
  - 파일 위치: `backend/app/modules/documents_v2/schemas.py`, `frontend/src/components/document-schema/components/`

## 마이그레이션·코드 기준선

- [ ] **9. Alembic head 확인**
  ```bash
  docker exec docutil-api alembic current
  # 출력: 006_evaluation (head) 확인
  ```

- [ ] **10. Alembic 007 draft 파일 검증**
  - 파일 존재: `backend/alembic/versions/007_*.py`
  - NOT VALID/VALIDATE 2단계 CHECK 적용 여부 (S0-13)
  - `tb_documents_v2` + `tb_documents_v2_templates` 생성 + `tb_generated_reports` → archive rename

- [ ] **11. QA 기준선 기록**
  ```bash
  scripts\qa_quick.bat   # Windows
  # 또는 bash scripts/qa_quick.sh (Ubuntu 서버)
  # 현재 점수 기록 → S1 회귀 판정 기준으로 사용
  ```

## 리스크·관측

- [ ] **12. S1 Watch List 확인**
  - **R1** Multi-provider Discriminated Union (OpenAI/Azure/Gemini/Claude)
  - 선제 대응: S1 D7 4 provider 교차 테스트 계획
  - 실패 시 `StrictSchemaFallback` 평탄화 스키마 +2일 소요

- [ ] **13. Prometheus/Grafana 접근 확인**
  - 기존 대시보드 로그인 성공
  - S1 말에 "DocumentSchema Pipeline" 신규 대시보드 구축 예정
  - 신규 메트릭 4종: `documents_v2_generated_total`, `builder_duration_seconds`, `llm_tokens_used_total`, `mode_transition_count`

## 최종 착수 승인

- [ ] **14. 사용자 S1 착수 승인**
  - Phase 3 로드맵 리뷰 완료
  - S1 DoD 합의 (6 컴포넌트 end-to-end + PATCH + agentic_rag.py 삭제 + QA ≥80)
  - S1 기간 2주 (10영업일) 합의

---

## 통과 시 즉시 착수 명령

```bash
# S1 D1 월요일 아침 시작 명령
git checkout -b feature/s1-document-schema-mvp
cd D:\workspace\document_utilization

# BE 세션 시작
docker exec docutil-api pytest backend/tests/test_documents_v2_schemas.py -v

# FE 세션 시작 (별도 터미널)
cd frontend && npm run dev
# 에디터에서 components/document-schema/components/SlideTitle.tsx 열기
```

---

**(체크리스트 끝)**
