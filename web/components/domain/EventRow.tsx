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
        borderBottom: "1px dashed var(--color-border)",
        alignItems: "flex-start",
      }}
    >
      {/* Date badge */}
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: 8,
          background: "var(--color-border)",
          border: "1px solid var(--color-border-medium)",
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
            fontSize: 24,
            color: "var(--color-text-primary)",
            lineHeight: 1,
          }}
        >
          {day}
        </span>
        <span
          style={{
            fontFamily: "var(--font-space-mono)",
            fontWeight: 400,
            fontSize: 13,
            color: "var(--color-text-label)",
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
            fontSize: 16,
            color: "var(--color-text-heading)",
            marginBottom: 4,
          }}
        >
          {title} — {venue}
        </div>
        <div
          style={{
            fontFamily: "var(--font-space-mono)",
            fontWeight: 400,
            fontSize: 13,
            color: "var(--color-text-faint)",
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
              fontSize: 12,
              color: "var(--color-text-ghost)",
            }}
          >
            {description}
          </div>
        )}
      </div>
    </div>
  );
}
