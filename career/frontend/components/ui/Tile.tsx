'use client';

import clsx from 'clsx';

interface TileProps {
  icon: React.ReactNode;
  iconColor?: string;
  label: string;
  value: string | number;
  subValue?: string;
  trend?: 'up' | 'down' | 'neutral';
  onClick?: () => void;
  className?: string;
}

export default function Tile({
  icon,
  iconColor = 'bg-primary',
  label,
  value,
  subValue,
  trend,
  onClick,
  className,
}: TileProps) {
  return (
    <div
      className={clsx('tile', onClick && 'cursor-pointer', className)}
      onClick={onClick}
    >
      <div className="tile-header">
        <div className={clsx('tile-icon', iconColor)}>
          {icon}
        </div>
        {trend && (
          <span className={clsx(
            'text-sm font-medium',
            trend === 'up' && 'text-green-500',
            trend === 'down' && 'text-red-500',
            trend === 'neutral' && 'text-muted'
          )}>
            {trend === 'up' && '↑'}
            {trend === 'down' && '↓'}
            {trend === 'neutral' && '—'}
          </span>
        )}
      </div>
      <p className="tile-label">{label}</p>
      <p className="tile-value">{value}</p>
      {subValue && (
        <p className="text-sm text-muted mt-1">{subValue}</p>
      )}
    </div>
  );
}
