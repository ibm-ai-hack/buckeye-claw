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
        background: "var(--color-surface-1)",
        borderTop: "1px solid var(--color-border)",
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
          background: "var(--color-scarlet)",
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
          fontSize: 16,
          letterSpacing: "0.5px",
          color: "var(--color-text-primary)",
          caretColor: "var(--color-scarlet)",
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
            filter: "drop-shadow(0 0 8px var(--color-scarlet-glow-strong))",
          }}
        >
          <path
            d="M2 8H14M14 8L9 3M14 8L9 13"
            style={{ stroke: "var(--color-scarlet)" }}
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
      <style jsx>{`
        input::placeholder {
          color: var(--color-text-placeholder);
          font-family: var(--font-space-mono);
        }
      `}</style>
    </div>
  );
}
