"use client";

import { useState } from "react";
import DomainHero from "@/components/DomainHero";
import EventRow from "@/components/domain/EventRow";

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
          gap: 4,
          borderBottom: "1px solid rgba(255, 240, 220, 0.06)",
          padding: "0 32px",
          flexShrink: 0,
        }}
      >
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              fontFamily: "var(--font-jakarta)",
              fontWeight: activeTab === tab ? 500 : 400,
              fontSize: 15,
              color: activeTab === tab ? "#ede8e3" : "rgba(237, 232, 227, 0.45)",
              padding: "14px 20px",
              background: activeTab === tab ? "rgba(255, 240, 220, 0.05)" : "transparent",
              border: "none",
              borderBottom: activeTab === tab ? "2px solid rgb(198, 50, 45)" : "2px solid transparent",
              borderRadius: "8px 8px 0 0",
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: "auto", padding: "20px 32px" }}>
        {activeTab === "events" && (
          <div style={{}}>
            {DEMO_EVENTS.map((e) => (
              <EventRow key={`${e.day}-${e.title}`} {...e} />
            ))}
          </div>
        )}

        {activeTab === "athletics" && (
          <div style={{}}>
            {DEMO_ATHLETICS.map((e) => (
              <EventRow key={`${e.day}-${e.title}`} {...e} />
            ))}
          </div>
        )}

        {activeTab === "organizations" && (
          <div style={{}}>
            {DEMO_ORGS.map((org, i) => (
              <div
                key={org.name}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "18px 16px",
                  marginBottom: 6,
                  background: "rgba(255, 240, 220, 0.02)",
                  borderRadius: 12,
                  border: "1px solid rgba(255, 240, 220, 0.04)",
                  transition: "background 0.15s ease",
                }}
              >
                <div>
                  <div
                    style={{
                      fontFamily: "var(--font-jakarta)",
                      fontWeight: 500,
                      fontSize: 16,
                      color: "#ede8e3",
                      marginBottom: 4,
                    }}
                  >
                    {org.name}
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-jakarta)",
                      fontWeight: 400,
                      fontSize: 13,
                      color: "rgba(237, 232, 227, 0.45)",
                    }}
                  >
                    {org.type}
                  </div>
                </div>
                <span
                  style={{
                    fontFamily: "var(--font-jakarta)",
                    fontWeight: 400,
                    fontSize: 14,
                    color: "rgba(237, 232, 227, 0.40)",
                  }}
                >
                  {org.members} members
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
