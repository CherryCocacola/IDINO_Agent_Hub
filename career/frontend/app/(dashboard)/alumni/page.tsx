'use client';

// 트랙 #97-pre2 (2026-05-14) — (dashboard) 라우트 4개 신설 중 alumni.
// 학생이 같은 학과/진로의 졸업 동문 코호트와 본인 위치를 비교 분석하는 화면.
// AlumniSection 컴포넌트가 데이터 표시를 담당하며, 본 페이지는 인증 가드와 헤더만 제공.

import { useAuth } from '@/hooks/useAuth';
import AlumniSection from '@/components/sections/AlumniSection';

export default function AlumniPage() {
  // 현재 로그인 사용자의 학번을 확보 — 인증되지 않은 사용자는 안내 화면으로 폴백.
  const { user } = useAuth();
  const studentId = user?.studentId || null;

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 — 화면 목적과 사용법을 한국어로 안내 */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900">동문 코호트 분석</h1>
        <p className="mt-2 text-gray-600">
          같은 학과·진로의 졸업 동문들의 성공 패턴과 본인 위치를 비교 분석합니다.
        </p>
      </div>

      {/* 메인 콘텐츠 — 인증 사용자에게만 분석 데이터 표시 */}
      {studentId ? (
        // 초기 진입 시 빈 데이터로 호출 — AlumniSection 내부의 defaultPatterns fallback 활용.
        // 정식 fetch 로직(alumni-service /api/v1/alumni/{studentId}/comparison)은 후속 트랙에서 적용.
        <AlumniSection comparison={null} patterns={[]} loading={false} />
      ) : (
        <div className="bg-white rounded-lg shadow-sm p-8 text-center">
          <p className="text-gray-500">로그인이 필요합니다.</p>
        </div>
      )}
    </div>
  );
}
