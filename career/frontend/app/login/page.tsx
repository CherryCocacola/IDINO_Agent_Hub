'use client';

import { useState, FormEvent, useRef, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/authContext';
import { GraduationCap, User, Lock, AlertCircle, Shield, Mail, ArrowLeft, KeyRound } from 'lucide-react';

type AuthStep = 'login' | 'mfa';

export default function LoginPage() {
  const router = useRouter();
  const { login, verifyMfa, requestEmailOtp, clearMfaState, isLoading, mfaState } = useAuth();
  const [step, setStep] = useState<AuthStep>('login');
  const [studentId, setStudentId] = useState('');
  const [password, setPassword] = useState('');
  const [mfaCode, setMfaCode] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [emailSending, setEmailSending] = useState(false);
  const mfaInputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Auto-focus first MFA input when entering MFA step
  useEffect(() => {
    if (step === 'mfa' && mfaInputRefs.current[0]) {
      mfaInputRefs.current[0]?.focus();
    }
  }, [step]);

  // Sync DOM values with React state (for Playwright/testing compatibility)
  // Using ref to avoid re-creating intervals on state changes
  const syncMfaValuesFromDom = useCallback(() => {
    const inputs = mfaInputRefs.current;
    const newCode = inputs.map((input) => input?.value || '');

    setMfaCode(prev => {
      const currentCode = prev.join('');
      const newCodeStr = newCode.join('');
      // Only update if values differ
      return currentCode !== newCodeStr ? newCode : prev;
    });
  }, []);

  // Monitor MFA inputs for programmatic changes (Playwright compatibility)
  // Simplified to avoid performance issues with multiple intervals
  useEffect(() => {
    if (step !== 'mfa') return;

    // Single interval for programmatic change detection (Playwright)
    // Reduced frequency to avoid input lag
    const intervalId = setInterval(syncMfaValuesFromDom, 500);

    return () => {
      clearInterval(intervalId);
    };
  }, [step, syncMfaValuesFromDom]);

  const handleLoginSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    if (!studentId.trim()) {
      setError('학번을 입력해주세요.');
      setIsSubmitting(false);
      return;
    }

    if (!password.trim()) {
      setError('비밀번호를 입력해주세요.');
      setIsSubmitting(false);
      return;
    }

    try {
      const result = await login(studentId.trim(), password);
      if (result.success) {
        if (result.mfaRequired) {
          // MFA required - show MFA input screen
          setStep('mfa');
          setMfaCode(['', '', '', '', '', '']);
        } else {
          // No MFA required - redirect to dashboard
          router.push('/');
        }
      } else {
        setError('학번 또는 비밀번호가 올바르지 않습니다.');
      }
    } catch (err) {
      setError('로그인 중 오류가 발생했습니다.');
      console.error('Login error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleMfaSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    
    // Sync values from DOM before submitting (Playwright compatibility)
    syncMfaValuesFromDom();
    
    // Small delay to ensure state is synced
    await new Promise(resolve => setTimeout(resolve, 50));
    
    setIsSubmitting(true);

    // Re-read from refs to get latest values
    const currentCode = mfaInputRefs.current.map(ref => ref?.value || '').join('');
    
    if (currentCode.length !== 6) {
      setError('6자리 인증 코드를 입력해주세요.');
      setIsSubmitting(false);
      return;
    }

    try {
      const success = await verifyMfa(currentCode);
      if (success) {
        router.push('/');
      } else {
        setError('인증 코드가 올바르지 않습니다. 다시 시도해주세요.');
        setMfaCode(['', '', '', '', '', '']);
        mfaInputRefs.current[0]?.focus();
      }
    } catch (err) {
      setError('인증 중 오류가 발생했습니다.');
      console.error('MFA verification error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleMfaCodeChange = (index: number, value: string) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) return;

    const newCode = [...mfaCode];
    newCode[index] = value;
    setMfaCode(newCode);

    // Auto-focus next input
    if (value && index < 5) {
      mfaInputRefs.current[index + 1]?.focus();
    }
  };

  const handleMfaKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    // Handle backspace
    if (e.key === 'Backspace' && !mfaCode[index] && index > 0) {
      mfaInputRefs.current[index - 1]?.focus();
    }
  };

  const handleMfaPaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pasteData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasteData.length > 0) {
      const newCode = [...mfaCode];
      for (let i = 0; i < pasteData.length; i++) {
        newCode[i] = pasteData[i];
      }
      setMfaCode(newCode);
      // Focus the appropriate input
      const nextEmptyIndex = pasteData.length < 6 ? pasteData.length : 5;
      mfaInputRefs.current[nextEmptyIndex]?.focus();
    }
  };

  const handleRequestEmailOtp = async () => {
    setEmailSending(true);
    setError('');
    try {
      const success = await requestEmailOtp();
      if (success) {
        setError(''); // Clear any previous errors
        // Show success message (could use a toast instead)
        alert('이메일로 인증 코드가 발송되었습니다.');
      } else {
        setError('이메일 발송에 실패했습니다. 다시 시도해주세요.');
      }
    } catch (err) {
      setError('이메일 발송 중 오류가 발생했습니다.');
      console.error('Email OTP request error:', err);
    } finally {
      setEmailSending(false);
    }
  };

  const handleBackToLogin = () => {
    setStep('login');
    setMfaCode(['', '', '', '', '', '']);
    setError('');
    clearMfaState();
  };

  // Check if MFA code is complete (either from state or DOM)
  const isMfaCodeComplete = () => {
    const stateCode = mfaCode.join('');
    if (stateCode.length === 6) return true;
    
    // Also check DOM values directly (Playwright compatibility)
    const domCode = mfaInputRefs.current.map(ref => ref?.value || '').join('');
    return domCode.length === 6;
  };

  // MFA Input Screen
  if (step === 'mfa') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/90 via-primary to-primary-dark px-4">
        <div className="w-full max-w-md">
          {/* Logo & Title */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-white/20 rounded-2xl mb-4">
              <Shield className="w-12 h-12 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">추가 인증</h1>
            <p className="text-white/80">2단계 인증 코드를 입력하세요</p>
          </div>

          {/* MFA Card */}
          <div className="bg-white rounded-2xl shadow-2xl p-8">
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-primary/10 rounded-full mb-3">
                <KeyRound className="w-6 h-6 text-primary" />
              </div>
              <h2 className="text-lg font-semibold text-gray-800">
                {mfaState?.method === 'email' ? '이메일 인증' : 'TOTP 인증'}
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                {mfaState?.method === 'email'
                  ? '이메일로 전송된 6자리 코드를 입력하세요'
                  : '인증 앱에서 생성된 6자리 코드를 입력하세요'}
              </p>
            </div>

            <form onSubmit={handleMfaSubmit} className="space-y-6">
              {/* MFA Code Input */}
              <div className="flex justify-center gap-2" onPaste={handleMfaPaste}>
                {mfaCode.map((digit, index) => (
                  <input
                    key={index}
                    ref={(el) => { mfaInputRefs.current[index] = el; }}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleMfaCodeChange(index, e.target.value)}
                    onKeyDown={(e) => handleMfaKeyDown(index, e)}
                    onBlur={syncMfaValuesFromDom}
                    data-testid={`mfa-input-${index}`}
                    className="w-12 h-14 text-center text-2xl font-bold border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary text-gray-900"
                    disabled={isSubmitting || isLoading}
                  />
                ))}
              </div>

              {/* Error Message */}
              {error && (
                <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 p-3 rounded-lg">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isSubmitting || isLoading || !isMfaCodeComplete()}
                data-testid="mfa-submit-button"
                className="w-full py-3 px-4 bg-primary text-white font-semibold rounded-xl hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? '인증 중...' : '인증하기'}
              </button>
            </form>

            {/* Alternative: Email OTP */}
            {mfaState?.method === 'totp' && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={handleRequestEmailOtp}
                  disabled={emailSending}
                  className="w-full flex items-center justify-center gap-2 py-2 px-4 text-sm text-primary hover:bg-primary/5 rounded-lg transition-colors disabled:opacity-50"
                >
                  <Mail className="w-4 h-4" />
                  {emailSending ? '발송 중...' : '이메일로 인증 코드 받기'}
                </button>
              </div>
            )}

            {/* Back to Login */}
            <div className="mt-4">
              <button
                type="button"
                onClick={handleBackToLogin}
                className="w-full flex items-center justify-center gap-2 py-2 px-4 text-sm text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                로그인으로 돌아가기
              </button>
            </div>
          </div>

          {/* Footer */}
          <p className="text-center text-white/60 text-sm mt-6">
            © 2025 AI 핵심역량 스튜디오
          </p>
        </div>
      </div>
    );
  }

  // Login Screen
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/90 via-primary to-primary-dark px-4">
      <div className="w-full max-w-md">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-white/20 rounded-2xl mb-4">
            <GraduationCap className="w-12 h-12 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">AI 핵심역량 스튜디오</h1>
          <p className="text-white/80">CAREER V5+</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-6 text-center">
            로그인
          </h2>

          <form onSubmit={handleLoginSubmit} className="space-y-5">
            {/* Student ID */}
            <div>
              <label htmlFor="studentId" className="block text-sm font-medium text-gray-700 mb-1">
                학번
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  id="studentId"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary text-gray-900 placeholder-gray-400"
                  placeholder="학번을 입력하세요"
                  autoComplete="username"
                  disabled={isSubmitting || isLoading}
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                비밀번호
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary text-gray-900 placeholder-gray-400"
                  placeholder="비밀번호를 입력하세요"
                  autoComplete="current-password"
                  disabled={isSubmitting || isLoading}
                />
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 p-3 rounded-lg">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting || isLoading}
              className="w-full py-3 px-4 bg-primary text-white font-semibold rounded-xl hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? '로그인 중...' : '로그인'}
            </button>
          </form>

        </div>

        {/* Footer */}
        <p className="text-center text-white/60 text-sm mt-6">
          © 2025 AI 핵심역량 스튜디오
        </p>
      </div>
    </div>
  );
}
