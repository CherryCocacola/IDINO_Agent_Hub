'use client';

import clsx from 'clsx';

interface ProgressBarProps {
  label: string;
  value: number;
  maxValue?: number;
  color?: string;
  showPercentage?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export default function ProgressBar({
  label,
  value,
  maxValue = 100,
  color = 'bg-primary',
  showPercentage = true,
  size = 'md',
  className,
}: ProgressBarProps) {
  const percentage = Math.min((value / maxValue) * 100, 100);

  const sizeClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4',
  };

  return (
    <div className={clsx('w-full', className)}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-text">{label}</span>
        {showPercentage && (
          <span className="text-sm text-muted">
            {value.toFixed(0)} / {maxValue}
          </span>
        )}
      </div>
      <div className={clsx('progress-bar', sizeClasses[size])}>
        <div
          className={clsx('progress-bar-fill', color)}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

// Competency-specific progress bar with status
interface CompetencyBarProps {
  name: string;
  score: number;
  maxScore?: number;
  status: 'excellent' | 'good' | 'average' | 'needs_improvement';
  percentile?: number;
}

// Format score with commas for large numbers (1000+ → 1,000)
function formatScore(score: number): string {
  if (score >= 1000) {
    return score.toLocaleString('ko-KR', { maximumFractionDigits: 1 });
  }
  return score.toFixed(1);
}

export function CompetencyBar({
  name,
  score,
  maxScore = 100,
  status,
  percentile,
}: CompetencyBarProps) {
  const statusConfig = {
    excellent: { color: 'bg-primary', badge: '우수', badgeClass: 'badge-primary' },
    good: { color: 'bg-secondary', badge: '양호', badgeClass: 'badge-secondary' },
    average: { color: 'bg-ethics', badge: '보통', badgeClass: 'badge-warning' },
    needs_improvement: { color: 'bg-accent', badge: '보완필요', badgeClass: 'badge-accent' },
  };

  const config = statusConfig[status];
  // Progress bar width based on percentile (0-100), not raw score
  const barPercentage = percentile !== undefined ? Math.min(percentile, 100) : 50;

  return (
    <div className="p-2 bg-gray-50 rounded-lg">
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-sm font-medium text-text">{name}</span>
        <span className={clsx('badge', config.badgeClass)}>{config.badge}</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="flex-1">
          <div className="progress-bar h-2">
            <div
              className={clsx('progress-bar-fill', config.color)}
              style={{ width: `${barPercentage}%` }}
            />
          </div>
        </div>
        <span className="text-sm font-semibold text-text min-w-[72px] text-right">
          {formatScore(score)}점
        </span>
      </div>
      {percentile !== undefined && (
        <p className="text-xs text-muted mt-0.5 text-right">
          상위 {100 - percentile}%
        </p>
      )}
    </div>
  );
}
