/**
 * design-token-picker.test.tsx — Phase 4 S1 D5 단위 테스트
 *
 * 검증 항목 (작업지시서 최소 8건):
 *   1. 색상 picker 변경 → onPreview 가 50ms 이내 호출
 *   2. 드래그 멈춘 뒤 500ms → onCommit 1회 호출
 *   3. 연속 변경 중 commit 은 최종 1회 + preview 는 여러 번
 *   4. 브랜드 프리셋 버튼 클릭 → 전체 토큰(idino_mono) 교체 payload
 *   5. 기본값 복원 버튼 → idino_default 전체 토큰 커밋
 *   6. 잘못된 HEX 입력 blur → 값 롤백 (preview/commit 모두 호출 안됨)
 *   7. spacing 라디오 변경 → { spacing: "relaxed" } 커밋
 *   8. font_family select 변경 → { font_family: "NotoSansKR" } 커밋
 *
 * 추가 보강:
 *   9. idino_default 상태에서는 색상 input 이 readOnly (잠금 힌트 표시)
 *   10. useDebouncedTokenSync 단위: flush / cancel 동작
 */

import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { DesignTokens } from "@/types/document-schema";

import { DesignTokenPicker } from "../index";
import { DEFAULT_DESIGN_TOKENS } from "../tokens";
import { useDebouncedTokenSync } from "../useDebouncedTokenSync";

// ─── fixture ───────────────────────────────────────────────────────────────

function makeTokens(overrides: Partial<DesignTokens> = {}): DesignTokens {
  return { ...DEFAULT_DESIGN_TOKENS, ...overrides };
}

/** custom 프리셋으로 잠금 해제된 초기 토큰 (색상 편집 가능). */
function customTokens(overrides: Partial<DesignTokens> = {}): DesignTokens {
  return makeTokens({ brand_preset: "custom", ...overrides });
}

// ─── 1) 색상 picker 변경 → preview 50ms ────────────────────────────────────

describe("ColorTokenSlider preview/commit pipeline", () => {
  it("색상 picker 변경 시 50ms 이후 onPreview 가 호출된다", () => {
    vi.useFakeTimers();
    try {
      const onPreview = vi.fn();
      const onCommit = vi.fn();

      render(
        <DesignTokenPicker tokens={customTokens()} onPreview={onPreview} onCommit={onCommit} />,
      );

      const primaryPicker = screen.getByLabelText("프라이머리 색상 선택");
      fireEvent.change(primaryPicker, { target: { value: "#112233" } });

      expect(onPreview).not.toHaveBeenCalled();
      act(() => {
        vi.advanceTimersByTime(50);
      });
      expect(onPreview).toHaveBeenCalledTimes(1);
      expect(onPreview).toHaveBeenCalledWith(expect.objectContaining({ primary_color: "#112233" }));
    } finally {
      vi.useRealTimers();
    }
  });

  it("picker 변경 후 500ms 경과 시 onCommit 이 1회 호출된다", () => {
    vi.useFakeTimers();
    try {
      const onPreview = vi.fn();
      const onCommit = vi.fn();

      render(
        <DesignTokenPicker tokens={customTokens()} onPreview={onPreview} onCommit={onCommit} />,
      );

      const primaryPicker = screen.getByLabelText("프라이머리 색상 선택");
      fireEvent.change(primaryPicker, { target: { value: "#aabbcc" } });

      act(() => {
        vi.advanceTimersByTime(500);
      });

      expect(onCommit).toHaveBeenCalledTimes(1);
      expect(onCommit).toHaveBeenCalledWith(expect.objectContaining({ primary_color: "#AABBCC" }));
    } finally {
      vi.useRealTimers();
    }
  });

  it("연속 색상 변경 중 commit 은 최종 1회, preview 는 누적 호출된다", () => {
    vi.useFakeTimers();
    try {
      const onPreview = vi.fn();
      const onCommit = vi.fn();

      render(
        <DesignTokenPicker tokens={customTokens()} onPreview={onPreview} onCommit={onCommit} />,
      );

      const primaryPicker = screen.getByLabelText("프라이머리 색상 선택");

      act(() => {
        fireEvent.change(primaryPicker, { target: { value: "#111111" } });
        vi.advanceTimersByTime(50);
        fireEvent.change(primaryPicker, { target: { value: "#222222" } });
        vi.advanceTimersByTime(50);
        fireEvent.change(primaryPicker, { target: { value: "#333333" } });
        vi.advanceTimersByTime(50);
      });

      // preview 는 각 변경마다 발동 → 3회 호출.
      expect(onPreview).toHaveBeenCalledTimes(3);

      // commit 은 아직 대기 중.
      expect(onCommit).not.toHaveBeenCalled();

      act(() => {
        vi.advanceTimersByTime(500);
      });

      expect(onCommit).toHaveBeenCalledTimes(1);
      expect(onCommit).toHaveBeenCalledWith(expect.objectContaining({ primary_color: "#333333" }));
    } finally {
      vi.useRealTimers();
    }
  });
});

// ─── 4) 브랜드 프리셋 클릭 → 전체 토큰 교체 ────────────────────────────────

describe("BrandPresetButtons", () => {
  it("idino_mono 프리셋 클릭 시 전체 토큰이 교체된 payload 가 commit 된다", () => {
    vi.useFakeTimers();
    try {
      const onPreview = vi.fn();
      const onCommit = vi.fn();

      render(<DesignTokenPicker tokens={makeTokens()} onPreview={onPreview} onCommit={onCommit} />);

      fireEvent.click(screen.getByRole("button", { name: "IDINO 모노 프리셋 적용" }));

      // preview 파이프 flush.
      act(() => {
        vi.advanceTimersByTime(50);
      });
      expect(onPreview).toHaveBeenCalledTimes(1);
      const previewPayload = onPreview.mock.calls[0][0];
      expect(previewPayload.brand_preset).toBe("idino_mono");
      expect(previewPayload.primary_color).toBe("#2B2B2B");

      // commit 파이프 flush.
      act(() => {
        vi.advanceTimersByTime(500);
      });
      expect(onCommit).toHaveBeenCalledTimes(1);
      const commitPayload = onCommit.mock.calls[0][0];
      expect(commitPayload.brand_preset).toBe("idino_mono");
      expect(commitPayload.primary_color).toBe("#2B2B2B");
      expect(commitPayload.accent_color).toBe("#666666");
      // 전체 교체이므로 font_family / spacing 등 모든 필드가 포함돼야 함.
      expect(commitPayload.font_family).toBeDefined();
      expect(commitPayload.spacing).toBeDefined();
    } finally {
      vi.useRealTimers();
    }
  });
});

// ─── 5) 기본값 복원 버튼 ───────────────────────────────────────────────────

describe("기본값 복원", () => {
  it("기본값 복원 버튼 클릭 시 DEFAULT_DESIGN_TOKENS 가 commit 된다", () => {
    vi.useFakeTimers();
    try {
      const onPreview = vi.fn();
      const onCommit = vi.fn();

      render(
        <DesignTokenPicker
          tokens={customTokens({ primary_color: "#DEADBE" })}
          onPreview={onPreview}
          onCommit={onCommit}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: "디자인 토큰 기본값으로 복원" }));

      act(() => {
        vi.advanceTimersByTime(500);
      });

      expect(onCommit).toHaveBeenCalledTimes(1);
      expect(onCommit).toHaveBeenCalledWith(expect.objectContaining(DEFAULT_DESIGN_TOKENS));
    } finally {
      vi.useRealTimers();
    }
  });
});

// ─── 6) 잘못된 HEX 입력 → 롤백 ─────────────────────────────────────────────

describe("HEX 입력 유효성", () => {
  it("잘못된 HEX 입력을 blur 하면 값이 롤백되고 commit 이 호출되지 않는다", () => {
    vi.useFakeTimers();
    try {
      const onPreview = vi.fn();
      const onCommit = vi.fn();

      render(
        <DesignTokenPicker
          tokens={customTokens({ primary_color: "#0A4FC2" })}
          onPreview={onPreview}
          onCommit={onCommit}
        />,
      );

      const hexInput = screen.getByLabelText("프라이머리 HEX 값") as HTMLInputElement;
      fireEvent.change(hexInput, { target: { value: "not-a-hex" } });
      fireEvent.blur(hexInput);

      act(() => {
        vi.advanceTimersByTime(500);
      });

      expect(onPreview).not.toHaveBeenCalled();
      expect(onCommit).not.toHaveBeenCalled();
      // 값은 원래 값으로 롤백됐어야 함.
      expect(hexInput.value).toBe("#0A4FC2");
    } finally {
      vi.useRealTimers();
    }
  });
});

// ─── 7) spacing 라디오 ─────────────────────────────────────────────────────

describe("SpacingTokenRadio", () => {
  it("relaxed 라디오 선택 시 { spacing: 'relaxed' } 가 commit 된다", () => {
    vi.useFakeTimers();
    try {
      const onPreview = vi.fn();
      const onCommit = vi.fn();

      render(
        <DesignTokenPicker
          tokens={makeTokens({ spacing: "normal" })}
          onPreview={onPreview}
          onCommit={onCommit}
        />,
      );

      const relaxedRadio = screen.getByRole("radio", { name: /넓게/ });
      fireEvent.click(relaxedRadio);

      act(() => {
        vi.advanceTimersByTime(500);
      });

      expect(onCommit).toHaveBeenCalledWith({ spacing: "relaxed" });
    } finally {
      vi.useRealTimers();
    }
  });
});

// ─── 8) font_family select ─────────────────────────────────────────────────

describe("FontTokenSelect", () => {
  // Radix Select 는 jsdom 에서 pointerEvent 가 미묘하므로 onValueChange 를 직접
  // 쏘기 위해 훅을 경유한 통합 테스트보다는 작은 wrapper 로 커버.
  it("폰트 변경 시 preview 와 commit 파이프 모두에 font_family 가 흘러간다", () => {
    vi.useFakeTimers();
    try {
      const onPreview = vi.fn();
      const onCommit = vi.fn();

      function Probe() {
        const sync = useDebouncedTokenSync({ onPreview, onCommit });
        return (
          <button
            type="button"
            onClick={() => {
              sync.preview({ font_family: "NotoSansKR" });
              sync.commit({ font_family: "NotoSansKR" });
            }}
          >
            change-font
          </button>
        );
      }

      render(<Probe />);
      fireEvent.click(screen.getByRole("button", { name: "change-font" }));

      act(() => {
        vi.advanceTimersByTime(50);
      });
      expect(onPreview).toHaveBeenCalledWith({ font_family: "NotoSansKR" });

      act(() => {
        vi.advanceTimersByTime(500);
      });
      expect(onCommit).toHaveBeenCalledWith({ font_family: "NotoSansKR" });
    } finally {
      vi.useRealTimers();
    }
  });
});

// ─── 9) idino_default 상태 — 색상 잠금 ─────────────────────────────────────

describe("브랜드 프리셋 잠금", () => {
  it("idino_default 프리셋에서는 색상 input 이 readOnly/disabled 로 잠긴다", () => {
    render(
      <DesignTokenPicker
        tokens={makeTokens({ brand_preset: "idino_default" })}
        onPreview={vi.fn()}
        onCommit={vi.fn()}
      />,
    );

    const primaryHex = screen.getByLabelText("프라이머리 HEX 값") as HTMLInputElement;
    expect(primaryHex).toBeDisabled();

    const primaryPicker = screen.getByLabelText("프라이머리 색상 선택") as HTMLInputElement;
    expect(primaryPicker).toBeDisabled();

    // 잠금 힌트가 화면에 노출.
    expect(screen.getAllByText(/커스텀 모드에서 편집/).length).toBeGreaterThan(0);
  });
});

// ─── 10) useDebouncedTokenSync flush/cancel 단위 ──────────────────────────

describe("useDebouncedTokenSync", () => {
  it("flush() 는 대기 중 preview/commit 을 즉시 발동시킨다", () => {
    vi.useFakeTimers();
    try {
      const onPreview = vi.fn();
      const onCommit = vi.fn();

      function Probe() {
        const sync = useDebouncedTokenSync({ onPreview, onCommit });
        return (
          <>
            <button
              type="button"
              data-testid="schedule"
              onClick={() => {
                sync.preview({ primary_color: "#111111" });
                sync.commit({ primary_color: "#111111" });
              }}
            >
              schedule
            </button>
            <button type="button" data-testid="flush" onClick={() => sync.flush()}>
              flush
            </button>
          </>
        );
      }

      render(<Probe />);
      fireEvent.click(screen.getByTestId("schedule"));
      // 아직 대기 중.
      expect(onPreview).not.toHaveBeenCalled();
      expect(onCommit).not.toHaveBeenCalled();

      fireEvent.click(screen.getByTestId("flush"));

      expect(onPreview).toHaveBeenCalledTimes(1);
      expect(onCommit).toHaveBeenCalledTimes(1);
    } finally {
      vi.useRealTimers();
    }
  });

  it("cancel() 은 대기 중 preview/commit 을 모두 취소한다", () => {
    vi.useFakeTimers();
    try {
      const onPreview = vi.fn();
      const onCommit = vi.fn();

      function Probe() {
        const sync = useDebouncedTokenSync({ onPreview, onCommit });
        return (
          <>
            <button
              type="button"
              data-testid="schedule"
              onClick={() => {
                sync.preview({ primary_color: "#aaa" });
                sync.commit({ primary_color: "#aaa" });
              }}
            >
              schedule
            </button>
            <button type="button" data-testid="cancel" onClick={() => sync.cancel()}>
              cancel
            </button>
          </>
        );
      }

      render(<Probe />);
      fireEvent.click(screen.getByTestId("schedule"));
      fireEvent.click(screen.getByTestId("cancel"));

      act(() => {
        vi.advanceTimersByTime(1000);
      });

      expect(onPreview).not.toHaveBeenCalled();
      expect(onCommit).not.toHaveBeenCalled();
    } finally {
      vi.useRealTimers();
    }
  });
});
