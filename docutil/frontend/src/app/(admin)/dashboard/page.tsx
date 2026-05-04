"use client";

import { Users, MessageSquare, FileCheck } from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import {
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MetricCard } from "@/components/ui/metric-card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBar } from "@/components/ui/status-badge";
import { apiClient } from "@/lib/api/client";
import { useToast } from "@/lib/hooks/use-toast";

// ---------- Type definitions ----------

interface DashboardMetricsResponse {
  total_users: number;
  active_users: number;
  total_documents: number;
  total_searches: number;
  feature_usage: Record<string, number>;
}

interface DashboardMetrics {
  search_users: number;
  feature_usage: number;
  registered_docs: number;
  total_searches: number;
}

interface UploadStatusData {
  name: string;
  value: number;
  color: string;
}

interface ResponseTimeResponse {
  timestamps: string[];
  values: number[];
}

interface ResponseTimeEntry {
  hour: string;
  avg_ms: number;
}

interface SearchErrorResponse {
  dates: string[];
  error_counts: number[];
}

interface SearchErrorEntry {
  date: string;
  errors: number;
}

interface FeatureUsageEntry {
  name: string;
  requests: number;
  responses: number;
  failures: number;
}

// ---------- Constants ----------

const UPLOAD_STATUS_COLORS: Record<string, string> = {
  completed: "#22c55e",
  processing: "#3b82f6",
  waiting: "#eab308",
  error: "#ef4444",
};

const REFRESH_INTERVAL_MS = 30_000;

// Sample feature usage data (in production, fetch from API)
const FEATURE_USAGE_DATA: FeatureUsageEntry[] = [
  { name: "검색", requests: 150, responses: 145, failures: 5 },
  { name: "Q&A", requests: 80, responses: 75, failures: 5 },
  { name: "챗봇", requests: 120, responses: 115, failures: 5 },
  { name: "에이전트", requests: 40, responses: 38, failures: 2 },
];

// ---------- Component ----------

export default function DashboardPage() {
  const { addToast } = useToast();

  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [uploadStatus, setUploadStatus] = useState<UploadStatusData[]>([]);
  const [responseTime, setResponseTime] = useState<ResponseTimeEntry[]>([]);
  const [searchErrors, setSearchErrors] = useState<SearchErrorEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = useCallback(async () => {
    try {
      const [metricsRes, uploadRes, responseRes, errorsRes] = await Promise.all([
        apiClient.get<DashboardMetricsResponse>("/dashboard/metrics").catch(() => null),
        apiClient.get<Record<string, number>>("/dashboard/upload-status").catch(() => null),
        apiClient.get<ResponseTimeResponse>("/dashboard/response-times").catch(() => null),
        apiClient.get<SearchErrorResponse>("/dashboard/search-errors").catch(() => null),
      ]);

      // Map API response to component format (with safe defaults)
      const mappedMetrics: DashboardMetrics = {
        search_users: metricsRes?.active_users ?? 0,
        feature_usage: metricsRes?.feature_usage
          ? Object.values(metricsRes.feature_usage).reduce((a, b) => a + b, 0)
          : 0,
        registered_docs: metricsRes?.total_documents ?? 0,
        total_searches: metricsRes?.total_searches ?? 0,
      };
      setMetrics(mappedMetrics);

      // Safe upload status mapping
      const uploadData: UploadStatusData[] = uploadRes
        ? Object.entries(uploadRes).map(([name, value]) => ({
            name,
            value: typeof value === "number" ? value : 0,
            color: UPLOAD_STATUS_COLORS[name] || "#94a3b8",
          }))
        : [];
      setUploadStatus(uploadData);

      // Safe response time mapping
      const timestamps = responseRes?.timestamps ?? [];
      const values = responseRes?.values ?? [];
      const mappedResponseTime: ResponseTimeEntry[] = timestamps.map((ts, i) => ({
        hour: String(ts),
        avg_ms: typeof values[i] === "number" ? values[i] : 0,
      }));
      setResponseTime(mappedResponseTime);

      // Safe search errors mapping
      const dates = errorsRes?.dates ?? [];
      const errorCounts = errorsRes?.error_counts ?? [];
      const mappedSearchErrors: SearchErrorEntry[] = dates.map((date, i) => ({
        date: String(date),
        errors: typeof errorCounts[i] === "number" ? errorCounts[i] : 0,
      }));
      setSearchErrors(mappedSearchErrors);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load dashboard data";
      addToast(message, "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  // Map upload status to StatusBar format
  const statusBarItems = uploadStatus.map((item) => ({
    label:
      item.name === "completed"
        ? "완료"
        : item.name === "processing"
          ? "진행중"
          : item.name === "waiting"
            ? "대기"
            : item.name === "error"
              ? "오류"
              : item.name,
    value: item.value,
    status:
      item.name === "completed"
        ? ("complete" as const)
        : item.name === "processing"
          ? ("progress" as const)
          : item.name === "waiting"
            ? ("waiting" as const)
            : item.name === "error"
              ? ("error" as const)
              : ("default" as const),
  }));

  // ---------- Render ----------

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-foreground text-2xl font-bold">대시보드</h1>
        <p className="text-muted-foreground mt-1 text-sm">문서 활용 현황을 한눈에 확인하세요</p>
      </div>

      {/* Row 1 -- Metric cards (3 colored cards) */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <>
            <Skeleton className="h-32 w-full rounded-xl" />
            <Skeleton className="h-32 w-full rounded-xl" />
            <Skeleton className="h-32 w-full rounded-xl" />
          </>
        ) : (
          <>
            <MetricCard
              variant="pink"
              title="검색 사용자 수"
              value={metrics?.search_users ?? 0}
              icon={<Users className="h-6 w-6" />}
              description="오늘 활성 사용자"
            />
            <MetricCard
              variant="green"
              title="검색 기능 사용 수"
              value={metrics?.feature_usage ?? 0}
              icon={<MessageSquare className="h-6 w-6" />}
              description="오늘 총 요청 수"
            />
            <MetricCard
              variant="yellow"
              title="등록 완료 문서 수"
              value={metrics?.registered_docs ?? 0}
              icon={<FileCheck className="h-6 w-6" />}
              description="처리 완료된 문서"
            />
          </>
        )}
      </div>

      {/* Row 2 -- Feature usage bar chart & Upload status donut */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Feature Usage Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">검색 기능 사용 수</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={FEATURE_USAGE_DATA}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" fontSize={12} />
                  <YAxis fontSize={12} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="requests" name="요청" fill="#7c3aed" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="responses" name="답변" fill="#22c55e" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="failures" name="실패" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Upload Status Donut Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">문서 업로드 상태</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="mx-auto h-64 w-64 rounded-full" />
            ) : (
              <div className="space-y-4">
                {/* Status bar summary */}
                <StatusBar items={statusBarItems} />

                {/* Donut chart */}
                {uploadStatus.length > 0 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie
                        data={uploadStatus}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={3}
                        dataKey="value"
                        nameKey="name"
                      >
                        {uploadStatus.map((entry) => (
                          <Cell key={entry.name} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value, name) => {
                          const numValue = typeof value === "number" ? value : 0;
                          const strName = String(name || "");
                          const label =
                            strName === "completed"
                              ? "완료"
                              : strName === "processing"
                                ? "진행중"
                                : strName === "waiting"
                                  ? "대기"
                                  : strName === "error"
                                    ? "오류"
                                    : strName;
                          return [numValue, label];
                        }}
                      />
                      <Legend
                        formatter={(value) => {
                          const strValue = String(value || "");
                          return strValue === "completed"
                            ? "완료"
                            : strValue === "processing"
                              ? "진행중"
                              : strValue === "waiting"
                                ? "대기"
                                : strValue === "error"
                                  ? "오류"
                                  : strValue;
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="text-muted-foreground flex h-[220px] items-center justify-center text-sm">
                    데이터가 없습니다
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Row 3 -- Response Time line chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">시간대별 응답 시간</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-64 w-full" />
          ) : responseTime.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={responseTime}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="hour" fontSize={12} />
                <YAxis unit="ms" fontSize={12} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="avg_ms"
                  name="평균 응답시간 (ms)"
                  stroke="#7c3aed"
                  strokeWidth={2}
                  dot={{ fill: "#7c3aed", r: 3 }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-muted-foreground flex h-[300px] items-center justify-center text-sm">
              데이터가 없습니다
            </div>
          )}
        </CardContent>
      </Card>

      {/* Row 4 -- Search Errors bar chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">날짜별 검색 오류 수</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-64 w-full" />
          ) : searchErrors.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={searchErrors}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Legend />
                <Bar dataKey="errors" name="오류 수" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-muted-foreground flex h-[300px] items-center justify-center text-sm">
              데이터가 없습니다
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
