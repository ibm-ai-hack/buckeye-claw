"use client";

import { useState, useRef, useCallback } from "react";

interface InputBarProps {
  placeholder?: string;
  onSubmit: (message: string) => void;
}

export default function InputBar({
  placeholder = "ask buckeye...",
  onSubmit,
}: InputBarProps) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
    setValue("");
  }, [value, onSubmit]);

  return (
    <div
      style={{
        position: "sticky",
        bottom: 0,
        width: "100%",
        height: 56,
        background: "rgba(255,255,255,0.02)",
        borderTop: "1px solid rgba(255,255,255,0.04)",
        display: "flex",
        alignItems: "center",
        padding: "0 24px",
        gap: 12,
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        zIndex: 20,
      }}
    >
      <div
        style={{
          width: 2,
          height: 18,
          background: "rgb(198,40,40)",
          borderRadius: 1,
          animation: "blinkCursor 1s step-end infinite",
          flexShrink: 0,
        }}
      />
      <input
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") handleSubmit();
        }}
        placeholder={placeholder}
        autoComplete="off"
        autoCorrect="off"
        spellCheck={false}
        style={{
          flex: 1,
          background: "transparent",
          border: "none",
          outline: "none",
          fontFamily: "var(--font-space-mono)",
          fontWeight: 400,
          fontSize: 14,
          letterSpacing: "0.5px",
          color: "rgba(255,255,255,0.85)",
          caretColor: "rgb(198,40,40)",
        }}
      />
      <button
        onClick={handleSubmit}
        style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          border: "none",
          background: "transparent",
          cursor: value.trim() ? "pointer" : "default",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          opacity: value.trim() ? 1 : 0,
          transition: "opacity 0.2s ease",
          flexShrink: 0,
        }}
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          style={{
            filter: "drop-shadow(0 0 8px rgba(198,40,40,0.4))",
          }}
        >
          <path
            d="M2 8H14M14 8L9 3M14 8L9 13"
            stroke="rgb(198,40,40)"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
      <style jsx>{`
        @keyframes blinkCursor {
          0%,
          100% {
            opacity: 1;
          }
          50% {
            opacity: 0;
          }
        }
        input::placeholder {
          color: rgba(255, 255, 255, 0.15);
          font-family: var(--font-space-mono);
        }
      `}</style>
    </div>
  );
}
