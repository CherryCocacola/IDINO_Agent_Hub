'use client';

import { useAuth } from '@/hooks/useAuth';
import PortfolioBuilderSection from '@/components/sections/PortfolioBuilderSection';

export default function PortfolioPage() {
  const { user } = useAuth();
  const studentId = user?.studentId || null;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900">포트폴리오 관리</h1>
        <p className="mt-2 text-gray-600">
          나만의 포트폴리오를 구성하고 다양한 형식으로 내보내세요.
          프로젝트, 수상 경력, 활동 기록을 체계적으로 관리할 수 있습니다.
        </p>
      </div>

      {/* Main Content */}
      {studentId ? (
        <PortfolioBuilderSection studentId={studentId} />
      ) : (
        <div className="bg-white rounded-lg shadow-sm p-8 text-center">
          <p className="text-gray-500">로그인이 필요합니다.</p>
        </div>
      )}
    </div>
  );
}
