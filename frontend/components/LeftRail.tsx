"use client";

import { useState, useRef, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

interface NavItem {
  path: string;
  icon: React.ReactNode;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  {
    path: "/app/feed",
    label: "feed",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="2" />
        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
      </svg>
    ),
  },
  {
    path: "/app/academics",
    label: "academics",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
        <path d="M6 12v5c0 1.1 2.7 3 6 3s6-1.9 6-3v-5" />
      </svg>
    ),
  },
  {
    path: "/app/campus",
    label: "campus",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="4" y="2" width="16" height="20" rx="2" />
        <path d="M9 22v-4h6v4M8 6h.01M16 6h.01M12 6h.01M12 10h.01M8 10h.01M16 10h.01M12 14h.01M8 14h.01M16 14h.01" />
      </svg>
    ),
  },
  {
    path: "/app/connect",
    label: "connect",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" />
        <line x1="8" y1="21" x2="16" y2="21" />
        <line x1="12" y1="17" x2="12" y2="21" />
      </svg>
    ),
  },
  {
    path: "/app/memory",
    label: "memory",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="2" />
        <circle cx="4"  cy="6"  r="1.5" />
        <circle cx="20" cy="6"  r="1.5" />
        <circle cx="4"  cy="18" r="1.5" />
        <circle cx="20" cy="18" r="1.5" />
        <line x1="5.5"  y1="6.8"  x2="10.2" y2="11" />
        <line x1="18.5" y1="6.8"  x2="13.8" y2="11" />
        <line x1="5.5"  y1="17.2" x2="10.2" y2="13" />
        <line x1="18.5" y1="17.2" x2="13.8" y2="13" />
      </svg>
    ),
  },
];

export default function LeftRail() {
  const pathname = usePathname();
  const router = useRouter();
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <nav
      style={{
        width: 220,
        height: "100vh",
        position: "fixed",
        top: 0,
        left: 0,
        background: "#1a1715",
        borderRight: "1px solid rgba(255, 240, 220, 0.06)",
        display: "flex",
        flexDirection: "column",
        padding: "20px 14px 16px",
        zIndex: 50,
        overflowY: "auto",
        overflowX: "hidden",
      }}
    >
      {/* Logo + brand */}
      <div
        onClick={() => router.push("/")}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          cursor: "pointer",
          padding: "6px 10px",
          marginBottom: 24,
          borderRadius: 12,
          transition: "background 0.2s ease",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(255, 240, 220, 0.04)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "transparent";
        }}
      >
        <img
          src="/chud.png"
          alt="buckeyeclaw"
          style={{
            width: 72,
            height: 72,
            borderRadius: 14,
            objectFit: "contain",
          }}
        />
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontWeight: 600,
            fontSize: 18,
            color: "#ede8e3",
            letterSpacing: "-0.3px",
          }}
        >
          BuckeyeClaw
        </span>
      </div>

      {/* Nav items */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 2,
          flex: 1,
        }}
      >
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.path || pathname.startsWith(item.path + "/");
          return (
            <button
              key={item.path}
              className="nav-item"
              onClick={() => router.push(item.path)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "11px 14px",
                background: isActive
                  ? "rgba(198, 50, 45, 0.10)"
                  : "transparent",
                border: "none",
                borderRadius: 10,
                cursor: "pointer",
                transition: "all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)",
                color: isActive
                  ? "#ede8e3"
                  : "rgba(237, 232, 227, 0.50)",
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = "rgba(255, 240, 220, 0.06)";
                  e.currentTarget.style.color = "rgba(237, 232, 227, 0.85)";
                }
                e.currentTarget.style.transform = "translateX(4px) scale(1.02)";
                const icon = e.currentTarget.querySelector(".nav-icon") as HTMLElement;
                if (icon) icon.style.transform = "rotate(-8deg) scale(1.15)";
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = "rgba(237, 232, 227, 0.50)";
                }
                e.currentTarget.style.transform = "translateX(0) scale(1)";
                const icon = e.currentTarget.querySelector(".nav-icon") as HTMLElement;
                if (icon) icon.style.transform = "rotate(0deg) scale(1)";
              }}
            >
              <span className="nav-icon" style={{
                display: "flex",
                alignItems: "center",
                transition: "transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)",
              }}>
                {item.icon}
              </span>
              <span
                style={{
                  fontFamily: "var(--font-jakarta)",
                  fontWeight: isActive ? 500 : 400,
                  fontSize: 14,
                  letterSpacing: "0.1px",
                }}
              >
                {item.label}
              </span>
              {isActive && (
                <div
                  style={{
                    width: 5,
                    height: 5,
                    borderRadius: "50%",
                    background: "rgb(198, 50, 45)",
                    marginLeft: "auto",
                    boxShadow: "0 0 8px rgba(198, 50, 45, 0.4)",
                    animation: "pulseDot 2s ease-in-out infinite",
                  }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom user section */}
      <div
        ref={profileRef}
        style={{
          borderTop: "1px solid rgba(255, 240, 220, 0.06)",
          paddingTop: 14,
          marginTop: 8,
          position: "relative",
        }}
      >
        {/* Dropdown */}
        {profileOpen && (
          <div
            style={{
              position: "absolute",
              bottom: "calc(100% + 6px)",
              left: 0,
              right: 0,
              background: "#242120",
              border: "1px solid rgba(255, 240, 220, 0.08)",
              borderRadius: 10,
              padding: 4,
              boxShadow: "0 8px 24px rgba(0, 0, 0, 0.4)",
              animation: "dropdownIn 0.15s ease-out",
            }}
          >
            <button
              onClick={async () => {
                const supabase = createClient();
                await supabase.auth.signOut();
                router.push("/");
              }}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "8px 12px",
                background: "transparent",
                border: "none",
                borderRadius: 8,
                cursor: "pointer",
                transition: "all 0.15s ease",
                color: "rgba(237, 232, 227, 0.5)",
                fontFamily: "var(--font-jakarta)",
                fontSize: 13,
                width: "100%",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(239, 68, 68, 0.10)";
                e.currentTarget.style.color = "rgba(239, 68, 68, 0.8)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "transparent";
                e.currentTarget.style.color = "rgba(237, 232, 227, 0.5)";
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
              log out
            </button>
          </div>
        )}

        {/* Profile button */}
        <div
          onClick={() => setProfileOpen((prev) => !prev)}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "8px 10px",
            borderRadius: 10,
            cursor: "pointer",
            transition: "background 0.2s ease",
            background: profileOpen ? "rgba(255, 240, 220, 0.04)" : "transparent",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(255, 240, 220, 0.04)";
          }}
          onMouseLeave={(e) => {
            if (!profileOpen) e.currentTarget.style.background = "transparent";
          }}
        >
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: "50%",
              background: "linear-gradient(135deg, rgb(198, 50, 45), rgb(168, 35, 35))",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-jakarta)",
                fontWeight: 500,
                fontSize: 13,
                color: "white",
              }}
            >
              bu
            </span>
          </div>
          <div style={{ flex: 1 }}>
            <div
              style={{
                fontFamily: "var(--font-jakarta)",
                fontWeight: 500,
                fontSize: 13,
                color: "#ede8e3",
              }}
            >
              buckeye
            </div>
            <div
              style={{
                fontFamily: "var(--font-jakarta)",
                fontWeight: 400,
                fontSize: 11,
                color: "rgba(237, 232, 227, 0.35)",
              }}
            >
              student
            </div>
          </div>
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="rgba(237, 232, 227, 0.3)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{
              transition: "transform 0.2s ease",
              transform: profileOpen ? "rotate(180deg)" : "rotate(0deg)",
            }}
          >
            <polyline points="18 15 12 9 6 15" />
          </svg>
        </div>
      </div>
    </nav>
  );
}
