/**
 * QuotasPage — 관리자 조직 월 쿼터 설정 페이지
 *
 * Phase 4 S3 D6 산출물 (phase3_execution_roadmap.md §2.3).
 *
 * 역할:
 *   - 현재 월 쿼터 2종 (dalle_monthly / unsplash_monthly) 의 한도 / 사용량 / 잔여량을
 *     한 테이블에 표시.
 *   - 한도 셀을 편집 모드로 전환해 `PUT /organizations/{id}/quotas/{type}` 호출.
 *
 * 권한:
 *   - AdminLayout 이 super_admin / admin / org_admin 만 진입 허용하므로,
 *     본 페이지는 추가 가드 없이 super_admin / org_admin 전용 기능만 on/off.
 *   - super_admin 은 자기 조직을 기본으로 하되, 다른 조직 ID 를 입력해 타 조직
 *     쿼터도 조회/수정 가능 (조직 목록 API 가 아직 없어 UUID 수동 입력 UX).
 *   - 그 외 admin 은 자기 조직 고정 (입력 필드 숨김).
 *
 * 주의:
 *   - 아직 조직 목록 API 가 없으므로 super_admin 용 조직 선택은 단순 텍스트 입력.
 *     조직 목록 API 추가 후 Select 로 교체 예정 (D10+).
 *   - `useOrganizationQuotas` 훅 응답은 snake_case 유지 (훅 내 매핑 주석 참조).
 */

"use client";

import { AlertCircle, Check, Pencil, RefreshCw, X } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { WarningBanner } from "@/components/ui/warning-banner";
import { isApiError } from "@/lib/api/client";
import { useAuth } from "@/lib/hooks/use-auth";
import {
  useOrganizationQuotas,
  useUpdateQuotaLimit,
  type QuotaStatus,
} from "@/lib/hooks/use-organization-quotas";
import { useToast } from "@/lib/hooks/use-toast";

// ─── 상수 ─────────────────────────────────────────────────────────────────

/** 관리자 UI 에 표시할 쿼터 타입 라벨 매핑. */
const QUOTA_TYPE_LABEL: Record<string, string> = {
  dalle_monthly: "DALL-E 이미지 (월)",
  unsplash_monthly: "Unsplash 이미지 (월)",
};

/** 표시 순서 고정 — 배열 렌더시 키 순서 의존 제거. */
const QUOTA_TYPE_ORDER = ["dalle_monthly", "unsplash_monthly"] as const;

// ─── 컴포넌트 ─────────────────────────────────────────────────────────────

export default function QuotasPage() {
  const { user } = useAuth();
  const { addToast } = useToast();

  // super_admin 은 조직 ID 를 수동 입력, 그 외 역할은 자기 조직 고정.
  const isSuperAdmin = user?.role === "super_admin";
  const [targetOrgId, setTargetOrgId] = useState<string>(() => user?.organization_id ?? "");

  const { quotas, isLoading, error, refetch } = useOrganizationQuotas(targetOrgId || undefined);

  const { mutateAsync: updateLimit, isPending: isUpdating } = useUpdateQuotaLimit(
    targetOrgId || undefined,
  );

  // 편집 중인 quota_type. null 이면 편집 없음.
  const [editingType, setEditingType] = useState<string | null>(null);
  const [editingValue, setEditingValue] = useState<string>("");

  /** 표시용 쿼터 배열. 빈 맵이면 빈 배열. */
  const rows: QuotaStatus[] = useMemo(() => {
    if (!quotas) return [];
    return QUOTA_TYPE_ORDER.flatMap((t) => (quotas[t] ? [quotas[t]] : []));
  }, [quotas]);

  // ── 편집 핸들러 ────────────────────────────────────────────────────────
  const handleEditStart = (quota: QuotaStatus) => {
    setEditingType(quota.quota_type);
    setEditingValue(String(quota.monthly_limit));
  };

  const handleEditCancel = () => {
    setEditingType(null);
    setEditingValue("");
  };

  const handleEditSave = async (quotaType: string) => {
    const parsed = Number.parseInt(editingValue, 10);
    if (Number.isNaN(parsed) || parsed < 0) {
      addToast("0 이상의 정수를 입력해 주세요.", "error");
      return;
    }
    try {
      await updateLimit({ quotaType, monthlyLimit: parsed });
      addToast(`${QUOTA_TYPE_LABEL[quotaType] ?? quotaType} 한도가 업데이트되었습니다.`, "success");
      setEditingType(null);
      setEditingValue("");
    } catch (err) {
      // 404 는 백엔드 미구현 시나리오 — 친절한 한국어 토스트.
      if (isApiError(err) && err.status === 404) {
        addToast("백엔드에 쿼터 수정 엔드포인트가 아직 배포되지 않았습니다.", "error");
      } else if (isApiError(err) && err.status === 403) {
        addToast("이 조직의 쿼터를 수정할 권한이 없습니다.", "error");
      } else {
        addToast(err instanceof Error ? err.message : "쿼터 수정에 실패했습니다.", "error");
      }
    }
  };

  // ── 조직 ID 변경 (super_admin only) ─────────────────────────────────────
  const [orgIdInput, setOrgIdInput] = useState<string>(targetOrgId);
  const handleApplyOrg = () => {
    const trimmed = orgIdInput.trim();
    if (trimmed.length === 0) {
      addToast("조직 ID 를 입력해 주세요.", "error");
      return;
    }
    setTargetOrgId(trimmed);
  };

  // ── 렌더 ──────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-foreground text-2xl font-bold">쿼터 관리</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            조직의 월 이미지 생성 한도를 조회하고 조정합니다.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isLoading || !targetOrgId}
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          새로고침
        </Button>
      </div>

      <WarningBanner title="쿼터 정책 안내" dismissible>
        한도는 매월 자동 집계되며, 이미지 자동 선택 기능이 소진되면 해당 월은 URL 업로드/프롬프트
        모드만 사용할 수 있습니다. DALL-E 는 비용이 발생하므로 조직 정책에 맞게 설정해 주세요.
      </WarningBanner>

      {/* super_admin 전용 조직 ID 입력 */}
      {isSuperAdmin && (
        <Card>
          <CardContent className="space-y-3 p-4">
            <Label htmlFor="target-org-id" className="text-sm font-medium">
              조회할 조직 ID (UUID)
            </Label>
            <div className="flex items-center gap-2">
              <Input
                id="target-org-id"
                value={orgIdInput}
                onChange={(e) => setOrgIdInput(e.target.value)}
                placeholder="예: 00000000-0000-0000-0000-000000000000"
              />
              <Button onClick={handleApplyOrg} disabled={!orgIdInput.trim()}>
                조회
              </Button>
            </div>
            {targetOrgId && (
              <p className="text-muted-foreground text-xs">
                현재 조회 대상: <code className="bg-muted rounded px-1">{targetOrgId}</code>
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* 에러 상태 */}
      {error && (
        <div
          role="alert"
          className="border-destructive/30 bg-destructive/5 text-destructive flex items-start gap-2 rounded-md border p-3 text-sm"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <div>
            <p className="font-medium">쿼터 정보를 불러오지 못했습니다.</p>
            <p className="mt-1 text-xs">{error.message}</p>
          </div>
        </div>
      )}

      {/* 테이블 */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-3 p-6">
              {Array.from({ length: 2 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !targetOrgId ? (
            <div className="text-muted-foreground p-6 text-center text-sm">
              조회할 조직 ID 를 먼저 지정해 주세요.
            </div>
          ) : rows.length === 0 ? (
            <div className="text-muted-foreground p-6 text-center text-sm">
              쿼터 정보가 없습니다.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>쿼터 유형</TableHead>
                  <TableHead className="text-right">월 한도</TableHead>
                  <TableHead className="text-right">사용</TableHead>
                  <TableHead className="text-right">잔여</TableHead>
                  <TableHead>연-월</TableHead>
                  <TableHead className="w-40">작업</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((quota) => {
                  const isEditing = editingType === quota.quota_type;
                  const label = QUOTA_TYPE_LABEL[quota.quota_type] ?? quota.quota_type;
                  const remainingVariant =
                    quota.remaining === 0
                      ? "destructive"
                      : quota.remaining <= Math.max(1, Math.floor(quota.monthly_limit * 0.1))
                        ? "warning"
                        : "success";

                  return (
                    <TableRow key={quota.quota_type}>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{label}</span>
                          <code className="text-muted-foreground text-xs">{quota.quota_type}</code>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        {isEditing ? (
                          <Input
                            type="number"
                            min={0}
                            value={editingValue}
                            onChange={(e) => setEditingValue(e.target.value)}
                            className="ml-auto w-28 text-right"
                            aria-label={`${label} 월 한도`}
                          />
                        ) : (
                          <span className="tabular-nums">
                            {quota.monthly_limit.toLocaleString()}
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-muted-foreground text-right tabular-nums">
                        {quota.used_count.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge variant={remainingVariant} className="tabular-nums">
                          {quota.remaining.toLocaleString()}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{quota.year_month}</TableCell>
                      <TableCell>
                        {isEditing ? (
                          <div className="flex items-center gap-1">
                            <Button
                              size="sm"
                              onClick={() => handleEditSave(quota.quota_type)}
                              disabled={isUpdating}
                            >
                              <Check className="mr-1 h-3 w-3" />
                              저장
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={handleEditCancel}
                              disabled={isUpdating}
                            >
                              <X className="mr-1 h-3 w-3" />
                              취소
                            </Button>
                          </div>
                        ) : (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleEditStart(quota)}
                          >
                            <Pencil className="mr-1 h-3 w-3" />
                            한도 수정
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
