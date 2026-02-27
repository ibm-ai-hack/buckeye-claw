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
    normal: "var(--color-border-medium)",
    soon: "var(--color-border-focus)",
    tomorrow: "var(--color-warning)",
    overdue: "var(--color-scarlet)",
  }[urgency];

  const dueColor = {
    normal: "var(--color-text-label)",
    soon: "var(--color-text-tertiary)",
    tomorrow: "var(--color-warning)",
    overdue: "var(--color-scarlet)",
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
          fontSize: 14,
          color: "var(--color-text-secondary)",
        }}
      >
        {course} — {title}
      </span>
      <span
        style={{
          fontFamily: "var(--font-space-mono)",
          fontWeight: 400,
          fontSize: 13,
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
