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
        padding: "48px 40px 28px",
        width: "100%",
        flexShrink: 0,
      }}
    >
      {/* Soft warm gradient */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse at 20% 80%, ${accentColor}12 0%, transparent 60%)`,
        }}
      />
      {/* Title */}
      <h1
        style={{
          position: "relative",
          fontFamily: "var(--font-jakarta)",
          fontWeight: 600,
          fontSize: 28,
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
