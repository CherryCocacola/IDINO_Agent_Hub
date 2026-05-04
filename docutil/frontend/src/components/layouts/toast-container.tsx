"use client";

import { X, CheckCircle, AlertCircle } from "lucide-react";

import { useToast } from "@/lib/hooks/use-toast";

export function ToastContainer() {
  const { toasts, dismiss } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed right-4 bottom-4 z-[100] flex flex-col gap-2">
      {toasts.map((toast) => {
        const isDestructive = toast.variant === "destructive";
        return (
          <div
            key={toast.id}
            className={`flex items-center gap-3 rounded-lg border px-4 py-3 shadow-lg transition-all duration-300 ${
              isDestructive
                ? "border-red-200 bg-red-50 text-red-800"
                : "border-gray-200 bg-white text-gray-800"
            }`}
            role="alert"
          >
            {isDestructive ? (
              <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
            ) : (
              <CheckCircle className="h-5 w-5 shrink-0 text-green-500" />
            )}
            <div className="flex flex-col">
              {toast.title && <p className="text-sm font-medium">{toast.title}</p>}
              {toast.description && <p className="text-sm">{toast.description}</p>}
            </div>
            <button
              onClick={() => dismiss(toast.id)}
              className="ml-2 shrink-0 rounded-md p-0.5 opacity-70 hover:opacity-100"
              aria-label="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
