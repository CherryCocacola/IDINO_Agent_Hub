import * as React from "react";

import { cn } from "@/lib/utils/cn";

export type MetricCardVariant = "pink" | "green" | "yellow" | "default";

interface MetricCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: MetricCardVariant;
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  description?: string;
}

// Fallback styles for browsers that don't support oklch custom properties
const fallbackVariantStyles: Record<MetricCardVariant, string> = {
  pink: "bg-pink-100",
  green: "bg-green-100",
  yellow: "bg-yellow-100",
  default: "bg-white",
};

export function MetricCard({
  variant = "default",
  title,
  value,
  icon,
  description,
  className,
  ...props
}: MetricCardProps) {
  return (
    <div
      className={cn(
        "border-border rounded-xl border p-6 shadow-sm",
        fallbackVariantStyles[variant],
        className,
      )}
      {...props}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-muted-foreground text-sm font-medium">{title}</p>
          <p className="text-foreground mt-2 text-3xl font-bold">
            {typeof value === "number" ? value.toLocaleString() : value}
          </p>
          {description && <p className="text-muted-foreground mt-1 text-xs">{description}</p>}
        </div>
        {icon && (
          <div className="text-foreground flex h-12 w-12 items-center justify-center rounded-full bg-white/50">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
