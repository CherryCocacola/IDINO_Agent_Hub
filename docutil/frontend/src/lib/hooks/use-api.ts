"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";

// Generic fetch hook
export function useApiQuery<T>(key: string[], endpoint: string, params?: Record<string, string>) {
  return useQuery<T>({
    queryKey: key,
    queryFn: () => apiClient.get<T>(endpoint, params),
  });
}

// Generic mutation hook
export function useApiMutation<T, V = unknown>(
  endpoint: string,
  options?: {
    method?: "post" | "put" | "delete";
    invalidateKeys?: string[][];
    onSuccess?: (data: T) => void;
  },
) {
  const queryClient = useQueryClient();
  const method = options?.method || "post";

  return useMutation<T, Error, V>({
    mutationFn: (data) => {
      switch (method) {
        case "put":
          return apiClient.put<T>(endpoint, data);
        case "delete":
          return apiClient.delete<T>(endpoint);
        default:
          return apiClient.post<T>(endpoint, data);
      }
    },
    onSuccess: (data) => {
      options?.invalidateKeys?.forEach((key) => {
        queryClient.invalidateQueries({ queryKey: key });
      });
      options?.onSuccess?.(data);
    },
  });
}

// Document-specific hooks
export function useDocuments(params: {
  page?: number;
  size?: number;
  status?: string;
  folderId?: string;
}) {
  const searchParams: Record<string, string> = {};
  if (params.page) searchParams.page = String(params.page);
  if (params.size) searchParams.size = String(params.size);
  if (params.status) searchParams.status = params.status;
  if (params.folderId) searchParams.folder_id = params.folderId;

  return useApiQuery(["documents", JSON.stringify(params)], "/documents", searchParams);
}

export function useProjects(page = 1, size = 20) {
  return useApiQuery(["projects", String(page)], "/projects", {
    page: String(page),
    size: String(size),
  });
}

export function useDashboardMetrics() {
  return useApiQuery(["dashboard", "metrics"], "/dashboard/metrics");
}

export function useSearchScopes() {
  return useApiQuery(["search-scopes"], "/search-scopes");
}

export function useChatSessions(page = 1) {
  return useApiQuery(["chat-sessions", String(page)], "/chat/sessions", { page: String(page) });
}
