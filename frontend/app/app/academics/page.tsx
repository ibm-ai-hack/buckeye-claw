"use client";

import { useState } from "react";
import DomainHero from "@/components/DomainHero";
import GradeBar from "@/components/domain/GradeBar";
import ScheduleGrid from "@/components/domain/ScheduleGrid";
import AssignmentRow from "@/components/domain/AssignmentRow";

const DEMO_GRADES = [
  { course: "CSE 2421", percentage: 92, letter: "A-" },
  { course: "ENGLISH 1110", percentage: 78, letter: "B+" },
  { course: "MATH 2153", percentage: 96, letter: "A" },
  { course: "PHYSICS 1251", percentage: 65, letter: "C+" },
  { course: "HISTORY 1212", percentage: 87, letter: "B+" },
];

const DEMO_SCHEDULE = [
  { code: "CSE 2421", days: ["Mon", "Wed"], startHour: 9, endHour: 10.5 },
  { code: "ENG 1110", days: ["Tue", "Thu"], startHour: 11, endHour: 12.25 },
  { code: "MATH 2153", days: ["Mon", "Wed", "Fri"], startHour: 13, endHour: 14 },
  { code: "PHYS 1251", days: ["Fri"], startHour: 10, endHour: 12 },
  { code: "HIST 1212", days: ["Tue", "Thu"], startHour: 14, endHour: 15.25 },
];

const DEMO_ASSIGNMENTS = [
  { course: "CSE 2421", title: "lab 5: linked lists", dueLabel: "due in 2d 4h", urgency: "normal" as const },
  { course: "ENGLISH 1110", title: "essay 3 draft", dueLabel: "due in 5d", urgency: "normal" as const },
  { course: "MATH 2153", title: "homework 8", dueLabel: "due tomorrow", urgency: "tomorrow" as const },
  { course: "PHYSICS 1251", title: "prelab 6", dueLabel: "overdue 2d", urgency: "overdue" as const },
  { course: "HISTORY 1212", title: "reading response 4", dueLabel: "due in 1d 8h", urgency: "soon" as const },
];

const TABS = ["schedule", "grades", "assignments"] as const;
type Tab = (typeof TABS)[number];

export default function AcademicsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("schedule");

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
      }}
    >
      <DomainHero title="academics" accentColor="rgb(220,170,50)" />

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

      {/* Tab content */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "20px 32px",
        }}
      >
        {activeTab === "schedule" && (
          <div>
            <ScheduleGrid courses={DEMO_SCHEDULE} />
          </div>
        )}

        {activeTab === "grades" && (
          <div style={{}}>
            {DEMO_GRADES.map((g, i) => (
              <GradeBar
                key={g.course}
                course={g.course}
                percentage={g.percentage}
                letter={g.letter}
                delay={i * 80}
              />
            ))}
          </div>
        )}

        {activeTab === "assignments" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {DEMO_ASSIGNMENTS.map((a) => (
              <AssignmentRow
                key={`${a.course}-${a.title}`}
                course={a.course}
                title={a.title}
                dueLabel={a.dueLabel}
                urgency={a.urgency}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
