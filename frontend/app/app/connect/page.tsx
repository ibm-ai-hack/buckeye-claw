"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

// ── Types ────────────────────────────────────────────────

interface IntegrationStatus {
  canvas_connected: boolean;
  canvas_connected_at: string | null;
}

// ── Canvas icon ──────────────────────────────────────────

function CanvasIcon() {
  return (
    <svg
      width="28"
      height="28"
      viewBox="0 0 28 28"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width="28" height="28" rx="7" fill="rgba(226,50,50,0.15)" />
      <text
        x="14"
        y="20"
        textAnchor="middle"
        fontFamily="var(--font-jakarta, sans-serif)"
        fontWeight="700"
        fontSize="15"
        fill="rgb(226,80,80)"
      >
        C
      </text>
    </svg>
  );
}

// ── Status dot ───────────────────────────────────────────

function StatusDot({ connected }: { connected: boolean }) {
  return (
    <span
      style={{
        width: 7,
        height: 7,
        borderRadius: "50%",
        background: connected ? "#22c55e" : "rgba(255,255,255,0.2)",
        display: "inline-block",
        boxShadow: connected ? "0 0 6px rgba(34,197,94,0.5)" : "none",
        flexShrink: 0,
      }}
    />
  );
}

// ── Toast ────────────────────────────────────────────────

function Toast({
  message,
  type,
  onClose,
}: {
  message: string;
  type: "success" | "error";
  onClose: () => void;
}) {
  useEffect(() => {
    const t = setTimeout(onClose, 4000);
    return () => clearTimeout(t);
  }, [onClose]);

  return (
    <div
      style={{
        position: "fixed",
        bottom: 32,
        left: "50%",
        transform: "translateX(-50%)",
        background: type === "success" ? "rgba(34,197,94,0.12)" : "rgba(239,68,68,0.12)",
        border: `1px solid ${type === "success" ? "rgba(34,197,94,0.25)" : "rgba(239,68,68,0.25)"}`,
        borderRadius: 10,
        padding: "12px 22px",
        fontFamily: "var(--font-jakarta)",
        fontSize: 13,
        letterSpacing: "0.5px",
        color: type === "success" ? "rgba(34,197,94,0.9)" : "rgba(239,68,68,0.9)",
        zIndex: 200,
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        whiteSpace: "nowrap",
        animation: "fadeInUp 0.3s ease",
      }}
    >
      {message}
    </div>
  );
}

// ── Integration card ─────────────────────────────────────

function IntegrationCard({
  icon,
  name,
  subtitle,
  description,
  connected,
  connectedAt,
  onConnect,
  onDisconnect,
  loading,
  comingSoon,
}: {
  icon: React.ReactNode;
  name: string;
  subtitle: string;
  description: string;
  connected: boolean;
  connectedAt?: string | null;
  onConnect?: () => void;
  onDisconnect?: () => void;
  loading?: boolean;
  comingSoon?: boolean;
}) {
  return (
    <div
      style={{
        background: "rgba(255,255,255,0.025)",
        border: `1px solid ${connected ? "rgba(34,197,94,0.15)" : "rgba(255,255,255,0.06)"}`,
        borderRadius: 14,
        padding: "24px 28px",
        display: "flex",
        alignItems: "flex-start",
        gap: 20,
        opacity: comingSoon ? 0.4 : 1,
        transition: "border-color 0.3s ease",
      }}
    >
      <div style={{ flexShrink: 0, paddingTop: 2 }}>{icon}</div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
          <span
            style={{
              fontFamily: "var(--font-jakarta)",
              fontWeight: 500,
              fontSize: 16,
              color: "rgba(255,255,255,0.88)",
              letterSpacing: "-0.1px",
            }}
          >
            {name}
          </span>
          <span
            style={{
              fontFamily: "var(--font-jakarta)",
              fontSize: 11,
              color: "rgba(255,255,255,0.28)",
              letterSpacing: "1px",
            }}
          >
            {subtitle}
          </span>
          {comingSoon && (
            <span
              style={{
                fontFamily: "var(--font-jakarta)",
                fontSize: 9,
                letterSpacing: "1.5px",
                color: "rgba(255,255,255,0.25)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 4,
                padding: "2px 7px",
                textTransform: "uppercase",
              }}
            >
              soon
            </span>
          )}
        </div>

        <p
          style={{
            fontFamily: "var(--font-jakarta)",
            fontSize: 13,
            color: "rgba(255,255,255,0.38)",
            lineHeight: 1.6,
            margin: 0,
            marginBottom: 18,
            maxWidth: 440,
          }}
        >
          {description}
        </p>

        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <StatusDot connected={connected} />
          <span
            style={{
              fontFamily: "var(--font-jakarta)",
              fontSize: 12,
              letterSpacing: "0.5px",
              color: connected ? "rgba(34,197,94,0.8)" : "rgba(255,255,255,0.25)",
            }}
          >
            {connected
              ? connectedAt
                ? `connected · ${new Date(connectedAt).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`
                : "connected"
              : "not connected"}
          </span>

          {!comingSoon && (
            <button
              onClick={connected ? onDisconnect : onConnect}
              disabled={loading}
              style={{
                marginLeft: "auto",
                fontFamily: "var(--font-jakarta)",
                fontSize: 12,
                letterSpacing: "1.5px",
                textTransform: "lowercase",
                color: connected ? "rgba(239,68,68,0.6)" : "rgba(255,255,255,0.55)",
                background: connected
                  ? "rgba(239,68,68,0.06)"
                  : "rgba(255,255,255,0.05)",
                border: `1px solid ${connected ? "rgba(239,68,68,0.15)" : "rgba(255,255,255,0.1)"}`,
                borderRadius: 8,
                padding: "8px 18px",
                cursor: loading ? "default" : "pointer",
                opacity: loading ? 0.5 : 1,
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                if (loading) return;
                e.currentTarget.style.background = connected
                  ? "rgba(239,68,68,0.12)"
                  : "rgba(255,255,255,0.1)";
                e.currentTarget.style.color = connected
                  ? "rgba(239,68,68,0.85)"
                  : "rgba(255,255,255,0.85)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = connected
                  ? "rgba(239,68,68,0.06)"
                  : "rgba(255,255,255,0.05)";
                e.currentTarget.style.color = connected
                  ? "rgba(239,68,68,0.6)"
                  : "rgba(255,255,255,0.55)";
              }}
            >
              {loading ? "..." : connected ? "disconnect" : "connect"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────

export default function ConnectPage() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [disconnecting, setDisconnecting] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  // Handle URL params from OAuth callback
  useEffect(() => {
    const success = searchParams.get("success");
    const error = searchParams.get("error");

    if (success === "canvas") {
      setToast({ message: "Canvas connected successfully", type: "success" });
    } else if (error === "canvas_denied") {
      setToast({ message: "Canvas authorization was cancelled", type: "error" });
    } else if (error === "token_exchange") {
      setToast({ message: "Failed to connect Canvas — please try again", type: "error" });
    } else if (error === "no_profile") {
      setToast({ message: "Profile not found — contact support", type: "error" });
    } else if (error === "not_configured") {
      setToast({ message: "Canvas OAuth is not configured yet", type: "error" });
    }
  }, [searchParams]);

  // Load integration status
  useEffect(() => {
    async function load() {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (!user) {
        setLoading(false);
        return;
      }

      // Get profile id
      const { data: profile } = await supabase
        .from("profiles")
        .select("id")
        .eq("auth_id", user.id)
        .single();

      if (!profile) {
        setLoading(false);
        return;
      }

      const { data: integrations } = await supabase
        .from("user_integrations")
        .select("canvas_token, canvas_connected_at")
        .eq("user_id", profile.id)
        .single();

      setStatus({
        canvas_connected: !!(integrations?.canvas_token),
        canvas_connected_at: integrations?.canvas_connected_at ?? null,
      });
      setLoading(false);
    }

    load();
  }, [searchParams]); // re-fetch after OAuth redirect

  const handleConnectCanvas = () => {
    window.location.href = "/api/auth/canvas";
  };

  const handleDisconnectCanvas = async () => {
    setDisconnecting(true);
    try {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) return;

      const { data: profile } = await supabase
        .from("profiles")
        .select("id")
        .eq("auth_id", user.id)
        .single();
      if (!profile) return;

      await supabase
        .from("user_integrations")
        .update({ canvas_token: null, canvas_connected_at: null })
        .eq("user_id", profile.id);

      setStatus((prev) =>
        prev ? { ...prev, canvas_connected: false, canvas_connected_at: null } : prev
      );
      setToast({ message: "Canvas disconnected", type: "success" });
    } catch {
      setToast({ message: "Failed to disconnect — try again", type: "error" });
    } finally {
      setDisconnecting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        padding: "56px 48px",
        maxWidth: 760,
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 40 }}>
        <h1
          style={{
            fontFamily: "var(--font-jakarta)",
            fontWeight: 200,
            fontSize: 28,
            letterSpacing: "0.22em",
            textTransform: "lowercase",
            color: "rgba(255,255,255,0.85)",
            margin: 0,
            lineHeight: 1,
          }}
        >
          connect
        </h1>
        <p
          style={{
            fontFamily: "var(--font-jakarta)",
            fontSize: 12,
            letterSpacing: "1.5px",
            color: "rgba(255,255,255,0.2)",
            margin: "10px 0 0",
          }}
        >
          manage your connected apps
        </p>
      </div>

      {/* Cards */}
      {loading ? (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            color: "rgba(255,255,255,0.2)",
            fontFamily: "var(--font-jakarta)",
            fontSize: 12,
            letterSpacing: "2px",
          }}
        >
          <span
            style={{
              width: 14,
              height: 14,
              border: "1.5px solid rgba(255,255,255,0.08)",
              borderTopColor: "rgba(255,255,255,0.3)",
              borderRadius: "50%",
              display: "inline-block",
              animation: "spin 0.9s linear infinite",
            }}
          />
          loading...
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <IntegrationCard
            icon={<CanvasIcon />}
            name="Canvas"
            subtitle="OSU Carmen"
            description="Connect your Canvas account so BuckeyeClaw can answer questions about your courses, assignments, grades, announcements, and upcoming due dates."
            connected={status?.canvas_connected ?? false}
            connectedAt={status?.canvas_connected_at}
            onConnect={handleConnectCanvas}
            onDisconnect={handleDisconnectCanvas}
            loading={disconnecting}
          />

          <IntegrationCard
            icon={
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 7,
                  background: "rgba(100,100,255,0.1)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 13,
                  fontWeight: 700,
                  color: "rgba(130,130,255,0.7)",
                  fontFamily: "var(--font-jakarta)",
                }}
              >
                G
              </div>
            }
            name="Grubhub"
            subtitle="food ordering"
            description="Order food delivery from nearby restaurants and schedule future orders."
            connected={false}
            comingSoon
          />

          <IntegrationCard
            icon={
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 7,
                  background: "rgba(255,160,60,0.1)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 13,
                  fontWeight: 700,
                  color: "rgba(255,160,60,0.7)",
                  fontFamily: "var(--font-jakarta)",
                }}
              >
                B
              </div>
            }
            name="BuckeyeLink"
            subtitle="student services"
            description="Access your class schedule, financial aid, grades, and enrollment info."
            connected={false}
            comingSoon
          />
        </div>
      )}

      {/* Toast */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Keyframes */}
      <style jsx global>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(8px) translateX(-50%); }
          to   { opacity: 1; transform: translateY(0)  translateX(-50%); }
        }
      `}</style>
    </div>
  );
}
