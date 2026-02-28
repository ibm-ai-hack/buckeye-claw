# BuckeyeBot — Use Cases & Implemented Functionality

## Overview

BuckeyeBot is a unified AI assistant for Ohio State University students, accessible via iMessage, RCS, and SMS. It consolidates campus services, academic tools, food ordering, and real-time campus data into a single messaging interface — with typing indicators, read receipts, and tapback reactions that make it feel alive. The system is built on the BeeAI Framework with IBM Granite as the LLM backbone, running 60 agent tools across 6 domains.

---

## Architecture Summary

| Component | Technology | Role |
|---|---|---|
| **Agent** | BeeAI `RequirementAgent` + IBM Granite 3 8B | Orchestrates all tool calls and generates SMS-friendly responses |
| **Messaging Gateway** | Flask + Linq Partner API v3 | Receives/sends iMessage, RCS, SMS; typing indicators, read receipts, tapbacks |
| **Campus APIs** | `httpx` async client → OSU content APIs | Real-time campus data (dining, buses, parking, events, etc.) |
| **Canvas (Carmen)** | `canvasapi` Python SDK | Course info, assignments, grades, announcements |
| **Grubhub** | Appium + Android emulator | Automated food ordering via UI automation |
| **BuckeyeLink** | Playwright browser automation | Class schedule, grades, financial aid, enrollment |
| **BuckeyeLink Web UI** | FastAPI + WebSocket + browser-use agent | Separate interactive web app for SSO-authenticated schedule extraction |

---

## Messaging Interface

**How it works:** A student texts the Linq-provisioned phone number. The Flask server receives a webhook event, returns `200 OK` immediately, then processes the message in a background thread — showing typing indicators, sending read receipts, and replying via the Linq API.

**Implemented features:**
- Incoming message webhook at `/webhook` (POST) with HMAC-SHA256 signature verification
- iMessage (blue bubbles) as preferred protocol, with automatic RCS/SMS fallback
- **Typing indicators** — dots appear while the agent is thinking
- **Read receipts** — messages marked as read upon receipt
- **Tapback reactions** — auto-acknowledges every message with a thumbs-up
- Outbound messaging via Linq Partner API v3 (iMessage/RCS/SMS)
- Phone-to-chat-ID mapping cache with JSON file persistence
- Error handling with user-friendly fallback messages

---

## Use Cases by Domain

### 1. Dining (3 tools)

| Use Case | Tool | Example Prompt |
|---|---|---|
| Find open dining halls | `get_dining_locations` | "What dining halls are open right now?" |
| Browse menus | `get_dining_locations_with_menus` | "What's for lunch on campus?" |
| Get specific menu items | `get_dining_menu` | "Show me the menu at Scott" |

**Data source:** `content.osu.edu/v2/api/v1/dining`

---

### 2. Bus Transportation (3 tools)

| Use Case | Tool | Example Prompt |
|---|---|---|
| List all bus routes | `get_bus_routes` | "What bus routes are running?" |
| Find stops on a route | `get_bus_stops` | "Where does the Campus Connector stop?" |
| Track buses in real time | `get_bus_vehicles` | "Where is the CABS bus right now?" |

**Supported routes:** ACK (Ackerman Shuttle), BE (Buckeye Express), CC (Campus Connector), CLS (Campus Loop South), ER (East Residential), MC (Medical Center), MM (Morehouse to Med Center), NWC (Northwest Connector), WMC (Wexner Medical Center)

**Data source:** `content.osu.edu/v2/bus`

---

### 3. Parking (1 tool)

| Use Case | Tool | Example Prompt |
|---|---|---|
| Check garage availability | `get_parking_availability` | "Is there parking at the Ohio Union garage?" |

**Data source:** `content.osu.edu/v2/parking/garages` — real-time availability

---

### 4. Campus Events (3 tools)

| Use Case | Tool | Example Prompt |
|---|---|---|
| Browse upcoming events | `get_campus_events` | "What's happening on campus this week?" |
| Search by keyword | `search_campus_events` | "Any concerts on campus?" |
| Filter by date range | `get_events_by_date_range` | "What events are between March 1-7?" |

**Data source:** `content.osu.edu/v2/events`

---

### 5. Class Search (1 tool)

| Use Case | Tool | Example Prompt |
|---|---|---|
| Search courses | `search_classes` | "Find CSE classes for spring" |

**Filters supported:** keyword, term code, campus (COL/LMA/MNS/MRN/NWK), subject code, academic career (UGRD/GRAD/LAW/MED), component type (LEC/LAB/REC/SEM), pagination

**Data source:** `content.osu.edu/v2/classes/search`

---

### 6. Libraries (6 tools)

| Use Case | Tool | Example Prompt |
|---|---|---|
| List all libraries | `get_library_locations` | "What libraries are open?" |
| Find a specific library | `search_library_locations` | "Where is Thompson Library?" |
| Browse study rooms | `get_library_rooms` | "What study rooms are available?" |
| Search rooms by name | `search_library_rooms` | "Any rooms at the 18th Ave Library?" |
| Find rooms by capacity | `get_rooms_by_capacity` | "I need a room for 6 people" |
| Find rooms by amenity | `get_rooms_with_amenities` | "Study rooms with a whiteboard?" |

**Amenities supported:** whiteboard, HDTV, video conferencing, computer, projector

**Data source:** `content.osu.edu/v2/library`

---

### 7. Rec Sports (4 tools)

| Use Case | Tool | Example Prompt |
|---|---|---|
| List all facilities | `get_recsports_facilities` | "What rec centers are there?" |
| Search by name | `search_recsports_facilities` | "Is the RPAC open?" |
| Check hours | `get_facility_hours` | "What time does the JO North open?" |
| View events | `get_facility_events` | "Any intramural events today?" |

**Data source:** `content.osu.edu/v3/recsports`

---

### 8. Buildings (4 tools)

| Use Case | Tool | Example Prompt |
|---|---|---|
| List all buildings | `get_buildings` | "Show me campus buildings" |
| Search buildings | `search_buildings` | "Where is Dreese Lab?" |
| Get building details | `get_building_details` | "Tell me about building 080" |
| Find special rooms | `find_room_type` | "Where are lactation rooms on campus?" |

**Special room types:** lactation, sanctuary, wellness, gender-inclusive restroom

**Data source:** `content.osu.edu/v2/api/buildings`

---

### 9. Academic Calendar (3 tools)

| Use Case | Tool | Example Prompt |
|---|---|---|
| View full calendar | `get_academic_calendar` | "When does spring semester start?" |
| Check holidays | `get_university_holidays` | "When is spring break?" |
| Search calendar | `search_calendar_events` | "When is the add/drop deadline?" |

**Data source:** `content.osu.edu/v2/calendar`

---

### 10. People Directory (1 tool)

| Use Case | Tool | Example Prompt |
|---|---|---|
| Look up faculty/staff | `search_people` | "Find Professor Smith in CSE" |

**Supports:** first name search, last name search, or both

**Data source:** `content.osu.edu/v2/people/search`

---

### 11. Athletics (4 tools)

| Use Case | Tool | Example Prompt |
|---|---|---|
| All athletics programs | `get_athletics_all` | "What sports does OSU have?" |
| Search by sport | `search_sports` | "Tell me about OSU football" |
| Filter by gender | `get_sport_by_gender` | "Women's sports at OSU?" |
| Upcoming games | `get_upcoming_games` | "When's the next basketball game?" |

**Data source:** `content.osu.edu/v3/athletics`

---

### 12. BuckID Merchants (4 tools)

| Use Case | Tool | Example Prompt |
|---|---|---|
| All BuckID merchants | `get_buckid_merchants` | "Where can I use my BuckID?" |
| Search merchants | `search_merchants` | "BuckID coffee shops?" |
| Find by food type | `get_merchants_by_food_type` | "Pizza places that take BuckID?" |
| Meal plan merchants | `get_merchants_with_meal_plan` | "Where can I use my meal plan?" |

**Data source:** `content.osu.edu/v2/merchants`

---

### 13. Food Trucks (3 tools)

| Use Case | Tool | Example Prompt |
|---|---|---|
| All food truck events | `get_foodtruck_events` | "Any food trucks out today?" |
| Search food trucks | `search_foodtrucks` | "Is there a taco truck on campus?" |
| Find by location | `get_foodtrucks_by_location` | "Food trucks near the Oval?" |

**Data source:** `content.osu.edu/v2/foodtruck`

---

### 14. Student Organizations (4 tools)

| Use Case | Tool | Example Prompt |
|---|---|---|
| All organizations | `get_student_organizations` | "List student orgs" |
| Search by keyword | `search_student_orgs` | "Coding clubs at OSU?" |
| Filter by type | `get_orgs_by_type` | "What Greek orgs exist?" |
| Filter by level | `get_orgs_by_career_level` | "Graduate student organizations?" |

**Data source:** `content.osu.edu/v2/student-org`

---

### 15. Canvas / Carmen (7 tools)

| Use Case | Tool | Example Prompt |
|---|---|---|
| List courses | `get_canvas_courses` | "What classes am I in?" |
| View assignments | `get_course_assignments` | "Assignments for CSE 2421?" |
| Upcoming due dates | `get_upcoming_assignments` | "What's due this week?" |
| Check grades | `get_course_grades` | "What's my grade in English?" |
| Read announcements | `get_course_announcements` | "Any new announcements?" |
| View to-do items | `get_canvas_todos` | "What's on my Canvas to-do list?" |
| Read syllabus | `get_course_syllabus` | "Show me the syllabus for my math class" |

**Integration:** Uses the `canvasapi` Python SDK connecting to `osu.instructure.com`. Requires a Canvas API token.

---

### 16. Grubhub Food Ordering (3 tools)

| Use Case | Tool | Example Prompt |
|---|---|---|
| Search restaurants | `search_grubhub_restaurants` | "What's on Grubhub near campus?" |
| Browse a menu | `get_restaurant_menu` | "Show me the Chipotle menu" |
| Place an order | `place_grubhub_order` | "Order a burrito bowl from Chipotle" |

**How it works:** Drives the Grubhub Android app through Appium UI automation on an Android emulator. The full ordering flow is automated: search → select restaurant → browse menu → add items to cart → checkout.

**Infrastructure:**
- `grubhub/emulator.py` — Manages Android emulator lifecycle (list/start/check AVDs, verify Grubhub APK, launch app)
- `grubhub/automation.py` — Appium-based UI automation (search, menu scraping, cart management, checkout)
- `grubhub/tools.py` — BeeAI tool wrappers exposing automation to the agent

---

### 17. BuckeyeLink Academic Services (6 tools)

| Use Case | Tool | Example Prompt |
|---|---|---|
| View class schedule | `get_class_schedule` | "What's my schedule this semester?" |
| Check grades | `get_grades` | "What are my grades?" |
| Financial aid status | `get_financial_aid_status` | "Check my financial aid" |
| Account holds/to-dos | `get_holds_and_todos` | "Do I have any holds?" |
| Enrollment info | `get_enrollment_info` | "Show my enrollment status" |
| Dashboard overview | `get_buckeyelink_dashboard` | "What's on my BuckeyeLink?" |

**How it works:** Uses Playwright to automate a headless Chromium browser. Authenticates through OSU's Shibboleth SSO (with Duo MFA support), then navigates the BuckeyeLink React SPA to extract data from pages and PeopleSoft iframes.

**Infrastructure:**
- `buckeyelink/auth.py` — Shibboleth SSO login with session caching and Duo MFA wait (up to 120s)
- `buckeyelink/browser.py` — Page navigation, SPA load detection, data extraction (visible text, tables, cards, iframe content)
- `buckeyelink/tools.py` — BeeAI tool wrappers with multiple extraction strategies per page

---

### 18. BuckeyeLink Web UI (Separate App)

Located in `current-buckeyelinkautomation/scarlet/`, this is a standalone Next.js + FastAPI web application for interactive BuckeyeLink authentication and schedule extraction.

**Features:**
- FastAPI backend with WebSocket streaming (screenshot frames at ~3 fps)
- Remote browser interaction — click and keyboard events forwarded via WebSocket
- `browser-use` agent with LLM-driven navigation to extract class schedules
- State machine flow: idle → awaiting_auth → authenticated → extracting → complete
- JSON schedule parsing from LLM agent output
- Session management (start, status check, screenshot, close)

**API endpoints:**
- `POST /api/session/start` — Start a headless browser session
- `GET /api/session/status` — Check session state
- `GET /api/session/screenshot` — Get current browser screenshot
- `WS /api/session/stream` — Real-time frame + input streaming
- `POST /api/session/close` — Close session

---

## Tool Count Summary

| Domain | Tools |
|---|---|
| Dining | 3 |
| Bus Transportation | 3 |
| Parking | 1 |
| Campus Events | 3 |
| Class Search | 1 |
| Libraries | 6 |
| Rec Sports | 4 |
| Buildings | 4 |
| Academic Calendar | 3 |
| People Directory | 1 |
| Athletics | 4 |
| BuckID Merchants | 4 |
| Food Trucks | 3 |
| Student Organizations | 4 |
| Canvas / Carmen | 7 |
| Grubhub | 3 |
| BuckeyeLink | 6 |
| **Total** | **60** |

---

## Dependencies

| Package | Purpose |
|---|---|
| `beeai-framework[watsonx]` | Agent framework + IBM watsonx LLM backend |
| `flask` | Messaging webhook server |
| `httpx` | Async HTTP client for OSU APIs |
| `python-dotenv` | Environment variable management |
| `canvasapi` | Canvas LMS Python SDK |
| `Appium-Python-Client` | Android UI automation (optional, for Grubhub) |
| `playwright` | Browser automation (optional, for BuckeyeLink) |
| `fastapi` + `uvicorn` | BuckeyeLink web UI backend |
| `browser-use` | LLM-driven browser agent (BuckeyeLink web UI) |
