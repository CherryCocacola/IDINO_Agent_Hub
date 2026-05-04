'use client';

import { useState, useEffect } from 'react';
import { Map, AlertTriangle } from 'lucide-react';
import { RoadmapCard } from '@/components/ui/Card';
import { roadmapService } from '@/lib/api/roadmap';
import type { Student, FullRoadmapResponse, GradeRoadmapResponse } from '@/types';

interface RoadmapSectionProps {
  student: Student | null;
}

// Transformed roadmap format for display
interface DisplayRoadmap {
  grade: number;
  title: string;
  courses: string[];
  activities: string[];
  goals: string[];
}

// Default fallback data (same as before)
const defaultGradeRoadmaps: DisplayRoadmap[] = [
  {
    grade: 1,
    title: '기초 역량 확립',
    courses: ['프로그래밍 기초', '컴퓨터 개론', '수학적 기초'],
    activities: ['프로그래밍 동아리 가입', '멘토링 참여'],
    goals: ['프로그래밍 언어 1개 마스터', '학점 3.5 이상'],
  },
  {
    grade: 2,
    title: '전문성 심화',
    courses: ['자료구조', '알고리즘', '데이터베이스'],
    activities: ['교내 해커톤 참가', '스터디 그룹 리딩'],
    goals: ['프로젝트 1회 이상 참여', '자격증 1개 취득'],
  },
  {
    grade: 3,
    title: '실무 경험 축적',
    courses: ['소프트웨어 공학', '캡스톤 프로젝트'],
    activities: ['인턴십 지원', '공모전 참가'],
    goals: ['인턴십 경험', '포트폴리오 완성'],
  },
  {
    grade: 4,
    title: '취업 준비',
    courses: ['졸업 프로젝트', '산학협력 과목'],
    activities: ['취업 설명회 참석', '모의 면접'],
    goals: ['취업 확정', '졸업 요건 충족'],
  },
];

// Grade title mapping
const GRADE_TITLES: Record<number, string> = {
  1: '기초 역량 확립',
  2: '전문성 심화',
  3: '실무 경험 축적',
  4: '취업 준비',
};

// Transform API response to display format
function transformRoadmapResponse(response: FullRoadmapResponse): DisplayRoadmap[] {
  return response.roadmaps.map((gradeRoadmap: GradeRoadmapResponse) => {
    // Collect all items from all semesters, deduplicate by title
    const allItems = gradeRoadmap.semesters.flatMap(sem => sem.items);

    // Extract unique courses (item_type === 'course')
    const courses = [...new Set(
      allItems
        .filter(item => item.item_type === 'course')
        .map(item => item.title)
    )];

    // Extract unique activities (item_type === 'activity', 'internship', 'project')
    const activities = [...new Set(
      allItems
        .filter(item => ['activity', 'internship', 'project'].includes(item.item_type))
        .map(item => item.title)
    )];

    // Extract unique goals from key_milestones
    const goals = [...new Set(
      gradeRoadmap.semesters.flatMap(sem => sem.key_milestones || [])
    )];

    // Use career_path or grade_name for title, fallback to default
    const title = gradeRoadmap.career_path ||
                  GRADE_TITLES[gradeRoadmap.grade_level] ||
                  gradeRoadmap.grade_name;

    return {
      grade: gradeRoadmap.grade_level,
      title,
      courses,
      activities: activities.length > 0 ? activities : defaultGradeRoadmaps[gradeRoadmap.grade_level - 1]?.activities || [],
      goals,
    };
  });
}

export default function RoadmapSection({ student }: RoadmapSectionProps) {
  // State for API data
  const [gradeRoadmaps, setGradeRoadmaps] = useState<DisplayRoadmap[]>(defaultGradeRoadmaps);
  const [loading, setLoading] = useState(false);
  const [isUsingRealData, setIsUsingRealData] = useState(false);
  const [overallCompletion, setOverallCompletion] = useState<number | null>(null);

  // Use current_grade from API (preferred) or grade alias
  const currentGrade = student?.current_grade || student?.grade || 3;

  // Fetch roadmap data from API
  useEffect(() => {
    const fetchRoadmap = async () => {
      if (!student?.student_id) return;

      setLoading(true);
      try {
        const response = await roadmapService.getFullRoadmap(student.student_id);

        // Handle both formats: { roadmaps: [...] } OR direct array [...]
        const roadmapsArray = Array.isArray(response) ? response : response?.roadmaps;
        const completion = Array.isArray(response) ? null : response?.overall_completion;

        if (roadmapsArray && roadmapsArray.length > 0) {
          // If we got a direct array, wrap it for the transform function
          const fullResponse: FullRoadmapResponse = Array.isArray(response)
            ? { student_id: student.student_id, roadmaps: response, overall_completion: 0, current_grade: student.current_grade || 1, current_semester: student.current_semester || 1 }
            : response;

          const transformed = transformRoadmapResponse(fullResponse);
          setGradeRoadmaps(transformed);
          setOverallCompletion(completion);
          setIsUsingRealData(true);
          console.log('✅ RoadmapSection: Using real API data', {
            roadmapsCount: roadmapsArray.length,
            overallCompletion: completion
          });
        } else {
          console.warn('⚠️ RoadmapSection: Empty API response, using fallback');
          setGradeRoadmaps(defaultGradeRoadmaps);
          setIsUsingRealData(false);
        }
      } catch (error) {
        console.warn('⚠️ RoadmapSection: API error, using fallback data', error);
        setGradeRoadmaps(defaultGradeRoadmaps);
        setIsUsingRealData(false);
      } finally {
        setLoading(false);
      }
    };

    fetchRoadmap();
  }, [student?.student_id]);

  // Debug logging for grade issue
  console.log('🗺️ RoadmapSection grade debug:', {
    student_id: student?.student_id,
    current_grade: student?.current_grade,
    grade_alias: student?.grade,
    computed_grade: currentGrade,
  });

  if (loading) {
    return (
      <section id="roadmap" className="section">
        <h2 className="section-title">
          <Map className="w-5 h-5 text-primary" />
          학년 로드맵
        </h2>
        <div className="animate-pulse space-y-4">
          <div className="h-16 bg-gray-100 rounded-xl"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-48 bg-gray-100 rounded-lg"></div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section id="roadmap" className="section animate-fadeIn">
      <h2 className="section-title">
        <Map className="w-5 h-5 text-primary" />
        학년 로드맵
        {isUsingRealData && (
          <span className="ml-2 text-xs font-normal text-green-600 bg-green-50 px-2 py-1 rounded-full">
            맞춤 로드맵
          </span>
        )}
      </h2>

      {/* Warning when using fallback data */}
      {!isUsingRealData && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-2 text-sm text-yellow-700">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>로드맵 데이터를 불러올 수 없어 기본 템플릿을 표시합니다. 학과별 맞춤 로드맵은 잠시 후 다시 시도해주세요.</span>
        </div>
      )}

      <div className="mb-6 p-4 bg-gradient-to-r from-primary/5 to-secondary/5 rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted">현재 위치</p>
            <p className="font-semibold text-text">{currentGrade}학년 - {gradeRoadmaps[currentGrade - 1]?.title}</p>
          </div>
          <div className="flex items-center gap-2">
            {[1, 2, 3, 4].map((grade) => (
              <div
                key={grade}
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                  ${grade === currentGrade
                    ? 'bg-primary text-white'
                    : grade < currentGrade
                      ? 'bg-secondary text-white'
                      : 'bg-gray-200 text-gray-500'
                  }`}
              >
                {grade}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {gradeRoadmaps.map((roadmap) => (
          <RoadmapCard
            key={roadmap.grade}
            grade={roadmap.grade}
            title={roadmap.title}
            courses={roadmap.courses}
            activities={roadmap.activities}
            goals={roadmap.goals}
            isCurrentGrade={roadmap.grade === currentGrade}
          />
        ))}
      </div>

      {/* Progress Summary */}
      <div className="mt-6 grid grid-cols-3 gap-4 text-center">
        <div className="p-4 bg-secondary/10 rounded-xl">
          <p className="text-2xl font-bold text-secondary">
            {overallCompletion !== null
              ? Math.round(overallCompletion)
              : Math.round((currentGrade / 4) * 100)}%
          </p>
          <p className="text-sm text-muted">전체 진행률</p>
        </div>
        <div className="p-4 bg-primary/10 rounded-xl">
          <p className="text-2xl font-bold text-primary">
            {4 - currentGrade}
          </p>
          <p className="text-sm text-muted">남은 학년</p>
        </div>
        <div className="p-4 bg-accent/10 rounded-xl">
          <p className="text-2xl font-bold text-accent">
            {(4 - currentGrade) * 2}
          </p>
          <p className="text-sm text-muted">남은 학기</p>
        </div>
      </div>
    </section>
  );
}
