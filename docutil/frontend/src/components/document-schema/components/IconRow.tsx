/**
 * IconRow — 아이콘 + 라벨 가로 나열 컴포넌트
 *
 * DocumentSchema catalog #14 (S3 D3 추가). 핵심 가치 / 프로세스 단계 / 주요 기능 등을
 * 아이콘과 짧은 라벨로 나열할 때 사용한다. HWPX 빌더에서는 BulletList 로 degrade.
 *
 * 디자인 규약:
 *   - Flex 가로 나열: `display: flex; gap: var(--doc-spacing-md); justify-content: center`
 *   - 각 아이템: 아이콘(primary 컬러) 위 + 라벨(base, text) 아래 세로 스택
 *   - 아이콘 크기: 40px (32~48 범위 내 중앙값)
 *   - lucide-react 아이콘은 **allowlist** 를 통해서만 노출 (임의 이름 차단)
 *   - 허용되지 않은 이름은 `HelpCircle` fallback + console.warn
 *
 * allowlist 방침:
 *   `ICON_ALLOWLIST` 는 UI 에서 자주 쓰는 30개를 선별. 폼의 Select 옵션도 이
 *   리스트를 소스로 삼아 일관성을 유지한다. 추가가 필요하면 이 파일에서만 확장.
 */

import {
  Activity,
  Award,
  BarChart3,
  Bell,
  Bookmark,
  Briefcase,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  Cloud,
  Database,
  FileText,
  Flag,
  Globe,
  Heart,
  HelpCircle,
  Home,
  Lightbulb,
  Lock,
  type LucideIcon,
  Mail,
  MessageSquare,
  Rocket,
  Search,
  Settings,
  Shield,
  Star,
  Target,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react";

import type { IconRowComponent } from "@/types/document-schema";

export interface IconRowProps {
  component: IconRowComponent;
  isSelected?: boolean;
  onSelect?: (componentId: string) => void;
}

/**
 * lucide-react 아이콘 allowlist (30종).
 * IconRow 폼의 Select 옵션과 같은 소스를 공유하므로 `ICON_ALLOWLIST_NAMES` 를
 * 별도 export 한다. 추가 시 이 객체 한 곳만 편집.
 */
export const ICON_ALLOWLIST: Record<string, LucideIcon> = {
  Activity,
  Award,
  BarChart3,
  Bell,
  Bookmark,
  Briefcase,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  Cloud,
  Database,
  FileText,
  Flag,
  Globe,
  Heart,
  HelpCircle,
  Home,
  Lightbulb,
  Mail,
  MessageSquare,
  Rocket,
  Search,
  Settings,
  Shield,
  Star,
  Target,
  TrendingUp,
  Users,
  Zap,
};

/** Select 드롭다운 등에서 순서대로 노출할 허용 아이콘 이름 배열. */
export const ICON_ALLOWLIST_NAMES: readonly string[] = Object.keys(ICON_ALLOWLIST);

/** 아이콘 이름이 allowlist 에 없으면 HelpCircle 을 fallback 으로 반환. */
function resolveIcon(name: string): LucideIcon {
  const found = ICON_ALLOWLIST[name];
  if (found) return found;
  // 개발자 가시성을 위해 경고 — 프로덕션에서도 조용히 동작.
  if (process.env.NODE_ENV !== "production") {
    console.warn(`[IconRow] 허용되지 않은 아이콘 "${name}" — HelpCircle 로 대체합니다.`);
  }
  return HelpCircle;
}

/** 한 행에 표시할 권장 최대 아이템 수. 폼에서도 동일 상한 적용. */
export const ICON_ROW_MAX_ITEMS = 8;

export function IconRow({ component, isSelected, onSelect }: IconRowProps) {
  const items = component.items;
  const handleClick = () => onSelect?.(component.id);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect?.(component.id);
    }
  };

  return (
    <div
      data-component="IconRow"
      data-component-id={component.id}
      data-item-count={items.length}
      data-locked={component.locked}
      data-selected={isSelected}
      role="group"
      tabIndex={0}
      aria-label={`아이콘 행 — ${items.length}개 항목`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="relative w-full outline-none"
      style={{
        padding: "var(--doc-spacing-md)",
        marginTop: "var(--doc-spacing-md)",
        marginBottom: "var(--doc-spacing-md)",
        borderRadius: "var(--doc-radius-md)",
        outline: isSelected ? "2px solid var(--doc-primary)" : undefined,
        outlineOffset: isSelected ? "2px" : undefined,
        cursor: component.locked ? "not-allowed" : "pointer",
        opacity: component.locked ? 0.85 : 1,
      }}
    >
      {component.locked && (
        <Lock
          aria-hidden="true"
          className="absolute top-2 right-2 h-3.5 w-3.5"
          style={{ color: "var(--doc-text-muted)" }}
        />
      )}
      <ul
        style={{
          listStyle: "none",
          margin: 0,
          padding: 0,
          display: "flex",
          flexWrap: "wrap",
          gap: "var(--doc-spacing-md)",
          justifyContent: "center",
          alignItems: "flex-start",
          fontFamily: "var(--doc-font-family)",
        }}
      >
        {items.map((item, idx) => {
          const Icon = resolveIcon(item.icon);
          return (
            <li
              key={`${component.id}-icon-${idx}`}
              data-item-index={idx}
              data-icon={item.icon}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "var(--doc-spacing-xs)",
                minWidth: 88,
                maxWidth: 160,
                textAlign: "center",
              }}
            >
              <Icon
                aria-hidden="true"
                style={{
                  width: 40,
                  height: 40,
                  color: "var(--doc-primary)",
                }}
              />
              <span
                style={{
                  fontSize: "var(--doc-font-size-sm)",
                  fontWeight: 600,
                  color: "var(--doc-text)",
                  lineHeight: "var(--doc-line-height-tight)",
                  wordBreak: "keep-all",
                }}
              >
                {item.label}
              </span>
              {item.description && (
                <span
                  style={{
                    fontSize: "var(--doc-font-size-xs)",
                    color: "var(--doc-text-muted)",
                    lineHeight: "var(--doc-line-height-normal)",
                    wordBreak: "keep-all",
                  }}
                >
                  {item.description}
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default IconRow;
