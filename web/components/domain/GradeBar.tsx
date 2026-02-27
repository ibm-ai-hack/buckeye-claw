"use client";

import { useEffect, useState } from "react";

interface GradeBarProps {
  course: string;
  percentage: number;
  letter: string;
  delay?: number;
}

export default function GradeBar({
  course,
  percentage,
  letter,
  delay = 0,
}: GradeBarProps) {
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), delay);
    return () => clearTimeout(t);
  }, [delay]);

  const color =
    percentage >= 85
      ? "#22c55e"
      : percentage >= 70
        ? "rgb(220,170,50)"
        : percentage >= 60
          ? "#eab308"
          : "#ef4444";

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 16,
        height: 40,
      }}
    >
      <span
        style={{
          fontFamily: "var(--font-space-mono)",
          fontWeight: 400,
          fontSize: 12,
          color: "rgba(255,255,255,0.55)",
          minWidth: 120,
          letterSpacing: "0.5px",
        }}
      >
        {course}
      </span>
      <div
        style={{
          flex: 1,
          height: 8,
          borderRadius: 4,
          background: "rgba(255,255,255,0.04)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: animated ? `${percentage}%` : "0%",
            height: "100%",
            borderRadius: 4,
            background: color,
            transition: `width 600ms cubic-bezier(0.16,1,0.3,1) ${delay}ms`,
          }}
        />
      </div>
      <span
        style={{
          fontFamily: "var(--font-space-mono)",
          fontWeight: 400,
          fontSize: 12,
          color: "rgba(255,255,255,0.70)",
          width: 36,
          textAlign: "right",
        }}
      >
        {percentage}%
      </span>
      <span
        style={{
          fontFamily: "var(--font-outfit)",
          fontWeight: 300,
          fontSize: 13,
          color: "rgba(255,255,255,0.50)",
          width: 28,
        }}
      >
        {letter}
      </span>
    </div>
  );
}
