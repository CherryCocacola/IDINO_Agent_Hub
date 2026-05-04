import type { Metadata } from 'next';
import './globals.css';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'AI 핵심역량 스튜디오 - CAREER V5',
  description: '대학생 AI 기반 역량 주도형 커리어 로드맵 시스템',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="bg-bg min-h-screen">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
