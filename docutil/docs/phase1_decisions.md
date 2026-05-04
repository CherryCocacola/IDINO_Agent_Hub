# DocUtil — Phase 1 후속 의사결정 (v1.2)

> **작성일**: 2026-04-19 (v1.0), 2026-04-20 v1.1, 2026-04-20 S0 후 v1.2
> **작성자**: enterprise-architect (Claude Opus 4.7) + 사용자 정책 결정 반영
> **결정 주체**: enterprise-architect (기준선 확정) + **사용자 승인 3건 (Q3·Q4·Q8) + S0 결과 반영 재확정**
> **상위 문서**: `docs/phase1_architecture.md` v1.6, `docs/s0_inventory_report.md`
>
> **v1.1 변경점** (2026-04-20 사용자 결정 반영):
> - **Q3 뒤집힘**: Mode 전환 기능 **Phase 1 범위 포함**으로 변경 (사용자 요청)
> - **Q4 확정**: 조직별 PPTX 템플릿 **실재 확인** (회사별·대학별). S4 자동 변환 범위 확장
> - **Q8 유지**: MVP 6종 확장이 S1 2주 일정과 **일치 확인**
>
> **v1.2 변경점** (2026-04-20 S0 조사 후 Q4 해석 정정):
> - **Q4 재해석**: 조직별 양식은 **"계획 중, 아직 데이터 등록 안 함"** 으로 확정 (사용자 확인). 현재 DB는 "아이디노" 단일 조직 + 템플릿 3건.
> - **다조직 설계는 유지**: DocumentSchema·ORM·Frontend 모두 `organization_id` 필터링 구조 그대로. 외부 고객사 온보딩 시점에 데이터만 추가 가능하도록 **확장성 확보**.
> - **S4 기간 축소**: 3.5주 → **2.5주** (조직별 배치 변환 스크립트 불필요. Mode 전환 API 2주 + Mode B Jinja2 UX 0.5주).
> - **Alembic 008 `organization_type` 스킵**: 현 단계에서 미추가. 외부 고객사 온보딩 스프린트(Phase 1 범위 외)에서 추가.
> - **S7 QA 여유분 1주 복원**: Q3·Q4 조정 누적으로 S4 +1주 → S7 -1주였으나, v1.2에서 S4 -1주 회수됐으므로 S7 원래 2주 유지 가능.
> **대응 질문 출처**:
> - `docs/phase1_database_design.md` §8 미해결 질문 4건 (Q1~Q4)
> - `docs/phase1_hwpx_adapter.md` §7.5 미해결 질문 3건 (Q5~Q7)
> - `docs/phase1_frontend_design.md` §8 미해결 질문 3건 (Q8~Q10)
> **상태**: Phase 1 종료 의사결정. Phase 2 (전환계획) 착수 전 확정본.

---

## 0. Executive Summary

Phase 1 기준선(`phase1_architecture.md`)을 소비한 3개 후속 에이전트(database-architect / frontend-specialist / research-assistant)가 각자 영역의 상세 설계를 완료하면서 기준선 해석 모호성 10건을 제기했다. 본 문서는 이 10건에 대해 P1~P6 아키텍처 원칙과 13~14주 전체 일정을 동시에 훼손하지 않는 방향으로 **확정 의사결정**을 내린다.

결정의 기조 세 가지:

1. **YAGNI 고수**. 현 시점에서 검증되지 않은 기능 확장(예: "자유 생성 후 템플릿 끼워맞추기", "조직별 사내 PPTX 템플릿 자동 이관")은 Phase 1 범위에서 제외하고 필요 시점에 별도 결정으로 승격한다.
2. **Mode A/B 동시 지원과 접근법 C 일관성 유지**. DocumentSchema가 SSOT라는 구조를 흐리는 결정은 허용하지 않는다. 특히 Mode 전환 소프트 체크 도입(Q3), PATCH 단위 오버엔지니어링(Q10)은 이 관점에서 보수적으로 판단했다.
3. **S1 DoD는 "배포 가능한 최소"**에 초점. DataTable을 MVP에서 뺄 경우 S1~S2 경계에서 end-to-end 시연이 어려워진다는 frontend-specialist의 관찰을 수용해 **MVP를 6종으로 확장**했다(Q8). 스케줄 영향은 동일 스프린트 내에서 흡수 가능.

10건 결정 중 **정책성(사용자 승인 권장) 3건**: Q3(Mode 전환 기능 범위), Q4(조직별 PPTX 템플릿 처리), Q8(MVP 5→6종 확장).

---

## 1. 결정 상세

### Q1 — `freeform_doc` 이름 중복

**원질문 (database-architect §8.1)**
`DocumentType` enum의 `freeform_doc`과 `tb_agents.agent_type`의 `freeform_doc`이 동일 문자열. 의도된 일치인가, 접두사 분리(`freeform_doc_agent`) 필요한가?

**결정** — **동일 문자열 유지. 분리하지 않음 (의도된 일치).**

**근거**

1. DocUtil 도메인에서 두 값은 서로 다른 축(문서 타입 vs 에이전트 역할)이지만 **의미상 1:1 대응**된다. 회의록 문서(`minutes`)를 회의록 에이전트(`agent_type='minutes'`)가 담당하듯, 자유 문서도 자유 문서 에이전트가 담당한다. `report/proposal/minutes` 4종이 이미 동일 문자열로 일치해 있고, 여기에 `freeform_doc`을 더해 **5종 전체가 같은 축**으로 정렬되는 것이 프롬프트/프로바이더 선택 로직의 단순함에 직접 기여한다.
2. LLM 프롬프트 내 구분 필요성은 **컨텍스트 위치로 충분히 해결**된다. `agent_type`은 "당신의 역할" 위치에, `document_type`은 "출력 형식" 위치에 주입되며, 둘을 혼동할 LLM은 실사용 프로바이더(OpenAI/Azure/Gemini/Claude) 중에 없다.
3. 접미사 `_agent`는 **전형적인 중복 레이블**(anti-patterns.md의 과도한 일반화에 해당). 컬럼명이 이미 `agent_type`이므로 값에 다시 `agent`를 붙이는 것은 의미 중첩이다.

**영향**

- `tb_agents.agent_type` CHECK 제약은 `('chatbot','report','proposal','minutes','freeform_doc')` 5종으로 확정 (database-architect §1.3 그대로 수용).
- `VARCHAR(20)` 길이 수용 확인 완료 (`freeform_doc` = 12자).
- LLM 프롬프트 템플릿(`documents_v2/service.py`에서 구성)은 `agent.system_prompt` 앞에 `"당신의 에이전트 타입은 '{agent_type}'이며, 지금 생성하는 문서 타입은 '{document_type}'입니다."` 한 줄 삽입만 추가.

**후속 조치**

- `phase1_database_design.md` 본문 변경 없음. §8.1은 본 결정으로 해소된 것으로 간주.
- Phase 4 S0 점검 단계에서 `SELECT DISTINCT agent_type FROM tb_agents` 실행 결과에 `chatbot/report/proposal/minutes` 외 값이 있는지 반드시 선행 검증(database-architect §5 D3 재확인).

---

### Q2 — `source_document_ids` ARRAY vs 조인 테이블

**원질문 (database-architect §8.2)**
`tb_documents_v2.source_document_ids UUID[]`로 유지할지, `tb_documents_v2_sources` 조인 테이블로 정규화할지?

**결정** — **Phase 1은 ARRAY 유지. 정규화는 Phase 4 S6 시점에 사용 실측으로 결정.**

**근거**

1. 역방향 질의("이 원본을 참조한 모든 생성물") 빈도는 **현 시점 0**이다. UI에 해당 기능이 없고 로드맵(S1~S7)에도 일정이 없다. YAGNI 원칙상 지금 정규화하면 마이그레이션 비용만 쓰는 셈.
2. ARRAY + `idx_tb_documents_v2_schema_gin`(jsonb_path_ops) 조합으로 `source_document_ids && ARRAY[:doc_id]::uuid[]` 쿼리는 GIN 보조 인덱스 하나 추가로 충분히 대응 가능하다. 정규화 전환 시점까지 **가역적**.
3. 조인 테이블로 가는 순간 `ON DELETE CASCADE` 양방향 정책, orphan 스캐너, 삭제 시 감사 로그 등 2차 구조가 따라온다. 기능 요구가 확정되지 않은 상태에서 이 비용을 감수할 이유가 없다.

**영향**

- 현재 `source_document_ids UUID[]` 유지 (database-architect §1.1 DDL 그대로).
- 리스크 D6("orphan 참조 가능")는 UI 표시로만 완화(database-architect §5 그대로).
- Phase 4 S6 DoD에 **"역방향 질의 실측 후 정규화 의사결정"** 항목을 명시적으로 추가.

**후속 조치**

- `phase1_database_design.md` §4 마이그레이션 타임라인 "S6: source_document_ids 사용 빈도 관찰 결과 리뷰. 정규화 필요 판정 시 008 마이그레이션 스펙 작성" 한 줄 추가 필요 (Phase 2 병합 시 반영).
- `phase1_architecture.md` §2.8에 "`source_document_ids`의 역방향 질의는 Phase 4 S6까지 ARRAY로 유지한다" 주석 추가.

---

### Q3 — Mode 전환 CHECK vs 소프트 체크 ⚠️ **v1.1 뒤집힘**

**원질문 (database-architect §8.3)**
`ck_tb_documents_v2_template_consistency` CHECK가 `mode ↔ template_id`를 엄격 강제. "자유 생성 후 템플릿 끼워맞추기" 같은 Mode 전환 기능이 필요한가?

**v1.0 초기 결정** (enterprise-architect): Phase 1 범위 외로 제외
**v1.1 최종 결정** (사용자 확인, 2026-04-20): **Mode 전환 기능 Phase 1 범위 포함. CHECK 제약을 소프트 체크(서비스 레이어 검증 + 감사 로그)로 전환.**

**근거 (v1.1)**

1. 사용자가 실무 사용 시나리오를 확인: **자유 생성으로 만든 문서를 조직의 기존 양식에 "끼워맞추기"** 하는 요구가 실재한다. 반대로 템플릿 기반 문서를 자유 편집 모드로 전환하는 경우도 있다. 두 방향 모두 Mode 전환이 필요하다.
2. 엄격 CHECK로는 이 시나리오를 구현할 수 없다. `mode` 컬럼을 수정하는 모든 업데이트가 차단된다. 대안으로 **"삭제 후 재생성"** 은 기존 편집 이력·comments·versions을 잃게 돼 사용자 가치를 훼손한다.
3. 소프트 체크(서비스 레이어 + 감사 로그)는 P5 에러 처리 일관성을 훼손하지 않는 범위에서 구현 가능: `documents_v2/service.py`에 `ModeTransitionValidator`를 두어 전환 시 필수 조건(`template_id`·`locked` 일관성)을 검증하고, 위반 시 `HTTPException`을 한국어 메시지로 반환. DB CHECK는 **존재는 하되 완화** (`mode='template_fill' AND template_id IS NULL`을 금지하되, `mode` 자체 변경은 허용).

**영향**

- **DB**: `ck_tb_documents_v2_template_consistency` CHECK 조건을 완화. `template_id IS NOT NULL` 을 `mode='template_fill'` 의 필요조건으로만 강제, 전환 과정은 허용. Alembic 007 재작성 필요.
- **API**: `POST /v2/documents/{id}/switch-mode` 엔드포인트 신설 필요. Payload: `{ target_mode, template_id?, conflict_policy }` (conflict_policy: `discard_unmapped | keep_all`).
- **Backend 로직**: 자유→템플릿 전환 시 기존 컴포넌트를 템플릿 슬롯에 **AI 자동 매핑** (기존 Jinja2 slot 매칭 로직 재활용 가능). 매칭 실패 컴포넌트는 policy에 따라 삭제 또는 자유 페이지로 보존.
- **Frontend**: `/designer` UX에 "Mode 전환" 메뉴 추가 (Export 메뉴 옆 또는 별도 드롭다운). `(user)/designer/` + `(admin)/template-designer/` 양쪽에 공통 UI.
- **감사 로그**: `audit_logs`에 `mode_transition` 이벤트 타입 추가. 전환 전/후 snapshot 저장.
- **스프린트**: **S4(Mode B 통합)에 편입**. S4 기간을 1.5주 → **2주로 확장**. 전체 13~14주 일정은 S7의 QA 여유분에서 흡수 가능.

**리스크**

- **R11 신설**: Mode 전환 시 컴포넌트 자동 매핑 AI 로직의 정확도. 심각: 중, 확률: 중. 대응: S4에서 매핑 실패 컴포넌트를 기본 "자유 페이지로 보존"하고 사용자가 명시적 policy 선택 가능.
- `phase1_database_design.md` D2 리스크는 **감소** (CHECK 완화로 migration 롤백 시나리오 단순화).

**후속 조치**

- `phase1_architecture.md` §2.4에 "**Mode 전환 기능 S4 포함**. 소프트 체크 + 서비스 레이어 검증 방식" 명시 (Phase 2에서 병합).
- `phase1_database_design.md` §1.1 (CHECK 정의) + §5 (리스크) 업데이트 (Phase 2 병합).
- `phase1_frontend_design.md` UX에 "Mode 전환 메뉴" 추가 (Phase 2 병합).
- `backend-specialist`에 Mode 전환 API + 자동 매핑 AI 로직 설계 위임 (Phase 2 스프린트 계획 수립 시).

---

### Q4 — 조직별 PPTX 템플릿 처리 ⚠️ **v1.2 재해석**

**원질문 (database-architect §8.4)**
`tb_report_templates`의 PPTX 파일이 IDINO 마스터가 아닌 **조직별 보고서 템플릿**이라면 Phase 4에서 별도 변환 경로 필요. `phase1_architecture.md §5.3` 항목 5는 IDINO 마스터만 다룸.

**v1.0 초기 결정** (enterprise-architect): "IDINO 마스터만 존재" 가정
**v1.1 사용자 결정** (2026-04-20): 조직별 양식 "실재"한다는 답변으로 S4 자동 변환 범위 확장
**v1.2 S0 후 재해석** (2026-04-20): **S0 조사 결과 실제 DB에 조직별 데이터가 없음을 확인.** 사용자 재답변: "아직 데이터를 등록하지 않은 것뿐. 실제로는 양식을 계속 업로드할 예정". → **향후 로드맵 성격**으로 확정. Phase 1~4 실행 범위에서는 **단일 조직(아이디노) 가정**으로 작업하되, **다조직 설계는 유지**하여 향후 업로드에 대비.

**근거 (v1.2)**

1. S0 실제 DB 조사 결과 (`s0_inventory_report.md`):
   - `tb_organizations`: 조직 1건 ("아이디노", default)
   - `tb_document_templates`: 3건 (보고서·회의록·제안서 각 1)
   - `tb_report_templates`: 0 rows
   - MinIO `documents` 버킷: 0 파일
   - **외부 고객사 데이터는 현재 운영 환경에 없음**
2. 사용자 재답변 (2026-04-20): "아직 데이터를 등록하지 않은 것뿐. 실제로는 양식을 계속 업로드할 예정". 즉 **조직별 양식 기능은 필요하나 현재 데이터는 없음** — Phase 4까지의 구현 범위에서는 **단일 조직(아이디노) 가정**으로 작업하고, 외부 고객사 온보딩은 **향후 별도 스프린트**.
3. 다조직 설계는 유지해야 함. DocumentSchema의 `organization_id`, ORM의 FK, Frontend의 조직별 스코프 필터링은 **현재 설계 그대로**. 이로써 외부 고객사 온보딩 시 데이터만 추가하면 되도록.
4. **Alembic 008 `organization_type`** 은 현 단계 스킵. 외부 고객사 온보딩 시점에 "회사/대학/공공" 구분이 실제 필요해질 때 별도 마이그레이션으로 추가. 현재 설계에 영향 없음.

**영향 (v1.2)**

- **S0 실행 완료** (`s0_inventory_report.md` v1.0):
  - 조직 1건, 템플릿 3건, report_templates 0건, MinIO 0 파일
  - LibreOffice 미설치 → S5 사이드카 컨테이너로 해결
  - Alembic head = 006_evaluation (007 draft 정합)
  - agent_type 4종 각 1건 (freeform_doc 값 없음, 정제 불필요)
- **S4 작업량 축소**:
  - IDINO 활성 3건 수동 재작성 (기존 16건 가정 → 3건으로 감소)
  - **조직별 배치 변환 스크립트 불필요** (데이터 없음)
  - Mode 전환 API + Mode B Jinja2 UX만 수행
  - **S4 기간 3.5주 → 2.5주로 축소** (S7 여유분 1주 복원)
- **Organization 도메인 모델**:
  - `tb_organizations.organization_type` 필드 추가 **스킵** (Phase 1~4 범위 외)
  - 외부 고객사 온보딩 스프린트에서 Alembic 008로 처리
  - `domain-model.md` 에 "DocUtil은 다조직 구조를 지원하며, 현재는 아이디노 단일 조직이나 향후 외부 고객사(회사·대학·공공 등) 수용 가능" 명시
- **MinIO 파일 부재 별도 조치**:
  - 현재 템플릿 3건의 `template_storage_path`는 DB에 있으나 MinIO 실제 파일 없음
  - 사용자 확인: 개발·이관 과정에서 삭제·미등록. 의도적
  - Phase 4 S1 시작 전 **운영팀이 현재 3건 템플릿 파일을 MinIO에 재업로드** (또는 재생성) 필요
  - 이는 Phase 1~4 범위 외 운영 작업

**리스크 (v1.2)**

- **R13 제거**: "대학" 조직 유형의 도메인 파급 효과는 Phase 1~4 범위 외. 향후 별도 스파이크.
- **R12 제거**: 조직별 극복잡 템플릿 자동 변환 실패 리스크도 현 단계 데이터 없음으로 소거.
- **U4 대폭 완화**: "조직별 템플릿 변환 실패"에서 "IDINO 3건 재작성"으로 범위 축소. 심각도 **중 → 낮**.
- **신규 R14**: 외부 고객사 온보딩이 Phase 1~4 **이후** 시작될 때 Alembic 008 + 조직별 배치 변환 + `organization_type` UI가 모두 **별도 스프린트로 추가** 필요. 추후 ROI 기준으로 착수.

**후속 조치**

- **S0 완료** (본 결정에 반영). 추가 조사 불필요.
- `phase1_database_design.md` §4 업데이트: 조직별 배치 변환 삭제, IDINO 3건 수동 재작성 유지 (Phase 2 병합)
- `phase1_architecture.md §5.3` 항목 5 원복: "IDINO 활성 템플릿 3건만" (Phase 2 병합)
- `phase2_transition_plan.md` §3.6 (S4) 축소: 기간 3.5주 → 2.5주. §5 리스크 매트릭스에서 U4 완화, R13 제거
- `techspec.md` §15 Phase 2 요약 갱신 (S4 기간 조정)
- `domain-model.md` 경량 보강: 다조직 구조 설명 추가 (현재 단일 조직, 향후 확장 가능)

---

### Q5 — `HwpxBuilder.build()` 반환 타입

**원질문 (research-assistant §7.5.1)**
`python-hwpx`의 `to_bytes()` API가 미확인이라 임시파일 경유 방식이 불가피. `build() -> bytes` 유지(내부 임시파일) vs `-> Path`?

**결정** — **`build() -> bytes` 유지. 임시파일은 빌더 내부 구현 세부로 은닉한다.**

**근거**

1. P7("Builder Adapter Interface")는 `DocumentBuilder.build(schema) -> bytes` 시그니처를 전 포맷 공통 규약으로 못 박았다. PPTX/DOCX/PDF는 `io.BytesIO`로 이미 이 규약을 만족한다. HWPX만 `-> Path`로 벗어나면 Service 레이어(P4)에서 포맷별 분기가 발생해 **P1(단일 구현)을 위반**한다.
2. 임시파일 경유는 I/O 1회 추가 비용에 불과하다(평균 50ms 이내). HWPX 생성은 Celery 비동기 경로(`export_worker`)에서 실행되므로 요청 지연에 미치는 영향은 실질적으로 없다.
3. 임시파일 cleanup은 research-assistant §3.1 `_to_bytes()` 내부의 `try/finally + os.unlink`로 충분히 관리된다. 파일 핸들 누수 위험은 없다.
4. 만약 Phase 4 S5 PoC에서 `python-hwpx`의 `save_to_path(BytesIO)`(방법 B)가 실제로 동작한다면, 반환 타입 변경 없이 내부만 교체하면 된다(**인터페이스 안정**).

**영향**

- research-assistant §3.1 `async def build(self, schema) -> bytes` 시그니처 확정.
- `_to_bytes()` 구현은 방법 A(임시파일)를 기본으로 하되 S5 PoC에서 방법 B(BytesIO) 실측 후 선택 교체.
- `BuilderRegistry.get("hwpx").build(schema)` 호출 측(Service)은 포맷별 분기 불필요.

**후속 조치**

- `phase1_architecture.md §7.4` 예시 코드 주석에 "_to_bytes는 임시파일 경유. to_bytes() 동작 확인 시 교체." 한 줄 명시.
- `phase1_hwpx_adapter.md §3.1` 본문 변경 불필요.

---

### Q6 — AttendeeList HWPX 빌더 포함 시점

**원질문 (research-assistant §7.5.2)**
`phase1_architecture.md §3.2`는 AttendeeList를 **S6 도입**으로 지정. `§7.3`은 HWPX 지원 14종에 포함. S5 HWPX 빌더 구현 시 AttendeeList도 포함해야 하는지?

**결정** — **S5에는 HWPX 빌더의 `AttendeeList` 핸들러 스텁(degrade_to_paragraph 경로)만 등록. 완전 구현은 S6와 동시 진행.**

**근거**

1. `§3.2` 카탈로그의 "도입 스프린트 = S6"은 **컴포넌트 자체의 최초 도입 시점**을 의미한다(React 렌더러·PPTX 빌더·DOCX 빌더 모두 포함). AttendeeList는 S5 시점에는 시스템 어디에도 존재하지 않으므로 HWPX 빌더가 먼저 구현될 수 없다.
2. 반면 `§7.3`의 "HWPX 지원 14종"은 **HWPX가 포맷 제약 때문에 표현 불가능한 컴포넌트가 아니다**라는 선언이다. 즉 "HWPX가 지원하는가"와 "언제 구현되는가"는 다른 축이다. §7.3 표가 S5 구현 범위로 오독된 것이 질문의 발생 원인.
3. HwpxBuilder는 **컴포넌트 레지스트리 기반**(research-assistant §3.1, `HWPX_BUILDERS: dict[str, Callable]`)이므로 S5에 5~7종만 등록하고, S6에서 AttendeeList/ExecutiveSummary/ActionItemList 등 보고서 특화 컴포넌트 4종을 추가 등록하는 **점진적 확장**이 자연스럽다. 이는 P7(ABC + Registry)이 의도한 바다.
4. S5에 미등록된 컴포넌트가 HWPX 출력 요청 중 발견되면 `degrade_to_paragraph(section, comp, tokens)` 경로로 처리되며 `metadata.degraded_components`에 기록된다. S5 기간 동안 AttendeeList 요청이 들어와도 서비스가 깨지지 않는다.

**영향**

- S5 HwpxBuilder DoD 범위: SlideTitle, Heading, Paragraph, BulletList, DataTable, Image, Quote + 레이아웃(TwoColumn/ThreeColumn/Hero/Comparison/ImageGrid) = **12종**.
- S6 추가: ExecutiveSummary, ActionItemList, AttendeeList = **3종** (§3.2 S6 도입 컴포넌트와 일치).
- `phase1_architecture.md §7.3` "완전 지원 14종" 표는 **HWPX에서의 표현 가능성 선언**임을 본문에 명시.

**후속 조치**

- `phase1_architecture.md §7.3` 상단에 "이 표는 HWPX 포맷이 지원하는 컴포넌트 집합을 의미하며, 실제 빌더 구현은 §3.2의 도입 스프린트를 따른다" 주석 추가.
- `phase1_hwpx_adapter.md §7.2` 표의 "도입 스프린트" 열을 위 분류에 맞춰 재정렬 필요 (Phase 2 병합 시 반영).

---

### Q7 — HWPX 컬러 주입 S5 DoD 수준

**원질문 (research-assistant §7.5.3)**
`primary_color` 표 헤더 배경 적용이 S5 완료 기준인가? 스타일 이름만 적용하는 최소 구현으로 시작 가능한가?

**결정** — **S5 DoD는 "스타일 이름 적용 + 폰트 적용"까지로 한정. 표 헤더 배경색 등 lxml 직접 조작이 필요한 색상 주입은 S5 stretch goal, 완전 구현은 S6 초반.**

**근거**

1. HWPX의 색상 시스템은 PPTX의 테마 색상 매핑과 달리 스타일별 `<hp:charPr>`·셀별 `<hp:cellBorderFill>`을 lxml로 직접 조작해야 한다(research-assistant §1.4, §4.3). 이 작업은 **XML 스키마 지식 + 한컴 뷰어 실기 검증 + 변환 실패 시 fallback 처리** 세 축이 모두 필요하며, S5의 2주 내에서 14종(실제 12종, Q6 결정 반영) 빌더 구현과 함께 수행하기에는 리스크가 크다.
2. 반면 **스타일 이름 매핑**(IDINO_제목1/IDINO_본문/목록 글머리표 등)은 python-hwpx 공개 API로 확인된 경로이며, 이것만으로도 IDINO 브랜드의 "골격"(폰트, 크기, 볼드 여부)은 유지된다. 최종 시각적 결과물은 **PPTX/DOCX 대비 간소한 수준**이 되지만, "열리고 읽을 수 있는 HWPX"라는 S5의 핵심 가치는 달성된다.
3. 색상 미적용 수준을 명시적으로 허용하면 S5 PoC(한컴 2020/2022 열기 테스트, 한글 인코딩 검증 등)에 더 많은 시간을 배분할 수 있다. 이는 research-assistant §7.4 R2("python-hwpx 생성 HWPX 한컴 2020 미열림") 리스크를 선제 대응하는 전략.
4. UI에서는 `metadata.degraded_components`와 유사한 개념으로 "HWPX 출력은 IDINO 색상이 제한적으로 표시됩니다" 배지를 Export 드롭다운에 표시.

**영향**

- S5 DoD 수정: "HwpxBuilder가 지원 12종 컴포넌트에 대해 스타일 이름·폰트를 적용해 HWPX 파일 생성, 한컴 2020/2022에서 열림, `degraded_components` 기록 확인". **표 헤더 배경색은 S6로 이연**.
- S6 DoD에 추가: "HWPX 표 헤더 배경색 lxml 직접 조작 구현, primary_color 필드가 헤더에 반영되는지 시각 검증".
- `phase1_architecture.md §9.1` S5 DoD 문구 업데이트 필요.

**후속 조치**

- `phase1_hwpx_adapter.md §7.3` S5 PoC 범위 표에 "색상 주입은 stretch goal" 메모 추가 (Phase 2 병합 시).
- `phase1_architecture.md §9.1` S5 DoD 업데이트 (본 문서 §2 보강에 반영).

---

### Q8 — MVP 5종 정의 불일치

**원질문 (frontend-specialist §8.1)**
`phase1_architecture.md §3.2`의 MVP는 SlideTitle/Heading/Paragraph/BulletList/KPI. 부록 E.3 및 frontend-specialist 입력 과제는 DataTable 포함. frontend-specialist는 합집합 6종 스켈레톤 작성. S1 DoD "5-컴포넌트 end-to-end"의 5종을 어떻게 확정?

**결정** — **MVP를 SlideTitle/Heading/Paragraph/BulletList/KPI/DataTable = 6종으로 확정 (MVP 확장). S1 DoD 문구를 "6-컴포넌트 end-to-end"로 갱신.** **[사용자 승인 권장]**

**근거**

1. 기준선의 MVP 5종과 후속 에이전트 입력 과제의 5종이 불일치한 것은 **애초의 설계 오류**다. 부록 E.3 research-assistant 입력에 `SlideTitle/Heading/Paragraph/BulletList/DataTable`이 명시되고 frontend-specialist 입력에도 DataTable이 포함되면서 결과적으로 세 에이전트 사이에 정의 괴리가 발생했다.
2. DataTable을 S1에 포함하는 것의 실질 가치:
   - "문서다움"을 보여주는 가장 강력한 컴포넌트다. SlideTitle+Paragraph+BulletList만 있는 프리뷰는 시연 가치가 낮다.
   - DataTable의 React 렌더(shadcn Table) / PPTX 빌더(`add_table`) / DOCX 빌더(`add_table`) / HWPX 빌더(`add_table`) 4쌍은 **가장 표준적인 API 조합**이라 구현 난이도가 낮다. S1에서 수용 가능.
   - Mode B 템플릿에서도 DataTable은 가장 자주 쓰이는 슬롯 형태다. S4 진입 전에 DataTable 패턴이 검증돼 있으면 Mode B 구현이 매끄러워진다.
3. KPI를 빼는 대신 DataTable을 넣는 대안은 기각한다. KPI는 Phase 0 진단(techspec §7.1.3, IDINO 보고서 표준 구성)에서 **필수 컴포넌트**로 확인되었고, React/PPTX 합성 로직이 이미 부분 존재한다.
4. Heading은 레벨(1~3) 처리가 필요하지만 코드 복잡도는 낮다. 빼지 않는다.
5. 결론: MVP를 **6종으로 확장**. S1 기간(2주)은 frontend-specialist가 이미 6종 스켈레톤을 작성한 전제이고, 백엔드 빌더 쪽에서 한 컴포넌트(DataTable) 추가는 1일 내 흡수 가능. **전체 13~14주 일정에 영향 없음**.

**영향**

- `phase1_architecture.md §3.2` "MVP 5종" → "MVP 6종"으로 업데이트. 도입 스프린트 열에서 DataTable이 S2 → S1로 이동.
- `phase1_architecture.md §9.1` S1 DoD: "5-컴포넌트 end-to-end" → "6-컴포넌트 end-to-end".
- `phase1_architecture.md §3.2` 본문 "MVP 5종 선정 근거" → "MVP 6종 선정 근거" 및 본 결정(Q8) 참조.
- database-architect는 영향 없음(스키마상 컴포넌트 수와 무관).
- research-assistant: S5 PoC 우선순위 5종(§7.3)에 DataTable이 이미 포함되어 있어 영향 없음.
- frontend-specialist: 현재 6종 스켈레톤 작성 상태가 그대로 확정본이 됨.

**후속 조치**

- `phase1_architecture.md §3.2`, §9.1 본문 수정 (본 문서 §2 보강에 반영).
- `phase1_frontend_design.md §3`의 "MVP 5종 + DataTable = 6개" 표현을 "MVP 6종"으로 정리 필요 (Phase 2 병합 시).
- 사용자 승인 포인트: MVP 확장이 S1 2주 내 달성 가능한지 및 제품 시연 우선순위와 일치하는지 확인.

---

### Q9 — `/designer` 라우트 그룹 (user vs admin)

**원질문 (frontend-specialist §8.2)**
현재 `frontend/src/app/(user)/designer/`만 존재. admin의 템플릿 편집(Mode B 슬롯 설계)도 동일 designer를 재사용할지, 별도 `(admin)/template-designer/`를 둘지?

**결정** — **(user) 하위의 `designer`는 그대로 유지하되, admin 전용 `(admin)/template-designer/`를 신설한다. 두 경로는 동일 Shell 컴포넌트(`components/document-designer/`)를 props 구성만 달리해 재사용한다.**

**근거**

1. Next.js App Router에서 route group `(user)`와 `(admin)`은 **미들웨어·레이아웃 경계**다. `(admin)`은 RBAC 검사·관리자 사이드바·감사 로그 헤더 등 사용자 영역과 다른 미들웨어 체인을 갖는다. 사용자 라우트에서 관리자 행동(템플릿 저장)을 허용하면 이 경계가 무너지고 감사 요구와 충돌할 수 있다.
2. Shell 컴포넌트(`components/document-designer/`)는 이미 "preview-pane / edit-sidebar / prompt-box / export-menu / design-token-picker" 5개 패널로 구성된 **컴포지션 유닛**이다. `(user)`는 "문서 생성 페이지"로, `(admin)`은 "템플릿 편집 페이지"로 다른 props(예: `mode="template_authoring"`, `allow_lock_toggle=true`)를 주입해 동일 Shell을 재사용할 수 있다. P1(단일 구현)은 **컴포넌트 수준**에서 지켜지고, 라우트는 단지 진입점이다.
3. `(admin)/template-designer/`의 구체 기능:
   - `components/edit-sidebar/forms/`에 `LockToggleForm`, `AnchorNameForm` 등 관리자 전용 폼 추가.
   - 저장 시 `tb_documents_v2_templates` 테이블로 라우팅(사용자 경로는 `tb_documents_v2`).
   - Export 메뉴 비활성화(템플릿은 파일로 내려받는 대상이 아님, 샘플 미리보기만).
4. **그룹 재사용은 기각**한다. 단일 `(any)/designer/`로 통합하면 URL이 모호해지고(`/designer/create`가 관리자 컨텍스트에서 무엇을 의미하는지 불명확), 미들웨어 분기가 라우트 내부로 스며들어 app shell의 책임 경계가 깨진다.

**영향**

- 프론트엔드 라우트 트리 확정:
  ```
  app/(user)/designer/
    ├── create/page.tsx         Mode A (자유 생성)
    ├── fill/[templateId]/page.tsx  Mode B (양식 채우기)
    └── [documentId]/page.tsx   편집/프리뷰
  app/(admin)/template-designer/
    ├── create/page.tsx         신규 템플릿 작성
    └── [templateId]/page.tsx   기존 템플릿 편집
  ```
- Shell 재사용: `components/document-designer/*`는 경로별 props로 동작 전환. 신규 파일 추가는 `edit-sidebar/forms/LockToggleForm.tsx` 등 관리자 전용 하위 컴포넌트만.
- S4 DoD에 "관리자 `template-designer/` 라우트 구현"을 명시.
- frontend-specialist의 기존 `(admin)/templates/` 유지 계획(§7.2)은 **템플릿 목록 페이지**로 역할 축소. 편집은 `/template-designer/[id]`로 위임.

**후속 조치**

- `phase1_architecture.md §4.2.2` 라우트 목록에 `(admin)/template-designer/` 항목 추가.
- `phase1_architecture.md` 부록 C 폴더 구조 트리에 해당 경로 추가.
- `phase1_frontend_design.md §1` 폴더 구조 및 §7.2 이관 계획 업데이트 필요 (Phase 2 병합 시).

---

### Q10 — iframe postMessage 프로토콜 + 서버 PATCH 단위

**원질문 (frontend-specialist §8.3)**
프리뷰 갱신 시 전체 Schema 교체 vs JSON Patch(RFC 6902)? 효율성·복잡도·동시편집 리스크 고려. backend-specialist 공동 결정.

**결정** — **Phase 1 기준선: (a) 브라우저 ↔ iframe 간은 **부분 메시지**(element-select, token-update, schema-patch-local), (b) 서버 저장은 **`PATCH /v2/documents/{id}`의 Partial DocumentSchema**로 확정. RFC 6902 JSON Patch는 도입하지 않는다.**

**근거**

1. **동시편집(collaborative editing)은 현 제품 요구 아니다**. DocUtil의 designer는 단일 사용자 세션 전제다(frontend-specialist §4.1 인터랙션 설명 참조). RFC 6902 JSON Patch가 빛나는 시나리오는 다중 사용자 OT/CRDT 환경이며, 현 단계에서 도입은 과도한 일반화다.
2. **페이로드 크기 실측**: 평균 문서 schema는 20페이지×10컴포넌트 기준 ~100KB(database-architect §3.1). 편집 단위는 보통 "한 컴포넌트 props 한 필드" → 수백 bytes. 전체 schema 교체 PATCH 비용은 100KB/500ms(debounce) = 200KB/s로 네트워크 부담이 실질적으로 없다. **Partial DocumentSchema**(변경된 `pages[n].components[m]`만 포함하는 부분 본체)로 보내면 이를 한 번 더 1~5KB로 줄일 수 있다.
3. **Partial DocumentSchema의 정의**:
   ```
   PATCH /v2/documents/{id}
   body: {
     "patch_type": "component",      // or "page", "tokens", "metadata"
     "page_id": "p3",
     "component_id": "c2",
     "component": { /* 전체 교체할 Component 객체 */ }
   }
   ```
   서버는 `patch_type`에 따라 JSONB 경로에 `jsonb_set`을 적용. 이는 RFC 6902의 "replace" 연산 하나만 쓰는 것과 동등하되, 도메인 타입 검증이 가능하다(Pydantic discriminator로 `Component` 교체 전 validation).
4. RFC 6902 도입의 실비용: (a) 클라이언트 JSON Patch 생성기 추가, (b) 서버 JSON Patch 적용·검증 라이브러리 추가, (c) `ComponentBase.id` 안정성 보장 테스트, (d) 잘못된 path 공격 방어. 이 네 가지는 단일 사용자 환경에서 비용만 지불하고 얻는 이득이 없다. YAGNI.
5. iframe ↔ Shell 메시지 프로토콜은 **도메인 전용 메시지** 3~4종으로 충분:
   ```
   { type: "element-select", component_id, page_id }
   { type: "token-update", tokens }                // 색상·폰트 등 (서버 저장 전 실시간 미리보기)
   { type: "schema-patch-local", patch }           // Shell → iframe 재렌더 트리거 (네트워크 무관)
   { type: "export-request", format }
   ```
   이들은 RFC 6902와 무관한 **앱 내부 프로토콜**로, 메시지 스키마는 `types/document-schema.ts`에 함께 둔다.

**영향**

- `lib/api/documents-v2.ts`의 `updatePage` 시그니처 확정:
  ```
  updatePage(documentId, { page_id, component_id?, component?, page? }): Promise<DocumentSchema>
  ```
- `PATCH /v2/documents/{id}` 서버 API:
  - request body: Partial DocumentSchema (`patch_type` 판별 필드 + 부분 본체).
  - response body: 전체 DocumentSchema (클라이언트 캐시 동기화용).
- frontend-specialist §5.1 훅 시그니처 확정(전체 교체 가정은 폐기).
- backend-specialist Phase 4 S1 scope: `documents_v2/router.py`에 PATCH 엔드포인트 + 서비스 레이어 `jsonb_set` 적용 로직.
- **동시편집 요구가 발생하면 v2.0 마이그레이션**: 본 결정은 RFC 6902로의 장래 이행을 막지 않는다(body 구조가 호환되므로).

**후속 조치**

- `phase1_architecture.md §4.4` 동기성 표에 "편집 저장 = PATCH (Partial DocumentSchema)" 행 추가.
- `phase1_architecture.md §4.3` 데이터 흐름도에 "편집: PATCH body = {patch_type, page_id, component_id?, component?}" 추가.
- `phase1_frontend_design.md §5.1`의 TODO("S1에서 JSON Patch 지원 여부 결정 필요")를 본 결정으로 해소했음을 명시 필요 (Phase 2 병합 시).

---

## 2. 변경이 필요한 다른 문서

| 문서 | 변경 유형 | 변경 내용 요약 | 반영 시점 |
|---|---|---|---|
| `phase1_architecture.md` | **본문 수정** | §3.2 MVP 5→6종, §7.3 표 주석, §9.1 S1/S5 DoD 갱신, §4.2.2/§4.3/§4.4 라우트·PATCH 반영. 변경이력 §Change Log v1.6 추가 | Phase 1 종료 시점(본 작업) |
| `phase1_database_design.md` | **변경이력만 추가** | §9 변경이력에 "v1.1 — `phase1_decisions.md` 반영 필요 (Q1~Q4 해소)" 한 줄. 본문 변경은 Phase 2 | 본 작업 |
| `phase1_frontend_design.md` | **변경이력 신설** | 문서 말미에 "## 10. 변경이력" 섹션 신설, v1.1 항목 추가 | 본 작업 |
| `phase1_hwpx_adapter.md` | **변경이력 신설** | 문서 말미에 "## 8. 변경이력" 섹션 신설, v1.1 항목 추가 | 본 작업 |
| `phase1_frontend_wireframes.md` | 변경 불필요 | Q10 결정은 wireframe 다이어그램 수준에 영향 없음 | — |
| `techspec.md` | **§14 신설** | "## 14. Phase 1 — 후속 의사결정" 추가, 10건 결정 요약 + 본 문서 링크 | 본 작업 |
| `phase1_decisions.md` | **본 문서** | — | — |

---

## 3. 정리

Phase 1의 기준선과 3개 후속 설계가 교차하면서 드러난 10건의 모호성은 본 문서로 모두 확정됐다. 결정의 공통 기조는 **(i) YAGNI**(Q2·Q10), **(ii) P1~P7 일관성**(Q1·Q5·Q9), **(iii) 스프린트 현실성**(Q6·Q7), **(iv) 제품 시연 가치**(Q8), **(v) 사용자 실무 요구 반영**(Q3·Q4, v1.1) 다섯 가지다.

**v1.1 변경 요약 (2026-04-20 사용자 결정)**:
- **Q3 뒤집힘**: Mode 전환 기능을 Phase 1 범위 포함으로 변경. S4 기간 1.5주 → 2주 확장. CHECK 제약을 서비스 레이어 소프트 체크로 전환. `POST /v2/documents/{id}/switch-mode` API 신설.
- **Q4 확정**: 조직별 PPTX 템플릿 실재 확인 (회사·대학 등). S4 기간 2주 → **2.5주** 추가 확장 (Q3 누적 시 S4 총 2주 확장 = 3.5주). S0 선행 조사 필수. Organization 도메인 모델 검토(`organization_type` 필드) 편입.
- 두 결정 누적으로 **S7 QA 여유분 2주에서 1주를 S4로 이전**. 전체 13~14주 일정은 유지.

전체적으로 사용자 요구(Mode A+B 동시 지원, **Mode 전환 포함**, **다조직 지원**, HWP/HWPX, 5대 이슈)를 모두 수용한다. Phase 2 전환계획 수립 에이전트는 본 문서 v1.1을 **불변 입력**으로 간주하고 S1~S7 실행 계획을 상세화하며, **S0 조직별 템플릿 전수 조사**를 첫 번째 작업으로 포함한다.

---

## 4. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|---|---|---|
| v1.0 | 2026-04-19 | 최초 작성. Q1~Q10 10건 확정 (enterprise-architect + 3건 사용자 승인 권장) |
| v1.1 | 2026-04-20 | 사용자 결정 반영. Q3 뒤집힘(Mode 전환 포함), Q4 확정(조직별 템플릿 실재), Q8 유지 확인. S4 기간 2주 확장, S0 조사 범위 확대 |
| v1.2 | 2026-04-20 | S0 조사 후 Q4 재해석. 조직별 양식은 "향후 로드맵, 현재 데이터 없음"으로 확정. S4 기간 3.5주 → 2.5주 축소. Alembic 008 스킵. R12·R13 제거, U4 완화. 다조직 설계 구조는 유지. |

---

**(문서 끝)**
