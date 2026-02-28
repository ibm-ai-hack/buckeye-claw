"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  motion,
  AnimatePresence,
  useMotionValue,
  useMotionTemplate,
} from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import Dither from "@/components/Dither";

export const dynamic = "force-dynamic";

const EASE = [0.16, 1, 0.3, 1] as const;

const stagger = { animate: { transition: { staggerChildren: 0.07 } } };
const fieldIn = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.3, ease: EASE } },
};

function Spinner() {
  return (
    <span
      style={{
        width: 14,
        height: 14,
        border: "1.5px solid rgba(198,40,40,0.2)",
        borderTopColor: "rgb(198,40,40)",
        borderRadius: "50%",
        display: "inline-block",
        animation: "spin 0.8s linear infinite",
      }}
    />
  );
}

function PrimaryButton({
  children,
  onClick,
  loading,
  disabled,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  loading?: boolean;
  disabled?: boolean;
}) {
  return (
    <motion.button
      onClick={onClick}
      disabled={loading || disabled}
      whileHover={!loading && !disabled ? { scale: 1.015 } : {}}
      whileTap={!loading && !disabled ? { scale: 0.985 } : {}}
      style={{
        width: "100%",
        padding: "14px 0",
        background:
          loading || disabled ? "rgba(198,40,40,0.04)" : "rgba(198,40,40,0.1)",
        border: `1px solid ${loading || disabled ? "rgba(198,40,40,0.12)" : "rgba(198,40,40,0.28)"}`,
        borderRadius: 10,
        fontFamily: "var(--font-jakarta)",
        fontSize: 12,
        letterSpacing: "2.5px",
        color: loading || disabled ? "rgba(198,40,40,0.35)" : "rgb(198,40,40)",
        cursor: loading || disabled ? "not-allowed" : "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        transition: "background 0.2s, border-color 0.2s, color 0.2s",
      }}
    >
      {loading ? <Spinner /> : children}
    </motion.button>
  );
}

type Step = "phone" | "success";

export default function OnboardingPage() {
  const router = useRouter();
  const supabase = createClient();
  const glassRef = useRef<HTMLDivElement>(null);

  const [visible, setVisible] = useState(false);
  const [step, setStep] = useState<Step>("phone");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const specularBg =
    useMotionTemplate`radial-gradient(circle at ${mouseX}px ${mouseY}px, rgba(255,255,255,0.07) 0%, rgba(255,255,255,0.03) 30%, rgba(255,255,255,0) 60%)`;

  useEffect(() => {
    const t = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(t);
  }, []);

  useEffect(() => {
    const el = glassRef.current;
    if (!el) return;
    const handle = (e: MouseEvent) => {
      const rect = el.getBoundingClientRect();
      mouseX.set(e.clientX - rect.left);
      mouseY.set(e.clientY - rect.top);
    };
    el.addEventListener("mousemove", handle);
    return () => el.removeEventListener("mousemove", handle);
  }, [mouseX, mouseY]); // eslint-disable-line react-hooks/exhaustive-deps

  // Phone formatting
  const formatPhone = (raw: string) => {
    const d = raw.replace(/\D/g, "").slice(0, 10);
    if (d.length <= 3) return d;
    if (d.length <= 6) return `(${d.slice(0, 3)}) ${d.slice(3)}`;
    return `(${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6)}`;
  };
  const digits = phone.replace(/\D/g, "");
  const e164 = "+1" + digits;
  const valid = digits.length === 10;

  const handleRegister = async () => {
    if (!valid) return;
    setLoading(true);
    setError(null);

    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      setError("session expired — please sign in again");
      setLoading(false);
      router.push("/");
      return;
    }

    const { error: dbError } = await supabase
      .from("profiles")
      .upsert({ id: user.id, phone: e164 });

    setLoading(false);
    if (dbError) {
      setError(dbError.message.toLowerCase());
      return;
    }

    setStep("success");
    setTimeout(() => router.push("/app/feed"), 1800);
  };

  return (
    <>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        ::placeholder {
          color: rgba(255,255,255,0.18);
          font-family: var(--font-jakarta);
        }
      `}</style>

      <div className="relative h-screen w-screen overflow-hidden bg-[#666666]">
        <Dither
          waveColor={[0.75, 0.0, 0.07]}
          baseColor={[0.22, 0.22, 0.22]}
          waveSpeed={0.05}
          waveFrequency={2}
          waveAmplitude={0.45}
          colorNum={5}
          pixelSize={1.5}
          enableMouseInteraction={true}
          mouseRadius={0.6}
        />

        {/* SVG distortion */}
        <svg width="0" height="0" style={{ position: "absolute" }}>
          <filter id="glass-distortion-ob">
            <feTurbulence type="turbulence" baseFrequency="0.008" numOctaves={2} result="noise" />
            <feDisplacementMap in="SourceGraphic" in2="noise" scale={77} />
          </filter>
        </svg>

        <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center">
          <motion.div
            ref={glassRef}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: visible ? 1 : 0, y: visible ? 0 : 16 }}
            transition={{ duration: 1.2, ease: EASE }}
            style={{
              position: "relative",
              width: 440,
              borderRadius: 20,
              overflow: "hidden",
              boxShadow: "0 0 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.06)",
              pointerEvents: "auto",
            }}
          >
            {/* Glass layers */}
            <div
              style={{
                position: "absolute",
                inset: 0,
                borderRadius: "inherit",
                zIndex: 1,
                backdropFilter: "blur(24px)",
                WebkitBackdropFilter: "blur(24px)",
                filter: "url(#glass-distortion-ob) saturate(110%) brightness(1.1)",
              }}
            />
            <div
              style={{
                position: "absolute",
                inset: 0,
                borderRadius: "inherit",
                zIndex: 2,
                background: "rgba(0,0,0,0.45)",
                border: "1px solid rgba(255,255,255,0.06)",
              }}
            />
            <motion.div
              style={{
                position: "absolute",
                inset: 0,
                borderRadius: "inherit",
                zIndex: 3,
                background: specularBg,
                pointerEvents: "none",
              }}
            />

            {/* Content */}
            <div style={{ position: "relative", zIndex: 4, padding: "48px 40px 44px" }}>
              {/* Logo */}
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2, duration: 0.6, ease: EASE }}
                style={{ textAlign: "center", marginBottom: 36 }}
              >
                <h1
                  style={{
                    fontFamily: "var(--font-jakarta)",
                    fontWeight: 200,
                    fontSize: 36,
                    letterSpacing: "0.28em",
                    textTransform: "lowercase",
                    color: "rgba(255,255,255,0.9)",
                    textShadow: "0 0 40px rgba(198,40,40,0.25)",
                    margin: 0,
                    lineHeight: 1,
                  }}
                >
                  BuckeyeClaw
                </h1>
                <p
                  style={{
                    fontFamily: "var(--font-jakarta)",
                    fontSize: 10,
                    letterSpacing: "2px",
                    color: "rgba(255,255,255,0.2)",
                    margin: "10px 0 0",
                  }}
                >
                  one last step
                </p>
              </motion.div>

              <AnimatePresence mode="wait">
                {step === "phone" ? (
                  <motion.div
                    key="phone"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.3, ease: EASE }}
                  >
                    <motion.div
                      variants={stagger}
                      initial="initial"
                      animate="animate"
                      style={{ display: "flex", flexDirection: "column", gap: 12 }}
                    >
                      <motion.p
                        variants={fieldIn}
                        style={{
                          fontFamily: "var(--font-jakarta)",
                          fontSize: 11,
                          letterSpacing: "1px",
                          color: "rgba(255,255,255,0.35)",
                          margin: "0 0 4px",
                          lineHeight: 1.7,
                          textAlign: "center",
                        }}
                      >
                        register your phone number
                        <br />
                        <span style={{ color: "rgba(255,255,255,0.18)", fontSize: 10 }}>
                          this is the number you&apos;ll text to use BuckeyeClaw 
                        </span>
                      </motion.p>

                      {/* Phone input */}
                      <motion.div
                        variants={fieldIn}
                        style={{ display: "flex", alignItems: "center", gap: 8 }}
                      >
                        <PhoneInput
                          value={formatPhone(phone)}
                          onChange={(v) => setPhone(v.replace(/\D/g, ""))}
                        />
                      </motion.div>

                      <AnimatePresence>
                        {error && (
                          <motion.p
                            initial={{ opacity: 0, y: -4 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0 }}
                            style={{
                              fontFamily: "var(--font-jakarta)",
                              fontSize: 11,
                              color: "#ef4444",
                              margin: 0,
                              textAlign: "center",
                            }}
                          >
                            {error}
                          </motion.p>
                        )}
                      </AnimatePresence>

                      <motion.div variants={fieldIn} style={{ marginTop: 4 }}>
                        <PrimaryButton
                          onClick={handleRegister}
                          loading={loading}
                          disabled={!valid}
                        >
                          register number
                        </PrimaryButton>
                      </motion.div>

                      <motion.p
                        variants={fieldIn}
                        style={{
                          fontFamily: "var(--font-jakarta)",
                          fontSize: 10,
                          color: "rgba(255,255,255,0.12)",
                          margin: 0,
                          textAlign: "center",
                        }}
                      >
                        us numbers only
                      </motion.p>
                    </motion.div>
                  </motion.div>
                ) : (
                  <motion.div
                    key="success"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      gap: 16,
                      padding: "8px 0",
                    }}
                  >
                    <motion.div
                      initial={{ scale: 0, rotate: -15 }}
                      animate={{ scale: 1, rotate: 0 }}
                      transition={{
                        type: "spring",
                        stiffness: 300,
                        damping: 20,
                        delay: 0.05,
                      }}
                      style={{
                        width: 52,
                        height: 52,
                        borderRadius: "50%",
                        background: "rgba(34,197,94,0.1)",
                        border: "1px solid rgba(34,197,94,0.3)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 22,
                        color: "#22c55e",
                      }}
                    >
                      ✓
                    </motion.div>
                    <motion.p
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.2, duration: 0.4, ease: EASE }}
                      style={{
                        fontFamily: "var(--font-jakarta)",
                        fontSize: 11,
                        letterSpacing: "2px",
                        color: "rgba(255,255,255,0.4)",
                        margin: 0,
                      }}
                    >
                      you&apos;re all set — entering...
                    </motion.p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </div>
      </div>
    </>
  );
}

function PhoneInput({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  const [focused, setFocused] = useState(false);
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        flex: 1,
        background: focused ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
        border: `1px solid ${focused ? "rgba(255,255,255,0.18)" : "rgba(255,255,255,0.07)"}`,
        borderRadius: 10,
        transition: "background 0.2s, border-color 0.2s",
        overflow: "hidden",
      }}
    >
      <span
        style={{
          padding: "13px 0 13px 16px",
          fontFamily: "var(--font-jakarta)",
          fontSize: 13,
          color: "rgba(255,255,255,0.3)",
          whiteSpace: "nowrap",
          userSelect: "none",
        }}
      >
        +1
      </span>
      <input
        type="tel"
        placeholder="(614) 000-0000"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        autoFocus
        style={{
          flex: 1,
          padding: "13px 16px 13px 8px",
          background: "transparent",
          border: "none",
          fontFamily: "var(--font-jakarta)",
          fontSize: 13,
          letterSpacing: "0.5px",
          color: "rgba(255,255,255,0.85)",
          outline: "none",
        }}
      />
    </div>
  );
}
