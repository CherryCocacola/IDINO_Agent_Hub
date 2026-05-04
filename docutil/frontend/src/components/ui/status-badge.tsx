import * as React from "react";

import { cn } from "@/lib/utils/cn";

export type StatusType = "progress" | "complete" | "waiting" | "error" | "default";

interface StatusBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  status: StatusType;
  children: React.ReactNode;
  showDot?: boolean;
}

const statusStyles: Record<StatusType, { bg: string; text: string; dot: string }> = {
  progress: {
    bg: "bg-blue-100",
    text: "text-blue-700",
    dot: "bg-blue-500",
  },
  complete: {
    bg: "bg-green-100",
    text: "text-green-700",
    dot: "bg-green-500",
  },
  waiting: {
    bg: "bg-yellow-100",
    text: "text-yellow-700",
    dot: "bg-yellow-500",
  },
  error: {
    bg: "bg-red-100",
    text: "text-red-700",
    dot: "bg-red-500",
  },
  default: {
    bg: "bg-gray-100",
    text: "text-gray-700",
    dot: "bg-gray-500",
  },
};

export function StatusBadge({
  status,
  children,
  showDot = true,
  className,
  ...props
}: StatusBadgeProps) {
  const styles = statusStyles[status];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
        styles.bg,
        styles.text,
        className,
      )}
      {...props}
    >
      {showDot && <span className={cn("h-1.5 w-1.5 rounded-full", styles.dot)} />}
      {children}
    </span>
  );
}

// Status bar component for showing distribution
interface StatusBarProps {
  items: Array<{
    label: string;
    value: number;
    status: StatusType;
  }>;
  className?: string;
}

export function StatusBar({ items, className }: StatusBarProps) {
  const total = items.reduce((sum, item) => sum + item.value, 0);

  if (total === 0) {
    return <div className={cn("h-2 w-full rounded-full bg-gray-200", className)} />;
  }

  return (
    <div className={cn("space-y-2", className)}>
      {/* Progress bar */}
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-gray-200">
        {items.map((item, index) => {
          const width = (item.value / total) * 100;
          const bgColors: Record<StatusType, string> = {
            progress: "bg-blue-500",
            complete: "bg-green-500",
            waiting: "bg-yellow-500",
            error: "bg-red-500",
            default: "bg-gray-500",
          };
          return (
            <div
              key={index}
              className={cn("h-full", bgColors[item.status])}
              style={{ width: `${width}%` }}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs">
        {items.map((item, index) => (
          <div key={index} className="flex items-center gap-1.5">
            <StatusBadge status={item.status} showDot={true}>
              {item.label}
            </StatusBadge>
            <span className="text-foreground font-medium">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
