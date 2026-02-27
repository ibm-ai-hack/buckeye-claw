"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";

// ── Types ──────────────────────────────────────────────

interface Course {
  code: string | null;
  title: string | null;
  days: string[] | null;
  start_time: string | null;
  end_time: string | null;
  location: string | null;
  instructor: string | null;
}

interface Schedule {
  term: string;
  courses: Course[];
  raw?: string;
}

type SessionStatus =
  | "idle"
  | "awaiting_auth"
  | "authenticated"
  | "extracting"
  | "complete"
  | "error";

interface FrameMessage {
  type: "frame";
  image: string;
  status: SessionStatus;
  message: string;
}

interface CompleteMessage {
  type: "complete";
  status: "complete";
  schedule: Schedule;
  message: string;
}

interface ErrorMessage {
  type: "error";
  message: string;
}

type WSMessage = FrameMessage | CompleteMessage | ErrorMessage;

interface ClickRipple {
  id: number;
  x: number;
  y: number;
}

const API = "http://localhost:8000";
const WS_URL = "ws://localhost:8000/api/session/stream";

const SPECIAL_KEYS = new Set([
  "Enter",
  "Tab",
  "Backspace",
  "Escape",
  "ArrowUp",
  "ArrowDown",
  "ArrowLeft",
  "ArrowRight",
  "Delete",
  "Home",
  "End",
  "PageUp",
  "PageDown",
]);

// ── Component ──────────────────────────────────────────

export default function ConnectPage() {
  const router = useRouter();
  const wsRef = useRef<WebSocket | null>(null);
  const mountedRef = useRef(true);
  const hiddenInputRef = useRef<HTMLInputElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const rippleIdRef = useRef(0);

  const [imageSrc, setImageSrc] = useState<string>("");
  const [hasFirstFrame, setHasFirstFrame] = useState(false);
  const [status, setStatus] = useState<SessionStatus>("idle");
  const [message, setMessage] = useState("connecting...");
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [showSchedule, setShowSchedule] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [browserFocused, setBrowserFocused] = useState(false);
  const [ripples, setRipples] = useState<ClickRipple[]>([]);

  // ── WebSocket helpers ──────────────────────────────

  const wsSend = useCallback((data: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const closeSession = useCallback(async () => {
    try {
      await fetch(`${API}/api/session/close`, { method: "POST" });
    } catch {
      /* ignore */
    }
  }, []);

  const cleanupWs = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onmessage = null;
      wsRef.current.onerror = null;
      wsRef.current.onclose = null;
      if (
        wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING
      ) {
        wsRef.current.close();
      }
      wsRef.current = null;
    }
  }, []);

  const connectWs = useCallback(() => {
    cleanupWs();
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onmessage = (ev) => {
      if (!mountedRef.current) return;
      try {
        const msg: WSMessage = JSON.parse(ev.data);

        if (msg.type === "frame") {
          if (msg.image) {
            setImageSrc(`data:image/png;base64,${msg.image}`);
            setHasFirstFrame(true);
          }
          setStatus(msg.status);
          setMessage(msg.message);
        }

        if (msg.type === "complete") {
          setStatus("complete");
          setMessage(msg.message);
          setSchedule(msg.schedule);
          setTimeout(() => {
            if (mountedRef.current) setShowSchedule(true);
          }, 2000);
        }

        if (msg.type === "error") {
          setStatus("error");
          setError(msg.message);
          setMessage(msg.message);
        }
      } catch {
        /* ignore */
      }
    };

    ws.onerror = () => {
      if (mountedRef.current) {
        setStatus("error");
        setError("Connection lost");
        setMessage("Connection lost");
      }
    };
  }, [cleanupWs]);

  // ── Lifecycle ──────────────────────────────────────

  useEffect(() => {
    mountedRef.current = true;
    let cancelled = false;

    (async () => {
      try {
        const res = await fetch(`${API}/api/session/start`, {
          method: "POST",
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        if (cancelled) return;
        setStatus("awaiting_auth");
        setMessage("waiting for you to log in...");
        connectWs();
      } catch (e) {
        if (cancelled) return;
        setStatus("error");
        setError(e instanceof Error ? e.message : "Failed to start session");
        setMessage("failed to start session");
      }
    })();

    return () => {
      cancelled = true;
      mountedRef.current = false;
      cleanupWs();
      closeSession();
    };
  }, [connectWs, cleanupWs, closeSession]);

  // ── Interaction handlers ───────────────────────────

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;

    wsSend({ type: "click", x, y });

    // Click ripple
    const id = ++rippleIdRef.current;
    const rippleX = e.clientX - rect.left;
    const rippleY = e.clientY - rect.top;
    setRipples((prev) => [...prev, { id, x: rippleX, y: rippleY }]);
    setTimeout(() => {
      setRipples((prev) => prev.filter((r) => r.id !== id));
    }, 400);

    // Focus hidden input for keyboard capture
    hiddenInputRef.current?.focus();
    setBrowserFocused(true);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (SPECIAL_KEYS.has(e.key)) {
      e.preventDefault();
      wsSend({ type: "keypress", key: e.key });
      return;
    }

    // Let the input event handle regular characters
  };

  const handleInput = (e: React.FormEvent<HTMLInputElement>) => {
    const input = e.currentTarget;
    const text = input.value;
    if (text) {
      wsSend({ type: "type", text });
      input.value = "";
    }
  };

  const handleBlur = () => {
    setBrowserFocused(false);
  };

  const handleRetry = async () => {
    setError(null);
    setStatus("idle");
    setMessage("connecting...");
    setImageSrc("");
    setHasFirstFrame(false);
    setSchedule(null);
    setShowSchedule(false);
    await closeSession();
    try {
      const res = await fetch(`${API}/api/session/start`, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setStatus("awaiting_auth");
      setMessage("waiting for you to log in...");
      connectWs();
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : "Failed to start session");
    }
  };

  const handleClose = async () => {
    cleanupWs();
    await closeSession();
    router.push("/");
  };

  // ── Render ─────────────────────────────────────────

  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100vw",
        background:
          "radial-gradient(ellipse at 50% 40%, rgba(40,5,5,1) 0%, rgba(15,2,2,1) 40%, var(--color-bg) 70%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        overflow: "auto",
      }}
    >
      {/* Header */}
      <div
        style={{
          paddingTop: 60,
          paddingBottom: 32,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <h1
          style={{
            fontFamily: "var(--font-outfit)",
            fontWeight: 200,
            fontSize: "clamp(24px, 4vw, 36px)",
            letterSpacing: "0.25em",
            textTransform: "lowercase",
            color: "var(--color-text-primary)",
            margin: 0,
            lineHeight: 1,
          }}
        >
          connect buckeyelink
        </h1>
        <p
          style={{
            fontFamily: "var(--font-space-mono)",
            fontWeight: 400,
            fontSize: 13,
            letterSpacing: "2px",
            color: "var(--color-text-faint)",
            margin: 0,
            marginTop: 10,
          }}
        >
          log in, and we&apos;ll handle the rest.
        </p>
      </div>

      {/* Browser view */}
      <div style={{ position: "relative", width: "72%", maxWidth: 1080 }}>
        <div
          style={{
            position: "relative",
            width: "100%",
            aspectRatio: "16 / 10",
            borderRadius: 16,
            overflow: "hidden",
            border: `1px solid ${browserFocused ? "var(--color-border-active)" : "var(--color-border-strong)"}`,
            background: "var(--color-surface-2)",
            backdropFilter: "blur(12px)",
            WebkitBackdropFilter: "blur(12px)",
            boxShadow: browserFocused
              ? "var(--shadow-browser-focus)"
              : "var(--shadow-browser)",
            transition: "border-color 0.2s ease, box-shadow 0.2s ease",
          }}
        >
          {/* Loading state */}
          {!hasFirstFrame && (
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 16,
                zIndex: 5,
              }}
            >
              <span
                style={{
                  width: 20,
                  height: 20,
                  border: "1.5px solid var(--color-border-bright)",
                  borderTopColor: "var(--color-text-muted)",
                  borderRadius: "50%",
                  display: "inline-block",
                  animation: "spin 0.9s linear infinite",
                }}
              />
              <span
                style={{
                  fontFamily: "var(--font-space-mono)",
                  fontSize: 13,
                  letterSpacing: "3px",
                  color: "var(--color-text-muted)",
                  textTransform: "lowercase",
                  animation: "pulse 2s ease infinite",
                }}
              >
                connecting...
              </span>
            </div>
          )}

          {/* Browser screenshot */}
          {imageSrc && (
            <img
              src={imageSrc}
              alt="Browser session"
              draggable={false}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "contain",
                display: "block",
                opacity: hasFirstFrame ? 1 : 0,
                transform: hasFirstFrame ? "scale(1)" : "scale(0.98)",
                transition: "opacity 0.5s ease-out, transform 0.5s ease-out",
                pointerEvents: "none",
                userSelect: "none",
              }}
            />
          )}

          {/* Transparent click overlay */}
          <div
            ref={overlayRef}
            onClick={handleOverlayClick}
            style={{
              position: "absolute",
              inset: 0,
              zIndex: 6,
              cursor: hasFirstFrame ? "crosshair" : "default",
            }}
          >
            {/* Click ripples */}
            {ripples.map((r) => (
              <span
                key={r.id}
                style={{
                  position: "absolute",
                  left: r.x - 12,
                  top: r.y - 12,
                  width: 24,
                  height: 24,
                  borderRadius: "50%",
                  border: "1.5px solid var(--color-text-faint)",
                  animation: "ripple 0.4s ease-out forwards",
                  pointerEvents: "none",
                }}
              />
            ))}
          </div>

          {/* Hidden input for keyboard capture */}
          <input
            ref={hiddenInputRef}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            onBlur={handleBlur}
            style={{
              position: "absolute",
              opacity: 0,
              width: 0,
              height: 0,
              top: 0,
              left: 0,
              pointerEvents: "none",
            }}
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
            spellCheck={false}
          />

          {/* Close button */}
          <button
            onClick={handleClose}
            style={{
              position: "absolute",
              top: 12,
              right: 12,
              width: 28,
              height: 28,
              borderRadius: 8,
              border: "1px solid var(--color-border-bright)",
              background: "var(--color-overlay-strong)",
              backdropFilter: "blur(8px)",
              WebkitBackdropFilter: "blur(8px)",
              color: "var(--color-text-faint)",
              fontSize: 14,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "all 0.2s ease",
              zIndex: 10,
              padding: 0,
              lineHeight: 1,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "var(--color-surface-hover)";
              e.currentTarget.style.color = "white";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "var(--color-overlay-strong)";
              e.currentTarget.style.color = "var(--color-text-faint)";
            }}
          >
            &times;
          </button>
        </div>

        {/* Focus hint */}
        {hasFirstFrame && !browserFocused && status === "awaiting_auth" && (
          <div
            style={{
              position: "absolute",
              bottom: -4,
              left: "50%",
              transform: "translateX(-50%) translateY(100%)",
              fontFamily: "var(--font-space-mono)",
              fontSize: 12,
              letterSpacing: "1.5px",
              color: "var(--color-text-muted)",
              marginTop: 8,
              whiteSpace: "nowrap",
            }}
          >
            click to interact
          </div>
        )}

        {/* Status bar */}
        <div
          style={{
            marginTop: 24,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 10,
            minHeight: 32,
          }}
        >
          <StatusIndicator status={status} />
          <span
            style={{
              fontFamily: "var(--font-space-mono)",
              fontSize: 13,
              letterSpacing: "2px",
              color: "var(--color-text-muted)",
              textTransform: "lowercase",
            }}
          >
            {message}
          </span>
          {status === "error" && (
            <button
              onClick={handleRetry}
              style={{
                fontFamily: "var(--font-space-mono)",
                fontSize: 12,
                letterSpacing: "2px",
                textTransform: "lowercase",
                color: "var(--color-text-faint)",
                background: "var(--color-surface-3)",
                border: "1px solid var(--color-border-bright)",
                borderRadius: 6,
                padding: "6px 16px",
                cursor: "pointer",
                marginLeft: 8,
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "var(--color-surface-hover)";
                e.currentTarget.style.color = "white";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "var(--color-surface-3)";
                e.currentTarget.style.color = "var(--color-text-faint)";
              }}
            >
              try again
            </button>
          )}
        </div>
      </div>

      {/* Schedule results */}
      {showSchedule && schedule && schedule.courses.length > 0 && (
        <div
          style={{
            width: "72%",
            maxWidth: 1080,
            marginTop: 40,
            paddingBottom: 80,
            animation: "fadeInUp 0.6s ease forwards",
          }}
        >
          <h2
            style={{
              fontFamily: "var(--font-outfit)",
              fontWeight: 200,
              fontSize: 24,
              letterSpacing: "0.15em",
              color: "var(--color-text-tertiary)",
              textTransform: "lowercase",
              marginBottom: 20,
            }}
          >
            {schedule.term}
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {schedule.courses.map((course, i) => (
              <div
                key={i}
                style={{
                  padding: "16px 20px",
                  borderRadius: 12,
                  border: "1px solid var(--color-border-medium)",
                  background: "var(--color-surface-1)",
                  display: "flex",
                  alignItems: "baseline",
                  gap: 16,
                  flexWrap: "wrap",
                  animation: `fadeInUp 0.4s ease ${i * 0.05}s forwards`,
                  opacity: 0,
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-space-mono)",
                    fontSize: 15,
                    fontWeight: 400,
                    color: "var(--color-text-heading)",
                    letterSpacing: "1px",
                    minWidth: 100,
                  }}
                >
                  {course.code}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-outfit)",
                    fontSize: 16,
                    fontWeight: 300,
                    color: "var(--color-text-secondary)",
                    flex: 1,
                    minWidth: 180,
                  }}
                >
                  {course.title}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-space-mono)",
                    fontSize: 13,
                    color: "var(--color-text-secondary)",
                    letterSpacing: "1px",
                  }}
                >
                  {course.days?.join(" ") ?? ""}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-space-mono)",
                    fontSize: 13,
                    color: "var(--color-text-secondary)",
                    letterSpacing: "1px",
                  }}
                >
                  {[course.start_time, course.end_time]
                    .filter(Boolean)
                    .join(" – ")}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-space-mono)",
                    fontSize: 13,
                    color: "var(--color-text-label)",
                    letterSpacing: "1px",
                  }}
                >
                  {course.location}
                </span>
              </div>
            ))}
          </div>

          {/* Continue button */}
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              marginTop: 40,
              animation: `fadeInUp 0.4s ease ${schedule.courses.length * 0.05 + 0.2}s forwards`,
              opacity: 0,
            }}
          >
            <button
              onClick={() => alert("coming soon")}
              style={{
                fontFamily: "var(--font-space-mono)",
                fontWeight: 400,
                fontSize: 12,
                letterSpacing: "3px",
                color: "var(--color-text-faint)",
                padding: "14px 48px",
                background: "var(--color-surface-3)",
                backdropFilter: "blur(16px)",
                WebkitBackdropFilter: "blur(16px)",
                border: "1px solid var(--color-border-bright)",
                borderRadius: 12,
                cursor: "pointer",
                transition: "all 0.3s ease",
              }}
              onMouseEnter={(e) => {
                const t = e.currentTarget;
                t.style.background = "var(--color-surface-hover)";
                t.style.borderColor = "var(--color-text-muted)";
                t.style.color = "white";
              }}
              onMouseLeave={(e) => {
                const t = e.currentTarget;
                t.style.background = "var(--color-surface-3)";
                t.style.borderColor = "var(--color-border-bright)";
                t.style.color = "var(--color-text-faint)";
              }}
            >
              continue
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Status indicator ───────────────────────────────────

function StatusIndicator({ status }: { status: SessionStatus }) {
  if (status === "idle") {
    return (
      <span
        style={{
          width: 12,
          height: 12,
          border: "1.5px solid var(--color-border-bright)",
          borderTopColor: "var(--color-text-muted)",
          borderRadius: "50%",
          display: "inline-block",
          animation: "spin 0.9s linear infinite",
        }}
      />
    );
  }

  if (status === "awaiting_auth") {
    return (
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: "var(--color-warning)",
          display: "inline-block",
          animation: "pulse 1.5s ease infinite",
        }}
      />
    );
  }

  if (status === "authenticated") {
    return (
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: "var(--color-success)",
          display: "inline-block",
        }}
      />
    );
  }

  if (status === "extracting") {
    return (
      <span
        style={{
          width: 12,
          height: 12,
          border: "1.5px solid var(--color-border-focus)",
          borderTopColor: "var(--color-text-muted)",
          borderRadius: "50%",
          display: "inline-block",
          animation: "spin 0.8s linear infinite",
        }}
      />
    );
  }

  if (status === "complete") {
    return (
      <span style={{ color: "var(--color-success)", fontSize: 14, lineHeight: 1 }}>
        &#10003;
      </span>
    );
  }

  if (status === "error") {
    return (
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: "var(--color-error)",
          display: "inline-block",
        }}
      />
    );
  }

  return null;
}
