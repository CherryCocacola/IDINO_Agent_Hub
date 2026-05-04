'use client';

import { useAuth } from '@/lib/auth/authContext';
import PassportSection from '@/components/sections/PassportSection';

export default function PassportPage() {
  const { user } = useAuth();
  const studentId = user?.studentId || null;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900">스킬 패스포트</h1>
        <p className="mt-2 text-gray-600">
          획득한 역량과 자격증, 배지를 한눈에 확인하세요.
          검증된 스킬 포트폴리오로 취업 경쟁력을 높일 수 있습니다.
        </p>
      </div>

      {/* Main Content */}
      {studentId ? (
        <PassportSection studentId={studentId} />
      ) : (
        <div className="bg-white rounded-lg shadow-sm p-8 text-center">
          <p className="text-gray-500">로그인이 필요합니다.</p>
        </div>
      )}
    </div>
  );
}
