"use client";

import { Sparkles, X } from "lucide-react";
import Link from "next/link";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";

/**
 * Mode A Designer 이관 안내 배너.
 *
 * 레거시 페이지(/reports, /templates 등) 상단에 노출해 사용자를
 * 신규 Mode A designer(/designer/create)로 유도한다.
 *
 * - 닫기(dismiss) 상태는 localStorage에 저장하여 재방문 시 미표시.
 * - S4에서 /templates 페이지에도 동일한 패턴으로 재사용되므로
 *   `storageKey`를 통해 페이지별로 닫힘 상태를 독립 관리한다.
 */

export interface ModeAPromoBannerProps {
  /** localStorage에 저장할 닫힘 상태 키. 페이지마다 달라야 한다. */
  storageKey: string;
  /** 배너 제목 (한글) */
  title?: string;
  /** 배너 상세 설명 (한글) */
  description?: string;
  /** CTA 버튼 라벨 */
  ctaLabel?: string;
  /** CTA 이동 경로 (Next.js Link href) */
  ctaHref?: string;
  /** 닫기 버튼 노출 여부 */
  dismissible?: boolean;
  /** 외부 래퍼 클래스 */
  className?: string;
  /** 접근성: 영역 aria-label (한글) */
  ariaLabel?: string;
}

export function ModeAPromoBanner({
  storageKey,
  title = "새로운 문서 생성 경험을 사용해 보세요",
  description = "Mode A designer로 슬라이드·보고서를 프롬프트만으로 자동 생성하고 실시간 프리뷰에서 편집할 수 있습니다.",
  ctaLabel = "디자이너로 이동",
  ctaHref = "/designer/create",
  dismissible = true,
  className,
  ariaLabel = "Mode A 디자이너 이관 안내",
}: ModeAPromoBannerProps) {
  // SSR 안전성: 초기값은 false로 두고 mount 이후 localStorage 값을 읽어온다.
  const [dismissed, setDismissed] = React.useState(false);
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
    try {
      if (window.localStorage.getItem(storageKey) === "1") {
        setDismissed(true);
      }
    } catch {
      // localStorage 접근 불가(프라이빗 모드 등) — 배너는 계속 노출
    }
  }, [storageKey]);

  const handleDismiss = React.useCallback(() => {
    setDismissed(true);
    try {
      window.localStorage.setItem(storageKey, "1");
    } catch {
      // 저장 실패는 무시 — 세션 내 닫기 상태는 유지
    }
  }, [storageKey]);

  // mount 전에는 hydration mismatch 방지를 위해 항상 노출 상태로 렌더링
  if (mounted && dismissed) {
    return null;
  }

  return (
    <div
      role="complementary"
      aria-label={ariaLabel}
      className={cn(
        "relative flex flex-col gap-3 rounded-lg border border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-4 shadow-sm sm:flex-row sm:items-center sm:gap-4",
        className,
      )}
    >
      {/* 아이콘 */}
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600">
        <Sparkles className="h-5 w-5" aria-hidden="true" />
      </div>

      {/* 본문 */}
      <div className="min-w-0 flex-1">
        <h3 className="text-sm font-semibold text-blue-900">{title}</h3>
        <p className="mt-1 text-sm text-blue-800/80">{description}</p>
      </div>

      {/* CTA */}
      <div className="flex items-center gap-2 sm:shrink-0">
        <Button asChild size="sm" className="bg-blue-600 text-white hover:bg-blue-700">
          <Link href={ctaHref}>{ctaLabel}</Link>
        </Button>

        {dismissible && (
          <button
            type="button"
            onClick={handleDismiss}
            aria-label="배너 닫기"
            className="rounded-md p-1.5 text-blue-700/70 transition-colors hover:bg-blue-100 hover:text-blue-900 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:outline-none"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        )}
      </div>
    </div>
  );
}
