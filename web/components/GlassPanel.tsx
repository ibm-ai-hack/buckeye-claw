"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";

export default function GlassPanel() {
  const router = useRouter();
  const [visible, setVisible] = useState(false);
  const glassRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const t = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(t);
  }, []);

  useEffect(() => {
    const el = glassRef.current;
    if (!el) return;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = el.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const specular = el.querySelector(".glass-specular") as HTMLElement;
      if (specular) {
        specular.style.background = `radial-gradient(circle at ${x}px ${y}px, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.04) 30%, rgba(255,255,255,0) 60%)`;
      }
    };

    const handleMouseLeave = () => {
      const specular = el.querySelector(".glass-specular") as HTMLElement;
      if (specular) {
        specular.style.background = "none";
      }
    };

    el.addEventListener("mousemove", handleMouseMove);
    el.addEventListener("mouseleave", handleMouseLeave);
    return () => {
      el.removeEventListener("mousemove", handleMouseMove);
      el.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, []);

  return (
    <>
      {/* SVG distortion filter — exact same values as darwin */}
      <svg width="0" height="0" style={{ position: "absolute" }}>
        <filter id="glass-distortion">
          <feTurbulence
            type="turbulence"
            baseFrequency="0.008"
            numOctaves={2}
            result="noise"
          />
          <feDisplacementMap in="SourceGraphic" in2="noise" scale={77} />
        </filter>
      </svg>

      <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center">
        <div
          ref={glassRef}
          style={{
            position: "relative",
            padding: "60px 80px",
            borderRadius: 20,
            overflow: "hidden",
            boxShadow: "var(--shadow-glass)",
            opacity: visible ? 1 : 0,
            transform: visible ? "translateY(0)" : "translateY(10px)",
            transition: "opacity 1.5s ease, transform 1.5s ease",
            pointerEvents: "none",
          }}
        >
          {/* Layer 1: Glass distortion filter + backdrop blur */}
          <div
            className="glass-filter"
            style={{
              position: "absolute",
              inset: 0,
              borderRadius: "inherit",
              zIndex: 1,
              backdropFilter: "blur(4px)",
              WebkitBackdropFilter: "blur(4px)",
              filter: "url(#glass-distortion) saturate(120%) brightness(1.15)",
            }}
          />
          {/* Layer 2: Color overlay */}
          <div
            className="glass-overlay"
            style={{
              position: "absolute",
              inset: 0,
              borderRadius: "inherit",
              zIndex: 2,
              background: "var(--color-overlay)",
            }}
          />
          {/* Layer 3: Specular highlight (follows mouse) */}
          <div
            className="glass-specular"
            style={{
              position: "absolute",
              inset: 0,
              borderRadius: "inherit",
              zIndex: 3,
              boxShadow: "var(--shadow-specular)",
            }}
          />
          {/* Content */}
          <div
            style={{ position: "relative", zIndex: 4, display: "flex", flexDirection: "column", alignItems: "center" }}
          >
            <h1
              style={{
                fontFamily: "var(--font-outfit)",
                fontWeight: 200,
                fontSize: "clamp(48px, 8vw, 100px)",
                letterSpacing: "0.3em",
                textTransform: "lowercase",
                color: "var(--color-text-bright)",
                textShadow: "var(--shadow-scarlet-text)",
                margin: 0,
                lineHeight: 1,
              }}
            >
              scarlet
            </h1>

            <p
              style={{
                fontFamily: "var(--font-space-mono)",
                fontWeight: 400,
                fontSize: 16,
                letterSpacing: "3.5px",
                color: "var(--color-text-label)",
                margin: 0,
                marginTop: 14,
              }}
            >
              your entire campus, one text away.
            </p>

            <div
              style={{
                display: "flex",
                gap: 24,
                marginTop: 56,
                pointerEvents: "auto",
              }}
            >
              <button
                onClick={() => {
                  navigator.clipboard.writeText("+1 (614) 555-0199");
                  const btn = document.getElementById("text-me-btn");
                  if (btn) {
                    btn.textContent = "copied";
                    setTimeout(() => { btn.textContent = "text me"; }, 1500);
                  }
                }}
                id="text-me-btn"
                style={{
                  fontFamily: "var(--font-space-mono)",
                  fontWeight: 400,
                  fontSize: 18,
                  letterSpacing: "2.5px",
                  color: "var(--color-text-subtle)",
                  padding: "22px 60px",
                  background: "var(--color-surface-3)",
                  backdropFilter: "blur(16px)",
                  WebkitBackdropFilter: "blur(16px)",
                  border: "1px solid var(--color-border-hover)",
                  borderRadius: 16,
                  cursor: "pointer",
                  transition: "all 0.3s ease",
                }}
                onMouseEnter={(e) => {
                  const t = e.currentTarget;
                  t.style.background = "var(--color-surface-hover)";
                  t.style.borderColor = "var(--color-border-emphasis)";
                  t.style.color = "white";
                }}
                onMouseLeave={(e) => {
                  const t = e.currentTarget;
                  t.style.background = "var(--color-surface-3)";
                  t.style.borderColor = "var(--color-border-hover)";
                  t.style.color = "var(--color-text-subtle)";
                }}
              >
                text me
              </button>
              <button
                onClick={() => router.push("/app/feed")}
                style={{
                  fontFamily: "var(--font-space-mono)",
                  fontWeight: 400,
                  fontSize: 18,
                  letterSpacing: "2.5px",
                  color: "var(--color-scarlet)",
                  padding: "22px 60px",
                  background: "var(--color-scarlet-bg)",
                  backdropFilter: "blur(16px)",
                  WebkitBackdropFilter: "blur(16px)",
                  border: "1px solid var(--color-scarlet-border)",
                  borderRadius: 16,
                  cursor: "pointer",
                  transition: "all 0.3s ease",
                }}
                onMouseEnter={(e) => {
                  const t = e.currentTarget;
                  t.style.background = "var(--color-scarlet-bg-hover)";
                  t.style.borderColor = "var(--color-scarlet-glow-strong)";
                  t.style.color = "var(--color-scarlet-light)";
                }}
                onMouseLeave={(e) => {
                  const t = e.currentTarget;
                  t.style.background = "var(--color-scarlet-bg)";
                  t.style.borderColor = "var(--color-scarlet-border)";
                  t.style.color = "var(--color-scarlet)";
                }}
              >
                open app
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
