"use client";

interface PulseDotProps {
  color?: string;
  size?: number;
  pulse?: boolean;
}

export default function PulseDot({
  color = "#22c55e",
  size = 6,
  pulse = false,
}: PulseDotProps) {
  return (
    <span
      style={{
        display: "inline-block",
        width: size,
        height: size,
        borderRadius: "50%",
        background: color,
        flexShrink: 0,
        animation: pulse ? "pulseDot 2s ease-in-out infinite" : undefined,
      }}
    />
  );
}
