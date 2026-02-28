"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import PulseDot from "@/components/PulseDot";

interface MenuItem {
  name: string;
  items: string[];
}

interface DiningCardProps {
  hallName: string;
  mealPeriod: string;
  hours: string;
  isOpen: boolean;
  stations: MenuItem[];
}

export default function DiningCard({
  hallName,
  mealPeriod,
  hours,
  isOpen,
  stations,
}: DiningCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      style={{
        flex: "1 1 calc(50% - 8px)",
        minWidth: 280,
        background: "rgba(255,255,255,0.02)",
        border: "1px solid rgba(255,255,255,0.05)",
        borderRadius: 14,
        padding: 20,
        opacity: isOpen ? 1 : 0.5,
        transition: "opacity 0.2s ease",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              fontFamily: "var(--font-jakarta)",
              fontWeight: 300,
              fontSize: 18,
              color: "rgba(255,255,255,0.80)",
            }}
          >
            {hallName}
          </span>
          <PulseDot
            color={isOpen ? "#22c55e" : "rgba(255,255,255,0.15)"}
            size={6}
            pulse={isOpen}
          />
        </div>
      </div>

      <div
        style={{
          fontFamily: "var(--font-jakarta)",
          fontWeight: 400,
          fontSize: 13,
          color: "rgba(255,255,255,0.55)",
          marginBottom: 4,
        }}
      >
        {mealPeriod}
      </div>
      <div
        style={{
          fontFamily: "var(--font-jakarta)",
          fontWeight: 400,
          fontSize: 13,
          color: "rgba(255,255,255,0.45)",
          marginBottom: 14,
        }}
      >
        {hours}
      </div>

      {isOpen && (
        <button
          onClick={() => setExpanded(!expanded)}
          style={{
            fontFamily: "var(--font-jakarta)",
            fontWeight: 400,
            fontSize: 13,
            color: expanded ? "rgba(255,255,255,0.60)" : "rgba(255,255,255,0.60)",
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: 0,
            transition: "color 0.15s ease",
            textDecoration: expanded ? "none" : "underline",
            textUnderlineOffset: 3,
            textDecorationColor: "rgba(255,255,255,0.10)",
          }}
        >
          {expanded ? "hide menu" : "view menu"}
        </button>
      )}

      <AnimatePresence>
        {expanded && (
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
                marginTop: 14,
                display: "flex",
                gap: 10,
                overflowX: "auto",
                paddingBottom: 4,
              }}
            >
              {stations.map((station, i) => (
                <div
                  key={station.name}
                  style={{
                    minWidth: 160,
                    width: 160,
                    padding: 14,
                    background: "rgba(255,255,255,0.03)",
                    border: "1px solid rgba(255,255,255,0.04)",
                    borderRadius: 10,
                    flexShrink: 0,
                    animation: `fadeInUp 300ms ease-out ${i * 60}ms forwards`,
                    opacity: 0,
                  }}
                >
                  <div
                    style={{
                      fontFamily: "var(--font-jakarta)",
                      fontWeight: 300,
                      fontSize: 15,
                      color: "rgba(255,255,255,0.80)",
                      marginBottom: 8,
                    }}
                  >
                    {station.name}
                  </div>
                  {station.items.map((item) => (
                    <div
                      key={item}
                      style={{
                        fontFamily: "var(--font-jakarta)",
                        fontWeight: 400,
                        fontSize: 12,
                        color: "rgba(255,255,255,0.50)",
                        lineHeight: 1.8,
                      }}
                    >
                      {item}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
