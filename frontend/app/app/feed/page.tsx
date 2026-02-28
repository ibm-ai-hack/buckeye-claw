"use client";

import { useRef, useEffect, useMemo, useState } from "react";
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
          padding: "14px 20px 12px",
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
          gap: 6,
          padding: "16px 0",
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
        fontSize: 11,
        fontWeight: 500,
        color: "rgb(198, 50, 45)",
        background: "rgba(198, 50, 45, 0.10)",
        border: "1px solid rgba(198, 50, 45, 0.18)",
        borderRadius: 6,
        padding: "2px 8px",
      }}
    >
      {intent}
    </span>
  );
}

function StepLabel({ name, description }: { name: string; description?: string }) {
  const stepDescriptions: Record<string, string> = {
    claude_intake: "classifying user intent and extracting parameters",
    claude_plan_execute: "selecting tools and executing the plan",
    granite_format: "formatting response for text message delivery",
  };

  return (
    <div
      style={{
        fontFamily: "var(--font-jakarta)",
        fontSize: 12,
        color: "rgba(237, 232, 227, 0.40)",
        fontStyle: "italic",
        paddingLeft: 16,
        padding: "2px 0 2px 16px",
      }}
    >
      {description ?? stepDescriptions[name] ?? name}
    </div>
  );
}

function ThinkingIndicator() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "6px 0 6px 16px",
        animation: "fadeInUp 300ms ease-out forwards",
      }}
    >
      <div style={{ display: "flex", gap: 3 }}>
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              width: 4,
              height: 4,
              borderRadius: "50%",
              background: "rgb(198, 50, 45)",
              animation: `subtleBreathe 1.4s ease-in-out ${i * 0.2}s infinite`,
            }}
          />
        ))}
      </div>
      <span
        style={{
          fontFamily: "var(--font-jakarta)",
          fontSize: 12,
          color: "rgba(237, 232, 227, 0.35)",
          fontStyle: "italic",
        }}
      >
        thinking...
      </span>
    </div>
  );
}

function ParamsBlock({ params }: { params: Record<string, unknown> }) {
  const entries = Object.entries(params).filter(([, v]) => v != null && v !== "");
  if (entries.length === 0) return null;

  return (
    <div
      style={{
        margin: "4px 0 4px 16px",
        padding: "8px 12px",
        background: "rgba(198, 50, 45, 0.04)",
        border: "1px solid rgba(198, 50, 45, 0.08)",
        borderRadius: 8,
        animation: "fadeInUp 200ms ease-out forwards",
      }}
    >
      <div
        style={{
          fontFamily: "var(--font-jakarta)",
          fontSize: 11,
          fontWeight: 500,
          color: "rgba(237, 232, 227, 0.35)",
          marginBottom: 4,
          letterSpacing: "0.5px",
          textTransform: "uppercase",
        }}
      >
        extracted parameters
      </div>
      {entries.map(([key, val]) => (
        <div
          key={key}
          style={{
            fontFamily: "var(--font-jakarta)",
            fontSize: 12,
            color: "rgba(237, 232, 227, 0.50)",
            padding: "1px 0",
          }}
        >
          <span style={{ color: "rgba(198, 50, 45, 0.6)" }}>{key}:</span>{" "}
          {typeof val === "object" ? JSON.stringify(val) : String(val)}
        </div>
      ))}
    </div>
  );
}

function FinalResponseBlock({ response }: { response: string }) {
  const [expanded, setExpanded] = useState(false);
  const isLong = response.length > 200;
  const displayText = !expanded && isLong ? response.slice(0, 200) + "..." : response;

  return (
    <div
      style={{
        margin: "8px 0 4px 0",
        padding: "10px 14px",
        background: "rgba(34, 197, 94, 0.04)",
        border: "1px solid rgba(34, 197, 94, 0.10)",
        borderRadius: 8,
        animation: "fadeInUp 300ms ease-out forwards",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          marginBottom: 6,
        }}
      >
        <div
          style={{
            width: 5,
            height: 5,
            borderRadius: "50%",
            background: "#22c55e",
          }}
        />
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontSize: 11,
            fontWeight: 500,
            color: "rgba(34, 197, 94, 0.6)",
            letterSpacing: "0.5px",
            textTransform: "uppercase",
          }}
        >
          agent response
        </span>
      </div>
      <div
        style={{
          fontFamily: "var(--font-jakarta)",
          fontSize: 13,
          color: "rgba(237, 232, 227, 0.55)",
          lineHeight: 1.5,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {displayText}
      </div>
      {isLong && (
        <button
          onClick={() => setExpanded(!expanded)}
          style={{
            fontFamily: "var(--font-jakarta)",
            fontSize: 11,
            color: "rgba(34, 197, 94, 0.5)",
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: "4px 0 0",
            transition: "color 0.15s ease",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.color = "rgba(34, 197, 94, 0.8)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = "rgba(34, 197, 94, 0.5)"; }}
        >
          {expanded ? "show less" : "show full response"}
        </button>
      )}
    </div>
  );
}

function StepMarker({
  event,
}: {
  event: AgentEvent;
}) {
  const isEnd = event.event_type === "step_end";
  const duration = event.duration_ms;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "4px 0",
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

  // Find the intent_classified event to get params
  const intentEvent = events.find((e) => e.event_type === "intent_classified");
  const intentMeta = intentEvent?.metadata as Record<string, unknown> | null;
  const extractedParams = intentMeta?.params as Record<string, unknown> | null;

  // Check if agent is currently in a step (started but not ended)
  const activeSteps = new Set<string>();
  for (const evt of events) {
    if (evt.event_type === "step_start" && evt.step) activeSteps.add(evt.step);
    if (evt.event_type === "step_end" && evt.step) activeSteps.delete(evt.step);
  }
  const isThinking = run.status === "running" && activeSteps.size > 0;

  return (
    <div
      style={{
        padding: "14px 14px",
        marginBottom: 6,
        background: run.status === "running"
          ? "rgba(198, 50, 45, 0.03)"
          : "rgba(255, 240, 220, 0.02)",
        borderRadius: 10,
        border: run.status === "running"
          ? "1px solid rgba(198, 50, 45, 0.08)"
          : "1px solid rgba(255, 240, 220, 0.04)",
        animation: "fadeInUp 300ms ease-out forwards",
        transition: "border-color 0.3s ease, background 0.3s ease",
      }}
    >
      {/* Run header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 8,
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
            color: run.status === "running"
              ? "rgba(237, 232, 227, 0.75)"
              : "rgba(237, 232, 227, 0.60)",
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
            color: "rgba(237, 232, 227, 0.45)",
            marginBottom: 8,
            padding: "6px 10px",
            background: "rgba(255, 240, 220, 0.03)",
            borderRadius: 6,
            borderLeft: "2px solid rgba(237, 232, 227, 0.10)",
          }}
        >
          &quot;{run.user_message}&quot;
        </div>
      )}

      {/* Events timeline */}
      <div style={{ display: "flex", flexDirection: "column", gap: 1, paddingLeft: 4 }}>
        {events.map((evt) => {
          if (evt.event_type === "step_start") {
            return (
              <div key={evt.id}>
                <StepMarker event={evt} />
                <StepLabel name={evt.step ?? ""} />
              </div>
            );
          }
          if (evt.event_type === "step_end") {
            return <StepMarker key={evt.id} event={evt} />;
          }
          if (evt.event_type === "intent_classified") {
            const meta = evt.metadata as Record<string, unknown> | null;
            return (
              <div key={evt.id}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "4px 0",
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
                    classified as
                  </span>
                  {meta?.intent ? (
                    <IntentBadge intent={meta.intent as string} />
                  ) : null}
                  {meta?.is_simple ? (
                    <span
                      style={{
                        fontFamily: "var(--font-jakarta)",
                        fontSize: 11,
                        color: "rgba(237, 232, 227, 0.30)",
                        background: "rgba(237, 232, 227, 0.05)",
                        padding: "2px 6px",
                        borderRadius: 4,
                      }}
                    >
                      simple query
                    </span>
                  ) : null}
                </div>
                {meta?.params && typeof meta.params === "object" && Object.keys(meta.params as Record<string, unknown>).length > 0 ? (
                  <ParamsBlock params={meta.params as Record<string, unknown>} />
                ) : null}
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
                    ? JSON.stringify(evt.tool_args).slice(0, 80)
                    : undefined
                }
                state={evt.event_type === "tool_invoked" ? "invoked" : "resolved"}
                durationMs={evt.duration_ms ?? undefined}
                summary={
                  evt.tool_result
                    ? JSON.stringify(evt.tool_result).slice(0, 120)
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
                  alignItems: "flex-start",
                  gap: 8,
                  padding: "6px 0",
                  animation: "fadeInUp 200ms ease-out forwards",
                }}
              >
                <div
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: "#ef4444",
                    flexShrink: 0,
                    marginTop: 5,
                  }}
                />
                <div>
                  <span
                    style={{
                      fontFamily: "var(--font-jakarta)",
                      fontSize: 12,
                      fontWeight: 500,
                      color: "rgba(239,68,68,0.7)",
                      display: "block",
                    }}
                  >
                    error encountered
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-jakarta)",
                      fontSize: 12,
                      color: "rgba(239,68,68,0.45)",
                      wordBreak: "break-word",
                    }}
                  >
                    {(meta?.error as string)?.slice(0, 200) ?? "unknown error"}
                  </span>
                </div>
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
                padding: "2px 0",
                paddingLeft: 16,
              }}
            >
              {evt.event_type}
            </div>
          );
        })}
        {isThinking && <ThinkingIndicator />}
        {events.length === 0 && run.status === "running" && (
          <ThinkingIndicator />
        )}
      </div>

      {/* Final response */}
      {run.final_response && run.status === "completed" && (
        <FinalResponseBlock response={run.final_response} />
      )}
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
          padding: "14px 20px 12px",
          borderBottom: "1px solid rgba(255, 240, 220, 0.06)",
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(198, 50, 45, 0.5)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z" />
          <path d="M12 6v6l4 2" />
        </svg>
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
            marginLeft: 4,
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
          padding: "8px 12px",
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
          padding: "16px 28px 12px",
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
            marginLeft: 8,
          }}
        >
          {phone}
        </span>
        {hasActiveRun && (
          <span
            style={{
              fontFamily: "var(--font-jakarta)",
              fontSize: 11,
              fontWeight: 500,
              color: "rgb(198, 50, 45)",
              background: "rgba(198, 50, 45, 0.10)",
              padding: "3px 10px",
              borderRadius: 12,
              marginLeft: "auto",
              animation: "subtleBreathe 2s ease-in-out infinite",
            }}
          >
            agent active
          </span>
        )}
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
        @keyframes subtleBreathe {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 1; }
        }
      `}</style>
    </div>
  );
}
