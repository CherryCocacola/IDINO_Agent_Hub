/**
 * postmessage-protocol.ts — Designer Shell ↔ Preview iframe 양방향 프로토콜
 *
 * Phase 4 S1 D3 확정본. `docs/phase1_decisions.md` v1.2 Q10 결정 반영.
 *
 * 3종 메시지 (모두 `docutil/<event>` namespace + `schemaVersion: 1`):
 *
 *   1. `docutil/element-select`      (iframe → parent)
 *      사용자가 프리뷰 안 컴포넌트를 클릭 → 부모 shell이 좌측 편집 사이드바 활성.
 *
 *   2. `docutil/token-update`        (parent → iframe)
 *      디자인 토큰 부분 변경 → iframe이 `--doc-*` CSS 변수만 override.
 *      (DesignTokens 전체가 아닌 부분 업데이트 허용. 병합은 `mergeTokens` 헬퍼.)
 *
 *   3. `docutil/schema-patch-local`  (parent → iframe)
 *      Partial DocumentSchema 부분 갱신 (서버 PATCH 와 동일한 body 구조).
 *      iframe은 해당 요소만 부분 리렌더. 전체 리렌더 X.
 *
 * origin 검증 필수 (XSS·타 도메인 주입 방어):
 *   - 부모는 iframe 로딩 시 expectedOrigin 을 보관했다가 수신 이벤트의 `event.origin`
 *     과 strict 비교한다. 다르면 silent drop.
 *   - Next.js same-origin 라우트(`/preview-host`)를 사용하므로 기본값은
 *     `window.location.origin`.
 *
 * 본 파일에는 런타임 의존성이 전혀 없다 (React / Next 모두 import 금지).
 * → iframe 내부 bootstrap 스크립트와 부모 shell 양쪽에서 동일하게 import 가능.
 */

import type { Component, DesignTokens, Page } from "@/types/document-schema";

// ─── 상수 ──────────────────────────────────────────────────────────────────

/** 현재 프로토콜 schemaVersion. Breaking change 시 2 로 올린다. */
export const PROTOCOL_SCHEMA_VERSION = 1 as const;

/** 네임스페이스 prefix — `docutil/` 로 시작하지 않는 메시지는 즉시 무시. */
export const PROTOCOL_NAMESPACE = "docutil/" as const;

// ─── 메시지 타입 리터럴 ────────────────────────────────────────────────────

export const MESSAGE_TYPES = {
  ELEMENT_SELECT: "docutil/element-select",
  TOKEN_UPDATE: "docutil/token-update",
  SCHEMA_PATCH_LOCAL: "docutil/schema-patch-local",
} as const;

export type MessageType = (typeof MESSAGE_TYPES)[keyof typeof MESSAGE_TYPES];

// ─── payload 정의 ──────────────────────────────────────────────────────────

/** 1) element-select: iframe → parent */
export interface ElementSelectPayload {
  pageId: string;
  componentId: string;
}

/**
 * 2) token-update: parent → iframe
 * DesignTokens 7필드 중 **변경된 키만** 담는다. iframe 측은 `mergeTokens` 로
 * 기존 토큰과 병합 후 CSS 변수를 갱신한다.
 */
export type TokenUpdatePayload = {
  tokens: Partial<DesignTokens>;
};

/**
 * 3) schema-patch-local: parent → iframe
 * 3가지 patchType 지원:
 *   - `page`      : 단일 Page 교체. `pageId` 필수, `data: Partial<Page>`
 *   - `component` : 단일 Component 교체. `pageId` + `componentId` 필수,
 *                   `data: Partial<Component>`
 *   - `tokens`    : DesignTokens 전체 교체. `pageId`/`componentId` 불필요,
 *                   `data: DesignTokens` (token-update 와 달리 전체 치환).
 *
 * 서버 PATCH `/v2/documents/{id}` 의 request body 구조와 1:1 매칭된다
 * (백엔드는 같은 형태를 받아 JSONB 에 적용). iframe 은 네트워크 없이
 * 로컬 스냅샷만 갱신.
 */
export type SchemaPatchPayload =
  | {
      patchType: "page";
      pageId: string;
      componentId?: never;
      data: Partial<Page>;
    }
  | {
      patchType: "component";
      pageId: string;
      componentId: string;
      data: Partial<Component>;
    }
  | {
      patchType: "tokens";
      pageId?: never;
      componentId?: never;
      data: DesignTokens;
    };

// ─── 통합 메시지 union ────────────────────────────────────────────────────

export interface BaseMessage<T extends MessageType, P> {
  type: T;
  schemaVersion: typeof PROTOCOL_SCHEMA_VERSION;
  payload: P;
}

export type ElementSelectMessage = BaseMessage<
  typeof MESSAGE_TYPES.ELEMENT_SELECT,
  ElementSelectPayload
>;

export type TokenUpdateMessage = BaseMessage<typeof MESSAGE_TYPES.TOKEN_UPDATE, TokenUpdatePayload>;

export type SchemaPatchMessage = BaseMessage<
  typeof MESSAGE_TYPES.SCHEMA_PATCH_LOCAL,
  SchemaPatchPayload
>;

export type PreviewMessage = ElementSelectMessage | TokenUpdateMessage | SchemaPatchMessage;

// ─── 타입 가드 ─────────────────────────────────────────────────────────────

function isPlainRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** `docutil/*` 네임스페이스 + schemaVersion 1 + 허용된 type 인 메시지만 true. */
export function isPreviewMessage(value: unknown): value is PreviewMessage {
  if (!isPlainRecord(value)) return false;
  const { type, schemaVersion, payload } = value;
  if (typeof type !== "string" || !type.startsWith(PROTOCOL_NAMESPACE)) return false;
  if (schemaVersion !== PROTOCOL_SCHEMA_VERSION) return false;
  if (!isPlainRecord(payload)) return false;

  const allowed: readonly string[] = Object.values(MESSAGE_TYPES);
  if (!allowed.includes(type)) return false;

  // payload 구조 최소 검증 (deep 검증은 TS 타입 + 런타임 zod 로 추후 강화)
  switch (type) {
    case MESSAGE_TYPES.ELEMENT_SELECT: {
      const { pageId, componentId } = payload as Record<string, unknown>;
      return typeof pageId === "string" && typeof componentId === "string";
    }
    case MESSAGE_TYPES.TOKEN_UPDATE: {
      const { tokens } = payload as Record<string, unknown>;
      return isPlainRecord(tokens);
    }
    case MESSAGE_TYPES.SCHEMA_PATCH_LOCAL: {
      const { patchType, data } = payload as Record<string, unknown>;
      if (patchType !== "page" && patchType !== "component" && patchType !== "tokens") {
        return false;
      }
      if (!isPlainRecord(data)) return false;
      if (patchType === "page") {
        return typeof (payload as Record<string, unknown>).pageId === "string";
      }
      if (patchType === "component") {
        const p = payload as Record<string, unknown>;
        return typeof p.pageId === "string" && typeof p.componentId === "string";
      }
      return true; // tokens
    }
    default:
      return false;
  }
}

// ─── 직렬화 / 역직렬화 ────────────────────────────────────────────────────

/**
 * 메시지를 postMessage 로 넘길 직렬화 가능한 객체로 인코딩한다.
 * postMessage 는 structured clone 으로 객체를 그대로 전달할 수 있으므로
 * JSON.stringify 까진 필요하지 않지만, 디버깅·로깅·테스트 목적의 헬퍼를 둔다.
 */
export function encode<M extends PreviewMessage>(message: M): M {
  if (!isPreviewMessage(message)) {
    throw new Error(
      `[postmessage-protocol] encode 거부: 알 수 없는 메시지 형태 (type=${
        (message as { type?: unknown }).type ?? "<missing>"
      })`,
    );
  }
  // freeze 로 호출자 측 우발적 mutate 방지.
  const frozen = Object.freeze({ ...message, payload: { ...message.payload } });
  return frozen as unknown as M;
}

/**
 * 수신한 임의 값을 안전하게 PreviewMessage 로 변환.
 * - `docutil/` 네임스페이스가 아니거나
 * - schemaVersion 이 다르거나
 * - payload 구조가 어긋나면 `null` 반환 (호출자는 silent drop).
 */
export function decode(value: unknown): PreviewMessage | null {
  if (!isPreviewMessage(value)) return null;
  return value;
}

// ─── origin 검증 ───────────────────────────────────────────────────────────

/**
 * 수신한 MessageEvent 가 예상 origin 에서 온 것인지 확인.
 * `expectedOrigin` 이 `"*"` 이면 검증 생략(비권장, 개발 중에만).
 */
export function verifyOrigin(
  eventOrigin: string,
  expectedOrigin: string,
): { ok: boolean; reason?: string } {
  if (expectedOrigin === "*") return { ok: true };
  if (eventOrigin === expectedOrigin) return { ok: true };
  return {
    ok: false,
    reason: `origin 불일치: received="${eventOrigin}" expected="${expectedOrigin}"`,
  };
}

// ─── 토큰 부분 병합 헬퍼 ──────────────────────────────────────────────────

/**
 * token-update 수신 시 기존 토큰에 부분 업데이트를 병합한다.
 * 값이 `undefined` 인 키는 무시 (기존 값 유지).
 */
export function mergeTokens(current: DesignTokens, partial: Partial<DesignTokens>): DesignTokens {
  const merged: Record<string, unknown> = { ...current };
  (Object.keys(partial) as Array<keyof DesignTokens>).forEach((key) => {
    const next = partial[key];
    if (next !== undefined) {
      merged[key as string] = next;
    }
  });
  return merged as unknown as DesignTokens;
}

// ─── 메시지 팩토리 (호출자 편의용) ────────────────────────────────────────

export function buildElementSelectMessage(payload: ElementSelectPayload): ElementSelectMessage {
  return {
    type: MESSAGE_TYPES.ELEMENT_SELECT,
    schemaVersion: PROTOCOL_SCHEMA_VERSION,
    payload,
  };
}

export function buildTokenUpdateMessage(payload: TokenUpdatePayload): TokenUpdateMessage {
  return {
    type: MESSAGE_TYPES.TOKEN_UPDATE,
    schemaVersion: PROTOCOL_SCHEMA_VERSION,
    payload,
  };
}

export function buildSchemaPatchMessage(payload: SchemaPatchPayload): SchemaPatchMessage {
  return {
    type: MESSAGE_TYPES.SCHEMA_PATCH_LOCAL,
    schemaVersion: PROTOCOL_SCHEMA_VERSION,
    payload,
  };
}
