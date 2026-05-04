import { authApi } from './client';

// Auth API Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface UserInfo {
  user_id: string;
  username: string;
  email: string;
  role_level: number;
  department_id?: string;
  name?: string;
  student_id?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  mfa_required: boolean;
  user: UserInfo;
}

export interface MfaVerifyRequest {
  user_id: string;
  code: string;
  method: 'totp' | 'email';
}

export interface MfaVerifyResponse {
  success: boolean;
  access_token?: string;
  refresh_token?: string;
  expires_in?: number;
}

export interface TokenRefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export const authService = {
  // Login with username and password
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const response = await authApi.post<LoginResponse>('/auth/login', {
      username,
      password,
    });
    return response.data;
  },

  // Verify MFA code (TOTP or Email OTP)
  verifyMfa: async (userId: string, code: string, method: 'totp' | 'email' = 'totp'): Promise<MfaVerifyResponse> => {
    const response = await authApi.post<MfaVerifyResponse>('/auth/mfa/verify', {
      user_id: userId,
      code,
      method,
    });
    return response.data;
  },

  // Request email OTP
  requestEmailOtp: async (userId: string): Promise<{ success: boolean }> => {
    const response = await authApi.post<{ success: boolean }>('/auth/mfa/send-email', {
      user_id: userId,
    });
    return response.data;
  },

  // Refresh access token
  refreshToken: async (refreshToken: string): Promise<TokenRefreshResponse> => {
    const response = await authApi.post<TokenRefreshResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  // Logout
  logout: async (accessToken: string): Promise<void> => {
    await authApi.post('/auth/logout', null, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
  },

  // Verify token validity
  // Returns: true if valid, false if invalid, null if network error
  verifyToken: async (accessToken: string): Promise<boolean | null> => {
    try {
      await authApi.get('/auth/verify', {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
      return true;
    } catch (error: unknown) {
      // Check if it's an axios error with response (server responded with error)
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number } };
        if (axiosError.response?.status === 401 || axiosError.response?.status === 403) {
          // Token is definitely invalid
          return false;
        }
      }
      // Network error or server unavailable - return null to indicate uncertainty
      return null;
    }
  },
};
