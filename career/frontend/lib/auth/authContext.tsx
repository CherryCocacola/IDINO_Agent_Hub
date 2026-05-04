'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService, LoginResponse, UserInfo } from '@/lib/api/auth';

// Auth user interface for frontend use
interface AuthUser {
  userId: string;
  studentId: string;
  name: string;
  departmentId: string;
  departmentName: string;
  grade: number;
  email: string;
  isAuthenticated: boolean;
  advisorId?: string;  // For advisor/professor users
}

// MFA state interface
interface MfaState {
  required: boolean;
  userId: string;
  method: 'totp' | 'email';
}

interface AuthContextType {
  user: AuthUser | null;
  isLoading: boolean;
  mfaState: MfaState | null;
  accessToken: string | null;
  login: (studentId: string, password: string) => Promise<{ success: boolean; mfaRequired?: boolean }>;
  verifyMfa: (code: string) => Promise<boolean>;
  requestEmailOtp: () => Promise<boolean>;
  logout: () => void;
  clearMfaState: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = 'idino_auth_user';
const TOKEN_KEY = 'idino_auth_token';
const REFRESH_TOKEN_KEY = 'idino_refresh_token';


// Convert API user info to frontend AuthUser
function toAuthUser(userInfo: UserInfo): AuthUser {
  return {
    userId: userInfo.user_id,
    studentId: userInfo.student_id || userInfo.username,
    name: userInfo.name || userInfo.username,
    departmentId: userInfo.department_id || '',
    departmentName: '', // Will be fetched from student service
    grade: 0, // Will be fetched from student service
    email: userInfo.email,
    isAuthenticated: true,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [mfaState, setMfaState] = useState<MfaState | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [pendingLoginResponse, setPendingLoginResponse] = useState<LoginResponse | null>(null);

  // Load saved auth state on mount with token validation
  useEffect(() => {
    const restoreSession = async () => {
      try {
        const savedUser = localStorage.getItem(STORAGE_KEY);
        const savedToken = localStorage.getItem(TOKEN_KEY);

        if (savedUser && savedToken) {
          // Verify token with server before restoring session
          const isValid = await authService.verifyToken(savedToken);

          if (isValid === true) {
            // Token is valid
            const parsed = JSON.parse(savedUser);
            setUser(parsed);
            setAccessToken(savedToken);
          } else if (isValid === false) {
            // Token is definitely invalid - clear localStorage
            console.warn('Saved token is invalid, clearing session');
            localStorage.removeItem(STORAGE_KEY);
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(REFRESH_TOKEN_KEY);
          } else {
            // isValid === null means network error
            // Keep the session but don't validate - user can still use the app
            // API calls will fail with 401 if token is actually invalid
            console.warn('Could not verify token (network error), keeping session');
            const parsed = JSON.parse(savedUser);
            setUser(parsed);
            setAccessToken(savedToken);
          }
        }
      } catch (e) {
        console.error('Failed to restore auth state:', e);
        // On parse error, clear potentially corrupted session data
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = async (studentId: string, password: string): Promise<{ success: boolean; mfaRequired?: boolean }> => {
    setIsLoading(true);
    setMfaState(null);

    try {
      // Try API authentication first
      try {
        const response = await authService.login(studentId, password);

        // Check if MFA is required
        if (response.mfa_required) {
          // Store pending login response for MFA verification
          setPendingLoginResponse(response);
          setMfaState({
            required: true,
            userId: response.user.user_id,
            method: 'totp', // Default to TOTP
          });
          return { success: true, mfaRequired: true };
        }

        // No MFA required - complete login
        const authUser = toAuthUser(response.user);
        setUser(authUser);
        setAccessToken(response.access_token);

        // Save to localStorage
        localStorage.setItem(STORAGE_KEY, JSON.stringify(authUser));
        localStorage.setItem(TOKEN_KEY, response.access_token);
        localStorage.setItem(REFRESH_TOKEN_KEY, response.refresh_token);

        return { success: true };
      } catch (apiError) {
        console.error('API login failed:', apiError);
        return { success: false };
      }
    } finally {
      setIsLoading(false);
    }
  };

  const verifyMfa = async (code: string): Promise<boolean> => {
    if (!mfaState || !pendingLoginResponse) {
      console.error('No pending MFA verification');
      return false;
    }

    setIsLoading(true);

    try {
      const response = await authService.verifyMfa(
        mfaState.userId,
        code,
        mfaState.method
      );

      if (response.success && response.access_token) {
        // MFA verification successful
        const authUser = toAuthUser(pendingLoginResponse.user);
        setUser(authUser);
        setAccessToken(response.access_token);
        setMfaState(null);
        setPendingLoginResponse(null);

        // Save to localStorage
        localStorage.setItem(STORAGE_KEY, JSON.stringify(authUser));
        localStorage.setItem(TOKEN_KEY, response.access_token);
        if (response.refresh_token) {
          localStorage.setItem(REFRESH_TOKEN_KEY, response.refresh_token);
        }

        return true;
      }

      return false;
    } catch (error) {
      console.error('MFA verification failed:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const requestEmailOtp = async (): Promise<boolean> => {
    if (!mfaState) {
      console.error('No pending MFA state');
      return false;
    }

    try {
      const response = await authService.requestEmailOtp(mfaState.userId);
      if (response.success) {
        // Switch MFA method to email
        setMfaState(prev => prev ? { ...prev, method: 'email' } : null);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to request email OTP:', error);
      return false;
    }
  };

  const clearMfaState = () => {
    setMfaState(null);
    setPendingLoginResponse(null);
  };

  const logout = async () => {
    try {
      // Try to logout from server if we have a token
      if (accessToken) {
        await authService.logout(accessToken);
      }
    } catch (error) {
      console.warn('Server logout failed:', error);
    } finally {
      // Clear local state regardless of server response
      setUser(null);
      setAccessToken(null);
      setMfaState(null);
      setPendingLoginResponse(null);

      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      isLoading,
      mfaState,
      accessToken,
      login,
      verifyMfa,
      requestEmailOtp,
      logout,
      clearMfaState,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
