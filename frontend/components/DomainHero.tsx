"use client";

interface DomainHeroProps {
  title: string;
  accentColor: string;
}

export default function DomainHero({ title, accentColor }: DomainHeroProps) {
  return (
    <div
      style={{
        position: "relative",
        padding: "24px 32px 16px",
        width: "100%",
        flexShrink: 0,
      }}
    >
      {/* Soft warm gradient */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse at 20% 80%, ${accentColor}18 0%, transparent 55%)`,
        }}
      />
      {/* Title */}
      <h1
        style={{
          position: "relative",
          fontFamily: "var(--font-jakarta)",
          fontWeight: 600,
          fontSize: 26,
          letterSpacing: "-0.5px",
          color: "#ede8e3",
          margin: 0,
        }}
      >
        {title}
      </h1>
    </div>
  );
}
