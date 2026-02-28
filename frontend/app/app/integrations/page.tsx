"use client";

import { useState } from "react";
import DomainHero from "@/components/DomainHero";

interface Tool {
  name: string;
  description: string;
}

interface Integration {
  category: string;
  icon: string;
  color: string;
  description: string;
  tools: Tool[];
}

const INTEGRATIONS: Integration[] = [
  {
    category: "Dining",
    icon: "\u{1F37D}",
    color: "rgb(234, 88, 12)",
    description: "Dining hall menus, hours, and locations across campus",
    tools: [
      { name: "get_dining_locations", description: "List all dining halls with hours and status" },
      { name: "get_dining_menu", description: "Get today's menu for a specific location" },
      { name: "get_dining_locations_with_menus", description: "All locations with full menus" },
      { name: "search_dining_locations", description: "Search dining halls by name or keyword" },
    ],
  },
  {
    category: "Bus Transit",
    icon: "\u{1F68C}",
    color: "rgb(59, 130, 246)",
    description: "Real-time CABS bus routes, stops, and vehicle tracking",
    tools: [
      { name: "get_bus_routes", description: "List all active bus routes" },
      { name: "get_bus_stops", description: "Get stops for a specific route" },
      { name: "get_bus_vehicles", description: "Real-time vehicle locations and ETAs" },
    ],
  },
  {
    category: "Parking",
    icon: "\u{1F697}",
    color: "rgb(107, 114, 128)",
    description: "Real-time garage availability across campus",
    tools: [
      { name: "get_parking_availability", description: "Live availability for all parking garages" },
    ],
  },
  {
    category: "Canvas LMS",
    icon: "\u{1F4DA}",
    color: "rgb(220, 38, 38)",
    description: "Courses, assignments, grades, and announcements from Carmen",
    tools: [
      { name: "get_canvas_courses", description: "List enrolled courses" },
      { name: "get_course_assignments", description: "Assignments for a course" },
      { name: "get_upcoming_assignments", description: "Due dates across all courses" },
      { name: "get_course_grades", description: "Current grades and scores" },
      { name: "get_course_announcements", description: "Recent announcements" },
      { name: "get_canvas_todos", description: "Canvas to-do items" },
      { name: "get_course_syllabus", description: "Course syllabus content" },
    ],
  },
  {
    category: "Grubhub",
    icon: "\u{1F354}",
    color: "rgb(249, 115, 22)",
    description: "Order food delivery from nearby restaurants",
    tools: [
      { name: "search_grubhub_restaurants", description: "Find restaurants on Grubhub" },
      { name: "get_restaurant_menu", description: "Browse a restaurant's menu" },
      { name: "place_grubhub_order", description: "Place an immediate order" },
      { name: "schedule_grubhub_order", description: "Schedule a future order" },
      { name: "list_scheduled_grubhub_orders", description: "View your scheduled orders" },
      { name: "cancel_scheduled_grubhub_order", description: "Cancel a scheduled order" },
    ],
  },
  {
    category: "BuckeyeLink",
    icon: "\u{1F393}",
    color: "rgb(168, 35, 35)",
    description: "Class schedule, grades, financial aid, and enrollment via browser automation",
    tools: [
      { name: "get_class_schedule", description: "Current semester schedule" },
      { name: "get_grades", description: "Grades and transcripts" },
      { name: "get_financial_aid_status", description: "Financial aid details" },
      { name: "get_holds_and_todos", description: "Account holds and action items" },
      { name: "get_enrollment_info", description: "Enrollment status" },
      { name: "get_buckeyelink_dashboard", description: "Dashboard overview" },
      { name: "query_buckeyelink", description: "Custom BuckeyeLink queries" },
    ],
  },
  {
    category: "BuckeyeMail",
    icon: "\u{2709}",
    color: "rgb(59, 130, 246)",
    description: "Read and search your OSU Microsoft 365 email",
    tools: [
      { name: "get_email_inbox", description: "Recent inbox messages" },
      { name: "search_emails", description: "Search by sender, subject, or keyword" },
      { name: "get_unread_email_count", description: "Number of unread messages" },
      { name: "get_email_detail", description: "Full content of a specific email" },
    ],
  },
  {
    category: "Events",
    icon: "\u{1F4C5}",
    color: "rgb(168, 85, 247)",
    description: "Campus events, lectures, and activities",
    tools: [
      { name: "get_campus_events", description: "Browse upcoming events" },
      { name: "search_campus_events", description: "Search events by keyword" },
      { name: "get_events_by_date_range", description: "Events within a date range" },
    ],
  },
  {
    category: "Classes",
    icon: "\u{1F4DD}",
    color: "rgb(14, 165, 233)",
    description: "Search the course catalog by subject, keyword, or instructor",
    tools: [
      { name: "search_classes", description: "Search classes by keyword, subject, or instructor" },
    ],
  },
  {
    category: "Library",
    icon: "\u{1F4D6}",
    color: "rgb(34, 197, 94)",
    description: "Library locations, study rooms, and room reservations",
    tools: [
      { name: "get_library_locations", description: "All library locations and hours" },
      { name: "search_library_locations", description: "Search libraries by name" },
      { name: "get_library_rooms", description: "Available study rooms" },
      { name: "search_library_rooms", description: "Search rooms by name" },
      { name: "get_rooms_by_capacity", description: "Find rooms by group size" },
      { name: "get_rooms_with_amenities", description: "Rooms with specific features" },
    ],
  },
  {
    category: "Rec Sports",
    icon: "\u{1F3CB}",
    color: "rgb(245, 158, 11)",
    description: "RPAC, JO South, and other rec facilities",
    tools: [
      { name: "get_recsports_facilities", description: "All rec facilities" },
      { name: "search_recsports_facilities", description: "Search facilities by name" },
      { name: "get_facility_hours", description: "Operating hours" },
      { name: "get_facility_events", description: "Rec sports events and programs" },
    ],
  },
  {
    category: "Athletics",
    icon: "\u{1F3C8}",
    color: "rgb(198, 50, 45)",
    description: "Buckeye sports schedules and upcoming games",
    tools: [
      { name: "get_athletics_all", description: "All sports teams" },
      { name: "search_sports", description: "Search by sport name" },
      { name: "get_sport_by_gender", description: "Filter by gender" },
      { name: "get_upcoming_games", description: "Next games on the schedule" },
    ],
  },
  {
    category: "Buildings",
    icon: "\u{1F3DB}",
    color: "rgb(107, 114, 128)",
    description: "Campus building locations and room types",
    tools: [
      { name: "get_buildings", description: "All campus buildings" },
      { name: "search_buildings", description: "Search buildings by name" },
      { name: "get_building_details", description: "Details for a specific building" },
      { name: "find_room_type", description: "Find rooms by type (lecture hall, lab, etc.)" },
    ],
  },
  {
    category: "BuckID Merchants",
    icon: "\u{1F4B3}",
    color: "rgb(16, 185, 129)",
    description: "Off-campus merchants that accept BuckID and meal swipes",
    tools: [
      { name: "get_buckid_merchants", description: "All BuckID-accepting merchants" },
      { name: "search_merchants", description: "Search merchants by name" },
      { name: "get_merchants_by_food_type", description: "Filter by cuisine type" },
      { name: "get_merchants_with_meal_plan", description: "Merchants accepting meal swipes" },
    ],
  },
  {
    category: "Food Trucks",
    icon: "\u{1F69A}",
    color: "rgb(251, 146, 60)",
    description: "Food truck schedules and locations on campus",
    tools: [
      { name: "get_foodtruck_events", description: "Upcoming food truck events" },
      { name: "search_foodtrucks", description: "Search food trucks by name" },
      { name: "get_foodtrucks_by_location", description: "Food trucks at a specific spot" },
    ],
  },
  {
    category: "Student Orgs",
    icon: "\u{1F465}",
    color: "rgb(139, 92, 246)",
    description: "Browse and search 1,400+ student organizations",
    tools: [
      { name: "get_student_organizations", description: "Browse all organizations" },
      { name: "search_student_orgs", description: "Search orgs by name or keyword" },
      { name: "get_orgs_by_type", description: "Filter by org type" },
      { name: "get_orgs_by_career_level", description: "Orgs for your career stage" },
    ],
  },
  {
    category: "Calendar",
    icon: "\u{1F5D3}",
    color: "rgb(236, 72, 153)",
    description: "Academic calendar, holidays, and important dates",
    tools: [
      { name: "get_academic_calendar", description: "Full academic calendar" },
      { name: "get_university_holidays", description: "University holiday schedule" },
      { name: "search_calendar_events", description: "Search calendar by keyword" },
    ],
  },
  {
    category: "Directory",
    icon: "\u{1F50D}",
    color: "rgb(99, 102, 241)",
    description: "Search the OSU people directory",
    tools: [
      { name: "search_people", description: "Find faculty, staff, and students" },
    ],
  },
];

export default function IntegrationsPage() {
  const [expanded, setExpanded] = useState<string | null>(null);
  const totalTools = INTEGRATIONS.reduce((sum, i) => sum + i.tools.length, 0);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
      }}
    >
      <DomainHero title="integrations" accentColor="rgb(59, 130, 246)" />

      {/* Summary bar */}
      <div
        style={{
          padding: "0 32px 16px",
          display: "flex",
          gap: 24,
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontSize: 13,
            color: "rgba(237, 232, 227, 0.45)",
          }}
        >
          {INTEGRATIONS.length} services
        </span>
        <span
          style={{
            fontFamily: "var(--font-jakarta)",
            fontSize: 13,
            color: "rgba(237, 232, 227, 0.45)",
          }}
        >
          {totalTools} tools
        </span>
      </div>

      {/* Scrollable grid */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "0 32px 32px",
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
            gap: 12,
          }}
        >
          {INTEGRATIONS.map((integration) => {
            const isExpanded = expanded === integration.category;
            return (
              <div
                key={integration.category}
                onClick={() =>
                  setExpanded(isExpanded ? null : integration.category)
                }
                style={{
                  background: isExpanded
                    ? "rgba(255, 240, 220, 0.05)"
                    : "rgba(255, 240, 220, 0.02)",
                  border: `1px solid ${
                    isExpanded
                      ? `${integration.color}30`
                      : "rgba(255, 240, 220, 0.06)"
                  }`,
                  borderRadius: 12,
                  padding: 16,
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                }}
                onMouseEnter={(e) => {
                  if (!isExpanded) {
                    e.currentTarget.style.background =
                      "rgba(255, 240, 220, 0.04)";
                    e.currentTarget.style.borderColor = `${integration.color}20`;
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isExpanded) {
                    e.currentTarget.style.background =
                      "rgba(255, 240, 220, 0.02)";
                    e.currentTarget.style.borderColor =
                      "rgba(255, 240, 220, 0.06)";
                  }
                }}
              >
                {/* Header */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    marginBottom: 8,
                  }}
                >
                  <span style={{ fontSize: 20 }}>{integration.icon}</span>
                  <div style={{ flex: 1 }}>
                    <div
                      style={{
                        fontFamily: "var(--font-jakarta)",
                        fontWeight: 500,
                        fontSize: 14,
                        color: "#ede8e3",
                      }}
                    >
                      {integration.category}
                    </div>
                    <div
                      style={{
                        fontFamily: "var(--font-jakarta)",
                        fontSize: 12,
                        color: "rgba(237, 232, 227, 0.4)",
                        marginTop: 2,
                      }}
                    >
                      {integration.description}
                    </div>
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-jakarta)",
                      fontSize: 11,
                      color: integration.color,
                      background: `${integration.color}15`,
                      padding: "3px 8px",
                      borderRadius: 6,
                      fontWeight: 500,
                      flexShrink: 0,
                    }}
                  >
                    {integration.tools.length} tool
                    {integration.tools.length !== 1 ? "s" : ""}
                  </div>
                </div>

                {/* Expanded tool list */}
                {isExpanded && (
                  <div
                    style={{
                      marginTop: 12,
                      borderTop: "1px solid rgba(255, 240, 220, 0.06)",
                      paddingTop: 12,
                      display: "flex",
                      flexDirection: "column",
                      gap: 8,
                    }}
                  >
                    {integration.tools.map((tool) => (
                      <div
                        key={tool.name}
                        style={{
                          display: "flex",
                          alignItems: "flex-start",
                          gap: 10,
                        }}
                      >
                        <div
                          style={{
                            width: 4,
                            height: 4,
                            borderRadius: "50%",
                            background: integration.color,
                            marginTop: 7,
                            flexShrink: 0,
                            opacity: 0.6,
                          }}
                        />
                        <div>
                          <div
                            style={{
                              fontFamily: "monospace",
                              fontSize: 12,
                              color: "rgba(237, 232, 227, 0.7)",
                            }}
                          >
                            {tool.name}
                          </div>
                          <div
                            style={{
                              fontFamily: "var(--font-jakarta)",
                              fontSize: 11,
                              color: "rgba(237, 232, 227, 0.35)",
                              marginTop: 1,
                            }}
                          >
                            {tool.description}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
