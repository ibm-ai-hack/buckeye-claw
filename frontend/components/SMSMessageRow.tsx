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
  const isAgent = role === "agent";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isAgent ? "flex-start" : "flex-end",
        padding: "2px 20px",
        animation: "fadeInUp 300ms ease-out forwards",
      }}
    >
      <div
        style={{
          maxWidth: "75%",
          display: "flex",
          flexDirection: "column",
          alignItems: isAgent ? "flex-start" : "flex-end",
        }}
      >
        <div
          style={{
            padding: "10px 14px",
            borderRadius: isAgent
              ? "4px 18px 18px 18px"
              : "18px 18px 4px 18px",
            background: isAgent
              ? "rgba(255, 255, 255, 0.07)"
              : "rgb(198, 50, 45)",
            color: isAgent
              ? "rgba(255, 255, 255, 0.88)"
              : "#fff",
            fontFamily: "var(--font-jakarta)",
            fontWeight: 400,
            fontSize: 15,
            lineHeight: 1.5,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {text}
        </div>
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontWeight: 400,
            fontSize: 11,
            color: "rgba(255, 255, 255, 0.25)",
            marginTop: 4,
            padding: "0 4px",
          }}
        >
          {timestamp}
        </span>
      </div>
    </div>
  );
}
