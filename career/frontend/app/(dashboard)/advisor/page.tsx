'use client';

import { useAuth } from '@/hooks/useAuth';
import AdvisorDashboardSection from '@/components/sections/AdvisorDashboardSection';

export default function AdvisorPage() {
  const { user } = useAuth();
  // For advisor workspace, we use the advisorId (professor/staff)
  const advisorId = user?.advisorId || user?.studentId || null;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900">지도교수 워크스페이스</h1>
        <p className="mt-2 text-gray-600">
          담당 학생들의 진로 현황을 모니터링하고 효과적인 상담을 진행하세요.
          학생별 위험 알림과 진도 현황을 확인할 수 있습니다.
        </p>
      </div>

      {/* Main Content */}
      {advisorId ? (
        <AdvisorDashboardSection advisorId={advisorId} />
      ) : (
        <div className="bg-white rounded-lg shadow-sm p-8 text-center">
          <p className="text-gray-500">로그인이 필요합니다.</p>
        </div>
      )}
    </div>
  );
}
