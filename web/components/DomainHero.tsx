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
        height: 120,
        width: "100%",
        overflow: "hidden",
        flexShrink: 0,
      }}
    >
      {/* Gradient background mimicking dither strip */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse at 50% 80%, ${accentColor}15 0%, transparent 70%)`,
          opacity: 0.6,
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `linear-gradient(180deg, transparent 0%, #0a0a0a 100%)`,
        }}
      />
      {/* Animated noise texture */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: 0.03,
          backgroundImage: `repeating-conic-gradient(rgba(255,255,255,0.1) 0% 25%, transparent 0% 50%)`,
          backgroundSize: "4px 4px",
        }}
      />
      {/* Title */}
      <h1
        style={{
          position: "absolute",
          bottom: 20,
          left: 32,
          fontFamily: "var(--font-outfit)",
          fontWeight: 200,
          fontSize: 24,
          letterSpacing: "0.2em",
          color: "rgba(255,255,255,0.70)",
          textTransform: "lowercase",
          margin: 0,
        }}
      >
        {title}
      </h1>
    </div>
  );
}
