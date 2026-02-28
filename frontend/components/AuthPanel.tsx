"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { createClient } from "@/lib/supabase/client";

// ── Types ───────────────────────────────────────────────────────────────

type Mode = "sign_in" | "sign_up";

const OSU_DOMAIN = "@osu.edu";

// ── Animation variants ─────────────────────────────────────────────────

const EASE = [0.16, 1, 0.3, 1] as const;

// ── Primitives ─────────────────────────────────────────────────────────

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
        animation: "authSpin 0.8s linear infinite",
      }}
    />
  );
}

function ErrorMsg({ msg }: { msg: string }) {
  return (
    <motion.p
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      style={{
        fontFamily: "var(--font-jakarta)",
        fontSize: 11,
        letterSpacing: "0.5px",
        color: "#ef4444",
        margin: 0,
        textAlign: "center",
      }}
    >
      {msg}
    </motion.p>
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
        transition: "background 0.2s ease, border-color 0.2s ease, color 0.2s ease",
      }}
    >
      {loading ? <Spinner /> : children}
    </motion.button>
  );
}

// ── OSU username input (hardcoded @osu.edu suffix) ─────────────────────

function OsuEmailInput({
  value,
  onChange,
  autoFocus,
}: {
  value: string;
  onChange: (v: string) => void;
  autoFocus?: boolean;
}) {
  const [focused, setFocused] = useState(false);
  const borderColor = focused
    ? "rgba(255,255,255,0.18)"
    : "rgba(255,255,255,0.07)";
  const bg = focused ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)";

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        background: bg,
        border: `1px solid ${borderColor}`,
        borderRadius: 10,
        transition: "background 0.2s ease, border-color 0.2s ease",
        overflow: "hidden",
      }}
    >
      <input
        type="text"
        placeholder="username"
        value={value}
        onChange={(e) =>
          onChange(e.target.value.toLowerCase().replace(/[^a-z0-9._-]/g, ""))
        }
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        autoFocus={autoFocus}
        autoComplete="off"
        autoCorrect="off"
        autoCapitalize="off"
        spellCheck={false}
        style={{
          flex: 1,
          padding: "13px 0 13px 16px",
          background: "transparent",
          border: "none",
          fontFamily: "var(--font-jakarta)",
          fontSize: 13,
          letterSpacing: "0.5px",
          color: "rgba(255,255,255,0.85)",
          outline: "none",
          minWidth: 0,
        }}
      />
      <span
        style={{
          padding: "13px 16px 13px 0",
          fontFamily: "var(--font-jakarta)",
          fontSize: 13,
          letterSpacing: "0.5px",
          color: "rgba(255,255,255,0.3)",
          whiteSpace: "nowrap",
          userSelect: "none",
        }}
      >
        {OSU_DOMAIN}
      </span>
    </div>
  );
}

function PasswordInput({
  value,
  onChange,
  placeholder = "password",
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  const [focused, setFocused] = useState(false);
  return (
    <input
      type="password"
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      autoComplete="current-password"
      style={{
        width: "100%",
        boxSizing: "border-box",
        padding: "13px 16px",
        background: focused ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
        border: `1px solid ${focused ? "rgba(255,255,255,0.18)" : "rgba(255,255,255,0.07)"}`,
        borderRadius: 10,
        fontFamily: "var(--font-jakarta)",
        fontSize: 13,
        letterSpacing: "0.5px",
        color: "rgba(255,255,255,0.85)",
        outline: "none",
        transition: "background 0.2s ease, border-color 0.2s ease",
      }}
    />
  );
}

// ── Step: Auth ─────────────────────────────────────────────────────────

function StepAuth({
  mode,
  onSignIn,
  onSignUp,
  error,
  loading,
}: {
  mode: Mode;
  onSignIn: (username: string, password: string) => void;
  onSignUp: (username: string, password: string) => void;
  error: string | null;
  loading: boolean;
}) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  const isSignUp = mode === "sign_up";
  const passwordsMatch = !isSignUp || password === confirm;
  const canSubmit =
    username.length > 0 &&
    password.length >= 8 &&
    passwordsMatch &&
    !loading;

  const submit = () => {
    if (!canSubmit) return;
    if (isSignUp) onSignUp(username, password);
    else onSignIn(username, password);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <OsuEmailInput value={username} onChange={setUsername} autoFocus />

      <PasswordInput
        value={password}
        onChange={setPassword}
        placeholder={isSignUp ? "create password" : "password"}
      />

      {isSignUp && (
        <PasswordInput
          value={confirm}
          onChange={setConfirm}
          placeholder="confirm password"
        />
      )}

      {isSignUp && confirm.length > 0 && !passwordsMatch && (
        <p
          style={{
            fontFamily: "var(--font-jakarta)",
            fontSize: 11,
            color: "#ef4444",
            margin: 0,
            textAlign: "center",
          }}
        >
          passwords don&apos;t match
        </p>
      )}

      {isSignUp && (
        <p
          style={{
            fontFamily: "var(--font-jakarta)",
            fontSize: 10,
            letterSpacing: "0.5px",
            color: "rgba(255,255,255,0.18)",
            margin: 0,
            textAlign: "center",
          }}
        >
          must be at least 8 characters
        </p>
      )}

      <AnimatePresence>{error && <ErrorMsg msg={error} />}</AnimatePresence>

      <div style={{ marginTop: 4 }}>
        <PrimaryButton onClick={submit} loading={loading} disabled={!canSubmit}>
          {isSignUp ? "create account" : "sign in"}
        </PrimaryButton>
      </div>
    </div>
  );
}

// ── Main AuthPanel ─────────────────────────────────────────────────────

export default function AuthPanel() {
  const router = useRouter();
  const supabase = createClient();

  const [mode, setMode] = useState<Mode>("sign_in");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const switchMode = (m: Mode) => {
    setMode(m);
    setError(null);
  };

  // ── Handlers ────────────────────────────────────────────────────────

  const handleSignIn = async (username: string, password: string) => {
    setLoading(true);
    setError(null);
    const email = username + OSU_DOMAIN;
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (error) {
      setError(error.message.toLowerCase());
      return;
    }
    router.push("/app/feed");
    router.refresh();
  };

  const handleSignUp = async (username: string, password: string) => {
    setLoading(true);
    setError(null);
    const email = username + OSU_DOMAIN;
    const { error } = await supabase.auth.signUp({ email, password });
    setLoading(false);
    if (error) {
      setError(error.message.toLowerCase());
      return;
    }
    router.push("/onboarding");
    router.refresh();
  };

  // ── Render ──────────────────────────────────────────────────────────

  return (
    <>
      <style>{`
        @keyframes authSpin { to { transform: rotate(360deg); } }
        ::placeholder {
          color: rgba(255,255,255,0.18);
          font-family: var(--font-jakarta);
          letter-spacing: 0.5px;
        }
      `}</style>

      <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, ease: EASE }}
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
            }}
          />
          <div
            style={{
              position: "absolute",
              inset: 0,
              borderRadius: "inherit",
              zIndex: 2,
              background: "rgba(10,10,10,0.6)",
              border: "1px solid rgba(255,255,255,0.08)",
            }}
          />

          {/* Content */}
          <div style={{ position: "relative", zIndex: 4, padding: "48px 40px 44px" }}>
            <div style={{ textAlign: "center", marginBottom: 32 }}>
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
                scarlet
              </h1>
              <p
                style={{
                  fontFamily: "var(--font-jakarta)",
                  fontSize: 10,
                  letterSpacing: "2.5px",
                  color: "rgba(255,255,255,0.25)",
                  margin: "10px 0 0",
                }}
              >
                your entire campus, one text away.
              </p>
            </div>

            {/* Tab switcher */}
            <div
              style={{
                display: "flex",
                background: "rgba(255,255,255,0.03)",
                borderRadius: 10,
                padding: 3,
                marginBottom: 20,
                border: "1px solid rgba(255,255,255,0.05)",
              }}
            >
              {(["sign_in", "sign_up"] as Mode[]).map((m) => (
                <button
                  key={m}
                  onClick={() => switchMode(m)}
                  style={{
                    flex: 1,
                    padding: "9px 0",
                    borderRadius: 8,
                    border: "none",
                    fontFamily: "var(--font-jakarta)",
                    fontSize: 11,
                    letterSpacing: "1.5px",
                    cursor: "pointer",
                    background:
                      mode === m ? "rgba(255,255,255,0.07)" : "transparent",
                    color:
                      mode === m
                        ? "rgba(255,255,255,0.8)"
                        : "rgba(255,255,255,0.28)",
                    transition: "background 0.2s ease, color 0.2s ease",
                  }}
                >
                  {m === "sign_in" ? "sign in" : "sign up"}
                </button>
              ))}
            </div>

            {/* Auth form */}
            <StepAuth
              key={mode}
              mode={mode}
              onSignIn={handleSignIn}
              onSignUp={handleSignUp}
              error={error}
              loading={loading}
            />

            {/* Footer */}
            <p
              style={{
                fontFamily: "var(--font-jakarta)",
                fontSize: 10,
                letterSpacing: "0.5px",
                color: "rgba(255,255,255,0.12)",
                margin: "20px 0 0",
                textAlign: "center",
                lineHeight: 1.7,
              }}
            >
              {mode === "sign_up"
                ? "by signing up you confirm you're an osu student."
                : "osu student accounts only."}
            </p>
          </div>
        </motion.div>
      </div>
    </>
  );
}
