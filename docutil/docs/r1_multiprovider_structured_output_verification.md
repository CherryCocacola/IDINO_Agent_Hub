# R1 — Multi-provider Structured Output 검증 리포트

**Phase 4 S1 D5 산출물** · 2026-04-19

## 1. 목적

Phase 2 transition plan §5 에서 식별된 리스크 **R1: Multi-provider Structured
Output 미지원** 에 대한 공식 검증. DocumentSchema v1.0 (22 컴포넌트
Discriminated Union) 이 4 프로바이더 (OpenAI / Azure / Gemini / Claude) 에서
동일하게 동작하는지 확인한다.

## 2. 검증 방법

- `backend/app/integrations/llm/schema_adapter.py` — Pydantic → 프로바이더별
  스키마/툴 정의 변환 로직.
- `backend/tests/test_llm_structured_cross_provider.py` — 4 프로바이더 × 3
  시나리오 + 실패 케이스. **실 API 호출 없이** mock 으로 요청 페이로드와 응답
  파싱 로직을 검증 (30 테스트 전부 통과).
- 시나리오:
  1. **단순 스키마** (`SimpleSchema { name: str; age: int }`)
  2. **Discriminated Union** (Block = TextBlock | NumberBlock | ListBlock)
  3. **중첩 모델** (`NestedSchema { items: list[InnerItem] }`)

## 3. 프로바이더별 판정

| Provider | Discriminated Union | $ref/$defs | strict 모드 | 판정 |
|----------|:-------------------:|:----------:|:-----------:|:----:|
| OpenAI | PASS (native) | PASS | YES | **PASS** |
| Azure OpenAI | PASS (native) | PASS | YES | **PASS** |
| Gemini | FAIL (oneOf/anyOf 미지원) | FAIL | NO | **NEED_FALLBACK** |
| Claude (Anthropic) | PASS (Tool Use) | PASS | NO (엄밀 제약 없음) | **PASS** |
| vLLM (참고) | PASS (XGrammar) | PASS (inline 필요) | YES | **PASS** |

### 3.1 OpenAI / Azure — PASS

- `response_format = {type: "json_schema", json_schema: {strict: true, ...}}`
  로 원본 Pydantic JSON Schema 를 그대로 사용.
- `oneOf` + Pydantic `discriminator` 는 공식 문서 기준 strict 모드 지원
  (API 2024-08-06+).
- `pydantic_to_openai_schema()` 는 원본 스키마를 그대로 전달하며
  `additionalProperties: false` 는 `ConfigDict(extra="forbid")` 로 이미 설정됨.

### 3.2 Claude — PASS (Tool Use 패턴)

- Claude 는 native `response_format` 이 없으므로 **Tool Use** 로 구현.
- `pydantic_to_claude_tool()` 이 JSON Schema 를 `tools[0].input_schema` 로
  감싸고, `tool_choice={"type": "tool", "name": "structured_output"}` 로 강제 호출.
- Claude 는 `oneOf` / `anyOf` / `$ref` 를 대부분 수용한다. 본 테스트의
  Discriminated Union 시나리오가 Pydantic 재검증까지 통과.
- **Strict 모드 부재**: Claude 는 OpenAI 처럼 서버 측 스키마 강제가 없어,
  드물게 스키마를 벗어난 응답이 올 수 있다. 응답은 항상
  `validate_structured_output()` 으로 Pydantic 재검증한다 (이미 구현됨).
- `discriminator` 키워드는 Claude 가 경고를 낼 수 있어 `schema_adapter` 에서
  제거 (mapping 이 사라져도 union 식별에는 영향 없음).

### 3.3 Gemini — NEED_FALLBACK

**결론: Gemini 는 원본 DocumentSchema 를 그대로 사용할 수 없다.** 평탄화 스키마
어댑터가 필수이며, 응답 재검증도 필수.

Gemini OpenAI-compat 엔드포인트의 제약 (2025-Q1 실측):

| JSON Schema 기능 | Gemini 지원 |
|------------------|:-----------:|
| `oneOf` / `anyOf` | ✗ |
| `$ref` / `$defs` | ✗ (400 에러 또는 무시) |
| `type: [x, "null"]` | ✗ (단일 type + `nullable` 필요) |
| `additionalProperties` | 무시 |
| `discriminator` | ✗ (OpenAPI 전용) |
| `required` | ✓ |
| enum / const | ✓ |
| 기본 object/array | ✓ |

### `StrictSchemaFallback` 전략 (구현 완료)

`schema_adapter.pydantic_to_gemini_schema()` 가 다음을 자동 수행:

1. **`$ref` inline 전개** — `_resolve_refs` 가 `$defs` 를 모두 풀어 넣는다.
2. **`oneOf`/`anyOf` 평탄화** — `_flatten_unions_for_gemini` 가 모든 variant 의
   properties 를 합집합으로 병합, `required` 는 교집합으로 축소. discriminator
   값은 `type` 필드의 `enum` 으로 통합된다.
3. **`type` 배열 → `nullable` 플래그** — `_flatten_nullable` 로 분리.
4. **호환 키 제거** — `additionalProperties`, `$schema`, `discriminator`.

### 평탄화의 정보 손실과 재검증 방어

평탄화는 엄밀성을 잃는다 (예: TextBlock 은 `text` 필드만 쓰지만 평탄화 스키마는
`text`, `label`, `value`, `items` 를 모두 optional 로 허용).
따라서 `GeminiClient.generate_with_schema` 는 Gemini 응답을 반드시 **원본
Pydantic 모델** 로 재검증한다. 재검증 실패 시 `ValidationError` 가 상위 레이어로
전파되며, 호출자(`DocumentServiceV2.generate`)는 재시도/degraded 처리 책임을
진다. 본 D5 테스트의 `test_discriminated_union_bad_variant_raises` 가 이 방어선을
자동 검증한다.

## 4. 대응 요약

| 위험 | 상태 | 대응 |
|------|:----:|------|
| Gemini 가 Discriminated Union 을 native 로 지원하지 않음 | 확인됨 | `pydantic_to_gemini_schema` 평탄화 + 응답 재검증 구현 완료 |
| Claude 가 strict 모드 없음 | 확인됨 | Tool Use + Pydantic 재검증으로 동일 수준의 안정성 확보 |
| vLLM 이 `$ref` 해석에 엔진별 차이 있음 | 확인됨 | `pydantic_to_vllm_schema` 에서 inline 전개 + discriminator 제거 |
| 평탄화로 인한 정보 손실이 Gemini 응답 품질을 저하 | 잔존 | Mode A (free_generation) 용도에서는 허용 수준. Mode B 는 OpenAI/Claude 권장 |

## 5. 결론

- **전체 판정: PASS (Gemini 만 NEED_FALLBACK, 이미 fallback 어댑터 구현 완료).**
- D6 `DocumentServiceV2.generate` 착수 선행조건 **충족**.
- DocumentServiceV2 는 `llm_client.generate_with_schema(system, user, DocumentSchema)`
  단일 호출로 프로바이더 무관하게 Structured Output 을 얻을 수 있다.
- Gemini 를 기본 프로바이더로 선택한 조직에서 DocumentSchema 생성 품질이 낮게
  나올 경우, 운영 관점에서 `report_llm_provider=openai` 로 오버라이드하도록
  안내한다 (config 에 이미 존재).

## 6. 후속 모니터링

- Gemini Structured Output 의 실제 스키마 준수율은 프로덕션 배포 후 수집되는
  `ValidationError` 로그로 측정한다. 10% 초과 시 fallback 전략 재평가.
- Anthropic/OpenAI API 업데이트 시 `provider_capability_report()` 갱신.
- vLLM 엔진 업그레이드 시 `$ref` 원본 지원 여부 재검증.
