import { AlertTriangle, X } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils/cn";

interface WarningBannerProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  dismissible?: boolean;
  onDismiss?: () => void;
  children: React.ReactNode;
}

export function WarningBanner({
  title,
  dismissible = false,
  onDismiss,
  children,
  className,
  ...props
}: WarningBannerProps) {
  const [dismissed, setDismissed] = React.useState(false);

  if (dismissed) {
    return null;
  }

  const handleDismiss = () => {
    setDismissed(true);
    onDismiss?.();
  };

  return (
    <div
      className={cn("relative rounded-lg border border-yellow-300 bg-yellow-50 p-4", className)}
      role="alert"
      {...props}
    >
      <div className="flex gap-3">
        <AlertTriangle className="h-5 w-5 shrink-0 text-yellow-600" />
        <div className="flex-1">
          {title && <h4 className="mb-1 text-sm font-semibold text-yellow-800">{title}</h4>}
          <div className="text-sm text-yellow-700">{children}</div>
        </div>
        {dismissible && (
          <button
            onClick={handleDismiss}
            className="shrink-0 rounded p-1 text-yellow-600 hover:bg-yellow-100 hover:text-yellow-800"
            aria-label="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}
