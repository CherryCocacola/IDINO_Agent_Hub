'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { RefreshCw, AlertTriangle } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  isChunkError: boolean;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, isChunkError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    const isChunkError =
      error.name === 'ChunkLoadError' ||
      error.message.includes('Loading chunk') ||
      error.message.includes('Failed to fetch dynamically imported module');

    return { hasError: true, error, isChunkError };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // ChunkLoadError인 경우 자동 새로고침 시도
    if (this.state.isChunkError) {
      // 무한 새로고침 방지를 위한 체크
      const lastRefresh = sessionStorage.getItem('lastChunkErrorRefresh');
      const now = Date.now();

      if (!lastRefresh || now - parseInt(lastRefresh) > 10000) {
        sessionStorage.setItem('lastChunkErrorRefresh', now.toString());
        window.location.reload();
      }
    }
  }

  handleRefresh = () => {
    sessionStorage.removeItem('lastChunkErrorRefresh');
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/90 via-primary to-primary-dark px-4">
          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-yellow-100 rounded-full mb-4">
              <AlertTriangle className="w-8 h-8 text-yellow-600" />
            </div>

            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              {this.state.isChunkError ? '페이지 로딩 오류' : '오류가 발생했습니다'}
            </h2>

            <p className="text-gray-600 mb-6">
              {this.state.isChunkError
                ? '페이지 리소스를 불러오는 중 문제가 발생했습니다. 새로고침을 시도해주세요.'
                : '예상치 못한 오류가 발생했습니다. 새로고침을 시도해주세요.'}
            </p>

            <button
              onClick={this.handleRefresh}
              className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-dark transition-colors"
            >
              <RefreshCw className="w-5 h-5" />
              새로고침
            </button>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-6 text-left">
                <summary className="text-sm text-gray-500 cursor-pointer">오류 상세</summary>
                <pre className="mt-2 p-3 bg-gray-100 rounded-lg text-xs text-gray-700 overflow-auto">
                  {this.state.error.toString()}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
