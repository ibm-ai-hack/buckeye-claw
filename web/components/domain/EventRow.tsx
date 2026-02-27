"use client";

interface EventRowProps {
  day: number;
  month: string;
  title: string;
  venue: string;
  time: string;
  description?: string;
}

export default function EventRow({
  day,
  month,
  title,
  venue,
  time,
  description,
}: EventRowProps) {
  return (
    <div
      style={{
        display: "flex",
        gap: 16,
        padding: "16px 0",
        borderBottom: "1px dashed rgba(255,255,255,0.04)",
        alignItems: "flex-start",
      }}
    >
      {/* Date badge */}
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: 8,
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.06)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-outfit)",
            fontWeight: 200,
            fontSize: 20,
            color: "rgba(255,255,255,0.70)",
            lineHeight: 1,
          }}
        >
          {day}
        </span>
        <span
          style={{
            fontFamily: "var(--font-space-mono)",
            fontWeight: 400,
            fontSize: 9,
            color: "rgba(255,255,255,0.25)",
            letterSpacing: "1px",
            textTransform: "lowercase",
          }}
        >
          {month}
        </span>
      </div>

      {/* Details */}
      <div style={{ flex: 1 }}>
        <div
          style={{
            fontFamily: "var(--font-outfit)",
            fontWeight: 300,
            fontSize: 14,
            color: "rgba(255,255,255,0.65)",
            marginBottom: 4,
          }}
        >
          {title} — {venue}
        </div>
        <div
          style={{
            fontFamily: "var(--font-space-mono)",
            fontWeight: 400,
            fontSize: 11,
            color: "rgba(255,255,255,0.30)",
            marginBottom: description ? 4 : 0,
          }}
        >
          {time}
        </div>
        {description && (
          <div
            style={{
              fontFamily: "var(--font-space-mono)",
              fontWeight: 400,
              fontSize: 10,
              color: "rgba(255,255,255,0.20)",
            }}
          >
            {description}
          </div>
        )}
      </div>
    </div>
  );
}
