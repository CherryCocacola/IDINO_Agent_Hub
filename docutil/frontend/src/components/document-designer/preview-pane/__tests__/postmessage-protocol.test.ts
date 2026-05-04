/**
 * postmessage-protocol.test.ts — Phase 4 S1 D3 프로토콜 단위 테스트
 *
 * 검증 항목:
 *   1. encode 가 JSON 직렬화 가능한 객체를 반환한다.
 *   2. decode 는 알 수 없는 type 을 거부(null 반환)한다.
 *   3. origin 검증이 예상 origin 과 다르면 fail 한다.
 *   4. mergeTokens 가 부분 업데이트를 기존 토큰과 병합한다.
 *   5. SchemaPatchPayload 의 3가지 patchType 이 applySchemaPatch 로 올바르게 분기된다.
 */

import { describe, expect, it } from "vitest";

import type { DesignTokens, DocumentSchema } from "@/types/document-schema";

import {
  buildElementSelectMessage,
  buildSchemaPatchMessage,
  buildTokenUpdateMessage,
  decode,
  encode,
  mergeTokens,
  MESSAGE_TYPES,
  PROTOCOL_SCHEMA_VERSION,
  verifyOrigin,
} from "../postmessage-protocol";
import { applySchemaPatch } from "../preview-host";

// ─── 공통 fixture ─────────────────────────────────────────────────────────

const DEFAULT_TOKENS: DesignTokens = {
  primary_color: "#0A4FC2",
  accent_color: "#FF6B35",
  text_color: "#1F2937",
  background_color: "#FFFFFF",
  font_family: "Pretendard",
  spacing: "normal",
  brand_preset: "idino_default",
};

function buildSchema(): DocumentSchema {
  return {
    document_id: "00000000-0000-4000-8000-000000000001",
    schema_version: "1.0",
    type: "slide_report",
    mode: "free_generation",
    template_id: null,
    design_tokens: { ...DEFAULT_TOKENS },
    pages: [
      {
        id: "p1",
        page_kind: "slide",
        layout: "title_slide",
        title: "첫 페이지",
        locked: false,
        speaker_notes: null,
        page_number_visible: true,
        components: [
          {
            id: "c1",
            type: "SlideTitle",
            text: "원본 제목",
            locked: false,
            anchor: null,
          },
          {
            id: "c2",
            type: "Paragraph",
            text: "원본 본문",
            emphasis: "normal",
            locked: false,
            anchor: null,
          },
        ],
      },
      {
        id: "p2",
        page_kind: "slide",
        layout: "content_body",
        title: "두번째",
        locked: false,
        speaker_notes: null,
        page_number_visible: true,
        components: [],
      },
    ],
    metadata: {
      created_at: "2026-04-19T00:00:00Z",
      updated_at: "2026-04-19T00:00:00Z",
      generated_by_user_id: null,
      llm_provider: null,
      llm_model: null,
      prompt_tokens: null,
      completion_tokens: null,
      source_document_ids: [],
      source_chat_session_id: null,
      citations: [],
      degraded_components: [],
    },
  };
}

// ─── 1. encode → JSON 직렬화 가능 ─────────────────────────────────────────

describe("encode", () => {
  it("element-select 메시지를 JSON 직렬화 가능한 형태로 반환한다", () => {
    const message = buildElementSelectMessage({ pageId: "p1", componentId: "c1" });
    const encoded = encode(message);
    expect(encoded.type).toBe(MESSAGE_TYPES.ELEMENT_SELECT);
    expect(encoded.schemaVersion).toBe(PROTOCOL_SCHEMA_VERSION);

    // JSON stringify 가 예외 없이 동작해야 한다 → 직렬화 가능.
    const serialized = JSON.stringify(encoded);
    const parsed = JSON.parse(serialized);
    expect(parsed).toEqual({
      type: MESSAGE_TYPES.ELEMENT_SELECT,
      schemaVersion: 1,
      payload: { pageId: "p1", componentId: "c1" },
    });
  });

  it("token-update 와 schema-patch 메시지도 동일하게 직렬화 된다", () => {
    const tokenMsg = buildTokenUpdateMessage({ tokens: { primary_color: "#123456" } });
    const patchMsg = buildSchemaPatchMessage({
      patchType: "component",
      pageId: "p1",
      componentId: "c1",
      data: { locked: true },
    });

    expect(() => JSON.stringify(encode(tokenMsg))).not.toThrow();
    expect(() => JSON.stringify(encode(patchMsg))).not.toThrow();
  });

  it("유효하지 않은 메시지는 encode 가 거부한다", () => {
    const bogus = { type: "random/unknown", schemaVersion: 1, payload: {} };
    expect(() =>
      encode(bogus as unknown as ReturnType<typeof buildElementSelectMessage>),
    ).toThrow();
  });
});

// ─── 2. decode — 알 수 없는 type 거부 ────────────────────────────────────

describe("decode", () => {
  it("유효한 message 를 통과시킨다", () => {
    const msg = buildElementSelectMessage({ pageId: "p1", componentId: "c1" });
    expect(decode(msg)).toEqual(msg);
  });

  it("docutil 네임스페이스가 아니면 null", () => {
    expect(decode({ type: "foo/bar", schemaVersion: 1, payload: {} })).toBeNull();
  });

  it("알 수 없는 docutil 타입이면 null", () => {
    expect(decode({ type: "docutil/unknown", schemaVersion: 1, payload: {} })).toBeNull();
  });

  it("schemaVersion 이 다르면 null", () => {
    expect(
      decode({
        type: MESSAGE_TYPES.ELEMENT_SELECT,
        schemaVersion: 99,
        payload: { pageId: "p1", componentId: "c1" },
      }),
    ).toBeNull();
  });

  it("payload 구조가 어긋나면 null", () => {
    expect(
      decode({
        type: MESSAGE_TYPES.ELEMENT_SELECT,
        schemaVersion: 1,
        payload: { pageId: 123 /* 숫자라 거부 */, componentId: "c1" },
      }),
    ).toBeNull();
  });

  it("primitive / null 입력도 안전하게 null 반환", () => {
    expect(decode(null)).toBeNull();
    expect(decode(undefined)).toBeNull();
    expect(decode("string")).toBeNull();
    expect(decode(42)).toBeNull();
  });
});

// ─── 3. origin 검증 ──────────────────────────────────────────────────────

describe("verifyOrigin", () => {
  it("같은 origin 이면 ok:true", () => {
    const result = verifyOrigin("http://localhost:3000", "http://localhost:3000");
    expect(result.ok).toBe(true);
  });

  it("다른 origin 이면 ok:false + reason", () => {
    const result = verifyOrigin("https://evil.example.com", "http://localhost:3000");
    expect(result.ok).toBe(false);
    expect(result.reason).toContain("origin 불일치");
  });

  it('expectedOrigin 이 "*" 이면 검증 생략', () => {
    expect(verifyOrigin("https://anywhere.test", "*").ok).toBe(true);
  });

  it("포트가 다르면 다른 origin 으로 판정", () => {
    expect(verifyOrigin("http://localhost:3000", "http://localhost:8080").ok).toBe(false);
  });
});

// ─── 4. mergeTokens — 부분 병합 ──────────────────────────────────────────

describe("mergeTokens", () => {
  it("변경된 키만 덮어쓰고 나머지는 유지한다", () => {
    const merged = mergeTokens(DEFAULT_TOKENS, { primary_color: "#123456" });
    expect(merged.primary_color).toBe("#123456");
    // 나머지 필드 유지
    expect(merged.accent_color).toBe(DEFAULT_TOKENS.accent_color);
    expect(merged.spacing).toBe(DEFAULT_TOKENS.spacing);
    expect(merged.font_family).toBe(DEFAULT_TOKENS.font_family);
  });

  it("빈 patch 는 현재 토큰을 그대로 반환(새 참조)한다", () => {
    const merged = mergeTokens(DEFAULT_TOKENS, {});
    expect(merged).toEqual(DEFAULT_TOKENS);
    expect(merged).not.toBe(DEFAULT_TOKENS); // 새 객체
  });

  it("여러 필드를 동시에 병합한다", () => {
    const merged = mergeTokens(DEFAULT_TOKENS, {
      accent_color: "#00FF00",
      spacing: "compact",
      brand_preset: "idino_mono",
    });
    expect(merged).toMatchObject({
      primary_color: DEFAULT_TOKENS.primary_color,
      accent_color: "#00FF00",
      spacing: "compact",
      brand_preset: "idino_mono",
    });
  });

  it("undefined 값은 병합하지 않는다 (기존 값 유지)", () => {
    const merged = mergeTokens(DEFAULT_TOKENS, { primary_color: undefined });
    expect(merged.primary_color).toBe(DEFAULT_TOKENS.primary_color);
  });
});

// ─── 5. applySchemaPatch — 3가지 patchType 분기 ──────────────────────────

describe("applySchemaPatch", () => {
  it("patchType='page' → 지정 page 만 부분 업데이트, 다른 page 는 동일 참조", () => {
    const schema = buildSchema();
    const p2Ref = schema.pages[1];

    const next = applySchemaPatch(schema, {
      patchType: "page",
      pageId: "p1",
      data: { title: "수정된 제목" },
    });

    expect(next.pages[0].title).toBe("수정된 제목");
    // p1 의 다른 필드는 유지
    expect(next.pages[0].components).toBe(schema.pages[0].components);
    // p2 는 수정되지 않아 참조 동일
    expect(next.pages[1]).toBe(p2Ref);
  });

  it("patchType='component' → 지정 component 만 부분 업데이트", () => {
    const schema = buildSchema();
    const next = applySchemaPatch(schema, {
      patchType: "component",
      pageId: "p1",
      componentId: "c1",
      data: { locked: true },
    });

    const patched = next.pages[0].components[0];
    expect(patched.id).toBe("c1");
    expect(patched.locked).toBe(true);
    // 같은 page 내 다른 component 는 수정되지 않음
    expect(next.pages[0].components[1]).toBe(schema.pages[0].components[1]);
    // 다른 page 도 수정되지 않음
    expect(next.pages[1]).toBe(schema.pages[1]);
  });

  it("patchType='component' → type discriminator 는 변경 불가", () => {
    const schema = buildSchema();
    const next = applySchemaPatch(schema, {
      patchType: "component",
      pageId: "p1",
      componentId: "c1",
      // 악의적 type 덮어쓰기 시도
      data: { type: "Paragraph" } as unknown as Partial<
        import("@/types/document-schema").Component
      >,
    });
    expect(next.pages[0].components[0].type).toBe("SlideTitle");
  });

  it("patchType='tokens' → design_tokens 전체 치환", () => {
    const schema = buildSchema();
    const newTokens: DesignTokens = {
      ...DEFAULT_TOKENS,
      primary_color: "#999999",
      brand_preset: "idino_mono",
    };
    const next = applySchemaPatch(schema, {
      patchType: "tokens",
      data: newTokens,
    });
    expect(next.design_tokens).toEqual(newTokens);
    // pages 는 동일 참조 유지
    expect(next.pages).toBe(schema.pages);
  });

  it("존재하지 않는 pageId 는 no-op (pages 변경 없음)", () => {
    const schema = buildSchema();
    const next = applySchemaPatch(schema, {
      patchType: "page",
      pageId: "p-nonexistent",
      data: { title: "X" },
    });
    expect(next.pages.map((p) => p.title)).toEqual(schema.pages.map((p) => p.title));
  });
});
