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
            ? "var(--color-scarlet)"
            : "var(--color-border-bright)"
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
          fontFamily: "var(--font-space-mono)",
          fontWeight: 400,
          fontSize: 15,
          lineHeight: 1.6,
          color: "var(--color-text-primary)",
          margin: 0,
          flex: 1,
          whiteSpace: "pre-wrap",
        }}
      >
        {text}
      </p>
      <span
        style={{
          fontFamily: "var(--font-space-mono)",
          fontWeight: 400,
          fontSize: 12,
          color: "var(--color-text-placeholder)",
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
