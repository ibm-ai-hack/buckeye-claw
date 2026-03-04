"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import {
  motion,
  AnimatePresence,
  useMotionValue,
  useTransform,
} from "framer-motion";
import { createClient } from "@/lib/supabase/client";

export const dynamic = "force-dynamic";

/* ── constants ───────────────────────────────────────────────────────── */

const EASE = [0.16, 1, 0.3, 1] as const;

const SERVICES = [
  "BuckeyeLink",
  "Grubhub",
  "Dining Services",
  "Canvas",
  "Campus Bus Routes",
  "Parking Garages",
  "Rec Sports",
  "BuckeyeMail",
  "Student Orgs",
  "Campus Events",
  "Library Rooms",
  "Class Search",
  "Food Trucks",
  "Academic Calendar",
];

/* ── noise SVG (inline data URI for grain texture) ───────────────────── */

const NOISE_SVG = `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`;

/* ── orbital ring animation around counter ───────────────────────────── */

function OrbitalRing() {
  return (
    <div
      style={{
        position: "absolute",
        inset: -20,
        borderRadius: "50%",
        border: "1px solid rgba(198,50,45,0.25)",
        animation: "wlOrbit 12s linear infinite",
      }}
    >
      {/* Orbiting dot */}
      <div
        style={{
          position: "absolute",
          top: -2,
          left: "50%",
          marginLeft: -2,
          width: 4,
          height: 4,
          borderRadius: "50%",
          background: "rgb(198,50,45)",
          boxShadow: "0 0 12px rgba(198,50,45,0.6)",
        }}
      />
    </div>
  );
}

/* ── rotating service typewriter ──────────────────────────────────────── */

function RotatingTagline() {
  const [serviceIdx, setServiceIdx] = useState(0);
  const [charIndex, setCharIndex] = useState(0);
  const [deleting, setDeleting] = useState(false);
  const [pause, setPause] = useState(false);

  const current = SERVICES[serviceIdx];

  useEffect(() => {
    if (pause) {
      const t = setTimeout(() => {
        setPause(false);
        setDeleting(true);
      }, 1800);
      return () => clearTimeout(t);
    }

    if (deleting) {
      if (charIndex === 0) {
        setDeleting(false);
        setServiceIdx((i) => (i + 1) % SERVICES.length);
        return;
      }
      const t = setTimeout(() => setCharIndex((i) => i - 1), 25);
      return () => clearTimeout(t);
    }

    if (charIndex < current.length) {
      const t = setTimeout(() => setCharIndex((i) => i + 1), 45);
      return () => clearTimeout(t);
    }

    // Done typing — pause before deleting
    setPause(true);
  }, [charIndex, deleting, pause, current, serviceIdx]);

  return (
    <span
      style={{
        fontFamily: "var(--font-jakarta)",
        fontSize: 15,
        fontWeight: 300,
        lineHeight: 1.8,
        letterSpacing: "0.3px",
      }}
    >
      <span style={{ color: "rgba(255,255,255,0.75)" }}>
        {current.slice(0, charIndex)}
      </span>
      <span
        style={{
          color: "rgb(198,50,45)",
          animation: "wlBlink 0.8s step-end infinite",
          marginLeft: 1,
          fontWeight: 300,
        }}
      >
        |
      </span>
      <br />
      <span
        style={{
          color: "rgb(198,50,45)",
          fontWeight: 500,
          letterSpacing: "0.5px",
        }}
      >
        one text away.
      </span>
    </span>
  );
}

/* ── animated counter ────────────────────────────────────────────────── */

function AnimatedCount({ target }: { target: number }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (target <= 0) { setDisplay(0); return; }
    const duration = Math.min(1200, target * 40);
    const start = performance.now();
    let raf: number;
    const tick = (now: number) => {
      const elapsed = now - start;
      const p = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(Math.round(eased * target));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target]);

  return <>{display}</>;
}

/* ── particle burst ──────────────────────────────────────────────────── */

function ParticleBurst({ active }: { active: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fired = useRef(false);

  useEffect(() => {
    if (!active || fired.current) return;
    fired.current = true;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const colors = [
      "rgba(198,50,45,0.9)",
      "rgba(255,255,255,0.7)",
      "rgba(255,200,50,0.8)",
      "rgba(198,50,45,0.5)",
    ];

    const particles = Array.from({ length: 60 }, () => {
      const angle = Math.random() * Math.PI * 2;
      const speed = 2 + Math.random() * 5;
      return {
        x: canvas.width / 2, y: canvas.height / 2,
        vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed - 2,
        size: 1.5 + Math.random() * 3,
        color: colors[Math.floor(Math.random() * colors.length)],
        opacity: 1,
      };
    });

    let frame = 0;
    const animate = () => {
      if (frame > 80) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (const p of particles) {
        p.x += p.vx; p.y += p.vy;
        p.vy += 0.08; p.vx *= 0.98; p.vy *= 0.98; p.opacity *= 0.96;
        ctx.globalAlpha = p.opacity;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      }
      frame++;
      requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [active]);

  return (
    <canvas
      ref={canvasRef}
      style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 50 }}
    />
  );
}

/* ── input components ────────────────────────────────────────────────── */

function TextInput({
  value, onChange, placeholder, autoFocus,
}: {
  value: string; onChange: (v: string) => void; placeholder: string; autoFocus?: boolean;
}) {
  const [focused, setFocused] = useState(false);
  return (
    <input
      type="text"
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      autoFocus={autoFocus}
      autoComplete="off"
      spellCheck={false}
      style={{
        width: "100%",
        boxSizing: "border-box",
        padding: "14px 0",
        background: "transparent",
        border: "none",
        borderBottom: `1px solid ${focused ? "rgba(198,50,45,0.5)" : "rgba(255,255,255,0.25)"}`,
        fontFamily: "var(--font-jakarta)",
        fontSize: 14,
        fontWeight: 300,
        letterSpacing: "0.5px",
        color: "rgba(255,255,255,0.95)",
        outline: "none",
        transition: "border-color 0.3s ease",
      }}
    />
  );
}

function OsuEmailInput({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [focused, setFocused] = useState(false);
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        borderBottom: `1px solid ${focused ? "rgba(198,50,45,0.5)" : "rgba(255,255,255,0.25)"}`,
        transition: "border-color 0.3s ease",
      }}
    >
      <input
        type="text"
        placeholder="username"
        value={value}
        onChange={(e) => onChange(e.target.value.toLowerCase().replace(/[^a-z0-9._-]/g, ""))}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        autoComplete="off"
        autoCapitalize="off"
        spellCheck={false}
        style={{
          flex: 1,
          padding: "14px 0",
          background: "transparent",
          border: "none",
          fontFamily: "var(--font-jakarta)",
          fontSize: 14,
          fontWeight: 300,
          letterSpacing: "0.5px",
          color: "rgba(255,255,255,0.95)",
          outline: "none",
          minWidth: 0,
        }}
      />
      <span
        style={{
          fontFamily: "var(--font-jakarta)",
          fontSize: 14,
          fontWeight: 300,
          letterSpacing: "0.5px",
          color: "rgba(255,255,255,0.5)",
          whiteSpace: "nowrap",
          userSelect: "none",
        }}
      >
        @osu.edu
      </span>
    </div>
  );
}

function PhoneInput({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [focused, setFocused] = useState(false);

  const formatPhone = (raw: string) => {
    const d = raw.replace(/\D/g, "").slice(0, 10);
    if (d.length <= 3) return d;
    if (d.length <= 6) return `(${d.slice(0, 3)}) ${d.slice(3)}`;
    return `(${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6)}`;
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        borderBottom: `1px solid ${focused ? "rgba(198,50,45,0.5)" : "rgba(255,255,255,0.25)"}`,
        transition: "border-color 0.3s ease",
      }}
    >
      <span
        style={{
          fontFamily: "var(--font-jakarta)",
          fontSize: 14,
          fontWeight: 300,
          color: "rgba(255,255,255,0.5)",
          whiteSpace: "nowrap",
          userSelect: "none",
          paddingRight: 8,
        }}
      >
        +1
      </span>
      <input
        type="tel"
        placeholder="(614) 000-0000"
        value={formatPhone(value)}
        onChange={(e) => onChange(e.target.value.replace(/\D/g, ""))}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        autoComplete="off"
        style={{
          flex: 1,
          padding: "14px 0",
          background: "transparent",
          border: "none",
          fontFamily: "var(--font-jakarta)",
          fontSize: 14,
          fontWeight: 300,
          letterSpacing: "0.5px",
          color: "rgba(255,255,255,0.95)",
          outline: "none",
          minWidth: 0,
        }}
      />
    </div>
  );
}

/* ── main page ───────────────────────────────────────────────────────── */

type Step = "form" | "success";

export default function WaitlistPage() {
  const supabase = createClient();

  const [step, setStep] = useState<Step>("form");
  const [username, setUsername] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [count, setCount] = useState<number | null>(null);
  const [position, setPosition] = useState<number | null>(null);
  const [showParticles, setShowParticles] = useState(false);

  // Parallax mouse tracking for ambient glow
  const mouseX = useMotionValue(0.5);
  const mouseY = useMotionValue(0.5);
  const glowX = useTransform(mouseX, [0, 1], ["30%", "70%"]);
  const glowY = useTransform(mouseY, [0, 1], ["30%", "70%"]);

  useEffect(() => {
    const handle = (e: MouseEvent) => {
      mouseX.set(e.clientX / window.innerWidth);
      mouseY.set(e.clientY / window.innerHeight);
    };
    window.addEventListener("mousemove", handle);
    return () => window.removeEventListener("mousemove", handle);
  }, [mouseX, mouseY]);

  // Fetch count
  useEffect(() => {
    supabase.rpc("waitlist_count").then(({ data }) => {
      if (data !== null && data !== undefined) setCount(data);
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const email = `${username}@osu.edu`;
  const phoneDigits = phone.replace(/\D/g, "");
  const canSubmit = username.length > 0 && name.trim().length > 0 && phoneDigits.length === 10 && !loading;

  const handleSubmit = useCallback(async () => {
    if (!canSubmit) return;
    setLoading(true);
    setError(null);

    const { error: dbError } = await supabase
      .from("waitlist")
      .insert({
        email,
        name: name.trim(),
        phone: phone.length === 10 ? `+1${phone}` : null,
      });

    if (dbError) {
      setLoading(false);
      if (dbError.code === "23505") {
        setError("you're already on the list");
        return;
      }
      setError(dbError.message.toLowerCase());
      return;
    }

    const { data: pos } = await supabase.rpc("waitlist_position", { p_email: email });

    setLoading(false);
    setPosition(pos ?? null);
    setStep("success");
    setShowParticles(true);
    setCount((c) => (c !== null ? c + 1 : 1));
  }, [canSubmit, email, name, phone, supabase]);

  return (
    <>
      <style>{`
        @keyframes wlSpin { to { transform: rotate(360deg); } }
        @keyframes wlBlink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
        @keyframes wlOrbit { to { transform: rotate(360deg); } }
        @keyframes wlPulse {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 0.7; }
        }
        @keyframes wlLineGrow {
          from { transform: scaleX(0); }
          to { transform: scaleX(1); }
        }
        ::placeholder {
          color: rgba(255,255,255,0.45);
          font-family: var(--font-jakarta);
          font-weight: 300;
          letter-spacing: 0.5px;
        }
      `}</style>

      <div
        style={{
          position: "relative",
          width: "100vw",
          minHeight: "100vh",
          background: "#181818",
          overflow: "hidden",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* Ambient scarlet glow — tracks mouse */}
        <motion.div
          style={{
            position: "absolute",
            inset: 0,
            background: useMotionValue(0).get() === 0
              ? undefined
              : undefined,
            pointerEvents: "none",
          }}
        >
          <motion.div
            style={{
              position: "absolute",
              width: "60vw",
              height: "60vh",
              borderRadius: "50%",
              background: "radial-gradient(circle, rgba(198,50,45,0.22) 0%, transparent 70%)",
              filter: "blur(80px)",
              left: glowX,
              top: glowY,
              transform: "translate(-50%, -50%)",
            }}
          />
          {/* Secondary cooler glow */}
          <div
            style={{
              position: "absolute",
              bottom: "-20%",
              right: "-10%",
              width: "50vw",
              height: "50vh",
              borderRadius: "50%",
              background: "radial-gradient(circle, rgba(140,140,160,0.14) 0%, transparent 70%)",
              filter: "blur(60px)",
            }}
          />
        </motion.div>

        {/* Grain overlay */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage: NOISE_SVG,
            backgroundRepeat: "repeat",
            backgroundSize: "256px 256px",
            opacity: 0.03,
            pointerEvents: "none",
            mixBlendMode: "overlay",
          }}
        />

        {/* Subtle grid lines */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)",
            backgroundSize: "80px 80px",
            pointerEvents: "none",
          }}
        />

        <ParticleBurst active={showParticles} />

        {/* Main content */}
        <div style={{ position: "relative", zIndex: 10, width: "100%", maxWidth: 520, padding: "40px 24px" }}>

          {/* Top marker */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1, duration: 0.8 }}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginBottom: 48,
            }}
          >
            <div
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: "rgb(198,50,45)",
                boxShadow: "0 0 10px rgba(198,50,45,0.5)",
                animation: "wlPulse 3s ease-in-out infinite",
              }}
            />
            <span
              style={{
                fontFamily: "var(--font-jakarta)",
                fontSize: 10,
                fontWeight: 400,
                letterSpacing: "3px",
                textTransform: "uppercase",
                color: "rgba(255,255,255,0.65)",
              }}
            >
              early access
            </span>
          </motion.div>

          {/* Hero text */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 1, ease: EASE }}
          >
            <h1
              style={{
                fontFamily: "var(--font-jakarta)",
                fontWeight: 200,
                fontSize: "clamp(40px, 7vw, 64px)",
                letterSpacing: "-0.02em",
                lineHeight: 1.05,
                color: "rgba(255,255,255,0.95)",
                margin: 0,
              }}
            >
              Buckeye
              <span style={{ color: "rgb(198,50,45)" }}>Claw</span>
            </h1>
          </motion.div>

          {/* Rotating tagline */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.8 }}
            style={{ margin: "20px 0 0", minHeight: 52 }}
          >
            <RotatingTagline />
          </motion.div>

          {/* Decorative line */}
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ delay: 0.8, duration: 1.2, ease: EASE }}
            style={{
              height: 1,
              background: "linear-gradient(90deg, rgba(198,50,45,0.5), rgba(198,50,45,0.08) 60%, transparent)",
              margin: "40px 0",
              transformOrigin: "left",
            }}
          />

          {/* Counter section */}
          {count !== null && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1, duration: 0.8, ease: EASE }}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 24,
                marginBottom: 48,
              }}
            >
              {/* Number with orbital ring */}
              <div style={{ position: "relative", width: 80, height: 80, flexShrink: 0 }}>
                <OrbitalRing />
                <div
                  style={{
                    position: "absolute",
                    inset: 0,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexDirection: "column",
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-jakarta)",
                      fontWeight: 300,
                      fontSize: 28,
                      color: "rgba(255,255,255,0.95)",
                      lineHeight: 1,
                    }}
                  >
                    <AnimatedCount target={count} />
                  </span>
                </div>
              </div>

              <div>
                <p
                  style={{
                    fontFamily: "var(--font-jakarta)",
                    fontSize: 12,
                    fontWeight: 400,
                    letterSpacing: "0.5px",
                    color: "rgba(255,255,255,0.75)",
                    margin: 0,
                  }}
                >
                  students on the waitlist
                </p>
                <p
                  style={{
                    fontFamily: "var(--font-jakarta)",
                    fontSize: 11,
                    fontWeight: 300,
                    color: "rgba(255,255,255,0.5)",
                    margin: "4px 0 0",
                  }}
                >
                  launching at ohio state soon
                </p>
              </div>
            </motion.div>
          )}

          {/* Form / Success */}
          <AnimatePresence mode="wait">
            {step === "form" ? (
              <motion.div
                key="form"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                transition={{ delay: 1.2, duration: 0.6, ease: EASE }}
              >
                <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
                  <TextInput
                    value={name}
                    onChange={setName}
                    placeholder="full name"
                  />

                  <div style={{ marginTop: 8 }}>
                    <OsuEmailInput value={username} onChange={setUsername} />
                  </div>

                  <div style={{ marginTop: 8 }}>
                    <PhoneInput value={phone} onChange={setPhone} />
                  </div>

                  <AnimatePresence>
                    {error && (
                      <motion.p
                        initial={{ opacity: 0, y: -4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        style={{
                          fontFamily: "var(--font-jakarta)",
                          fontSize: 12,
                          fontWeight: 300,
                          color: error === "you're already on the list" ? "#eab308" : "#ef4444",
                          margin: "12px 0 0",
                          letterSpacing: "0.3px",
                        }}
                      >
                        {error}
                      </motion.p>
                    )}
                  </AnimatePresence>

                  {/* Submit button */}
                  <motion.button
                    onClick={handleSubmit}
                    disabled={!canSubmit || loading}
                    whileHover={canSubmit && !loading ? { scale: 1.01, x: 2 } : {}}
                    whileTap={canSubmit && !loading ? { scale: 0.99 } : {}}
                    style={{
                      marginTop: 32,
                      padding: "16px 0",
                      background: loading || !canSubmit
                        ? "transparent"
                        : "rgba(198,50,45,0.08)",
                      border: `1px solid ${loading || !canSubmit ? "rgba(255,255,255,0.15)" : "rgba(198,50,45,0.4)"}`,
                      borderRadius: 8,
                      fontFamily: "var(--font-jakarta)",
                      fontSize: 12,
                      fontWeight: 400,
                      letterSpacing: "3px",
                      textTransform: "uppercase",
                      color: loading || !canSubmit ? "rgba(255,255,255,0.35)" : "rgb(198,50,45)",
                      cursor: loading || !canSubmit ? "not-allowed" : "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: 10,
                      transition: "all 0.3s ease",
                      position: "relative",
                      overflow: "hidden",
                    }}
                  >
                    {loading ? (
                      <span
                        style={{
                          width: 14,
                          height: 14,
                          border: "1.5px solid rgba(198,50,45,0.2)",
                          borderTopColor: "rgb(198,50,45)",
                          borderRadius: "50%",
                          display: "inline-block",
                          animation: "wlSpin 0.8s linear infinite",
                        }}
                      />
                    ) : (
                      <>
                        join the waitlist
                        <span style={{ fontSize: 16, lineHeight: 1 }}>→</span>
                      </>
                    )}
                  </motion.button>

                  <p
                    style={{
                      fontFamily: "var(--font-jakarta)",
                      fontSize: 10,
                      fontWeight: 300,
                      color: "rgba(255,255,255,0.4)",
                      margin: "16px 0 0",
                      letterSpacing: "1px",
                    }}
                  >
                    osu students only
                  </p>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="success"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, ease: EASE }}
                style={{ textAlign: "left" }}
              >
                {/* Position */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{
                    type: "spring",
                    stiffness: 200,
                    damping: 20,
                    delay: 0.1,
                  }}
                  style={{
                    display: "inline-flex",
                    alignItems: "baseline",
                    gap: 4,
                    marginBottom: 20,
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-jakarta)",
                      fontWeight: 200,
                      fontSize: 56,
                      color: "rgb(198,50,45)",
                      lineHeight: 1,
                      textShadow: "0 0 40px rgba(198,50,45,0.3)",
                    }}
                  >
                    #{position}
                  </span>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3, duration: 0.5, ease: EASE }}
                >
                  <p
                    style={{
                      fontFamily: "var(--font-jakarta)",
                      fontSize: 16,
                      fontWeight: 300,
                      color: "rgba(255,255,255,0.9)",
                      margin: 0,
                      lineHeight: 1.5,
                    }}
                  >
                    you&apos;re on the list.
                  </p>
                  <p
                    style={{
                      fontFamily: "var(--font-jakarta)",
                      fontSize: 13,
                      fontWeight: 300,
                      color: "rgba(255,255,255,0.55)",
                      margin: "8px 0 0",
                      lineHeight: 1.6,
                    }}
                  >
                    we&apos;ll reach out when it&apos;s your turn.
                  </p>
                </motion.div>

                {/* Decorative line */}
                <motion.div
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ delay: 0.5, duration: 1, ease: EASE }}
                  style={{
                    height: 1,
                    background: "linear-gradient(90deg, rgba(198,50,45,0.3), transparent)",
                    margin: "32px 0 0",
                    transformOrigin: "left",
                  }}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Bottom-right version tag */}
        <div
          style={{
            position: "absolute",
            bottom: 24,
            right: 32,
            fontFamily: "var(--font-jakarta)",
            fontSize: 10,
            fontWeight: 300,
            letterSpacing: "2px",
            color: "rgba(255,255,255,0.25)",
          }}
        >
          v0.1
        </div>
      </div>
    </>
  );
}
