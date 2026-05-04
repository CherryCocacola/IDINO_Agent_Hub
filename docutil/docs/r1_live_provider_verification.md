# R1 Live Provider Verification — Phase 4 S1 D7

- 실행 일자: 2026-04-19
- 실행 환경: 서버 `docutil-api` 컨테이너 (192.168.10.39)
- 스크립트: `scripts/run_s1_d7_live_api.py` (SSH → docker exec pytest)
- 메트릭 원본: `backend/tests/qa_reports/20260421_s1_d7_live_api_metrics.json`

## 1. 요약

| provider | 실 API 호출 | 스키마 PASS | 시나리오 품질 PASS | 판정 |
|----------|-------------|-------------|---------------------|------|
| openai (gpt-4o) | 8/8 | 7/8 (87.5%) | 3/8 (37.5%) | **NEED_FIX (프롬프트 개선 필요)** |
| azure_openai | 0/0 (skip) | N/A | N/A | **BLOCKED (API 키 부재)** |
| gemini | 0/0 (skip) | N/A | N/A | **BLOCKED (API 키 부재)** |
| anthropic | 0/0 (skip) | N/A | N/A | **BLOCKED (API 키 부재)** |

- 총 실 API 호출: **8회** (슬라이드 3 + 회의록 3 + 제안서 2)
- 추정 비용: **$0.15** (gpt-4o 입력 $0.0025/1K + 출력 $0.01/1K 기반 근사치)

## 2. 발견 1 — D5 `pydantic_to_openai_schema` strict 모드 결함

**현상**: OpenAI `response_format.json_schema.strict=true` 로 DocumentSchema 를 전송하면 400 Bad Request.

```
"Invalid schema for response_format 'DocumentSchema': In context=(),
 'required' is required to be supplied and to be an array including every key in properties.
 Missing 'status'."
```

**원인**: OpenAI strict 모드는 object 타입의 `required` 배열이 `properties` 의 **모든 키** 를 포함하도록 요구한다. Pydantic v2 는 Optional 필드 (예: `ActionItem.status`) 는 `required` 에서 제외하므로 strict 검증에 실패한다.

**검증**: D5 mock 테스트 30 PASS 는 httpx.AsyncClient.post 를 monkeypatch 하여 응답을 가짜로 반환했기 때문에 실 API 호출 경로에서 이 400 이 발견되지 않았다.

**권고 (integrations/llm/ 수정 필요 — D5 보정)**:

1. `pydantic_to_openai_schema` 에 후처리 단계 추가:
   - 모든 object 타입 노드에 대해 `required = list(properties.keys())` 로 확장.
   - Optional 필드는 `type: [<원래>, "null"]` 로 표현.
2. 또는 DocumentSchema 의 모든 필드를 명시적 기본값 (`None`) + `required` 포함으로 재설계.

본 검증에서는 `integrations/llm/` 수정 금지 제약에 따라 **테스트 내에서 `strict=false`** 로 우회 호출했다. 이 우회의 대가는 OpenAI 가 스키마를 "가이드라인" 으로만 간주하여 `document_id="doc_001"` 같은 비UUID 값을 반환한다는 점이다 (아래 발견 2 참고).

## 3. 발견 2 — LLM 은 `document_id` UUID 를 안정적으로 생성하지 못함

첫 3회 slide_report 호출에서 LLM 은 다음과 같은 비UUID 값을 반환했다.

| repeat | document_id 값 |
|--------|----------------|
| 0 | `2026_q1_sales_report` |
| 1 | `2026Q1_Sales_Report` |
| 2 | `doc_001` |

**상태**: 실 production 경로 (`DocumentServiceV2._apply_metadata_overrides`) 는 서버가 생성한 UUID 로 이를 **덮어쓴다**. 테스트는 이 덮어쓰기 로직을 재현하도록 수정하여 3건 모두 PASS 처리했다.

**권고**: D6 시스템 프롬프트에 `document_id` 는 서버가 채우므로 LLM 은 임의 UUID (예: `"00000000-0000-0000-0000-000000000000"`) 를 넣으라고 명시하거나, 아예 `document_id` 필드를 required 에서 제외하고 LLM 응답 후 서버가 주입하도록 스키마를 분리.

## 4. 발견 3 — `ActionItem.due` ISO-8601 준수 실패

D6 `_MINUTES` 프롬프트에 날짜 형식 규정이 없어 LLM 은 `"2023년 10월 27일"` 같은 한국어 표기를 생성.

**권고 (D6 constants.py 개선)**: `COMMON_INSTRUCTIONS` 에 다음을 추가.

```python
"- 모든 date 필드 (ActionItem.due 등) 는 반드시 ISO-8601 형식 "
"'YYYY-MM-DD' 로만 작성. '2025년 10월 27일' 같은 한국어 표기 금지."
```

본 검증에서는 live 테스트용 inline 보강으로 이 문제를 해결했다. 보강 후 minutes 3/3 스키마 검증은 PASS.

## 5. 발견 4 — 페이지 수 / 컴포넌트 수 가이드 미준수

### 5.1 minutes: 4~6 페이지 생성 (기대 1~3)

모든 minutes 호출이 `title / attendees / agenda / action_items` 를 **별도 페이지로 분리**하여 4~6 페이지 생성.

D6 `_MINUTES` 프롬프트 원문:
> "1) 회의 제목 / 일시, 2) AttendeeList, 3) 안건별 Heading + Paragraph + BulletList, 4) ActionItemList"

LLM 이 위 번호 목록을 "페이지 분할" 신호로 해석. 안건 개수 × 페이지 × ActionItemList 1 페이지 + 제목 페이지 = 쉽게 4~6 페이지.

**권고**: 프롬프트에 **명시적 페이지 수 상한** 추가.

```
"회의록 페이지 수는 최대 3 페이지로 제한합니다. 여러 안건은 하나의 page.components "
"배열에 순차적으로 나열하고, 안건마다 새 페이지를 만들지 마세요."
```

### 5.2 proposal: 필수 컴포넌트 누락 (RiskMatrix / DataTable)

시나리오 C 의 `proposal #1` 은 `RiskMatrix / DataTable` 중 하나 이상을 포함해야 하는데 둘 다 누락. LLM 이 "리스크" 를 `BulletList` 로만 표현.

**권고**: 프롬프트에 **조건부 강제** 추가.

```
"제안서에 '리스크', '위험', 'risk' 등 단어가 프롬프트에 포함되면 반드시 RiskMatrix "
"컴포넌트를 1개 이상 생성하세요. 일반 BulletList 로 대체 금지."
```

### 5.3 proposal: ExecutiveSummary.bullets 개수 위반

`ExecutiveSummary.bullets` 는 `min_length=3, max_length=5` 제약인데 LLM 이 2 개 bullet 만 생성 → ValidationError.

**권고**: `_PROPOSAL` 프롬프트에 `"ExecutiveSummary 는 반드시 3~5 개 bullet 항목으로 작성"` 명시.

## 6. OpenAI 레이트 리밋 (429 TPM=30,000)

첫 실행에서 `slide_report + minutes + proposal` 을 sleep 없이 연속 호출하여 `proposal #0` 에서 TPM (tokens-per-minute) 제한 도달. 두 번째 실행에서 각 호출 사이 `asyncio.sleep(20)` 추가로 해결.

**권고 (서비스 레이어)**: `DocumentServiceV2.generate` 에 429 수신 시 `Retry-After` 헤더 기반 재시도 로직 추가. 현재는 예외가 502 Bad Gateway 로 매핑되어 사용자 체감 실패.

## 7. Gemini 평탄화 어댑터 실 동작 검증

Gemini API 키 부재로 **live 검증 불가**. D5 mock 테스트에서 `pydantic_to_gemini_schema` 가 `$ref / oneOf / anyOf` 제거를 정상 수행하는 것은 확인 (unit test `TestSchemaAdapter::test_gemini_schema_removes_unions_and_refs` PASS).

D8 이전에 GOOGLE_API_KEY 확보 + 재실행 필요 (BLOCKED).

## 8. Claude Tool Use 실 동작 검증

Anthropic API 키 부재로 **live 검증 불가**. D5 mock 테스트에서 Claude Tool Use 패턴이 정상 동작하는 것은 확인. 실 API 에서의 Discriminated Union 수용성은 미검증 — BLOCKED.

## 9. Azure OpenAI 검증

Azure 리소스 미준비 + 환경변수 4 종 (endpoint/deployment/version/key) 미설정 — 검증 범위에서 제외. Azure 는 OpenAI 와 동일 response_format 을 사용하므로 발견 1 (strict 모드 결함) 이 동일하게 재현될 것으로 예상.

## 10. Provider 기본값 선택 가이드 (document_type 별)

현 시점 검증 결과만 근거로 한 **잠정** 권고 (실 API 가용성이 OpenAI 로 한정됨):

| document_type | 권장 기본 provider | 사유 |
|---------------|-------------------|------|
| slide_report | openai | 시나리오 A 3/3 PASS, 페이지/컴포넌트 기대 일치 |
| minutes | openai | (프롬프트 개선 후) 한국어 자연스러움 양호 (한글 비율 82%) |
| proposal | openai | (프롬프트 개선 후) 복잡 구조도 수용. ExecutiveSummary 제약 강화 필요 |
| docx_report / one_pager / weekly_status / freeform_doc | openai (기본값) | 본 D7 범위 밖, D8 에서 추가 검증 예정 |

**Gemini** 는 저비용 (약 1/30) 이므로 프롬프트 개선 후 재검증 시 `slide_report` 기본값 후보로 평가 권고.

**Claude** 는 Tool Use 의 엄격한 스키마 준수 경향을 고려해 `proposal` (복잡 스키마) 기본값 후보.

## 11. R1 최종 판정

| 항목 | 상태 |
|------|------|
| OpenAI | **PARTIAL PASS** — strict 모드 결함으로 strict=false 우회 필요, 프롬프트 개선 시 3/3 slide_report |
| Azure OpenAI | **BLOCKED** — API 키 부재 |
| Gemini | **BLOCKED** — API 키 부재 (mock 30 PASS 유효) |
| Anthropic | **BLOCKED** — API 키 부재 (mock 30 PASS 유효) |

**R1 `live_verified` = PARTIAL PASS (openai only)**

D8 선행조건:
1. **Required**: D5 `pydantic_to_openai_schema` 의 strict 모드 결함 수정 (혹은 LLMClient 수준 fallback).
2. **Required**: D6 `constants.py` 에 § 4·5 권고사항 반영.
3. **Recommended**: Azure/Gemini/Anthropic API 키 환경 구비 후 재검증 (32 호출 × ~$0.10 = $3 예상).
