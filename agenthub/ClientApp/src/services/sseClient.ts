/**
 * SSE (Server-Sent Events) 스트리밍 클라이언트
 *
 * EventSource는 GET 전용이므로 POST 본문을 보내야 하는 채팅 스트리밍에는 사용할 수 없다.
 * 따라서 fetch + ReadableStream + TextDecoder 패턴으로 직접 구현한다.
 *
 * 백엔드 SSE 응답 명세 (POST /api/chat/send/stream):
 *   data: {"type":"delta","content":"<token>"}\n\n
 *   data: {"type":"meta","conversationId":123,"messageId":456,"model":"gpt-4o-mini"}\n\n
 *   data: {"type":"usage","promptTokens":10,"completionTokens":20,"totalTokens":30,"cost":0.0001}\n\n
 *   data: {"type":"error","code":"...","message":"..."}\n\n
 *   data: [DONE]\n\n
 *
 * 인증:
 * - axios 인터셉터(`@/services/api`)와 동일하게 localStorage `'token'`(JWT)을 Bearer 헤더로 부착
 * - 401 응답 시 `/api/auth/refresh`로 토큰 갱신 후 1회 재시도
 *
 * 의존성:
 * - 새 npm 패키지 추가 없음 (fetch / ReadableStream / TextDecoder 모두 표준 브라우저 API)
 */

import {
  safeGetAuthStorage,
  safeGetLocalStorage,
  safeSetAuthStorage,
  safeRemoveAuthStorage
} from '@/utils/storage'
import { notifyAndRedirectToLogin } from '@/services/api'

// ============================================================================
// 타입 정의
// ============================================================================

/**
 * 백엔드가 SSE 프레임으로 흘려주는 모든 이벤트 타입의 합집합.
 * 한 프레임에는 type별 일부 필드만 채워져 옴.
 */
export interface ChatStreamEvent {
  type: 'delta' | 'meta' | 'usage' | 'error'
  // delta
  content?: string
  // meta
  conversationId?: number
  messageId?: number
  model?: string
  // usage
  promptTokens?: number
  completionTokens?: number
  totalTokens?: number
  cost?: number
  // error
  code?: string
  message?: string
}

/**
 * /api/chat/send/stream 요청 본문.
 * `/api/chat/send`(비스트리밍)와 동일한 페이로드 — `stream: true`만 다름.
 */
export interface SendDirectMessageStreamRequest {
  serviceId: number
  agentId?: number | null
  conversationId?: number
  model?: string
  temperature?: number
  maxTokens?: number
  messages: Array<{
    role: string
    content?: string
    contents?: Array<{
      type: string
      text?: string
      image_url?: { url: string }
      audio_url?: string
      file_url?: string
      file_name?: string
    }>
  }>
  stream?: boolean
  enableWebSearch?: boolean
  enableRag?: boolean
  ragTopK?: number
  documentIds?: number[] | null
  language?: string
  enableDeepResearch?: boolean
  enableDeepThinking?: boolean
  thinkingMode?: string
}

// ============================================================================
// SSE 라인 파서
// ============================================================================

/**
 * `[DONE]` 마커 전용 sentinel. 일반 ChatStreamEvent와 union으로 구별된다.
 */
const DONE_MARKER: unique symbol = Symbol('SSE_DONE')

/**
 * SSE 본문을 ChatStreamEvent 스트림으로 변환하는 AsyncGenerator.
 *
 * fetch ReadableStream chunk는 임의 경계로 잘려 도착하므로, `\n\n` 프레임 구분자에 도달할
 * 때까지 buffer에 누적한 뒤, 완성된 프레임만 yield하고 미완성 잔여분은 다음 chunk 처리로
 * 이월(carry over)한다.
 *
 * 각 프레임은 `data: <payload>\n\n` 형태:
 * - payload가 `[DONE]`이면 generator 종료
 * - payload가 JSON이면 ChatStreamEvent로 yield
 * - JSON 파싱 실패는 console.warn 후 silently skip (스트림 자체는 종료하지 않음)
 *
 * SSE 표준상 `event:` `id:` `retry:` 라인도 있으나 백엔드 명세는 `data:` 단일 라인이므로
 * 본 구현은 `data:` 만 처리한다.
 */
async function* parseSseStream(
  reader: ReadableStreamDefaultReader<Uint8Array>
): AsyncGenerator<ChatStreamEvent, void, unknown> {
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      // 스트림이 끝났는데 buffer에 잔여 데이터가 있으면 마지막으로 처리 시도.
      // Phase 3 vue-tsc 2.x 부채 정리 — DONE_MARKER 가드 추가 (TS2322 해소).
      // 잔여 buffer 가 [DONE] 마커 단독이면 종료 신호로 흡수, 일반 이벤트만 yield.
      if (buffer.trim().length > 0) {
        const event = parseFrame(buffer)
        if (event && event !== DONE_MARKER) yield event
      }
      return
    }

    buffer += decoder.decode(value, { stream: true })

    // \n\n 으로 프레임을 분할. 마지막 조각은 미완성일 수 있으므로 buffer에 유지
    let frameEndIndex: number
    while ((frameEndIndex = buffer.indexOf('\n\n')) !== -1) {
      const rawFrame = buffer.slice(0, frameEndIndex)
      buffer = buffer.slice(frameEndIndex + 2)

      const event = parseFrame(rawFrame)
      if (event === DONE_MARKER) {
        return
      }
      if (event) {
        yield event
      }
    }
  }
}

/**
 * 단일 SSE 프레임 텍스트(예: "data: {...}")를 파싱한다.
 * - `[DONE]` 마커: 스트림 종료 신호 → DONE_MARKER 반환
 * - 정상 JSON: ChatStreamEvent 반환
 * - 빈 줄/주석/`data:` 미시작: null
 * - JSON 파싱 실패: null + console.warn
 */
function parseFrame(rawFrame: string): ChatStreamEvent | typeof DONE_MARKER | null {
  // CRLF 정규화 + 빈 라인 제거. SSE 프레임은 여러 라인일 수 있으나 백엔드는 단일 data 라인.
  const lines = rawFrame.split('\n').map((l) => l.replace(/\r$/, ''))
  const dataLines = lines
    .filter((l) => l.startsWith('data:'))
    .map((l) => l.slice(5).replace(/^ /, '')) // "data: " 또는 "data:" 모두 대응

  if (dataLines.length === 0) return null

  // 다중 data 라인은 \n으로 join하여 단일 payload로 합침 (SSE 표준)
  const payload = dataLines.join('\n').trim()
  if (payload.length === 0) return null

  if (payload === '[DONE]') return DONE_MARKER

  try {
    const parsed = JSON.parse(payload) as ChatStreamEvent
    return parsed
  } catch (err) {
    // 잘못된 JSON 한 프레임이 전체 스트림을 죽이지 않도록 silently skip
    console.warn('[sseClient] Invalid JSON frame, skipping:', payload, err)
    return null
  }
}

// ============================================================================
// 토큰 갱신 (axios 인터셉터의 정책을 단순화하여 재구현)
// ============================================================================

/**
 * Refresh Token 으로 신규 access token 을 받아 저장한다.
 *
 * 트랙 #97-post3 fix-A:
 * - 기존: safeRemoveLocalStorage 만 호출 → sessionStorage 토큰 잔존 →
 *   /login 진입 시 router 가드(index.ts:438-441) 가 token 잔존 판정으로
 *   `/` (Dashboard) 로 redirect → "Send 후 대시보드 이탈" 결함
 * - 신규: safeRemoveAuthStorage(양쪽 청소) + notifyAndRedirectToLogin 호출
 *   (axios 인터셉터와 동일 정책 — i18n 알림 + in-flight 가드 + 양쪽 storage 청소)
 *
 * 신규 access token 영속성:
 * - 기존 token 이 localStorage 에 있었으면 영속(persistent=true) 모드 유지
 * - sessionStorage 에 있었으면 휘발(persistent=false) 모드 유지
 *   → safeSetAuthStorage 가 반대편 저장소를 자동 청소하므로 일관성 보장
 */
async function refreshAccessToken(): Promise<string | null> {
  // refresh token 은 양쪽 저장소 어디든 (rememberMe 켰다 껐다 한 흔적 대응)
  const refreshToken = safeGetAuthStorage('refreshToken')
  if (!refreshToken) {
    // 양쪽 청소 + 사용자 알림 + /login 리다이렉트 (axios 인터셉터와 동일)
    notifyAndRedirectToLogin('auth.session.noRefreshToken')
    return null
  }

  // 현재 토큰의 저장 위치로 영속성 결정 (rememberMe 정책 유지)
  const persistent = !!safeGetLocalStorage('token') || !!safeGetLocalStorage('refreshToken')

  try {
    const resp = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken })
    })
    if (!resp.ok) throw new Error(`refresh failed: ${resp.status}`)
    const data = (await resp.json()) as { token?: string; refreshToken?: string }
    if (!data.token) throw new Error('refresh response missing token')

    safeSetAuthStorage('token', data.token, persistent)
    // 신규 refreshToken 도 같이 회전되어 오면 갱신 (백엔드가 회전 정책일 때)
    if (data.refreshToken) {
      safeSetAuthStorage('refreshToken', data.refreshToken, persistent)
    }
    return data.token
  } catch (err) {
    console.warn('[sseClient] Token refresh failed:', err)
    notifyAndRedirectToLogin('auth.session.expired')
    return null
  }
}

// ============================================================================
// 공개 API
// ============================================================================

/**
 * /api/chat/send/stream 으로 SSE 스트리밍 채팅을 시작하고, 받은 ChatStreamEvent를 순차 yield한다.
 *
 * 사용 예:
 * ```ts
 * const ctrl = new AbortController()
 * for await (const evt of streamChat(payload, ctrl.signal)) {
 *   if (evt.type === 'delta') assistantMsg.content += evt.content ?? ''
 * }
 * ```
 *
 * 에러 처리 정책:
 * - HTTP 401 → refreshAccessToken() 후 1회 재시도
 * - HTTP 4xx/5xx (401 제외) → Error throw (호출자가 catch)
 * - AbortController.abort() → fetch가 AbortError throw → 호출자가 catch
 * - 네트워크 단절 → fetch reject → 호출자가 catch
 * - SSE 본문 내 `{"type":"error",...}` → 정상적으로 yield (스트림 종료 신호 아님,
 *   백엔드가 곧이어 [DONE]을 흘려야 함)
 *
 * @param payload 비스트리밍 /api/chat/send 와 동일 페이로드. stream 플래그는 자동으로 true로 강제
 * @param signal AbortController.signal — 사용자가 "중단" 버튼 등을 누를 때 호출
 */
export async function* streamChat(
  payload: SendDirectMessageStreamRequest,
  signal?: AbortSignal
): AsyncGenerator<ChatStreamEvent, void, unknown> {
  const body = JSON.stringify({ ...payload, stream: true })

  let response = await sendStreamRequest(body, signal)

  // 401 처리: refresh 후 1회 재시도
  if (response.status === 401) {
    const newToken = await refreshAccessToken()
    if (!newToken) {
      throw new Error('인증이 만료되었습니다. 다시 로그인해 주세요.')
    }
    response = await sendStreamRequest(body, signal, newToken)
  }

  if (!response.ok) {
    // 에러 본문이 JSON이면 message 추출
    let errorMessage = `요청이 실패했습니다. (HTTP ${response.status})`
    try {
      const errBody = await response.json()
      if (errBody?.message) errorMessage = errBody.message
    } catch {
      // 본문이 JSON이 아니면 상태 코드만 노출
    }
    throw new Error(errorMessage)
  }

  if (!response.body) {
    throw new Error('응답 본문이 비어 있습니다.')
  }

  const reader = response.body.getReader()
  try {
    yield* parseSseStream(reader)
  } finally {
    // ReadableStream은 abort/소비 완료 시 자동 정리되지만, 명시적 cancel로 잔여 chunk 폐기
    try {
      await reader.cancel()
    } catch {
      // 이미 닫혔으면 무시
    }
  }
}

/**
 * fetch POST 호출. 토큰을 Bearer 헤더로 부착한다.
 */
function sendStreamRequest(
  body: string,
  signal?: AbortSignal,
  overrideToken?: string
): Promise<Response> {
  const token = overrideToken ?? safeGetLocalStorage('token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream'
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  return fetch('/api/chat/send/stream', {
    method: 'POST',
    headers,
    body,
    signal,
    // SSE는 keep-alive가 필요 — 기본 fetch가 처리하나, 일부 환경에서 캐시 회피 권장
    cache: 'no-store'
  })
}
