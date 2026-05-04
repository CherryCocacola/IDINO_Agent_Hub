'use client';

import clsx from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export default function Card({ children, className, onClick }: CardProps) {
  return (
    <div
      className={clsx(
        'card',
        onClick && 'cursor-pointer hover:shadow-md transition-shadow',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}

export function CardHeader({ children, className, action }: CardHeaderProps) {
  return (
    <div className={clsx('card-header flex items-center justify-between', className)}>
      <div className="font-semibold text-text">{children}</div>
      {action && <div>{action}</div>}
    </div>
  );
}

interface CardBodyProps {
  children: React.ReactNode;
  className?: string;
}

export function CardBody({ children, className }: CardBodyProps) {
  return (
    <div className={clsx('card-body', className)}>
      {children}
    </div>
  );
}

// Grade Roadmap Card
interface RoadmapCardProps {
  grade: number;
  title: string;
  courses: string[];
  activities: string[];
  goals: string[];
  isCurrentGrade?: boolean;
}

export function RoadmapCard({
  grade,
  title,
  courses,
  activities,
  goals,
  isCurrentGrade,
}: RoadmapCardProps) {
  return (
    <div
      className={clsx(
        'card p-5',
        isCurrentGrade && 'ring-2 ring-primary'
      )}
    >
      <div className="flex items-center gap-2 mb-4">
        <span className="w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center font-bold text-sm">
          {grade}
        </span>
        <span className="font-semibold text-text">{title}</span>
        {isCurrentGrade && (
          <span className="badge badge-primary ml-auto">현재</span>
        )}
      </div>

      <div className="space-y-4 text-sm">
        <div>
          <p className="text-muted mb-1 font-medium">📚 교과</p>
          {courses.length > 0 ? (
            <ul className="space-y-1">
              {courses.map((course, i) => (
                <li key={i} className="text-text">• {course}</li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-gray-400">등록된 교과목이 없습니다</p>
          )}
        </div>

        <div>
          <p className="text-muted mb-1 font-medium">🎯 비교과</p>
          <ul className="space-y-1">
            {activities.map((activity, i) => (
              <li key={i} className="text-text">• {activity}</li>
            ))}
          </ul>
        </div>

        <div>
          <p className="text-muted mb-1 font-medium">✨ 목표</p>
          <ul className="space-y-1">
            {goals.map((goal, i) => (
              <li key={i} className="text-text">• {goal}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
