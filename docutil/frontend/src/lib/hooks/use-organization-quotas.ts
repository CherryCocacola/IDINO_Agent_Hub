/**
 * use-organization-quotas.ts — 조직 월 쿼터 조회 훅
 *
 * Phase 4 S3 D5 산출물. 문서 디자이너의 `ImageForm` 이 DALL-E 잔여량을
 * 표시하기 위해 호출하는 훅. 백엔드 ``GET /organizations/{org_id}/quotas/current``
 * 의 응답을 normalize 해서 FE camelCase + typed 구조로 반환한다.
 *
 * 동작:
 *   - organizationId 가 undefined 면 훅 내부적으로 query 를 비활성화한다
 *     (SSR/로딩 중 초기 상태 대응).
 *   - React Query 의 ``staleTime`` 5 분 캐시로, 폼이 빠르게 재렌더되어도
 *     과도한 네트워크 호출을 방지.
 *   - 403/404 등 에러는 quiet fallback — 호출부는 `error` 만 확인하고 UI 를
 *     숨기면 된다 (쿼터 표시는 보조 정보라 필수 아님).
 *
 * 제약 (CLAUDE.md / anti-patterns.md):
 *   - apiClient 외 fetch 금지.
 *   - response snake_case 를 훅에서 camelCase 로 변환 (backend 경계 매핑).
 */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";

// ─── 타입 ─────────────────────────────────────────────────────────────────

/** 백엔드 응답 raw 타입 (snake_case). */
interface QuotaStatusRaw {
  quota_type: string;
  monthly_limit: number;
  used_count: number;
  remaining: number;
  year_month: string;
}

interface QuotasResponseRaw {
  organization_id: string;
  year_month: string;
  quotas: Record<string, QuotaStatusRaw>;
}

/** FE 에서 사용하는 쿼터 상태. 필드명은 backend 와 동일하게 유지 (매핑 오버헤드 최소화). */
export interface QuotaStatus {
  quota_type: string;
  monthly_limit: number;
  used_count: number;
  remaining: number;
  year_month: string;
}

export interface UseOrganizationQuotasResult {
  /** quota_type → QuotaStatus 맵. 미로딩/에러 시 undefined. */
  quotas: Record<string, QuotaStatus> | undefined;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

// ─── 상수 ─────────────────────────────────────────────────────────────────

/** 캐시 staleTime — 5 분. 이 기간 동안 동일 query key 는 재요청하지 않는다. */
const QUOTA_STALE_TIME_MS = 5 * 60 * 1000;

// ─── 훅 본체 ───────────────────────────────────────────────────────────────

/**
 * 조직 월 쿼터 조회 훅.
 *
 * @param organizationId 조회할 조직 ID. undefined 이면 query 비활성.
 * @returns quotas (quota_type 매핑), 로딩/에러 상태, 재조회 함수.
 */
export function useOrganizationQuotas(
  organizationId: string | undefined,
): UseOrganizationQuotasResult {
  const query = useQuery<QuotasResponseRaw, Error>({
    queryKey: ["organization-quotas", organizationId ?? "__none__"],
    queryFn: () => {
      if (!organizationId) {
        // 실제로는 enabled=false 로 호출 자체가 막히지만, 타입 가드.
        return Promise.reject(new Error("organizationId required"));
      }
      return apiClient.get<QuotasResponseRaw>(`/organizations/${organizationId}/quotas/current`);
    },
    enabled: Boolean(organizationId),
    staleTime: QUOTA_STALE_TIME_MS,
    // 403/404 등은 재시도 해봐야 의미 없음.
    retry: false,
  });

  return {
    quotas: query.data?.quotas,
    isLoading: query.isLoading,
    error: query.error ?? null,
    refetch: () => {
      void query.refetch();
    },
  };
}

// ─── 한도 수정 훅 (Phase 4 S3 D6) ────────────────────────────────────────

/** 한도 수정 mutation 인자. */
export interface UpdateQuotaLimitInput {
  quotaType: string;
  monthlyLimit: number;
}

export interface UseUpdateQuotaLimitResult {
  /** mutation 실행 함수. resolves 시 새 쿼터 상태를 반환한다. */
  mutateAsync: (input: UpdateQuotaLimitInput) => Promise<QuotaStatus>;
  isPending: boolean;
  error: Error | null;
}

/**
 * 조직 월 쿼터 한도 수정 훅.
 *
 * ``PUT /organizations/{org_id}/quotas/{quota_type}`` 를 호출해 ``monthly_limit``
 * 을 갱신한 뒤, 관련 query 캐시를 invalidate 한다.
 *
 * @param organizationId 수정 대상 조직 ID.
 * @returns mutation 실행 함수 + 상태.
 */
export function useUpdateQuotaLimit(organizationId: string | undefined): UseUpdateQuotaLimitResult {
  const queryClient = useQueryClient();

  const mutation = useMutation<QuotaStatus, Error, UpdateQuotaLimitInput>({
    mutationFn: async ({ quotaType, monthlyLimit }) => {
      if (!organizationId) {
        throw new Error("organizationId가 지정되지 않아 쿼터를 수정할 수 없습니다.");
      }
      // 서버 응답은 snake_case 이므로 raw 로 받고, 훅 내부에서 그대로 반환.
      const raw = await apiClient.put<QuotaStatusRaw>(
        `/organizations/${organizationId}/quotas/${quotaType}`,
        { monthly_limit: monthlyLimit },
      );
      return {
        quota_type: raw.quota_type,
        monthly_limit: raw.monthly_limit,
        used_count: raw.used_count,
        remaining: raw.remaining,
        year_month: raw.year_month,
      };
    },
    onSuccess: () => {
      // 조회 query 재검증 — 다음 ImageForm/관리자 페이지 렌더에 반영.
      void queryClient.invalidateQueries({
        queryKey: ["organization-quotas", organizationId ?? "__none__"],
      });
    },
  });

  return {
    mutateAsync: (input) => mutation.mutateAsync(input),
    isPending: mutation.isPending,
    error: mutation.error ?? null,
  };
}

export default useOrganizationQuotas;
