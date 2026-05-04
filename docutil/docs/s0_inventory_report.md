# S0 사전 조사 결과 보고서

> **조사일**: 2026-04-20
> **조사 주체**: Claude Code (paramiko SSH → 192.168.10.39 운영 서버)
> **조사 대상**: Ubuntu 운영 서버 `192.168.10.39` (IDINO 사내망)
> **연관 문서**: `docs/phase2_transition_plan.md` §6, `docs/phase1_decisions.md` v1.1

---

## 0. Executive Summary — 핵심 발견 8건

1. **조직은 "아이디노" 1개**. 외부 고객사(회사·대학) 데이터 없음.
2. **`tb_report_templates` 0 rows** — Phase 2 계획 전제 중 "조직별 PPTX 템플릿 다수 존재"와 불일치.
3. **`tb_document_templates` 3건만** — 보고서_양식(Jinja2, 11 변수), 회의록_양식(Jinja2, 7 변수), ppt_제안서_가로양식(structured, 0 변수).
4. **`tb_agents.agent_type` 4종** (chatbot/report/proposal/minutes). 각 1건씩. `freeform_doc` 없음. 데이터 정제 불필요.
5. **`tb_organizations.organization_type` 필드 없음** — Q4 결정대로 추가 시 Alembic 008 필요. 다만 현재 조직이 1개라 긴급성 낮음.
6. ~~**MinIO `documents` 버킷 0 파일** — 템플릿 storage_path 경로는 DB에 있으나 실제 파일 부재. 서버 이관 시 누락 가능성.~~ → **정정**: 실제 83 파일 존재. `mc` alias 설정 문제로 초기 조사가 0 반환. DB↔MinIO 정합 상태. (§2.7 참조)
7. **`tb_generated_reports` 49건 completed**, 최근 2026-04-16 생성. 이후 신규 생성 중단 (PPT 슬라이드마스터 실패 핫픽스와 연관 가능성).
8. **Alembic head = `006_evaluation`**. phase1_database_design의 007 draft는 down_revision=006과 일치.

---

## 1. 사용자 Q4 결정 재검증 필요

사용자가 2026-04-20 "회사별, 대학별 양식이 별도로 존재"라 답했으나 **실제 운영 DB에는 조직 1개(아이디노)만 존재**. 다음 중 무엇인지 사용자 재확인 필요:

- (a) **향후 로드맵** — 외부 고객사 온보딩이 계획돼 있어 Phase 1 설계에 반영해야 함 (현재 데이터는 없음)
- (b) **별도 환경** — dev·staging·다른 서버에 실제 데이터 존재
- (c) **MinIO에만 존재** — DB 미연동 파일이 MinIO에 있음 (현재 조사로는 MinIO도 비어있어 부정)
- (d) **DB·MinIO 양쪽 손실** — 서버 이관 과정에서 일부 데이터 누락

**권장**: 사용자에게 재확인 후 Phase 2 계획 조정.

---

## 2. 상세 조사 결과

### 2.1 조직·사용자 (Q8)

```
    id    |   name   |  slug
----------+----------+---------
 00000000 | 아이디노 | default
(1 row)
```

**해석**: UUID `00000000-0000-4000-a000-000000000001` 단일 조직. 다조직 구조 미도입.

### 2.2 Document Templates (Q17, Q18, Q25)

```
 template_type | rendering_mode | count
---------------+----------------+------
 제안서        | structured     |     1
 회의록        | jinja2         |     1
 보고서        | jinja2         |     1
```

| ID | Name | Type | Mode | Vars | Storage Path |
|---|---|---|---|---|---|
| dcfbd218 | 보고서_양식 | 보고서 | jinja2 | 11 | `templates/{org}/{id}/보고서_양식.docx` |
| 993e7767 | 회의록_양식 | 회의록 | jinja2 | 7 | `templates/{org}/{id}/회의록_양식.docx` |
| 066c3c3d | ppt_제안서_가로양식 | 제안서 | structured | 0 | `templates/{org}/{id}/ppt_제안서_가로양식.pptx` |

**해석**: project_status.md는 "16개 IDINO 템플릿"을 언급하나 실제는 3개만 활성. S4 수동 재작성 대상 = 3개 (원래 계획의 5개 미달).

### 2.3 Report Templates (Q1)

```
 organization_id | format | cnt
-----------------+--------+-----
(0 rows)
```

**해석**: 테이블은 있으나 비어있음. S4 조직별 배치 변환 작업 **불필요** (데이터가 없으므로).

### 2.4 Agents (Q3)

```
 agent_type | count
------------+-------
 chatbot    |     1
 minutes    |     1
 report     |     1
 proposal   |     1
```

**해석**: 4종 각 1건. `freeform_doc` 값 없음. Phase 1에서 계획한 CHECK 제약 (`NOT VALID` → `VALIDATE`) 추가 시 기존 데이터 위반 없음.

### 2.5 Organizations 스키마 (Q4)

`tb_organizations` 필드 (11개):
```
id (uuid, NN), name (VARCHAR, NN), slug (VARCHAR, NN), description (text),
settings (jsonb), ins_dt, ins_user, ins_ip, upd_dt, upd_user, upd_ip
```

**해석**: `organization_type` 필드 없음. 다업종 구분 컬럼 미존재. Q4 "회사/대학" 구분은 현재 불가. Alembic 008 필요 여부는 Q4 재확인 후 결정.

### 2.6 Generated Reports (Q19)

```
  status   | count |             last
-----------+-------+-------------------------------
 completed |    49 | 2026-04-16 01:35:18.719051+00
```

**해석**: 49건 성공 생성. 최근 생성이 2026-04-16이고 이후 중단. MinIO 파일 부재와 상관 가능성 (보고서 생성 시 템플릿 로드 실패로 추정).

### 2.7 MinIO 상태 (Q22, Q23, Q24) — **정정됨 (2026-04-20)**

**초기 조사 결과 (오류)**: `mc ls local/` 실행 시 0 반환 → "0 파일" 판단
**정정 (2026-04-20, MinIOService로 재조사)**: **실제 83개 파일 존재**

```
documents 버킷: 83 파일
- templates/{org}/{template_id}/ 하위 다수
- DB 등록 3건 (dcfbd218, 993e7767, 066c3c3d) 파일 모두 정상 존재
- 추가로 개발·이관 과정에서 생성된 원본 파일(`original_*`) 다수
```

**정정 원인**: `mc` CLI의 alias 설정이 서버에 없었던 것으로, 빈 결과를 반환했으나 실제 MinIO 내부에는 데이터가 정상 보관돼 있었음. `MinIOService._client.list_objects()` 로 직접 조회 시 83건 확인.

**결론**: **"MinIO 파일 부재" 블로커는 실재하지 않았음**. DB의 `template_storage_path` ↔ MinIO 파일은 이미 정합 상태. 운영팀 별도 재업로드 트랙 **불필요**.

**부가 조치**: 2026-04-20 검증 과정에서 user_mig/의 최신 3개 파일을 확인차 업로드(기존 파일 위에 덮어쓰기). 동일 경로·동일 내용이므로 영향 없음.

### 2.8 Alembic 상태 (Q12, Q26)

```
현재 head: 006_evaluation
존재 파일: 001 ~ 006_evaluation
```

**해석**: database-architect의 `007_documents_v2_and_template_consolidation.py`는 **로컬(Windows) 저장소에만 존재**. 서버에는 미배포. Phase 4에서 `deploy_to_server.py`로 배포 필요.

### 2.9 서버 리소스 (Q5b)

```
RAM: 31Gi (used 4.5Gi, available 26Gi)
Swap: 8.0Gi (used 34Mi)
Disk /: 591G (used 90G, avail 476G, 16% used)
```

**해석**: 리소스 여유 풍부. LibreOffice 사이드카 (~1GB+) 추가 무리 없음.

### 2.10 Docker 컨테이너 (Q5c)

14개 컨테이너 정상 구동:
- API: 662MB, Celery Worker: 390MB (limit 2GB), Postgres: 403MB
- Nginx, Frontend, MinIO, RabbitMQ, Redis, Qdrant, Grafana, Prometheus, Loki, Flower 전부 정상

**해석**: 인프라 안정. Phase 4 구현 중 배포 가능.

### 2.11 LibreOffice 상태 (Q5a)

```
soffice NOT installed
```

**해석**: S5 옵션 PDF 변환을 위해 LibreOffice + H2Orestart 사이드카 추가 시, 사이드카 **컨테이너 방식**으로만 가능 (호스트 설치 불요).

---

## 3. Phase 2 계획 조정 권고

### 3.1 Q4 결정 재해석 옵션별 영향

| 옵션 | Phase 2 조정 사항 | S4 기간 | Alembic 008 | S0 추가 작업 |
|---|---|---|---|---|
| **(a) 향후 로드맵** | 단일 조직 가정 + 다조직 설계 유지 | 3.5주 → **2.5주** | 스킵 (외부 고객사 온보딩 시 추가) | 없음 |
| **(b) 별도 환경 존재** | dev·staging 조사 필요 | 3.5주 (유지) | 즉시 추가 | dev·staging 조사 명령 수립 |
| **(c) MinIO 데이터 손실** | 복원 필요 + 기존 계획 재검토 | 3.5주 + MinIO 복구 | 즉시 추가 | MinIO 백업 확인 |
| **(d) misspoke** | 단일 조직 확정 + Q4 결정 롤백 | 3.5주 → **2.0주** | 스킵 | 없음 |

### 3.2 MinIO 빈 상태 별도 조사 필요

`tb_generated_reports` 49건은 성공 상태이나 MinIO 파일 없음. 이는 Phase 0 진단 §7.1 "PPT 슬라이드마스터 실패"의 한 원인일 수 있음 (템플릿 파일 로드 실패). 추가 조사:

- MinIO 데이터 볼륨 확인 (`docker volume inspect docutil_minio_data`)
- 파일 삭제 이력 로그 (MinIO `.minio.sys/`)
- 서버 이관 시 볼륨 마이그레이션 스크립트 재검토

---

## 4. 조정 후 S4 스프린트 권장 범위

사용자 Q4 재확인 결과에 따라:

**옵션 (a) 향후 로드맵 가정 시 (가장 현실적)**:
- S4 작업: Mode B 통합 (Jinja2 기존 3건 재작성) + Mode 전환 API + `(admin)/template-designer/`
- 조직별 배치 변환 스크립트 **제외**
- `organization_type` 컬럼 추가 **스킵** (Phase 4 외부 고객사 온보딩 시 추가)
- S4 기간 2.5주 (Q3 Mode 전환 2주 + Mode B 구성 0.5주)
- S7 여유분 1주 회수 가능 (Phase 1 로드맵의 원래 1~2주 여유분 복원)

**옵션 (d) 단일 조직 확정 + Q4 전면 롤백 시 (리스크 최소)**:
- S4 기간 2.0주 (Mode 전환 API + Mode B만)
- `phase1_decisions.md` v1.2로 Q4 재개정 필요

---

## 5. 사용자 확인 결과 (2026-04-20)

사용자 답변: **"아직 데이터를 등록하지 않은 것뿐. 실제로는 양식을 계속 업로드할 예정"**

→ 옵션 **(a) 향후 로드맵** 으로 확정. MinIO 0 파일·템플릿 3건도 같은 맥락(개발 중 데이터 미등록)으로 해석.

## 6. 반영 결과

- `docs/phase1_decisions.md` **v1.2** 업데이트 (Q4 재해석 + v1.2 변경이력 추가)
- `docs/phase2_transition_plan.md` **v1.1** 업데이트 (Executive Summary 핵심 결정 3·7·8 갱신)
- **S4 기간 3.5주 → 2.5주 축소**, S7 여유분 2주 원복
- Alembic 008 `organization_type` **Phase 1~4 범위 외**로 이동 (외부 고객사 온보딩 스프린트)
- 리스크 R12·R13 제거, U4 대폭 완화, **R14 신설** (외부 고객사 온보딩 후속 작업)
- **다조직 설계는 그대로 유지** (DocumentSchema·ORM·Frontend의 `organization_id` 구조)
- **운영팀 별도 트랙**: Phase 4 S1 시작 전 MinIO 템플릿 3건 수동 재업로드 필수

---

**(문서 끝)**
