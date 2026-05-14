'use client';

// 트랙 #97-pre2 (2026-05-14) — (dashboard) 라우트 4개 신설 중 roadmap.
// 학생의 학년별 단계적 진로/학업 로드맵을 시각화하는 화면.
// RoadmapSection 컴포넌트가 데이터 표시를 담당하며, 본 페이지는 인증 가드와 헤더만 제공.
// 학생 상세 객체가 전달되면 Section 내부에서 roadmap-service 를 직접 fetch.

import { useAuth } from '@/hooks/useAuth';
import RoadmapSection from '@/components/sections/RoadmapSection';

export default function RoadmapPage() {
  // 사용자 인증 상태 확인 — 로그인 사용자에게만 로드맵 데이터 노출.
  const { user } = useAuth();

  // RoadmapSection 은 Student 타입 객체를 받아 내부에서 fetch.
  // useAuth.user 의 형태가 Student 와 정확히 일치하지 않을 수 있어 null 전달 → Section 의 fallback 활용.
  // 정식 student fetch(student-service /api/v1/students/{studentId})는 후속 트랙에서 적용.
  const student = null;

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 — 진로 로드맵의 목적 안내 */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900">진로 로드맵</h1>
        <p className="mt-2 text-gray-600">
          학년별 단계적 학습·진로 로드맵을 확인하고 지금 해야 할 다음 행동을 계획합니다.
        </p>
      </div>

      {/* 메인 콘텐츠 — 로그인 사용자에게만 RoadmapSection 노출 */}
      {user ? (
        <RoadmapSection student={student} />
      ) : (
        <div className="bg-white rounded-lg shadow-sm p-8 text-center">
          <p className="text-gray-500">로그인이 필요합니다.</p>
        </div>
      )}
    </div>
  );
}
