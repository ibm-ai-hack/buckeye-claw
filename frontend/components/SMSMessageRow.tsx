"use client";

interface SMSMessageRowProps {
  text: string;
  role: "student" | "agent";
  timestamp: string;
}

export default function SMSMessageRow({
  text,
  role,
  timestamp,
}: SMSMessageRowProps) {
  return (
    <div
      style={{
        width: "100%",
        padding: "16px 24px",
        borderLeft: `2px solid ${
          role === "agent"
            ? "rgb(198,40,40)"
            : "rgba(255,255,255,0.10)"
        }`,
        animation: "fadeInUp 300ms ease-out forwards",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        gap: 16,
      }}
    >
      <p
        style={{
          fontFamily: "var(--font-jakarta)",
          fontWeight: 400,
          fontSize: 15,
          lineHeight: 1.6,
          color:
            role === "agent"
              ? "rgba(255,255,255,0.85)"
              : "rgba(255,255,255,0.85)",
          margin: 0,
          flex: 1,
          whiteSpace: "pre-wrap",
        }}
      >
        {text}
      </p>
      <span
        style={{
          fontFamily: "var(--font-jakarta)",
          fontWeight: 400,
          fontSize: 12,
          color: "rgba(255,255,255,0.35)",
          letterSpacing: "1px",
          flexShrink: 0,
          marginTop: 2,
        }}
      >
        {timestamp}
      </span>
    </div>
  );
}
