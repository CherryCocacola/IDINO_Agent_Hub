"use client";

import * as React from "react";

import { cn } from "@/lib/utils/cn";

interface SliderProps extends Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  "onChange" | "value"
> {
  value?: number[];
  onValueChange?: (value: number[]) => void;
  min?: number;
  max?: number;
  step?: number;
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ className, value = [0], onValueChange, min = 0, max = 100, step = 1, ...props }, ref) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      onValueChange?.([Number(e.target.value)]);
    };

    return (
      <div className={cn("relative flex w-full touch-none items-center select-none", className)}>
        <input
          ref={ref}
          type="range"
          min={min}
          max={max}
          step={step}
          value={value[0]}
          onChange={handleChange}
          className="bg-secondary accent-primary h-2 w-full cursor-pointer appearance-none rounded-full"
          {...props}
        />
      </div>
    );
  },
);
Slider.displayName = "Slider";

export { Slider };
