"use client";

import { gradeColor } from "@/lib/utils";

interface ScoreGaugeProps {
  score: number;
  maxScore?: number;
  grade: string;
  size?: "sm" | "md" | "lg";
}

export default function ScoreGauge({ score, maxScore = 100, grade, size = "md" }: ScoreGaugeProps) {
  const pct = maxScore > 0 ? (score / maxScore) * 100 : 0;
  const radius = size === "lg" ? 70 : size === "md" ? 50 : 35;
  const stroke = size === "lg" ? 8 : size === "md" ? 6 : 4;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (pct / 100) * circumference;
  const svgSize = (radius + stroke) * 2;

  const strokeColor =
    pct >= 80 ? "#10b981" : pct >= 60 ? "#3b82f6" : pct >= 40 ? "#eab308" : "#ef4444";

  return (
    <div className="flex flex-col items-center">
      <svg width={svgSize} height={svgSize} className="transform -rotate-90">
        <circle
          cx={radius + stroke}
          cy={radius + stroke}
          r={radius}
          stroke="#e2e8f0"
          strokeWidth={stroke}
          fill="none"
        />
        <circle
          cx={radius + stroke}
          cy={radius + stroke}
          r={radius}
          stroke={strokeColor}
          strokeWidth={stroke}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center" style={{ width: svgSize, height: svgSize }}>
        <span className={`font-bold ${size === "lg" ? "text-3xl" : size === "md" ? "text-2xl" : "text-lg"}`}>
          {score}
        </span>
        <span className="text-xs text-gray-500">/ {maxScore}</span>
      </div>
      <div className={`mt-2 px-3 py-1 rounded-full border font-semibold text-sm ${gradeColor(grade)}`}>
        {grade}
      </div>
    </div>
  );
}
