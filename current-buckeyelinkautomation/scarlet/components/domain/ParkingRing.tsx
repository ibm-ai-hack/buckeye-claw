"use client";

import { useEffect, useState } from "react";

interface ParkingRingProps {
  name: string;
  available: number;
  total: number;
}

export default function ParkingRing({ name, available, total }: ParkingRingProps) {
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 100);
    return () => clearTimeout(t);
  }, []);

  const pct = total > 0 ? available / total : 0;
  const radius = 32;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - pct);

  const color =
    available === 0
      ? "#ef4444"
      : pct < 0.2
        ? "rgb(198,40,40)"
        : pct < 0.5
          ? "#eab308"
          : "#22c55e";

  return (
    <div
      style={{
        width: 140,
        height: 160,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 12,
      }}
    >
      <div style={{ position: "relative", width: 72, height: 72 }}>
        <svg width="72" height="72" viewBox="0 0 72 72">
          {/* Track */}
          <circle
            cx="36"
            cy="36"
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.04)"
            strokeWidth="6"
          />
          {/* Fill */}
          <circle
            cx="36"
            cy="36"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={animated ? offset : circumference}
            transform="rotate(-90 36 36)"
            style={{
              transition: "stroke-dashoffset 0.8s ease-out",
            }}
          />
        </svg>
        {/* Count */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-outfit)",
              fontWeight: 200,
              fontSize: available === 0 ? 18 : 24,
              color: "rgba(255,255,255,0.80)",
              lineHeight: 1,
            }}
          >
            {available === 0 ? "full" : available}
          </span>
        </div>
      </div>
      <span
        style={{
          fontFamily: "var(--font-space-mono)",
          fontWeight: 400,
          fontSize: 10,
          color: "rgba(255,255,255,0.30)",
          letterSpacing: "0.5px",
          textAlign: "center",
        }}
      >
        {name}
      </span>
    </div>
  );
}
