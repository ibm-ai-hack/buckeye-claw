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
      ? "var(--color-success)"
      : percentage >= 70
        ? "var(--color-grade-mid)"
        : percentage >= 60
          ? "var(--color-warning)"
          : "var(--color-error)";

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
          fontSize: 14,
          color: "var(--color-text-secondary)",
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
          background: "var(--color-border)",
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
          fontSize: 14,
          color: "var(--color-text-primary)",
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
          fontSize: 15,
          color: "var(--color-text-tertiary)",
          width: 28,
        }}
      >
        {letter}
      </span>
    </div>
  );
}
