"use client";

export default function ScanLine() {
  return (
    <div
      style={{
        width: "100%",
        height: 2,
        overflow: "hidden",
        position: "relative",
        marginTop: 6,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "40%",
          height: "100%",
          background:
            "linear-gradient(90deg, transparent 0%, var(--color-scarlet) 50%, transparent 100%)",
          animation: "scanLine 1.5s linear infinite",
        }}
      />
    </div>
  );
}
