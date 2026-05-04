"use client";

/**
 * DatePicker 컴포넌트 — 클릭하면 달력 팝업이 열리는 날짜 선택 입력
 *
 * 사용 예시:
 *   <DatePicker
 *     value="2026-03-26"
 *     onChange={(date) => setValue(date)}
 *     placeholder="날짜를 선택하세요"
 *   />
 *
 * value/onChange는 "YYYY-MM-DD" 문자열 형식을 사용한다.
 * 내부적으로 Date 객체로 변환하여 Calendar에 전달하고,
 * 선택 결과를 다시 문자열로 변환하여 onChange에 전달한다.
 */

import { format, parse, isValid } from "date-fns";
import { ko } from "date-fns/locale";
import { CalendarDays } from "lucide-react";
import * as React from "react";

import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils/cn";

interface DatePickerProps {
  /** 현재 선택된 날짜 (YYYY-MM-DD 형식 문자열) */
  value: string;
  /** 날짜 변경 시 호출되는 콜백 (YYYY-MM-DD 형식 문자열 전달) */
  onChange: (value: string) => void;
  /** 날짜 미선택 시 표시할 안내 텍스트 */
  placeholder?: string;
  /** 비활성화 여부 */
  disabled?: boolean;
  /** 추가 CSS 클래스 */
  className?: string;
}

export function DatePicker({
  value,
  onChange,
  placeholder = "날짜를 선택하세요",
  disabled = false,
  className,
}: DatePickerProps) {
  // 팝업 열림/닫힘 상태
  const [open, setOpen] = React.useState(false);

  // 문자열 → Date 객체 변환 (캘린더 표시용)
  const selectedDate = React.useMemo(() => {
    if (!value) return undefined;
    const parsed = parse(value, "yyyy-MM-dd", new Date());
    return isValid(parsed) ? parsed : undefined;
  }, [value]);

  // 달력에서 날짜 선택 시 처리
  const handleSelect = (date: Date | undefined) => {
    if (date) {
      // Date 객체 → "YYYY-MM-DD" 문자열로 변환하여 부모에 전달
      onChange(format(date, "yyyy-MM-dd"));
    } else {
      onChange("");
    }
    // 날짜 선택 후 팝업 닫기
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      {/* 트리거 버튼 — 클릭하면 달력 팝업이 열린다 */}
      <PopoverTrigger asChild>
        <button
          type="button"
          disabled={disabled}
          className={cn(
            "flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left text-sm transition-colors",
            "focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none",
            "hover:bg-gray-50",
            // 날짜 선택됨: 진한 텍스트, 미선택: 연한 텍스트
            selectedDate ? "border-gray-300 text-gray-900" : "border-gray-300 text-gray-400",
            disabled && "cursor-not-allowed bg-gray-50 opacity-50",
            className,
          )}
        >
          {/* 선택된 날짜 또는 placeholder 텍스트 */}
          <span>
            {selectedDate
              ? format(selectedDate, "yyyy년 M월 d일 (EEE)", { locale: ko })
              : placeholder}
          </span>
          {/* 달력 아이콘 */}
          <CalendarDays className="h-4 w-4 text-gray-400" />
        </button>
      </PopoverTrigger>

      {/* 팝업 내용 — 달력 */}
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="single"
          selected={selectedDate}
          onSelect={handleSelect}
          defaultMonth={selectedDate || new Date()}
        />
      </PopoverContent>
    </Popover>
  );
}
