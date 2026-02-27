"use client";

interface AssignmentRowProps {
  course: string;
  title: string;
  dueLabel: string;
  urgency: "normal" | "soon" | "tomorrow" | "overdue";
}

export default function AssignmentRow({
  course,
  title,
  dueLabel,
  urgency,
}: AssignmentRowProps) {
  const borderColor = {
    normal: "rgba(255,255,255,0.06)",
    soon: "rgba(255,255,255,0.15)",
    tomorrow: "#eab308",
    overdue: "rgb(198,40,40)",
  }[urgency];

  const dueColor = {
    normal: "rgba(255,255,255,0.25)",
    soon: "rgba(255,255,255,0.50)",
    tomorrow: "#eab308",
    overdue: "rgb(198,40,40)",
  }[urgency];

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: 44,
        borderLeft: `2px solid ${borderColor}`,
        paddingLeft: 16,
      }}
    >
      <span
        style={{
          fontFamily: "var(--font-space-mono)",
          fontWeight: 400,
          fontSize: 12,
          color: "rgba(255,255,255,0.55)",
        }}
      >
        {course} — {title}
      </span>
      <span
        style={{
          fontFamily: "var(--font-space-mono)",
          fontWeight: 400,
          fontSize: 11,
          color: dueColor,
          textTransform: urgency === "overdue" ? "uppercase" : "lowercase",
          letterSpacing: urgency === "overdue" ? "1px" : "0.5px",
        }}
      >
        {dueLabel}
      </span>
    </div>
  );
}
