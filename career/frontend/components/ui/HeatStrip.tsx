'use client';

import clsx from 'clsx';

interface HeatStripProps {
  data: Array<{
    label: string;
    values: number[]; // Values from 0-100
    color?: string;
  }>;
  months?: string[];
  showLabels?: boolean;
  onCellClick?: (label: string, monthIndex: number, value: number) => void;
}

const defaultMonths = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];

export default function HeatStrip({
  data,
  months = defaultMonths,
  showLabels = true,
  onCellClick,
}: HeatStripProps) {
  const getOpacity = (value: number) => {
    if (value === 0) return 0.1;
    if (value < 25) return 0.25;
    if (value < 50) return 0.5;
    if (value < 75) return 0.75;
    return 1;
  };

  return (
    <div className="space-y-3">
      {/* Month labels */}
      {showLabels && (
        <div className="flex gap-1 text-xs text-muted">
          <div className="w-20" /> {/* Spacer for row labels */}
          {months.map((month, i) => (
            <div key={i} className="flex-1 text-center">{month}</div>
          ))}
        </div>
      )}

      {/* Heat strips */}
      {data.map((row, rowIndex) => (
        <div key={rowIndex} className="flex gap-1 items-center">
          <div className="w-20 text-sm text-text font-medium truncate">
            {row.label}
          </div>
          <div className="flex gap-1 flex-1">
            {row.values.map((value, colIndex) => (
              <div
                key={colIndex}
                onClick={() => onCellClick?.(row.label, colIndex, value)}
                className="flex-1 h-6 rounded transition-all hover:scale-110 hover:ring-2 hover:ring-primary/50 cursor-pointer"
                style={{
                  backgroundColor: row.color || '#5b6dff',
                  opacity: getOpacity(value),
                }}
                title={`${row.label} ${months[colIndex]}: ${value}%`}
              />
            ))}
          </div>
        </div>
      ))}

      {/* Legend */}
      <div className="flex items-center justify-end gap-2 mt-4">
        <span className="text-xs text-muted">활동량:</span>
        <div className="flex gap-1">
          {[0.1, 0.25, 0.5, 0.75, 1].map((opacity, i) => (
            <div
              key={i}
              className="w-4 h-4 rounded"
              style={{ backgroundColor: '#5b6dff', opacity }}
            />
          ))}
        </div>
        <span className="text-xs text-muted">낮음 → 높음</span>
      </div>
    </div>
  );
}

// Competency HeatStrip for action board
interface CompetencyHeatStripProps {
  competencies: Array<{
    name: string;
    monthlyScores: number[];
    color: string;
  }>;
  onCellClick?: (competencyName: string, monthIndex: number) => void;
}

export function CompetencyHeatStrip({ competencies, onCellClick }: CompetencyHeatStripProps) {
  const handleCellClick = (label: string, monthIndex: number) => {
    onCellClick?.(label, monthIndex);
  };

  return (
    <HeatStrip
      data={competencies.map(c => ({
        label: c.name,
        values: c.monthlyScores,
        color: c.color,
      }))}
      onCellClick={handleCellClick}
    />
  );
}
