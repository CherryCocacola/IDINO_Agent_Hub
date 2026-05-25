"use client";

import { User, Lock, Eye, EyeOff, Loader2, Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, FormEvent } from "react";

import { useAuth } from "@/lib/hooks/use-auth";
import { useToast } from "@/lib/hooks/use-toast";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const { addToast } = useToast();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!username.trim() || !password.trim()) {
      setError("아이디와 비밀번호를 입력해주세요.");
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username.trim(),
          password,
          remember_me: rememberMe,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          setError(data.message || "아이디 또는 비밀번호가 올바르지 않습니다.");
        } else if (response.status === 423) {
          const remainingMinutes = data.remaining_minutes
            ? Math.ceil(data.remaining_minutes)
            : null;
          if (remainingMinutes) {
            setError(`계정이 잠겼습니다. ${remainingMinutes}분 후에 다시 시도해주세요.`);
          } else {
            setError(data.message || "계정이 잠겼습니다. 관리자에게 문의해주세요.");
          }
        } else {
          setError(data.message || "오류가 발생했습니다. 다시 시도해주세요.");
        }
        return;
      }

      const { user, access_token, refresh_token } = data;

      login(user, access_token, refresh_token);
      addToast("로그인되었습니다.", "success");

      // Admin roles go to dashboard, others go to search
      const adminRoles = ["super_admin", "admin", "org_admin"];
      if (adminRoles.includes(user.role)) {
        router.push("/dashboard");
      } else {
        router.push("/search");
      }
    } catch (_err) {
      setError("서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-background flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="border-border rounded-2xl border bg-white px-8 py-10 shadow-lg">
          {/* Logo */}
          <div className="mb-8 flex flex-col items-center">
            <img src="/idino-logo.png" alt="IDINO" className="mb-3 h-16 w-16 rounded-xl object-contain" />
            <h1 className="text-foreground text-2xl font-bold">DocUtil</h1>
            <p className="text-muted-foreground mt-2 text-sm">관리자 로그인</p>
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username */}
            <div>
              <label
                htmlFor="username"
                className="text-foreground mb-1.5 block text-sm font-medium"
              >
                아이디
              </label>
              <div className="relative">
                <User className="text-muted-foreground absolute top-1/2 left-3.5 h-5 w-5 -translate-y-1/2" />
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="아이디를 입력하세요"
                  autoComplete="username"
                  autoFocus
                  disabled={isLoading}
                  className="border-border text-foreground placeholder-muted-foreground focus:border-primary focus:ring-primary/20 disabled:bg-muted disabled:text-muted-foreground block w-full rounded-lg border bg-white py-3 pr-4 pl-11 text-sm focus:ring-2 focus:outline-none disabled:cursor-not-allowed"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="text-foreground mb-1.5 block text-sm font-medium"
              >
                비밀번호
              </label>
              <div className="relative">
                <Lock className="text-muted-foreground absolute top-1/2 left-3.5 h-5 w-5 -translate-y-1/2" />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="비밀번호를 입력하세요"
                  autoComplete="current-password"
                  disabled={isLoading}
                  className="border-border text-foreground placeholder-muted-foreground focus:border-primary focus:ring-primary/20 disabled:bg-muted disabled:text-muted-foreground block w-full rounded-lg border bg-white py-3 pr-11 pl-11 text-sm focus:ring-2 focus:outline-none disabled:cursor-not-allowed"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-muted-foreground hover:text-foreground absolute top-1/2 right-3.5 -translate-y-1/2"
                  tabIndex={-1}
                  aria-label={showPassword ? "비밀번호 숨기기" : "비밀번호 보기"}
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            {/* Remember me */}
            <div className="flex items-center">
              <input
                id="remember-me"
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                disabled={isLoading}
                className="border-border text-primary focus:ring-primary h-4 w-4 rounded"
              />
              <label htmlFor="remember-me" className="text-muted-foreground ml-2 text-sm">
                아이디 저장
              </label>
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={isLoading}
              className="bg-primary text-primary-foreground hover:bg-primary/90 focus:ring-primary flex w-full items-center justify-center rounded-lg px-4 py-3 text-sm font-medium transition-colors focus:ring-2 focus:ring-offset-2 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  로그인 중...
                </>
              ) : (
                "로그인"
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-muted-foreground mt-8 text-center text-xs">
          Copyright 2026. G2 SOFT. All rights reserved.
        </p>
      </div>
    </div>
  );
}
