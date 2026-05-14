'use client';

// 트랙 #97-pre2 (2026-05-14) — (dashboard) 라우트 4개 신설 중 competency.
// 학생의 8대 핵심역량 점수와 분포를 시각화하는 화면.
// CompetencySection 컴포넌트가 데이터 표시를 담당하며, 본 페이지는 인증 가드와 헤더만 제공.

import { useAuth } from '@/hooks/useAuth';
import CompetencySection from '@/components/sections/CompetencySection';

export default function CompetencyPage() {
  // 인증된 학생만 분석 결과를 조회할 수 있도록 학번 확보.
  const { user } = useAuth();
  const studentId = user?.studentId || null;

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 — 8대 핵심역량 안내 */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900">역량 분석</h1>
        <p className="mt-2 text-gray-600">
          8대 핵심역량(전문지식·문제해결·소통협업·직업윤리 등) 점수를 확인하고 성장 우선순위를 파악합니다.
        </p>
      </div>

      {/* 메인 콘텐츠 — 인증 사용자에게만 표시 */}
      {studentId ? (
        // 초기 진입 시 빈 report 로 호출 — CompetencySection 내부에서 데이터 미존재 시 자동 숨김 또는 fallback.
        // 정식 fetch(competency-service /api/v1/competencies/students/{studentId}/report)는 후속 트랙에서 적용.
        <CompetencySection report={null} loading={false} />
      ) : (
        <div className="bg-white rounded-lg shadow-sm p-8 text-center">
          <p className="text-gray-500">로그인이 필요합니다.</p>
        </div>
      )}
    </div>
  );
}
