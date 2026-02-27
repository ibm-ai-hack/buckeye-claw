"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import SMSMessageRow from "@/components/SMSMessageRow";
import ToolCallCard from "@/components/ToolCallCard";
import type { ToolCallState } from "@/components/ToolCallCard";
import InputBar from "@/components/InputBar";
import PulseDot from "@/components/PulseDot";

// ── Types ───────────────────────────────────────────────

interface SMSItem {
  type: "sms";
  id: string;
  text: string;
  role: "student" | "agent";
  timestamp: string;
}

interface ToolCallItem {
  type: "tool_call";
  id: string;
  toolName: string;
  args?: string;
  state: ToolCallState;
  durationMs?: number;
  summary?: string;
  result?: Record<string, unknown>;
}

type FeedItem = SMSItem | ToolCallItem;

// ── Demo data ───────────────────────────────────────────

const DEMO_FEED: FeedItem[] = [
  {
    type: "sms",
    id: "1",
    text: "what's for lunch at scott?",
    role: "student",
    timestamp: "12:34 pm",
  },
  {
    type: "tool_call",
    id: "2",
    toolName: "get_dining_menu",
    args: "scott",
    state: "resolved",
    durationMs: 820,
    summary: "6 stations serving lunch",
    result: {
      hall: "scott traditions",
      meal: "lunch",
      stations: [
        { name: "grilled chicken", items: ["breast w/ herb butter", "thigh w/ bbq glaze"] },
        { name: "pasta bar", items: ["marinara", "alfredo", "pesto"] },
        { name: "salad bar", items: ["caesar", "garden", "greek"] },
        { name: "soup station", items: ["tomato bisque", "chicken noodle"] },
        { name: "pizza", items: ["cheese", "pepperoni", "veggie"] },
        { name: "desserts", items: ["brownies", "cookies", "fruit"] },
      ],
    },
  },
  {
    type: "sms",
    id: "3",
    text: "scott is serving grilled chicken breast with herb butter, pasta bar with marinara, alfredo, and pesto sauces, caesar and garden salads, tomato bisque soup, cheese and pepperoni pizza, plus brownies and cookies for dessert.",
    role: "agent",
    timestamp: "12:34 pm",
  },
  {
    type: "sms",
    id: "4",
    text: "where's the campus connector right now?",
    role: "student",
    timestamp: "12:36 pm",
  },
  {
    type: "tool_call",
    id: "5",
    toolName: "get_bus_vehicles",
    args: "CC",
    state: "resolved",
    durationMs: 640,
    summary: "3 buses on route",
    result: {
      route: "campus connector",
      vehicles: [
        { id: "bus 1", destination: "ohio union", eta: "3 min" },
        { id: "bus 2", destination: "18th & high", eta: "7 min" },
        { id: "bus 3", destination: "west campus", eta: "12 min" },
      ],
    },
  },
  {
    type: "sms",
    id: "6",
    text: "there are 3 campus connector buses running right now. the nearest one is heading to ohio union with an eta of about 3 minutes.",
    role: "agent",
    timestamp: "12:36 pm",
  },
  {
    type: "sms",
    id: "7",
    text: "what's my grade in cse 2421?",
    role: "student",
    timestamp: "12:38 pm",
  },
  {
    type: "tool_call",
    id: "8",
    toolName: "get_course_grades",
    args: "CSE 2421",
    state: "resolved",
    durationMs: 1240,
    summary: "92% A-",
    result: {
      course: "CSE 2421",
      title: "Systems I",
      percentage: 92,
      letter: "A-",
    },
  },
  {
    type: "sms",
    id: "9",
    text: "you have a 92% (A-) in CSE 2421 — systems I: introduction to low-level programming.",
    role: "agent",
    timestamp: "12:38 pm",
  },
];

// ── Demo visualizations ─────────────────────────────────

function DiningResult({ data }: { data: Record<string, unknown> }) {
  const stations = data.stations as { name: string; items: string[] }[];
  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 12,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-outfit)",
            fontWeight: 200,
            fontSize: 16,
            color: "rgba(255,255,255,0.70)",
            letterSpacing: "0.1em",
          }}
        >
          {data.hall as string} — {data.meal as string}
        </span>
        <PulseDot color="#22c55e" size={6} />
      </div>
      <div
        style={{
          display: "flex",
          gap: 10,
          overflowX: "auto",
          paddingBottom: 4,
          scrollSnapType: "x mandatory",
        }}
      >
        {stations.map((station, i) => (
          <div
            key={station.name}
            style={{
              minWidth: 160,
              width: 160,
              height: 140,
              padding: 14,
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.04)",
              borderRadius: 10,
              flexShrink: 0,
              scrollSnapAlign: "start",
              animation: `fadeInUp 300ms ease-out ${i * 60}ms forwards`,
              opacity: 0,
            }}
          >
            <div
              style={{
                fontFamily: "var(--font-outfit)",
                fontWeight: 300,
                fontSize: 13,
                color: "rgba(255,255,255,0.65)",
                marginBottom: 8,
              }}
            >
              {station.name}
            </div>
            {station.items.map((item) => (
              <div
                key={item}
                style={{
                  fontFamily: "var(--font-space-mono)",
                  fontWeight: 400,
                  fontSize: 10,
                  color: "rgba(255,255,255,0.30)",
                  lineHeight: 1.8,
                }}
              >
                {item}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

function BusResult({ data }: { data: Record<string, unknown> }) {
  const vehicles = data.vehicles as { id: string; destination: string; eta: string }[];
  return (
    <div>
      <div
        style={{
          fontFamily: "var(--font-outfit)",
          fontWeight: 300,
          fontSize: 14,
          color: "rgba(255,255,255,0.60)",
          marginBottom: 12,
        }}
      >
        {data.route as string}
      </div>
      {vehicles.map((v, i) => (
        <div
          key={v.id}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            height: 36,
            borderBottom:
              i < vehicles.length - 1
                ? "1px solid rgba(255,255,255,0.03)"
                : "none",
            animation: `fadeInUp 200ms ease-out ${i * 80}ms forwards`,
            opacity: 0,
          }}
        >
          <PulseDot color="rgb(198,40,40)" size={6} pulse />
          <span
            style={{
              fontFamily: "var(--font-space-mono)",
              fontWeight: 400,
              fontSize: 11,
              color: "rgba(255,255,255,0.35)",
              width: 60,
            }}
          >
            {v.id}
          </span>
          <span
            style={{
              fontFamily: "var(--font-space-mono)",
              fontWeight: 400,
              fontSize: 11,
              color: "rgba(255,255,255,0.35)",
              flex: 1,
            }}
          >
            → {v.destination}
          </span>
          <span
            style={{
              fontFamily: "var(--font-space-mono)",
              fontWeight: 400,
              fontSize: 12,
              color:
                parseInt(v.eta) <= 5
                  ? "rgb(198,40,40)"
                  : "rgba(255,255,255,0.50)",
              letterSpacing: "0.5px",
            }}
          >
            eta {v.eta}
          </span>
        </div>
      ))}
    </div>
  );
}

function GradeResult({ data }: { data: Record<string, unknown> }) {
  const pct = data.percentage as number;
  const barColor =
    pct >= 85
      ? "#22c55e"
      : pct >= 70
        ? "rgb(220,170,50)"
        : pct >= 60
          ? "#eab308"
          : "#ef4444";

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          height: 40,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-space-mono)",
            fontWeight: 400,
            fontSize: 12,
            color: "rgba(255,255,255,0.55)",
            width: 120,
          }}
        >
          {data.course as string}
        </span>
        <div
          style={{
            flex: 1,
            height: 8,
            borderRadius: 4,
            background: "rgba(255,255,255,0.04)",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${pct}%`,
              height: "100%",
              borderRadius: 4,
              background: barColor,
              animation: "gradeBarFill 600ms cubic-bezier(0.16,1,0.3,1) forwards",
            }}
          />
        </div>
        <span
          style={{
            fontFamily: "var(--font-space-mono)",
            fontWeight: 400,
            fontSize: 12,
            color: "rgba(255,255,255,0.70)",
            width: 36,
            textAlign: "right",
          }}
        >
          {pct}%
        </span>
        <span
          style={{
            fontFamily: "var(--font-outfit)",
            fontWeight: 300,
            fontSize: 13,
            color: "rgba(255,255,255,0.50)",
            width: 28,
          }}
        >
          {data.letter as string}
        </span>
      </div>
    </div>
  );
}

function getToolVisualization(toolName: string, result?: Record<string, unknown>) {
  if (!result) return null;
  if (toolName === "get_dining_menu") return <DiningResult data={result} />;
  if (toolName === "get_bus_vehicles") return <BusResult data={result} />;
  if (toolName === "get_course_grades") return <GradeResult data={result} />;
  return null;
}

// ── Nerve Center Page ───────────────────────────────────

export default function FeedPage() {
  const [feed, setFeed] = useState<FeedItem[]>(DEMO_FEED);
  const [isProcessing, setIsProcessing] = useState(false);
  const feedEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    feedEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [feed, scrollToBottom]);

  const handleSubmit = useCallback(
    (message: string) => {
      const now = new Date();
      const timeStr = now
        .toLocaleTimeString("en-US", {
          hour: "numeric",
          minute: "2-digit",
          hour12: true,
        })
        .toLowerCase();

      // Add student message
      const studentMsg: SMSItem = {
        type: "sms",
        id: `msg-${Date.now()}`,
        text: message,
        role: "student",
        timestamp: timeStr,
      };
      setFeed((prev) => [...prev, studentMsg]);
      setIsProcessing(true);

      // Simulate tool call invocation
      const toolId = `tool-${Date.now()}`;
      setTimeout(() => {
        const toolCall: ToolCallItem = {
          type: "tool_call",
          id: toolId,
          toolName: "search_classes",
          args: message.slice(0, 30),
          state: "invoked",
        };
        setFeed((prev) => [...prev, toolCall]);
      }, 400);

      // Simulate tool call resolution
      setTimeout(() => {
        setFeed((prev) =>
          prev.map((item) =>
            item.id === toolId
              ? {
                  ...item,
                  state: "resolved" as ToolCallState,
                  durationMs: 920,
                  summary: "results found",
                }
              : item
          )
        );
      }, 2200);

      // Simulate agent response
      setTimeout(() => {
        const agentMsg: SMSItem = {
          type: "sms",
          id: `resp-${Date.now()}`,
          text: `i found some results for "${message}". this is a demo response — connect the backend to see real data.`,
          role: "agent",
          timestamp: timeStr,
        };
        setFeed((prev) => [...prev, agentMsg]);
        setIsProcessing(false);
      }, 2800);
    },
    []
  );

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
          padding: "24px 32px 16px",
          display: "flex",
          alignItems: "center",
          gap: 8,
          flexShrink: 0,
        }}
      >
        <PulseDot color="rgb(198,40,40)" size={6} pulse={isProcessing} />
        <h1
          style={{
            fontFamily: "var(--font-outfit)",
            fontWeight: 200,
            fontSize: 14,
            letterSpacing: "0.25em",
            color: "rgba(255,255,255,0.70)",
            textTransform: "lowercase",
            margin: 0,
          }}
        >
          nerve center
        </h1>
      </div>

      {/* Feed */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            width: "100%",
            maxWidth: 720,
            display: "flex",
            flexDirection: "column",
            gap: 2,
            paddingBottom: 16,
          }}
        >
          {feed.map((item) => {
            if (item.type === "sms") {
              return (
                <SMSMessageRow
                  key={item.id}
                  text={item.text}
                  role={item.role}
                  timestamp={item.timestamp}
                />
              );
            }
            if (item.type === "tool_call") {
              return (
                <ToolCallCard
                  key={item.id}
                  toolName={item.toolName}
                  args={item.args}
                  state={item.state}
                  durationMs={item.durationMs}
                  summary={item.summary}
                >
                  {getToolVisualization(item.toolName, item.result)}
                </ToolCallCard>
              );
            }
            return null;
          })}
          <div ref={feedEndRef} />
        </div>
      </div>

      {/* Input */}
      <InputBar onSubmit={handleSubmit} />

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
        @keyframes gradeBarFill {
          from {
            width: 0;
          }
        }

        /* Hide scrollbar but keep scrollable */
        ::-webkit-scrollbar {
          width: 4px;
        }
        ::-webkit-scrollbar-track {
          background: transparent;
        }
        ::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.06);
          border-radius: 2px;
        }
        ::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.12);
        }
      `}</style>
    </div>
  );
}
