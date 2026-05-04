'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth/authContext';
import SimulationSection from '@/components/sections/SimulationSection';

export default function SimulationPage() {
  const { user } = useAuth();
  const studentId = user?.studentId || null;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900">What-if 시뮬레이션</h1>
        <p className="mt-2 text-gray-600">
          다양한 시나리오를 시뮬레이션하여 진로 결정에 도움을 받으세요.
          과목 선택, 활동 참여, 취업 준비 등의 영향을 미리 확인할 수 있습니다.
        </p>
      </div>

      {/* Main Content */}
      {studentId ? (
        <SimulationSection studentId={studentId} />
      ) : (
        <div className="bg-white rounded-lg shadow-sm p-8 text-center">
          <p className="text-gray-500">로그인이 필요합니다.</p>
        </div>
      )}
    </div>
  );
}
