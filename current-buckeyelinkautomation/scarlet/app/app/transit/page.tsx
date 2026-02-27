"use client";

import DomainHero from "@/components/DomainHero";
import PulseDot from "@/components/PulseDot";
import ParkingRing from "@/components/domain/ParkingRing";
import InputBar from "@/components/InputBar";

const DEMO_ROUTES = [
  { code: "CC", name: "campus connector", buses: 3, active: true, eta: "4 min" },
  { code: "BE", name: "buckeye express", buses: 2, active: true, eta: "8 min" },
  { code: "CLS", name: "campus loop south", buses: 1, active: true, eta: "11 min" },
  { code: "ER", name: "east residential", buses: 0, active: false, eta: "---" },
  { code: "NWC", name: "northwest connector", buses: 2, active: true, eta: "6 min" },
];

const DEMO_PARKING = [
  { name: "ohio union", available: 342, total: 600 },
  { name: "tuttle park", available: 89, total: 400 },
  { name: "arps garage", available: 12, total: 300 },
  { name: "lane ave", available: 0, total: 350 },
  { name: "12th ave", available: 201, total: 500 },
];

export default function TransitPage() {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
      }}
    >
      <DomainHero title="transit" accentColor="rgb(100,130,180)" />

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "0 32px",
        }}
      >
        {/* Map placeholder */}
        <div
          style={{
            width: "100%",
            height: 320,
            borderRadius: 14,
            background: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(255,255,255,0.04)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: 32,
            position: "relative",
            overflow: "hidden",
          }}
        >
          {/* Fake map grid */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              opacity: 0.03,
              backgroundImage:
                "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
              backgroundSize: "40px 40px",
            }}
          />
          {/* Fake route line */}
          <svg
            style={{ position: "absolute", inset: 0 }}
            viewBox="0 0 800 400"
            preserveAspectRatio="none"
          >
            <path
              d="M100,200 C200,100 350,300 500,180 C600,100 700,250 750,200"
              stroke="rgba(255,255,255,0.08)"
              strokeWidth="3"
              fill="none"
            />
            {/* Bus dots */}
            <circle cx="250" cy="160" r="5" fill="rgb(198,40,40)">
              <animate
                attributeName="opacity"
                values="1;0.5;1"
                dur="2s"
                repeatCount="indefinite"
              />
            </circle>
            <circle cx="480" cy="190" r="5" fill="rgb(198,40,40)">
              <animate
                attributeName="opacity"
                values="1;0.5;1"
                dur="2s"
                begin="0.5s"
                repeatCount="indefinite"
              />
            </circle>
            <circle cx="680" cy="220" r="5" fill="rgb(198,40,40)">
              <animate
                attributeName="opacity"
                values="1;0.5;1"
                dur="2s"
                begin="1s"
                repeatCount="indefinite"
              />
            </circle>
          </svg>
          <span
            style={{
              fontFamily: "var(--font-space-mono)",
              fontWeight: 400,
              fontSize: 10,
              color: "rgba(255,255,255,0.15)",
              letterSpacing: "2px",
              zIndex: 1,
            }}
          >
            connect mapbox for live map
          </span>
        </div>

        {/* Routes */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <h2
            style={{
              fontFamily: "var(--font-outfit)",
              fontWeight: 200,
              fontSize: 16,
              letterSpacing: "0.15em",
              color: "rgba(255,255,255,0.55)",
              margin: 0,
            }}
          >
            routes
          </h2>
          <span
            style={{
              fontFamily: "var(--font-space-mono)",
              fontWeight: 400,
              fontSize: 9,
              color: "rgba(255,255,255,0.20)",
              letterSpacing: "1px",
            }}
          >
            auto-refresh 15s
          </span>
        </div>

        <div
          style={{
            background: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(255,255,255,0.04)",
            borderRadius: 12,
            padding: "4px 16px",
            marginBottom: 40,
          }}
        >
          {DEMO_ROUTES.map((route, i) => (
            <div
              key={route.code}
              style={{
                display: "flex",
                alignItems: "center",
                height: 44,
                gap: 12,
                borderBottom:
                  i < DEMO_ROUTES.length - 1
                    ? "1px solid rgba(255,255,255,0.03)"
                    : "none",
              }}
            >
              <PulseDot
                color={route.active ? "rgb(198,40,40)" : "rgba(255,255,255,0.15)"}
                size={6}
                pulse={route.active}
              />
              <span
                style={{
                  fontFamily: "var(--font-space-mono)",
                  fontWeight: 400,
                  fontSize: 11,
                  color: "rgba(255,255,255,0.45)",
                  flex: 1,
                }}
              >
                {route.name} ({route.code})
              </span>
              <span
                style={{
                  fontFamily: "var(--font-space-mono)",
                  fontWeight: 400,
                  fontSize: 10,
                  color: "rgba(255,255,255,0.25)",
                  width: 120,
                }}
              >
                {route.buses > 0 ? `${route.buses} buses active` : "no buses"}
              </span>
              <span
                style={{
                  fontFamily: "var(--font-space-mono)",
                  fontWeight: 400,
                  fontSize: 12,
                  color:
                    route.eta !== "---" && parseInt(route.eta) <= 5
                      ? "rgb(198,40,40)"
                      : "rgba(255,255,255,0.40)",
                  width: 60,
                  textAlign: "right",
                }}
              >
                {route.eta !== "---" ? `eta ${route.eta}` : "---"}
              </span>
            </div>
          ))}
        </div>

        {/* Parking */}
        <h2
          style={{
            fontFamily: "var(--font-outfit)",
            fontWeight: 200,
            fontSize: 16,
            letterSpacing: "0.15em",
            color: "rgba(255,255,255,0.55)",
            margin: 0,
            marginBottom: 16,
          }}
        >
          parking
        </h2>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 12,
            justifyContent: "center",
            marginBottom: 40,
          }}
        >
          {DEMO_PARKING.map((garage) => (
            <ParkingRing
              key={garage.name}
              name={garage.name}
              available={garage.available}
              total={garage.total}
            />
          ))}
        </div>
      </div>

      <InputBar
        placeholder="ask about transit..."
        onSubmit={(msg) => console.log("transit:", msg)}
      />
    </div>
  );
}
