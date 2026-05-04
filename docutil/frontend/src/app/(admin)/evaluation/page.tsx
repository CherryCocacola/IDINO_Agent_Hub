"use client";

import { format } from "date-fns";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Play,
  RefreshCw,
  Settings2,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiClient } from "@/lib/api/client";
import { useAuth } from "@/lib/hooks/use-auth";
import { useToast } from "@/lib/hooks/use-toast";

// ---------- Types ----------

interface RunSummary {
  run_id: string;
  run_type: string;
  created_at: string;
  question_count: number;
  avg_context_relevancy: number;
  avg_answer_faithfulness: number;
  avg_answer_relevancy: number;
  avg_hallucination_score: number;
  avg_composite_score: number;
  hallucination_count: number;
}

interface TrendPoint {
  date: string;
  avg_context_relevancy: number;
  avg_answer_faithfulness: number;
  avg_answer_relevancy: number;
  avg_hallucination_score: number;
  avg_composite_score: number;
}

interface EvalConfig {
  id: string;
  organization_id: string;
  context_relevancy_weight: number;
  answer_faithfulness_weight: number;
  answer_relevancy_weight: number;
  hallucination_weight: number;
}

interface EvaluationLog {
  id: string;
  run_id: string;
  question: string;
  answer: string;
  context_relevancy: number;
  answer_faithfulness: number;
  answer_relevancy: number;
  hallucination_score: number;
  has_hallucination: boolean;
  composite_score: number;
  run_type: string;
  question_index: number;
  created_at: string;
}

// ---------- Helpers ----------

function scoreColor(score: number): string {
  if (score >= 0.8) return "text-green-600";
  if (score >= 0.6) return "text-yellow-600";
  return "text-red-600";
}

function scoreBadge(score: number) {
  if (score >= 0.8)
    return <Badge className="bg-green-100 text-green-800">{score.toFixed(2)}</Badge>;
  if (score >= 0.6)
    return <Badge className="bg-yellow-100 text-yellow-800">{score.toFixed(2)}</Badge>;
  return <Badge className="bg-red-100 text-red-800">{score.toFixed(2)}</Badge>;
}

// ---------- Chart colors ----------

const CHART_COLORS = {
  context_relevancy: "#3b82f6",
  answer_faithfulness: "#10b981",
  answer_relevancy: "#8b5cf6",
  hallucination_score: "#f59e0b",
  composite_score: "#ef4444",
};

// ---------- Component ----------

export default function EvaluationPage() {
  const { user } = useAuth();
  const { addToast } = useToast();

  const [tab, setTab] = useState<"runs" | "trend" | "details">("runs");
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [logs, setLogs] = useState<EvaluationLog[]>([]);
  const [config, setConfig] = useState<EvalConfig | null>(null);

  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [configOpen, setConfigOpen] = useState(false);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [logsLoading, setLogsLoading] = useState(false);

  // Config form state
  const [configForm, setConfigForm] = useState({
    context_relevancy_weight: 0.25,
    answer_faithfulness_weight: 0.3,
    answer_relevancy_weight: 0.25,
    hallucination_weight: 0.2,
  });

  // ---------- Data fetching ----------

  const fetchRuns = useCallback(async () => {
    try {
      const res = await apiClient.get<{ items: RunSummary[] }>("/evaluation/runs?limit=30");
      setRuns(res.items || []);
    } catch {
      /* empty */
    }
  }, []);

  const fetchTrend = useCallback(async () => {
    try {
      const res = await apiClient.get<{ data: TrendPoint[] }>("/evaluation/trend?days=30");
      setTrend(res.data || []);
    } catch {
      /* empty */
    }
  }, []);

  const fetchConfig = useCallback(async () => {
    try {
      const res = await apiClient.get<EvalConfig>("/evaluation/config");
      setConfig(res);
      setConfigForm({
        context_relevancy_weight: res.context_relevancy_weight,
        answer_faithfulness_weight: res.answer_faithfulness_weight,
        answer_relevancy_weight: res.answer_relevancy_weight,
        hallucination_weight: res.hallucination_weight,
      });
    } catch {
      /* empty */
    }
  }, []);

  const fetchLogs = useCallback(async (runId: string) => {
    setLogsLoading(true);
    try {
      const res = await apiClient.get<{ items: EvaluationLog[] }>(
        `/evaluation/logs?run_id=${runId}&size=50`
      );
      setLogs(res.items || []);
    } catch {
      /* empty */
    } finally {
      setLogsLoading(false);
    }
  }, []);

  useEffect(() => {
    Promise.all([fetchRuns(), fetchTrend(), fetchConfig()]).finally(() =>
      setLoading(false)
    );
  }, [fetchRuns, fetchTrend, fetchConfig]);

  // ---------- Actions ----------

  const handleRunEvaluation = async () => {
    setRunning(true);
    try {
      const res = await apiClient.post<{ run_id: string }>("/evaluation/run");
      addToast(`평가 시작됨 — 실행 ID: ${res.run_id}`, "success");
    } catch {
      addToast("평가 시작 실패 — 잠시 후 다시 시도해주세요.", "error");
    } finally {
      setRunning(false);
    }
  };

  const handleSaveConfig = async () => {
    const total =
      configForm.context_relevancy_weight +
      configForm.answer_faithfulness_weight +
      configForm.answer_relevancy_weight +
      configForm.hallucination_weight;

    if (Math.abs(total - 1.0) > 0.01) {
      addToast(`가중치 합계가 1.0이어야 합니다. (현재: ${total.toFixed(2)})`, "error");
      return;
    }

    try {
      const res = await apiClient.put<EvalConfig>("/evaluation/config", configForm);
      setConfig(res);
      setConfigOpen(false);
      addToast("평가 가중치가 업데이트되었습니다.", "success");
    } catch {
      addToast("설정 저장 실패", "error");
    }
  };

  const handleViewRunDetails = (runId: string) => {
    setSelectedRunId(runId);
    setTab("details");
    fetchLogs(runId);
  };

  // ---------- Render ----------

  if (loading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-80" />
      </div>
    );
  }

  const latestRun = runs.length > 0 ? runs[0] : null;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">AI 응답 품질 평가</h1>
          <p className="text-sm text-muted-foreground mt-1">
            RAG 파이프라인의 응답 품질을 자동으로 평가하고 추적합니다.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setConfigOpen(true)}
          >
            <Settings2 className="w-4 h-4 mr-1" />
            가중치 설정
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchRuns();
              fetchTrend();
            }}
          >
            <RefreshCw className="w-4 h-4 mr-1" />
            새로고침
          </Button>
          <Button size="sm" onClick={handleRunEvaluation} disabled={running}>
            <Play className="w-4 h-4 mr-1" />
            {running ? "실행 중..." : "수동 평가 실행"}
          </Button>
        </div>
      </div>

      {/* Summary cards */}
      {latestRun && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">컨텍스트 관련성</p>
              <p className={`text-2xl font-bold ${scoreColor(latestRun.avg_context_relevancy)}`}>
                {latestRun.avg_context_relevancy.toFixed(2)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">답변 충실도</p>
              <p className={`text-2xl font-bold ${scoreColor(latestRun.avg_answer_faithfulness)}`}>
                {latestRun.avg_answer_faithfulness.toFixed(2)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">답변 관련성</p>
              <p className={`text-2xl font-bold ${scoreColor(latestRun.avg_answer_relevancy)}`}>
                {latestRun.avg_answer_relevancy.toFixed(2)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">환각 점수</p>
              <p className={`text-2xl font-bold ${scoreColor(latestRun.avg_hallucination_score)}`}>
                {latestRun.avg_hallucination_score.toFixed(2)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">종합 점수</p>
              <p className={`text-2xl font-bold ${scoreColor(latestRun.avg_composite_score)}`}>
                {latestRun.avg_composite_score.toFixed(2)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Tabs value={tab} onValueChange={(v) => setTab(v as typeof tab)}>
        <TabsList>
          <TabsTrigger value="runs">
            <BarChart3 className="w-4 h-4 mr-1" />
            실행 이력
          </TabsTrigger>
          <TabsTrigger value="trend">
            <Activity className="w-4 h-4 mr-1" />
            추이 차트
          </TabsTrigger>
          <TabsTrigger value="details">
            <AlertTriangle className="w-4 h-4 mr-1" />
            상세 결과
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Tab content: Runs */}
      {tab === "runs" && (
        <Card>
          <CardContent className="pt-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>실행 ID</TableHead>
                  <TableHead>유형</TableHead>
                  <TableHead>일시</TableHead>
                  <TableHead className="text-center">질문 수</TableHead>
                  <TableHead className="text-center">컨텍스트</TableHead>
                  <TableHead className="text-center">충실도</TableHead>
                  <TableHead className="text-center">관련성</TableHead>
                  <TableHead className="text-center">환각</TableHead>
                  <TableHead className="text-center">종합</TableHead>
                  <TableHead className="text-center">환각 건수</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={11} className="text-center text-muted-foreground py-8">
                      평가 실행 이력이 없습니다.
                    </TableCell>
                  </TableRow>
                ) : (
                  runs.map((run) => (
                    <TableRow key={run.run_id}>
                      <TableCell className="font-mono text-xs">
                        {run.run_id.slice(0, 10)}...
                      </TableCell>
                      <TableCell>
                        <Badge variant={run.run_type === "manual" ? "outline" : "secondary"}>
                          {run.run_type === "manual" ? "수동" : "예약"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm">
                        {format(new Date(run.created_at), "MM/dd HH:mm")}
                      </TableCell>
                      <TableCell className="text-center">{run.question_count}</TableCell>
                      <TableCell className="text-center">{scoreBadge(run.avg_context_relevancy)}</TableCell>
                      <TableCell className="text-center">{scoreBadge(run.avg_answer_faithfulness)}</TableCell>
                      <TableCell className="text-center">{scoreBadge(run.avg_answer_relevancy)}</TableCell>
                      <TableCell className="text-center">{scoreBadge(run.avg_hallucination_score)}</TableCell>
                      <TableCell className="text-center">{scoreBadge(run.avg_composite_score)}</TableCell>
                      <TableCell className="text-center">
                        {run.hallucination_count > 0 ? (
                          <Badge className="bg-red-100 text-red-800">
                            {run.hallucination_count}
                          </Badge>
                        ) : (
                          <span className="text-green-600">0</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewRunDetails(run.run_id)}
                        >
                          상세
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Tab content: Trend */}
      {tab === "trend" && (
        <Card>
          <CardContent className="pt-4">
            {trend.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                추이 데이터가 없습니다.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={trend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="avg_context_relevancy"
                    name="컨텍스트 관련성"
                    stroke={CHART_COLORS.context_relevancy}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="avg_answer_faithfulness"
                    name="답변 충실도"
                    stroke={CHART_COLORS.answer_faithfulness}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="avg_answer_relevancy"
                    name="답변 관련성"
                    stroke={CHART_COLORS.answer_relevancy}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="avg_hallucination_score"
                    name="환각 점수"
                    stroke={CHART_COLORS.hallucination_score}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="avg_composite_score"
                    name="종합 점수"
                    stroke={CHART_COLORS.composite_score}
                    strokeWidth={3}
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab content: Details */}
      {tab === "details" && (
        <Card>
          <CardContent className="pt-4">
            {selectedRunId ? (
              <>
                <p className="text-sm text-muted-foreground mb-4">
                  실행 ID: <span className="font-mono">{selectedRunId}</span>
                </p>
                {logsLoading ? (
                  <div className="space-y-2">
                    {[1, 2, 3].map((i) => (
                      <Skeleton key={i} className="h-12" />
                    ))}
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-8">#</TableHead>
                        <TableHead>질문</TableHead>
                        <TableHead className="text-center">컨텍스트</TableHead>
                        <TableHead className="text-center">충실도</TableHead>
                        <TableHead className="text-center">관련성</TableHead>
                        <TableHead className="text-center">환각</TableHead>
                        <TableHead className="text-center">종합</TableHead>
                        <TableHead className="text-center">환각 여부</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {logs.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={8} className="text-center text-muted-foreground py-8">
                            결과가 없습니다.
                          </TableCell>
                        </TableRow>
                      ) : (
                        logs.map((log) => (
                          <TableRow key={log.id}>
                            <TableCell className="text-xs text-muted-foreground">
                              {log.question_index + 1}
                            </TableCell>
                            <TableCell className="max-w-xs truncate text-sm">
                              {log.question}
                            </TableCell>
                            <TableCell className="text-center">{scoreBadge(log.context_relevancy)}</TableCell>
                            <TableCell className="text-center">{scoreBadge(log.answer_faithfulness)}</TableCell>
                            <TableCell className="text-center">{scoreBadge(log.answer_relevancy)}</TableCell>
                            <TableCell className="text-center">{scoreBadge(log.hallucination_score)}</TableCell>
                            <TableCell className="text-center">{scoreBadge(log.composite_score)}</TableCell>
                            <TableCell className="text-center">
                              {log.has_hallucination ? (
                                <Badge className="bg-red-100 text-red-800">있음</Badge>
                              ) : (
                                <Badge className="bg-green-100 text-green-800">없음</Badge>
                              )}
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                )}
              </>
            ) : (
              <p className="text-center text-muted-foreground py-8">
                실행 이력에서 항목을 선택하면 상세 결과를 확인할 수 있습니다.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Config dialog */}
      <Dialog open={configOpen} onOpenChange={setConfigOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>평가 가중치 설정</DialogTitle>
            <DialogDescription>
              각 메트릭의 가중치를 설정합니다. 합계는 1.0이어야 합니다.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>컨텍스트 관련성 (Context Relevancy)</Label>
              <Input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={configForm.context_relevancy_weight}
                onChange={(e) =>
                  setConfigForm((f) => ({
                    ...f,
                    context_relevancy_weight: parseFloat(e.target.value) || 0,
                  }))
                }
              />
            </div>
            <div>
              <Label>답변 충실도 (Answer Faithfulness)</Label>
              <Input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={configForm.answer_faithfulness_weight}
                onChange={(e) =>
                  setConfigForm((f) => ({
                    ...f,
                    answer_faithfulness_weight: parseFloat(e.target.value) || 0,
                  }))
                }
              />
            </div>
            <div>
              <Label>답변 관련성 (Answer Relevancy)</Label>
              <Input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={configForm.answer_relevancy_weight}
                onChange={(e) =>
                  setConfigForm((f) => ({
                    ...f,
                    answer_relevancy_weight: parseFloat(e.target.value) || 0,
                  }))
                }
              />
            </div>
            <div>
              <Label>환각 탐지 (Hallucination Detection)</Label>
              <Input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={configForm.hallucination_weight}
                onChange={(e) =>
                  setConfigForm((f) => ({
                    ...f,
                    hallucination_weight: parseFloat(e.target.value) || 0,
                  }))
                }
              />
            </div>
            <p className="text-sm text-muted-foreground">
              합계:{" "}
              <span
                className={
                  Math.abs(
                    configForm.context_relevancy_weight +
                      configForm.answer_faithfulness_weight +
                      configForm.answer_relevancy_weight +
                      configForm.hallucination_weight -
                      1.0
                  ) > 0.01
                    ? "text-red-600 font-bold"
                    : "text-green-600 font-bold"
                }
              >
                {(
                  configForm.context_relevancy_weight +
                  configForm.answer_faithfulness_weight +
                  configForm.answer_relevancy_weight +
                  configForm.hallucination_weight
                ).toFixed(2)}
              </span>
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfigOpen(false)}>
              취소
            </Button>
            <Button onClick={handleSaveConfig}>저장</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
