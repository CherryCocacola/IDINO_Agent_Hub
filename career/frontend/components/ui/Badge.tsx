'use client';

import clsx from 'clsx';

type BadgeVariant = 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'error' | 'muted';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  primary: 'bg-primary/10 text-primary',
  secondary: 'bg-secondary/10 text-secondary',
  accent: 'bg-accent/10 text-accent',
  success: 'bg-green-100 text-green-700',
  warning: 'bg-yellow-100 text-yellow-700',
  error: 'bg-red-100 text-red-700',
  muted: 'bg-gray-100 text-gray-600',
};

const sizeClasses = {
  sm: 'px-1.5 py-0.5 text-xs',
  md: 'px-2 py-0.5 text-xs',
  lg: 'px-3 py-1 text-sm',
};

export default function Badge({
  children,
  variant = 'primary',
  size = 'md',
  className,
}: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full font-medium',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
    >
      {children}
    </span>
  );
}

// Grade badge component
interface GradeBadgeProps {
  grade: string;
  size?: 'sm' | 'md' | 'lg';
}

export function GradeBadge({ grade, size = 'md' }: GradeBadgeProps) {
  const getVariant = (g: string): BadgeVariant => {
    if (g.startsWith('A')) return 'primary';
    if (g.startsWith('B')) return 'secondary';
    if (g.startsWith('C')) return 'warning';
    return 'muted';
  };

  return (
    <Badge variant={getVariant(grade)} size={size}>
      {grade}
    </Badge>
  );
}

// Status badge component
interface StatusBadgeProps {
  status: 'completed' | 'in_progress' | 'pending' | 'cancelled';
  size?: 'sm' | 'md' | 'lg';
}

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const config: Record<string, { variant: BadgeVariant; label: string }> = {
    completed: { variant: 'success', label: '완료' },
    in_progress: { variant: 'primary', label: '진행중' },
    pending: { variant: 'warning', label: '대기' },
    cancelled: { variant: 'error', label: '취소' },
  };

  const { variant, label } = config[status] || config.pending;

  return (
    <Badge variant={variant} size={size}>
      {label}
    </Badge>
  );
}
