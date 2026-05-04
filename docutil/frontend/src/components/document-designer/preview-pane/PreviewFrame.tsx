/**
 * PreviewFrame — iframe 컨테이너 컴포넌트
 *
 * 설계 결정 (Phase 4 S1 D3):
 *   - iframe src 는 **같은 Next.js origin 의 `/preview-host` 라우트**로 고정한다.
 *   - 이유: Designer Shell 이 iframe 에 React 컴포넌트 22종(S1~S6 에 걸쳐 추가)을
 *     렌더해야 하므로 `srcdoc` 로 인라인 주입은 bundle 부담이 크다. Next.js
 *     페이지 라우트를 재사용하면 webpack 청크가 공유되고, `React.lazy` 로
 *     컴포넌트를 동적 로드할 수 있어 효율적이다.
 *   - 보안: same-origin 이지만 `sandbox="allow-scripts allow-same-origin"` 을
 *     명시해 iframe 내부 스크립트의 권한을 명확히 선언한다. 외부 CDN/도메인
 *     주입 자원 없음을 CSP 로 별도 보장한다(Phase 4 S7 에서 CSP 헤더 도입 예정).
 *
 *   - 대안 검토:
 *     (a) `sandbox="allow-scripts"` 만 — same-origin 이 끊겨 localStorage /
 *         fetch(credentials) 가 차단됨. Designer 가 세션 토큰을 같이 써야 하는
 *         프리뷰 데이터 조회(예: MinIO presigned URL 로 이미지 가져오기)가 막힘.
 *         → 기각.
 *     (b) `srcdoc` + 인라인 부트스트랩 — JSX 모듈 로딩 없이 DOM 직접 조작
 *         필요. 22종 컴포넌트를 수동 DOM 빌더로 다시 쓰는 비용이 과대. → 기각.
 *
 * 부모 shell 은 본 컴포넌트에 ref 로 접근해 iframe.contentWindow.postMessage 를
 * 호출한다. onReady 콜백은 iframe 이 첫 `docutil/*` 메시지 수신 준비 완료 상태가
 * 됐을 때 1회 호출된다 (iframe 측이 initial element-select 이전에 ready ping 을
 * 보내는 방식은 Phase 4 S1 D4 에서 PreviewPane 훅 단으로 분리).
 */

"use client";

import { forwardRef, useImperativeHandle, useRef } from "react";

export interface PreviewFrameProps {
  /**
   * iframe 소스 경로. 기본값은 `/preview-host`.
   * 같은 Next.js origin 내부 경로여야 postMessage origin 검증이 단순해진다.
   */
  src?: string;
  /** iframe 제목 (접근성). 스크린리더가 프레임 경계 안내 시 사용. */
  title?: string;
  /**
   * 로드 완료(iframe `onLoad`) 시 호출. contentWindow 핸들을 함께 전달하여
   * 부모가 즉시 postMessage 를 보낼 수 있다.
   */
  onFrameLoad?: (frame: HTMLIFrameElement) => void;
  /** 접근성 / 테스트 식별자. */
  className?: string;
  dataTestId?: string;
}

export interface PreviewFrameHandle {
  /** 내부 iframe DOM 엘리먼트. postMessage 발신 시 사용. */
  getIframe: () => HTMLIFrameElement | null;
  /** contentWindow 편의 접근자. */
  getContentWindow: () => Window | null;
}

const DEFAULT_SRC = "/preview-host";
const DEFAULT_TITLE = "문서 프리뷰";

/**
 * same-origin 라우트이므로 `allow-same-origin` 이 필요하다. 추가 권한(`allow-forms`,
 * `allow-popups`, `allow-top-navigation` 등)은 현재 범위에 불필요 → 부여하지 않는다.
 */
const SANDBOX = "allow-scripts allow-same-origin";

export const PreviewFrame = forwardRef<PreviewFrameHandle, PreviewFrameProps>(function PreviewFrame(
  { src = DEFAULT_SRC, title = DEFAULT_TITLE, onFrameLoad, className, dataTestId },
  ref,
) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);

  useImperativeHandle(
    ref,
    () => ({
      getIframe: () => iframeRef.current,
      getContentWindow: () => iframeRef.current?.contentWindow ?? null,
    }),
    [],
  );

  const handleLoad = () => {
    const frame = iframeRef.current;
    if (frame) onFrameLoad?.(frame);
  };

  return (
    <iframe
      ref={iframeRef}
      src={src}
      title={title}
      sandbox={SANDBOX}
      // referrer 최소화 — 프리뷰 내부에서 외부 요청 발생 시 origin 만 전달.
      referrerPolicy="same-origin"
      // loading="eager" 가 기본이지만 명시. 사용자가 /designer 진입 즉시 프리뷰
      // 렌더가 보여야 하므로 지연 로딩 금지.
      loading="eager"
      onLoad={handleLoad}
      data-testid={dataTestId}
      className={className}
      style={{
        width: "100%",
        height: "100%",
        border: "none",
        display: "block",
        background: "var(--doc-background)",
      }}
    />
  );
});

export default PreviewFrame;
