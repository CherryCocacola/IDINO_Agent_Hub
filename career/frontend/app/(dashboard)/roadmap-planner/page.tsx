'use client';

import { useAuth } from '@/hooks/useAuth';
import RoadmapPlannerSection from '@/components/sections/RoadmapPlannerSection';

export default function RoadmapPlannerPage() {
  const { user } = useAuth();
  const studentId = user?.studentId || null;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900">로드맵 플래너</h1>
        <p className="mt-2 text-gray-600">
          학기별 계획을 세우고 장기적인 진로 로드맵을 설계하세요.
          목표 달성을 위한 단계별 마일스톤을 관리할 수 있습니다.
        </p>
      </div>

      {/* Main Content */}
      {studentId ? (
        <RoadmapPlannerSection studentId={studentId} />
      ) : (
        <div className="bg-white rounded-lg shadow-sm p-8 text-center">
          <p className="text-gray-500">로그인이 필요합니다.</p>
        </div>
      )}
    </div>
  );
}
