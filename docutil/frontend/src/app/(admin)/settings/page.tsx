"use client";

import {
  Settings,
  Shield,
  Database,
  Save,
  Loader2,
  CheckCircle2,
  XCircle,
  Trash2,
  Wrench,
} from "lucide-react";
import { useState, useEffect, useCallback } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { apiClient } from "@/lib/api/client";
import { useAuth } from "@/lib/hooks/use-auth";
import { useToast } from "@/lib/hooks/use-toast";

// ---------- Types ----------

interface GeneralSettings {
  default_language: string;
  maintenance_mode: boolean;
}

interface SecuritySettings {
  password_min_length: number;
  password_require_uppercase: boolean;
  password_require_number: boolean;
  password_require_special: boolean;
  session_timeout_minutes: number;
}

interface StorageSettings {
  minio_connected: boolean;
  minio_endpoint: string;
  total_storage_bytes: number;
  used_storage_bytes: number;
}

interface SettingsData {
  general: GeneralSettings;
  security: SecuritySettings;
  storage: StorageSettings;
}

// ---------- Helpers ----------

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

// ---------- Component ----------

interface CleanupResult {
  status: string;
  message?: string;
  orphaned_documents_cleaned: number;
  qdrant_document_ids_total?: number;
  db_document_ids_total?: number;
  orphaned_document_ids?: string[];
}

export default function SettingsPage() {
  const { addToast } = useToast();
  const { user } = useAuth();

  const [loading, setLoading] = useState(true);

  // General settings
  const [general, setGeneral] = useState<GeneralSettings>({
    default_language: "en",
    maintenance_mode: false,
  });
  const [generalSaving, setGeneralSaving] = useState(false);

  // Security settings
  const [security, setSecurity] = useState<SecuritySettings>({
    password_min_length: 8,
    password_require_uppercase: true,
    password_require_number: true,
    password_require_special: true,
    session_timeout_minutes: 30,
  });
  const [securitySaving, setSecuritySaving] = useState(false);

  // Storage settings
  const [storage, setStorage] = useState<StorageSettings>({
    minio_connected: false,
    minio_endpoint: "",
    total_storage_bytes: 0,
    used_storage_bytes: 0,
  });
  const [storageSaving, setStorageSaving] = useState(false);

  // Maintenance
  const [cleanupRunning, setCleanupRunning] = useState(false);
  const [cleanupResult, setCleanupResult] = useState<CleanupResult | null>(null);

  // ---------- Fetch ----------

  const fetchSettings = useCallback(async () => {
    try {
      const data = await apiClient.get<SettingsData>("/settings");
      if (data?.general) setGeneral(data.general);
      if (data?.security) setSecurity(data.security);
      if (data?.storage) setStorage(data.storage);
    } catch {
      // Settings API not available - use defaults silently
      console.log("Settings API not available, using defaults");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  // ---------- Save handlers ----------

  const saveGeneral = async () => {
    setGeneralSaving(true);
    try {
      await apiClient.put("/settings/general", general);
      addToast("General settings saved successfully", "success");
    } catch {
      addToast("Settings API not available", "default");
    } finally {
      setGeneralSaving(false);
    }
  };

  const saveSecurity = async () => {
    setSecuritySaving(true);
    try {
      await apiClient.put("/settings/security", security);
      addToast("Security settings saved successfully", "success");
    } catch {
      addToast("Settings API not available", "default");
    } finally {
      setSecuritySaving(false);
    }
  };

  const saveStorage = async () => {
    setStorageSaving(true);
    try {
      await apiClient.put("/settings/storage", storage);
      addToast("Storage settings saved successfully", "success");
    } catch {
      addToast("Settings API not available", "default");
    } finally {
      setStorageSaving(false);
    }
  };

  // ---------- Maintenance ----------

  const runOrphanCleanup = async () => {
    setCleanupRunning(true);
    setCleanupResult(null);
    try {
      const result = await apiClient.post<CleanupResult>("/maintenance/cleanup-orphaned-vectors");
      setCleanupResult(result);
      if (result.orphaned_documents_cleaned > 0) {
        addToast(`${result.orphaned_documents_cleaned}건의 고아 벡터를 정리했습니다.`, "success");
      } else {
        addToast("정리할 고아 벡터가 없습니다.", "default");
      }
    } catch {
      addToast("고아 벡터 정리에 실패했습니다.", "error");
    } finally {
      setCleanupRunning(false);
    }
  };

  // ---------- Derived ----------

  const storageUsagePercent =
    storage.total_storage_bytes > 0
      ? Math.round((storage.used_storage_bytes / storage.total_storage_bytes) * 100)
      : 0;

  // ---------- Render ----------

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-3xl font-bold">System Settings</h1>

      <Tabs defaultValue="general" className="w-full">
        <TabsList>
          <TabsTrigger value="general" className="gap-2">
            <Settings className="h-4 w-4" />
            General
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-2">
            <Shield className="h-4 w-4" />
            Security
          </TabsTrigger>
          <TabsTrigger value="storage" className="gap-2">
            <Database className="h-4 w-4" />
            Storage
          </TabsTrigger>
          {user?.role === "super_admin" && (
            <TabsTrigger value="maintenance" className="gap-2">
              <Wrench className="h-4 w-4" />
              Maintenance
            </TabsTrigger>
          )}
        </TabsList>

        {/* ---- General Tab ---- */}
        <TabsContent value="general">
          <Card>
            <CardHeader>
              <CardTitle>General Settings</CardTitle>
              <CardDescription>Configure general system preferences.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>Default Language</Label>
                <Select
                  value={general.default_language}
                  onValueChange={(val) =>
                    setGeneral((prev) => ({ ...prev, default_language: val }))
                  }
                >
                  <SelectTrigger className="max-w-xs">
                    <SelectValue placeholder="Select language" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="ko">Korean</SelectItem>
                    <SelectItem value="ja">Japanese</SelectItem>
                    <SelectItem value="zh">Chinese</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Maintenance Mode</p>
                  <p className="text-muted-foreground text-sm">
                    When enabled, the system will show a maintenance page to users.
                  </p>
                </div>
                <Switch
                  checked={general.maintenance_mode}
                  onCheckedChange={(checked) =>
                    setGeneral((prev) => ({ ...prev, maintenance_mode: checked }))
                  }
                />
              </div>

              <div className="flex justify-end">
                <Button onClick={saveGeneral} disabled={generalSaving}>
                  {generalSaving ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  Save General Settings
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ---- Security Tab ---- */}
        <TabsContent value="security">
          <Card>
            <CardHeader>
              <CardTitle>Security Settings</CardTitle>
              <CardDescription>Configure password policies and session management.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Password Policy Display */}
              <div>
                <h3 className="mb-3 font-medium">Password Policy</h3>
                <div className="space-y-3 rounded-lg border p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Minimum length</span>
                    <Input
                      type="number"
                      value={security.password_min_length}
                      onChange={(e) =>
                        setSecurity((prev) => ({
                          ...prev,
                          password_min_length: Number(e.target.value),
                        }))
                      }
                      className="w-20 text-center"
                      min={6}
                      max={32}
                    />
                  </div>

                  <Separator />

                  <div className="flex items-center justify-between">
                    <span className="text-sm">Require uppercase letter</span>
                    <Badge variant={security.password_require_uppercase ? "success" : "secondary"}>
                      {security.password_require_uppercase ? "Required" : "Optional"}
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm">Require number</span>
                    <Badge variant={security.password_require_number ? "success" : "secondary"}>
                      {security.password_require_number ? "Required" : "Optional"}
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm">Require special character</span>
                    <Badge variant={security.password_require_special ? "success" : "secondary"}>
                      {security.password_require_special ? "Required" : "Optional"}
                    </Badge>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Session timeout */}
              <div className="space-y-2">
                <Label htmlFor="session-timeout">Session Timeout (minutes)</Label>
                <Input
                  id="session-timeout"
                  type="number"
                  value={security.session_timeout_minutes}
                  onChange={(e) =>
                    setSecurity((prev) => ({
                      ...prev,
                      session_timeout_minutes: Number(e.target.value),
                    }))
                  }
                  className="max-w-xs"
                  min={5}
                  max={480}
                />
                <p className="text-muted-foreground text-xs">
                  Users will be automatically logged out after this period of inactivity.
                </p>
              </div>

              <div className="flex justify-end">
                <Button onClick={saveSecurity} disabled={securitySaving}>
                  {securitySaving ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  Save Security Settings
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ---- Storage Tab ---- */}
        <TabsContent value="storage">
          <Card>
            <CardHeader>
              <CardTitle>Storage Settings</CardTitle>
              <CardDescription>View MinIO connection status and storage usage.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* MinIO connection status */}
              <div className="rounded-lg border p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">MinIO Connection</h3>
                    <p className="text-muted-foreground mt-1 text-sm">
                      {storage.minio_endpoint || "Not configured"}
                    </p>
                  </div>
                  {storage.minio_connected ? (
                    <Badge variant="success" className="gap-1">
                      <CheckCircle2 className="h-3 w-3" />
                      Connected
                    </Badge>
                  ) : (
                    <Badge variant="destructive" className="gap-1">
                      <XCircle className="h-3 w-3" />
                      Disconnected
                    </Badge>
                  )}
                </div>
              </div>

              <Separator />

              {/* Storage usage */}
              <div>
                <h3 className="mb-3 font-medium">Storage Usage</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Used</span>
                    <span className="font-medium">
                      {formatBytes(storage.used_storage_bytes)} /{" "}
                      {formatBytes(storage.total_storage_bytes)}
                    </span>
                  </div>
                  <Progress value={storageUsagePercent} className="h-3" />
                  <p className="text-muted-foreground text-xs">
                    {storageUsagePercent}% of total storage used
                  </p>
                </div>
              </div>

              <Separator />

              {/* Storage breakdown */}
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <p className="text-muted-foreground text-sm">Total Capacity</p>
                    <p className="text-2xl font-bold">{formatBytes(storage.total_storage_bytes)}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <p className="text-muted-foreground text-sm">Available</p>
                    <p className="text-2xl font-bold">
                      {formatBytes(storage.total_storage_bytes - storage.used_storage_bytes)}
                    </p>
                  </CardContent>
                </Card>
              </div>

              <div className="flex justify-end">
                <Button onClick={saveStorage} disabled={storageSaving}>
                  {storageSaving ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  Save Storage Settings
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        {/* ---- Maintenance Tab (super_admin only) ---- */}
        {user?.role === "super_admin" && (
          <TabsContent value="maintenance">
            <Card>
              <CardHeader>
                <CardTitle>Maintenance</CardTitle>
                <CardDescription>
                  시스템 유지보수 작업을 실행합니다. 주의하여 사용하세요.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Orphan Vector Cleanup */}
                <div className="space-y-3 rounded-lg border p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="flex items-center gap-2 font-medium">
                        <Trash2 className="h-4 w-4" />
                        고아 벡터 정리
                      </h3>
                      <p className="text-muted-foreground mt-1 text-sm">
                        DB에서 삭제되었지만 Qdrant에 남아 있는 벡터 데이터를 정리합니다.
                      </p>
                    </div>
                    <Button
                      variant="destructive"
                      onClick={runOrphanCleanup}
                      disabled={cleanupRunning}
                    >
                      {cleanupRunning ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="mr-2 h-4 w-4" />
                      )}
                      {cleanupRunning ? "정리 중..." : "정리 실행"}
                    </Button>
                  </div>

                  {cleanupResult && (
                    <div className="bg-muted mt-3 space-y-1 rounded-md p-3 text-sm">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={cleanupResult.status === "success" ? "success" : "destructive"}
                        >
                          {cleanupResult.status}
                        </Badge>
                        {cleanupResult.status === "error" && cleanupResult.message && (
                          <span className="text-destructive">{cleanupResult.message}</span>
                        )}
                      </div>
                      <div className="grid grid-cols-3 gap-4 pt-2">
                        <div>
                          <p className="text-muted-foreground">Qdrant 문서 수</p>
                          <p className="text-lg font-semibold">
                            {cleanupResult.qdrant_document_ids_total ?? "-"}
                          </p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">DB 문서 수</p>
                          <p className="text-lg font-semibold">
                            {cleanupResult.db_document_ids_total ?? "-"}
                          </p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">정리된 고아 문서</p>
                          <p className="text-destructive text-lg font-semibold">
                            {cleanupResult.orphaned_documents_cleaned}
                          </p>
                        </div>
                      </div>
                      {cleanupResult.orphaned_document_ids &&
                        cleanupResult.orphaned_document_ids.length > 0 && (
                          <div className="pt-2">
                            <p className="text-muted-foreground mb-1">삭제된 Document IDs:</p>
                            <pre className="bg-background max-h-32 overflow-auto rounded p-2 text-xs">
                              {cleanupResult.orphaned_document_ids.join("\n")}
                            </pre>
                          </div>
                        )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}
