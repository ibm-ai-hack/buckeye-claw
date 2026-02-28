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
        padding: "24px 16px 20px",
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
          padding: "4px 8px",
          marginBottom: 32,
        }}
      >
        <img
          src="/chud.png"
          alt="buckeyeclaw"
          style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            objectFit: "contain",
          }}
        />
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontWeight: 600,
            fontSize: 17,
            color: "#ede8e3",
            letterSpacing: "-0.2px",
          }}
        >
          buckeyeclaw
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
                transition: "all 0.15s ease",
                color: isActive
                  ? "#ede8e3"
                  : "rgba(237, 232, 227, 0.50)",
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = "rgba(255, 240, 220, 0.05)";
                  e.currentTarget.style.color = "rgba(237, 232, 227, 0.75)";
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = "rgba(237, 232, 227, 0.50)";
                }
              }}
            >
              {item.icon}
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
                  }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom user section */}
      <div
        style={{
          borderTop: "1px solid rgba(255, 240, 220, 0.06)",
          paddingTop: 16,
          marginTop: 12,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "8px 8px",
            borderRadius: 10,
            cursor: "pointer",
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
          <div>
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
        </div>
      </div>
    </nav>
  );
}
