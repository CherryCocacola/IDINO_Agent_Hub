'use client';

interface RingChartProps {
  data: Array<{
    name: string;
    value: number;
    color: string;
  }>;
  size?: number;
  strokeWidth?: number;
  showLegend?: boolean;
  centerLabel?: string;
  centerValue?: string;
}

export default function RingChart({
  data,
  size = 160,
  strokeWidth = 20,
  showLegend = true,
  centerLabel,
  centerValue,
}: RingChartProps) {
  // Safety check for undefined or empty data
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center" style={{ width: size, height: size }}>
        <span className="text-sm text-muted">데이터 없음</span>
      </div>
    );
  }

  const total = data.reduce((sum, item) => sum + item.value, 0);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  // Calculate segments
  let accumulatedOffset = 0;
  const segments = data.map((item) => {
    const percentage = (item.value / total) * 100;
    const dashLength = (percentage / 100) * circumference;
    const dashOffset = circumference - accumulatedOffset;
    accumulatedOffset += dashLength;

    return {
      ...item,
      percentage,
      dashLength,
      dashOffset: -accumulatedOffset + dashLength,
    };
  });

  return (
    <div className="flex items-center gap-6">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          {/* Background circle */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={strokeWidth}
          />

          {/* Data segments */}
          {segments.map((segment, index) => (
            <circle
              key={index}
              cx={center}
              cy={center}
              r={radius}
              fill="none"
              stroke={segment.color}
              strokeWidth={strokeWidth}
              strokeDasharray={`${segment.dashLength} ${circumference}`}
              strokeDashoffset={segment.dashOffset}
              strokeLinecap="round"
              className="transition-all duration-500"
            />
          ))}
        </svg>

        {/* Center text */}
        {(centerLabel || centerValue) && (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            {centerValue && (
              <span className="text-2xl font-bold text-text">{centerValue}</span>
            )}
            {centerLabel && (
              <span className="text-sm text-muted">{centerLabel}</span>
            )}
          </div>
        )}
      </div>

      {/* Legend */}
      {showLegend && (
        <div className="flex flex-col gap-2">
          {data.map((item, index) => (
            <div key={index} className="flex items-center gap-2">
              <span
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-sm text-muted">{item.name}</span>
              <span className="text-sm font-medium text-text ml-auto">
                {item.value}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
