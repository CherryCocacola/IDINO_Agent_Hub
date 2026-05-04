'use client';

import { ReactNode } from 'react';
import { AuthProvider } from '@/lib/auth/authContext';
import ErrorBoundary from '@/components/ErrorBoundary';

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ErrorBoundary>
      <AuthProvider>
        {children}
      </AuthProvider>
    </ErrorBoundary>
  );
}
