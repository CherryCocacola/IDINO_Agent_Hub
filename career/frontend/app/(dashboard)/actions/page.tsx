'use client';

// 트랙 #97-pre2 (2026-05-14) — (dashboard) 라우트 4개 신설 중 actions.
// 학생이 진로 발전을 위해 지금 시작할 수 있는 구체적 행동 추천 화면.
// coaching-service 또는 advisor-service 의 actions endpoint 와 연동 예정.
// 본 페이지는 1차 진입점 — 정식 Section 컴포넌트(ActionsSection) 는 후속 트랙에서 신설.

import { useAuth } from '@/hooks/useAuth';
import { Lightbulb } from 'lucide-react';

export default function ActionsPage() {
  // 인증된 학생만 추천 행동을 확인할 수 있도록 학번 확보.
  const { user } = useAuth();
  const studentId = user?.studentId || null;

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 — 추천 행동 화면의 목적 안내 */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900">추천 행동</h1>
        <p className="mt-2 text-gray-600">
          진로 발전을 위해 지금 시작할 수 있는 구체적인 행동을 우선순위와 함께 추천합니다.
        </p>
      </div>

      {/* 메인 콘텐츠 — 인증 사용자에게만 표시. 정식 ActionsSection 구현 전까지 안내 카드 */}
      {studentId ? (
        <div className="bg-white rounded-lg shadow-sm p-8">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-indigo-100 flex items-center justify-center">
              <Lightbulb className="w-6 h-6 text-indigo-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900">행동 추천 데이터 준비 중</h2>
              <p className="mt-2 text-gray-600">
                현재 학생 데이터를 기반으로 한 맞춤 행동 추천 화면을 준비하고 있습니다.
                정식 화면은 후속 트랙에서 coaching-service 와 advisor-service 의 데이터를 통합하여 제공됩니다.
              </p>
              <p className="mt-3 text-sm text-gray-500">
                그동안 좌측 메뉴의 &quot;진로 로드맵&quot;과 &quot;역량 분석&quot;에서 본인의 현재 위치를 확인할 수 있습니다.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm p-8 text-center">
          <p className="text-gray-500">로그인이 필요합니다.</p>
        </div>
      )}
    </div>
  );
}
