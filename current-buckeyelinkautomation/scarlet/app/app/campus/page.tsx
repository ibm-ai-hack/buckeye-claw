"use client";

import { useState } from "react";
import DomainHero from "@/components/DomainHero";
import EventRow from "@/components/domain/EventRow";
import InputBar from "@/components/InputBar";

const DEMO_EVENTS = [
  { day: 15, month: "mar", title: "spring concert", venue: "schottenstein center", time: "7:00 pm — 10:00 pm", description: "free with buckid" },
  { day: 17, month: "mar", title: "career fair", venue: "ohio union ballrooms", time: "10:00 am — 3:00 pm", description: "engineering & cs majors" },
  { day: 19, month: "mar", title: "guest lecture: ai ethics", venue: "dreese lab 305", time: "4:00 pm — 5:30 pm" },
  { day: 22, month: "mar", title: "intramural basketball finals", venue: "rpac courts", time: "6:00 pm — 9:00 pm" },
  { day: 24, month: "mar", title: "food truck festival", venue: "the oval", time: "11:00 am — 3:00 pm", description: "10+ trucks, live music" },
];

const DEMO_ATHLETICS = [
  { day: 16, month: "mar", title: "men's basketball vs michigan", venue: "value city arena", time: "2:00 pm" },
  { day: 20, month: "mar", title: "women's lacrosse vs maryland", venue: "jesse owens stadium", time: "4:00 pm" },
  { day: 23, month: "mar", title: "baseball vs penn state", venue: "bill davis stadium", time: "6:30 pm" },
];

const DEMO_ORGS = [
  { name: "osu ai club", type: "academic", members: 340 },
  { name: "hacking society", type: "technology", members: 220 },
  { name: "data science club", type: "academic", members: 180 },
  { name: "entrepreneurship club", type: "professional", members: 410 },
  { name: "design collective", type: "creative", members: 95 },
  { name: "robotics club", type: "engineering", members: 150 },
];

const TABS = ["events", "athletics", "organizations"] as const;
type Tab = (typeof TABS)[number];

export default function CampusPage() {
  const [activeTab, setActiveTab] = useState<Tab>("events");

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
      }}
    >
      <DomainHero title="campus" accentColor="rgb(140,90,180)" />

      {/* Tabs */}
      <div
        style={{
          display: "flex",
          gap: 0,
          borderBottom: "1px solid rgba(255,255,255,0.04)",
          padding: "0 32px",
          flexShrink: 0,
        }}
      >
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              fontFamily: "var(--font-space-mono)",
              fontWeight: 400,
              fontSize: 12,
              letterSpacing: "1px",
              color: activeTab === tab ? "rgba(255,255,255,0.70)" : "rgba(255,255,255,0.25)",
              padding: "12px 24px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === tab ? "2px solid rgb(198,40,40)" : "2px solid transparent",
              cursor: "pointer",
              transition: "color 0.2s ease, border-color 0.2s ease",
              textTransform: "lowercase",
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px 32px" }}>
        {activeTab === "events" && (
          <div style={{ maxWidth: 700 }}>
            {DEMO_EVENTS.map((e) => (
              <EventRow key={`${e.day}-${e.title}`} {...e} />
            ))}
          </div>
        )}

        {activeTab === "athletics" && (
          <div style={{ maxWidth: 700 }}>
            {DEMO_ATHLETICS.map((e) => (
              <EventRow key={`${e.day}-${e.title}`} {...e} />
            ))}
          </div>
        )}

        {activeTab === "organizations" && (
          <div style={{ maxWidth: 700 }}>
            {DEMO_ORGS.map((org, i) => (
              <div
                key={org.name}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "14px 0",
                  borderBottom: i < DEMO_ORGS.length - 1 ? "1px solid rgba(255,255,255,0.03)" : "none",
                }}
              >
                <div>
                  <div
                    style={{
                      fontFamily: "var(--font-outfit)",
                      fontWeight: 300,
                      fontSize: 14,
                      color: "rgba(255,255,255,0.60)",
                      marginBottom: 4,
                    }}
                  >
                    {org.name}
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-space-mono)",
                      fontWeight: 400,
                      fontSize: 10,
                      color: "rgba(255,255,255,0.25)",
                      letterSpacing: "1px",
                    }}
                  >
                    {org.type}
                  </div>
                </div>
                <span
                  style={{
                    fontFamily: "var(--font-space-mono)",
                    fontWeight: 400,
                    fontSize: 11,
                    color: "rgba(255,255,255,0.25)",
                  }}
                >
                  {org.members} members
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <InputBar placeholder="ask about campus..." onSubmit={(msg) => console.log("campus:", msg)} />
    </div>
  );
}
