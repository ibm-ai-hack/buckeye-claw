"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ScanLine from "./ScanLine";

export type ToolCallState = "invoked" | "resolved" | "collapsed";

interface ToolCallCardProps {
  toolName: string;
  args?: string;
  state: ToolCallState;
  durationMs?: number;
  summary?: string;
  children?: React.ReactNode;
  onToggle?: () => void;
}

export default function ToolCallCard({
  toolName,
  args,
  state,
  durationMs,
  summary,
  children,
  onToggle,
}: ToolCallCardProps) {
  const [manualExpanded, setManualExpanded] = useState(false);

  const isExpanded = state === "resolved" || manualExpanded;
  const showScanLine = state === "invoked";

  const label = `--- ${toolName}${args ? ` ${args}` : ""} ---`;

  return (
    <div
      style={{
        width: "100%",
        padding: "12px 24px",
        borderLeft: "2px solid rgb(198,40,40)",
        animation: "fadeInUp 300ms ease-out forwards",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-space-mono)",
            fontWeight: 400,
            fontSize: 12,
            color: "rgba(255,255,255,0.40)",
            letterSpacing: "1px",
          }}
        >
          {label}
        </span>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          {durationMs !== undefined && state !== "invoked" && (
            <span
              style={{
                fontFamily: "var(--font-space-mono)",
                fontWeight: 400,
                fontSize: 10,
                color: "rgba(255,255,255,0.15)",
                letterSpacing: "1px",
              }}
            >
              {(durationMs / 1000).toFixed(1)}s
            </span>
          )}
          {state === "collapsed" && (
            <button
              onClick={() => {
                setManualExpanded(true);
                onToggle?.();
              }}
              style={{
                fontFamily: "var(--font-space-mono)",
                fontWeight: 400,
                fontSize: 10,
                color: "rgba(255,255,255,0.15)",
                letterSpacing: "1px",
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: "4px 8px",
                borderRadius: 4,
                transition: "color 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "rgba(255,255,255,0.40)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "rgba(255,255,255,0.15)";
              }}
            >
              expand
            </button>
          )}
        </div>
      </div>

      {/* Summary line when collapsed */}
      {state === "collapsed" && !manualExpanded && summary && (
        <span
          style={{
            fontFamily: "var(--font-space-mono)",
            fontWeight: 400,
            fontSize: 11,
            color: "rgba(255,255,255,0.25)",
            marginTop: 4,
            display: "block",
          }}
        >
          {summary}
        </span>
      )}

      {/* Scan line when invoked */}
      {showScanLine && <ScanLine />}

      {/* Rich content when resolved/expanded */}
      <AnimatePresence>
        {isExpanded && children && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{
              height: { duration: 0.3, ease: [0.16, 1, 0.3, 1] },
              opacity: { duration: 0.2 },
            }}
            style={{ overflow: "hidden" }}
          >
            <div
              style={{
                marginTop: 12,
                padding: 16,
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.04)",
                borderRadius: 12,
              }}
            >
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
