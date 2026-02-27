"use client";

import { usePathname, useRouter } from "next/navigation";

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
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="2" />
        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
      </svg>
    ),
  },
  {
    path: "/app/dining",
    label: "dine",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M18 8h1a4 4 0 010 8h-1M2 8h16v9a4 4 0 01-4 4H6a4 4 0 01-4-4V8z" />
        <line x1="6" y1="1" x2="6" y2="4" />
        <line x1="10" y1="1" x2="10" y2="4" />
        <line x1="14" y1="1" x2="14" y2="4" />
      </svg>
    ),
  },
  {
    path: "/app/transit",
    label: "bus",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M8 6v6M15 6v6M2 12h19.6M18 18h3s.5-1.7.8-2.8c.1-.4.2-.8.2-1.2 0-.4-.1-.8-.2-1.2l-1.4-5C20.1 6.8 19.1 6 18 6H4a2 2 0 00-2 2v10h3" />
        <circle cx="7" cy="18" r="2" />
        <path d="M9 18h5" />
        <circle cx="16" cy="18" r="2" />
      </svg>
    ),
  },
  {
    path: "/app/academics",
    label: "acad",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
        <path d="M6 12v5c0 1.1 2.7 3 6 3s6-1.9 6-3v-5" />
      </svg>
    ),
  },
  {
    path: "/app/food",
    label: "food",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M15 11h.01M11 15h.01M16 16a5 5 0 10-6.5-6.5" />
        <path d="M8 2a5 5 0 00-2.65 9.25L2 21l9.75-3.35A5 5 0 008 2z" />
      </svg>
    ),
  },
  {
    path: "/app/campus",
    label: "camp",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="4" y="2" width="16" height="20" rx="2" />
        <path d="M9 22v-4h6v4M8 6h.01M16 6h.01M12 6h.01M12 10h.01M8 10h.01M16 10h.01M12 14h.01M8 14h.01M16 14h.01" />
      </svg>
    ),
  },
  {
    path: "/app/connect",
    label: "link",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" />
        <line x1="8" y1="21" x2="16" y2="21" />
        <line x1="12" y1="17" x2="12" y2="21" />
      </svg>
    ),
  },
];

export default function LeftRail() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <nav
      style={{
        width: 64,
        height: "100vh",
        position: "fixed",
        top: 0,
        left: 0,
        background: "#0a0a0a",
        borderRight: "1px solid rgba(255,255,255,0.04)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        paddingTop: 20,
        paddingBottom: 20,
        zIndex: 50,
        overflowY: "auto",
        overflowX: "hidden",
      }}
    >
      {/* Logo mark */}
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: 8,
          background: "rgba(198,40,40,0.15)",
          border: "1px solid rgba(198,40,40,0.25)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 28,
          cursor: "pointer",
        }}
        onClick={() => router.push("/")}
      >
        <span
          style={{
            fontFamily: "var(--font-outfit)",
            fontWeight: 200,
            fontSize: 14,
            color: "rgb(198,40,40)",
          }}
        >
          s
        </span>
      </div>

      {/* Nav items */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 4,
          flex: 1,
        }}
      >
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.path || pathname.startsWith(item.path + "/");
          return (
            <button
              key={item.path}
              onClick={() => router.push(item.path)}
              style={{
                width: 56,
                padding: "10px 0 6px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 4,
                background: "transparent",
                border: "none",
                borderLeft: isActive
                  ? "2px solid rgb(198,40,40)"
                  : "2px solid transparent",
                cursor: "pointer",
                transition: "all 0.15s ease",
                borderRadius: 0,
                color: isActive
                  ? "rgba(255,255,255,0.85)"
                  : "rgba(255,255,255,0.30)",
                filter: isActive
                  ? "drop-shadow(0 0 6px rgba(198,40,40,0.3))"
                  : "none",
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.color = "rgba(255,255,255,0.55)";
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.color = "rgba(255,255,255,0.30)";
                }
              }}
            >
              {item.icon}
              <span
                style={{
                  fontFamily: "var(--font-space-mono)",
                  fontWeight: 400,
                  fontSize: 8,
                  letterSpacing: "0.5px",
                  color: isActive
                    ? "rgba(255,255,255,0.50)"
                    : "rgba(255,255,255,0.20)",
                }}
              >
                {item.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* Bottom section */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 12,
          marginTop: "auto",
        }}
      >
        <div
          style={{
            width: 1,
            height: 20,
            background: "rgba(255,255,255,0.06)",
            marginBottom: 4,
          }}
        />
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: "50%",
            background: "rgb(198,40,40)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-outfit)",
              fontWeight: 300,
              fontSize: 12,
              color: "white",
              letterSpacing: "0.5px",
            }}
          >
            bu
          </span>
        </div>
      </div>
    </nav>
  );
}
