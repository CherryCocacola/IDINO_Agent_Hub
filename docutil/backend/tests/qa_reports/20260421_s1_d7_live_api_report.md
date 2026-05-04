# Phase 4 S1 D7 Live API 검증 리포트

- 총 호출 수: 8
- 추정 총 비용 (USD): 0.1546

## 프로바이더별 요약

| provider | calls | passed | pass_rate | avg_latency_s | avg_cost_usd |
|----------|-------|--------|-----------|---------------|--------------|
| openai | 8 | 7 | 87.5% | 6.58 | 0.022091 |

## 시나리오별 요약

| scenario | calls | passed | avg_pages | avg_components | avg_korean |
|----------|-------|--------|-----------|----------------|------------|
| minutes | 3 | 3 | 4.7 | 13.0 | 0.82 |
| proposal | 2 | 1 | 5.0 | 10.0 | 0.88 |
| slide_report | 3 | 3 | 3.0 | 6.3 | 0.75 |

## 실패 케이스

- [openai/proposal #0] ValidationError: 1 validation error for DocumentSchema
pages.1.components.0.ExecutiveSummary.bullets
  List should have at least 3 items after validation, not 2 [type=too_short, input_value=['현재 IT 인프라의 ...연성 향상 기대'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.13/v/too_short
