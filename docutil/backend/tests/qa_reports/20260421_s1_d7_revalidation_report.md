# Phase 4 S1 D7 Live API 검증 리포트

- 총 호출 수: 5
- 추정 총 비용 (USD): 0.0521

## 프로바이더별 요약

| provider | calls | passed | pass_rate | avg_latency_s | avg_cost_usd |
|----------|-------|--------|-----------|---------------|--------------|
| openai | 5 | 2 | 40.0% | 6.09 | 0.026058 |

## 시나리오별 요약

| scenario | calls | passed | avg_pages | avg_components | avg_korean |
|----------|-------|--------|-----------|----------------|------------|
| minutes | 3 | 1 | 2.0 | 7.0 | 0.80 |
| proposal | 2 | 1 | 5.0 | 11.0 | 0.96 |

## 실패 케이스

- [openai/minutes #0] HTTPStatusError: Client error '429 Too Many Requests' for url 'https://api.openai.com/v1/chat/completions'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429 | body={
    "error": {
        "message": "Rate limit reached for gpt-4o in organization org-heWlSIDqskxWM3Ubqb3sK4LL on tokens per min (TPM): Limit 30000, Used 30000, Requested 890. Please try again in 1.78s. Visit https://platform.openai.com/account/rate-limits to learn more.",
        "type": "tokens",
        "param": null,
        "code": "rate_limit_exceeded"
    }
}

- [openai/minutes #2] HTTPStatusError: Client error '429 Too Many Requests' for url 'https://api.openai.com/v1/chat/completions'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429 | body={
    "error": {
        "message": "Rate limit reached for gpt-4o in organization org-heWlSIDqskxWM3Ubqb3sK4LL on tokens per min (TPM): Limit 30000, Used 30000, Requested 890. Please try again in 1.78s. Visit https://platform.openai.com/account/rate-limits to learn more.",
        "type": "tokens",
        "param": null,
        "code": "rate_limit_exceeded"
    }
}

- [openai/proposal #0] HTTPStatusError: Client error '429 Too Many Requests' for url 'https://api.openai.com/v1/chat/completions'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429 | body={
    "error": {
        "message": "Rate limit reached for gpt-4o in organization org-heWlSIDqskxWM3Ubqb3sK4LL on tokens per min (TPM): Limit 30000, Used 30000, Requested 854. Please try again in 1.708s. Visit https://platform.openai.com/account/rate-limits to learn more.",
        "type": "tokens",
        "param": null,
        "code": "rate_limit_exceeded"
    }
}

