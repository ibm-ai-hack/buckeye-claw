"use client";

import { useRef, useEffect, useMemo } from "react";
import SMSMessageRow from "@/components/SMSMessageRow";
import ToolCallCard from "@/components/ToolCallCard";
import PulseDot from "@/components/PulseDot";
import {
  useUserPhone,
  useMessages,
  useAgentRuns,
  useAgentEvents,
  type AgentRun,
  type AgentEvent,
} from "@/lib/supabase/hooks";

// ── Message thread (left panel) ──────────────────────────

function MessageThread({
  phone,
}: {
  phone: string;
}) {
  const messages = useMessages(phone);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        height: "100%",
        overflow: "hidden",
      }}
    >
      {/* Panel header */}
      <div
        style={{
          padding: "18px 24px 14px",
          borderBottom: "1px solid rgba(255, 240, 220, 0.06)",
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontWeight: 500,
            fontSize: 14,
            color: "rgba(237, 232, 227, 0.55)",
          }}
        >
          conversation
        </span>
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontWeight: 400,
            fontSize: 12,
            color: "rgba(237, 232, 227, 0.30)",
            marginLeft: 12,
          }}
        >
          {messages.length} msgs
        </span>
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          display: "flex",
          flexDirection: "column",
          gap: 2,
          paddingBottom: 16,
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              padding: 32,
              textAlign: "center",
              fontFamily: "var(--font-jakarta)",
              fontSize: 14,
              color: "rgba(237, 232, 227, 0.25)",
            }}
          >
            waiting for messages...
          </div>
        )}
        {messages.map((msg) => (
          <SMSMessageRow
            key={msg.id}
            text={msg.text}
            role={msg.role === "user" ? "student" : "agent"}
            timestamp={new Date(msg.created_at).toLocaleTimeString("en-US", {
              hour: "numeric",
              minute: "2-digit",
              hour12: true,
            }).toLowerCase()}
          />
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}

// ── Reasoning timeline (right panel) ─────────────────────

function IntentBadge({ intent }: { intent: string }) {
  return (
    <span
      style={{
        fontFamily: "var(--font-jakarta)",
        fontSize: 12,
        fontWeight: 500,
        color: "rgb(198, 50, 45)",
        background: "rgba(198, 50, 45, 0.10)",
        border: "1px solid rgba(198, 50, 45, 0.18)",
        borderRadius: 6,
        padding: "3px 10px",
      }}
    >
      {intent}
    </span>
  );
}

function StepMarker({
  event,
  endEvent,
}: {
  event: AgentEvent;
  endEvent?: AgentEvent;
}) {
  const isEnd = event.event_type === "step_end";
  const duration = endEvent?.duration_ms ?? event.duration_ms;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "5px 0",
      }}
    >
      <div
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: isEnd ? "rgba(237, 232, 227, 0.15)" : "rgba(198, 50, 45, 0.5)",
          flexShrink: 0,
        }}
      />
      <span
        style={{
          fontFamily: "var(--font-jakarta)",
          fontSize: 13,
          color: "rgba(237, 232, 227, 0.50)",
        }}
      >
        {event.step ?? "unknown"} {isEnd ? "done" : "started"}
      </span>
      {duration != null && (
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontSize: 12,
            color: "rgba(237, 232, 227, 0.30)",
            marginLeft: "auto",
          }}
        >
          {(duration / 1000).toFixed(1)}s
        </span>
      )}
    </div>
  );
}

function RunBlock({
  run,
  events,
}: {
  run: AgentRun;
  events: AgentEvent[];
}) {
  const statusColor =
    run.status === "running"
      ? "rgb(198, 50, 45)"
      : run.status === "completed"
        ? "#22c55e"
        : "#ef4444";

  return (
    <div
      style={{
        padding: "18px 16px",
        marginBottom: 8,
        background: "rgba(255, 240, 220, 0.02)",
        borderRadius: 12,
        border: "1px solid rgba(255, 240, 220, 0.04)",
        animation: "fadeInUp 300ms ease-out forwards",
      }}
    >
      {/* Run header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginBottom: 12,
        }}
      >
        <PulseDot
          color={statusColor}
          size={6}
          pulse={run.status === "running"}
        />
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontWeight: 500,
            fontSize: 13,
            color: "rgba(237, 232, 227, 0.60)",
          }}
        >
          {run.status}
        </span>
        {run.intent && <IntentBadge intent={run.intent} />}
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontSize: 11,
            color: "rgba(237, 232, 227, 0.20)",
            marginLeft: "auto",
          }}
        >
          {run.id.slice(0, 8)}
        </span>
      </div>

      {/* User message snippet */}
      {run.user_message && (
        <div
          style={{
            fontFamily: "var(--font-jakarta)",
            fontSize: 13,
            color: "rgba(237, 232, 227, 0.40)",
            marginBottom: 12,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            maxWidth: "100%",
          }}
        >
          &quot;{run.user_message}&quot;
        </div>
      )}

      {/* Events timeline */}
      <div style={{ display: "flex", flexDirection: "column", gap: 2, paddingLeft: 8 }}>
        {events.map((evt) => {
          if (evt.event_type === "step_start" || evt.event_type === "step_end") {
            return <StepMarker key={evt.id} event={evt} />;
          }
          if (evt.event_type === "intent_classified") {
            const meta = evt.metadata as Record<string, unknown> | null;
            return (
              <div
                key={evt.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "5px 0",
                }}
              >
                <div
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: "rgba(198, 50, 45, 0.4)",
                    flexShrink: 0,
                  }}
                />
                <span
                  style={{
                    fontFamily: "var(--font-jakarta)",
                    fontSize: 13,
                    color: "rgba(237, 232, 227, 0.50)",
                  }}
                >
                  intent:
                </span>
                {meta?.intent && (
                  <IntentBadge intent={meta.intent as string} />
                )}
                {meta?.is_simple && (
                  <span
                    style={{
                      fontFamily: "var(--font-jakarta)",
                      fontSize: 12,
                      color: "rgba(237, 232, 227, 0.30)",
                    }}
                  >
                    (simple)
                  </span>
                )}
              </div>
            );
          }
          if (
            evt.event_type === "tool_invoked" ||
            evt.event_type === "tool_resolved"
          ) {
            return (
              <ToolCallCard
                key={evt.id}
                toolName={evt.tool_name ?? "unknown"}
                args={
                  evt.tool_args
                    ? JSON.stringify(evt.tool_args).slice(0, 60)
                    : undefined
                }
                state={evt.event_type === "tool_invoked" ? "invoked" : "resolved"}
                durationMs={evt.duration_ms ?? undefined}
                summary={
                  evt.tool_result
                    ? JSON.stringify(evt.tool_result).slice(0, 80)
                    : undefined
                }
              />
            );
          }
          if (evt.event_type === "error") {
            const meta = evt.metadata as Record<string, unknown> | null;
            return (
              <div
                key={evt.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "5px 0",
                }}
              >
                <div
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: "#ef4444",
                    flexShrink: 0,
                  }}
                />
                <span
                  style={{
                    fontFamily: "var(--font-jakarta)",
                    fontSize: 13,
                    color: "rgba(239,68,68,0.7)",
                  }}
                >
                  error: {(meta?.error as string)?.slice(0, 100) ?? "unknown"}
                </span>
              </div>
            );
          }
          // Generic event fallback
          return (
            <div
              key={evt.id}
              style={{
                fontFamily: "var(--font-jakarta)",
                fontSize: 12,
                color: "rgba(237, 232, 227, 0.25)",
                padding: "3px 0",
                paddingLeft: 16,
              }}
            >
              {evt.event_type}
            </div>
          );
        })}
        {events.length === 0 && run.status === "running" && (
          <div
            style={{
              fontFamily: "var(--font-jakarta)",
              fontSize: 13,
              color: "rgba(237, 232, 227, 0.20)",
              padding: "5px 0",
              paddingLeft: 16,
            }}
          >
            processing...
          </div>
        )}
      </div>
    </div>
  );
}

function ReasoningTimeline({ phone }: { phone: string }) {
  const runs = useAgentRuns(phone);
  const runIds = useMemo(() => runs.map((r) => r.id), [runs]);
  const events = useAgentEvents(runIds);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [runs, events]);

  // Group events by run
  const eventsByRun = useMemo(() => {
    const map = new Map<string, AgentEvent[]>();
    for (const evt of events) {
      const list = map.get(evt.run_id) ?? [];
      list.push(evt);
      map.set(evt.run_id, list);
    }
    return map;
  }, [events]);

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        height: "100%",
        overflow: "hidden",
      }}
    >
      {/* Panel header */}
      <div
        style={{
          padding: "18px 24px 14px",
          borderBottom: "1px solid rgba(255, 240, 220, 0.06)",
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontWeight: 500,
            fontSize: 14,
            color: "rgba(237, 232, 227, 0.55)",
          }}
        >
          agent reasoning
        </span>
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontWeight: 400,
            fontSize: 12,
            color: "rgba(237, 232, 227, 0.30)",
            marginLeft: 12,
          }}
        >
          {runs.length} runs
        </span>
      </div>

      {/* Runs */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          padding: "12px 16px",
        }}
      >
        {runs.length === 0 && (
          <div
            style={{
              padding: 32,
              textAlign: "center",
              fontFamily: "var(--font-jakarta)",
              fontSize: 14,
              color: "rgba(237, 232, 227, 0.25)",
            }}
          >
            waiting for agent runs...
          </div>
        )}
        {runs.map((run) => (
          <RunBlock
            key={run.id}
            run={run}
            events={eventsByRun.get(run.id) ?? []}
          />
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}

// ── Main page ────────────────────────────────────────────

export default function FeedPage() {
  const { phone, loading } = useUserPhone();
  const runs = useAgentRuns(phone);
  const hasActiveRun = runs.some((r) => r.status === "running");

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          fontFamily: "var(--font-jakarta)",
          fontSize: 14,
          color: "rgba(237, 232, 227, 0.30)",
        }}
      >
        connecting...
      </div>
    );
  }

  if (!phone) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          flexDirection: "column",
          gap: 10,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontWeight: 500,
            fontSize: 15,
            color: "rgba(237, 232, 227, 0.45)",
          }}
        >
          no phone number linked to your account
        </span>
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontSize: 13,
            color: "rgba(237, 232, 227, 0.25)",
          }}
        >
          complete onboarding to connect your number
        </span>
      </div>
    );
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "28px 40px 18px",
          display: "flex",
          alignItems: "center",
          gap: 10,
          flexShrink: 0,
          borderBottom: "1px solid rgba(255, 240, 220, 0.06)",
        }}
      >
        <PulseDot color="rgb(198, 50, 45)" size={7} pulse={hasActiveRun} />
        <h1
          style={{
            fontFamily: "var(--font-jakarta)",
            fontWeight: 600,
            fontSize: 20,
            color: "#ede8e3",
            margin: 0,
          }}
        >
          nerve center
        </h1>
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontWeight: 400,
            fontSize: 13,
            color: "rgba(237, 232, 227, 0.30)",
            marginLeft: 12,
          }}
        >
          {phone}
        </span>
      </div>

      {/* Split view */}
      <div
        style={{
          flex: 1,
          display: "flex",
          overflow: "hidden",
        }}
      >
        {/* Left: conversation */}
        <div
          style={{
            flex: 1,
            borderRight: "1px solid rgba(255, 240, 220, 0.06)",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          <MessageThread phone={phone} />
        </div>

        {/* Right: reasoning */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          <ReasoningTimeline phone={phone} />
        </div>
      </div>

      {/* Global keyframes */}
      <style jsx global>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes pulseDot {
          0%,
          100% {
            transform: scale(1);
            opacity: 1;
          }
          50% {
            transform: scale(1.4);
            opacity: 0.7;
          }
        }
      `}</style>
    </div>
  );
}
