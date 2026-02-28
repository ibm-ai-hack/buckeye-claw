# BuckeyeClaw

Your entire campus, one text away.

BuckeyeClaw is a locally-hosted AI agent that unifies Ohio State University's fragmented student services into a single messaging interface. Text a phone number from iMessage, RCS, or SMS and the agent handles everything — dining menus, bus tracking, Grubhub orders, class schedules, grades, financial aid, and 50+ more campus tools — with typing indicators, read receipts, and tapback reactions that make it feel like you're talking to a person.

---

## Why This Exists

OSU students juggle a dozen different apps and portals daily: BuckeyeLink for registration, Carmen for grades, separate sites for dining hours, bus routes, parking availability, rec center schedules, and more. Each has its own login, UI, and quirks. BuckeyeClaw collapses all of that into a single text conversation.

---

## Features

### Messaging (Linq Partner API)
- **iMessage blue bubbles** with automatic RCS/SMS fallback
- **Typing indicators** — dots appear while the agent thinks
- **Read receipts** — messages marked as read on receipt
- **Tapback reactions** — auto-acknowledges your message with a thumbs-up
- **Rich media** — supports images, videos, and file attachments
- **HMAC-SHA256 webhook verification** for security

### Campus Services (50+ Tools)
| Category | Examples |
|---|---|
| **Dining** | Dining hall hours, today's menus, meal plan merchants |
| **Bus** | Real-time vehicle locations, route stops, all 9 campus routes |
| **Parking** | Live garage availability |
| **Classes** | Course catalog search by keyword, subject, or instructor |
| **Events** | Campus events, date-range filtering, keyword search |
| **Libraries** | Locations, study rooms, search by capacity or amenity |
| **Rec Sports** | Facility hours, events, availability |
| **Buildings** | Building lookup, room type search |
| **Calendar** | Academic calendar, university holidays |
| **Directory** | People search |
| **Athletics** | Upcoming games, sport search |
| **BuckID** | Merchant lookup, meal plan acceptance |
| **Food Trucks** | Schedules, location search |
| **Student Orgs** | Organization search, filter by type or career level |

### Food Ordering (Grubhub)
- Search restaurants and browse menus
- Place immediate orders via Android emulation
- Schedule future orders ("order me Raising Cane's at 6pm")
- List and cancel scheduled orders
- Persistent job storage survives server restarts

### Academic Tools (BuckeyeLink)
- View class schedule
- Check grades and transcripts
- Financial aid and billing status
- Holds and to-do items
- Course enrollment
- Generalized queries via Claude-enhanced browser automation

### Canvas (Carmen)
- List courses
- View assignments and due dates
- Check grades
- Read announcements
- Get to-do items
- View syllabi

### Web Dashboard
- Three.js animated landing page with dithered wave shader
- BuckeyeLink SSO browser session with real-time screenshot streaming
- Domain-specific pages for dining, transit, academics, campus, and food
- Glass morphism UI with scanline and pulse-dot effects

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     User's Phone                         │
│              (iMessage / RCS / SMS)                       │
└────────────────────────┬─────────────────────────────────┘
                         │
                    Linq Partner API
                         │
┌────────────────────────▼─────────────────────────────────┐
│                   Flask Webhook (/webhook)                │
│          HMAC verify → 200 OK → background thread         │
└────────────────────────┬─────────────────────────────────┘
                         │
          ┌──────────────▼──────────────┐
          │     Alive Features Pipeline  │
          │  read receipt → tapback →    │
          │  typing indicator → ack msg  │
          └──────────────┬──────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│              Dual-Model Agent Orchestrator                │
│                                                          │
│  ┌─────────────────┐  ┌──────────────────────────────┐   │
│  │  Granite 3 8B   │  │      Claude Opus 4.6         │   │
│  │  (IBM watsonx)  │  │      (Anthropic)             │   │
│  │                 │  │                              │   │
│  │  • Classify     │→ │  • Select & execute tools    │   │
│  │    intent       │  │  • Synthesize results        │   │
│  │  • Extract      │  │  • Draft response            │   │
│  │    params       │  │                              │   │
│  └─────────────────┘  └──────────────────────────────┘   │
│            │                       │                     │
│            └───────────┬───────────┘                     │
│                        ▼                                 │
│               Granite Formatter                          │
│           (plain text, <800 chars)                        │
└────────────────────────┬─────────────────────────────────┘
                         │
          ┌──────────────▼──────────────┐
          │      87 Tools Available      │
          ├─────────────────────────────┤
          │  Campus APIs (50+ tools)     │
          │  Canvas (7 tools)            │
          │  Grubhub (6 tools)           │
          │  BuckeyeLink (7 tools)       │
          └─────────────────────────────┘
```

### Agent Workflow

1. **Granite Intake** — IBM Granite 3 8B (fast, cheap) classifies the user's message into one of 18 intents and extracts parameters. Simple greetings are handled directly.
2. **Claude Execution** — Claude Opus 4.6 (powerful reasoning) selects from 87 tools, executes them, and drafts a response. Skipped for simple queries.
3. **Granite Format** — Granite reformats the response as plain text under 800 characters for SMS delivery.

### Intent Classification

```
dining_query    bus_query        parking_query     event_query
class_query     library_query    recsports_query   building_query
calendar_query  directory_query  athletics_query   merchant_query
foodtruck_query studentorg_query canvas_query      grubhub_order
buckeyelink_query  chitchat     unknown
```

---

## Project Structure

```
BuckeyeClaw/
├── main.py                              # Entry point (Flask + asyncio)
├── pyproject.toml                       # Python deps (uv)
├── Dockerfile                           # Python 3.11-slim + uv
├── .env.example                         # Required env vars
│
├── agents/                              # AI orchestration
│   ├── orchestrator.py                  # 3-step workflow (intake → execute → format)
│   ├── factories.py                     # Agent creation (Granite + Claude)
│   └── models.py                        # PipelineState (Pydantic)
│
├── backend/
│   ├── messaging/                       # Linq Partner API v3
│   │   ├── client.py                    # Async HTTP client (httpx)
│   │   ├── sender.py                    # High-level send/typing/react
│   │   ├── webhook.py                   # Flask webhook handler
│   │   ├── verify.py                    # HMAC-SHA256 signature verification
│   │   ├── events.py                    # Event dataclasses & parsing
│   │   └── chat_store.py               # Phone-to-chat-ID JSON cache
│   │
│   └── integrations/
│       ├── campus/                      # OSU content APIs (15 modules)
│       │   ├── dining.py                # Dining halls, menus
│       │   ├── bus.py                   # Routes, stops, real-time vehicles
│       │   ├── parking.py               # Live garage availability
│       │   ├── events.py                # Campus events
│       │   ├── classes.py               # Course catalog search
│       │   ├── library.py               # Locations, rooms, amenities
│       │   ├── recsports.py             # Facilities, hours, events
│       │   ├── buildings.py             # Building/room lookup
│       │   ├── calendar.py              # Academic calendar, holidays
│       │   ├── directory.py             # People search
│       │   ├── athletics.py             # Games, sports
│       │   ├── merchants.py             # BuckID merchants, meal plans
│       │   ├── foodtrucks.py            # Food truck schedules
│       │   ├── studentorgs.py           # Student organizations
│       │   └── utils.py                 # Shared helpers (fetch, timezone)
│       │
│       ├── canvas/                      # Carmen LMS
│       │   └── tools.py                 # canvasapi SDK wrapper (7 tools)
│       │
│       ├── grubhub/                     # Food ordering
│       │   ├── tools.py                 # BeeAI tool wrappers (6 tools)
│       │   ├── automation.py            # Appium UI automation
│       │   ├── scheduler.py             # APScheduler + SQLite persistence
│       │   ├── intelligence.py          # Order fulfillment logic
│       │   └── emulator.py              # Android emulator management
│       │
│       └── buckeyelink/                 # Academic services
│           ├── tools.py                 # BeeAI tool wrappers (7 tools)
│           ├── main.py                  # Interactive CLI
│           ├── browser_agent.py         # browser-use Agent wrapper
│           ├── auth.py                  # OSU SSO authentication
│           ├── enhancer.py              # Claude prompt enhancement
│           ├── knowledge.py             # Navigation hints & sitemap
│           ├── config.py                # Constants
│           └── workflows/               # Task-specific automation
│               ├── schedule.py
│               ├── grades.py
│               ├── financial.py
│               ├── enroll.py
│               └── holds.py
│
├── frontend/                            # Next.js 16 + React 19
│   ├── app/
│   │   ├── page.tsx                     # Landing (Three.js wave shader)
│   │   ├── connect/page.tsx             # BuckeyeLink SSO session
│   │   └── app/                         # Dashboard pages
│   │       ├── feed/
│   │       ├── academics/
│   │       ├── campus/
│   │       ├── dining/
│   │       ├── food/
│   │       └── transit/
│   └── components/
│       ├── Dither.tsx                   # Three.js dithered wave shader
│       ├── GlassPanel.tsx               # Glass morphism overlay
│       ├── LeftRail.tsx                 # Navigation sidebar
│       ├── ScanLine.tsx                 # CRT scanline effect
│       └── domain/                      # Domain-specific UI components
│
├── docs/
│   ├── USECASES.md                      # Full feature matrix (80+ use cases)
│   ├── EVENT-LOOP-PLAN.md               # Event loop architecture
│   └── osu-tech-complaints.md           # User research
│
└── .github/workflows/
    └── deploy.yml                       # CI/CD → IBM Cloud Code Engine
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 18+ (for frontend)
- A [Linq Partner API](https://dashboard.linqapp.com) account with a provisioned phone number
- IBM watsonx credentials (for Granite LLM)
- Anthropic API key (for Claude)

### 1. Clone and configure

```bash
git clone https://github.com/your-org/BuckeyeClaw.git
cd BuckeyeClaw
cp .env.example .env
# Fill in all credentials in .env
```

### 2. Install Python dependencies

```bash
pip install uv
uv sync
```

For optional integrations:

```bash
uv sync --extra grubhub       # Grubhub (requires Android emulator)
uv sync --extra buckeyelink    # BuckeyeLink (requires Playwright)
```

### 3. Register Linq webhook (one-time)

```bash
curl -X POST https://api.linqapp.com/api/partner/v3/webhook-subscriptions \
  -H "Authorization: Bearer $LINQ_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://your-domain/webhook",
    "subscribed_events": [
      "message.received", "message.delivered", "message.read", "message.failed",
      "reaction.added", "reaction.removed",
      "chat.typing_indicator.started", "chat.typing_indicator.stopped"
    ]
  }'
```

Save the returned `signing_secret` as `LINQ_WEBHOOK_SECRET` in your `.env`.

### 4. Run the agent

```bash
uv run python main.py
```

The Flask webhook server starts on port 5000 (configurable via `PORT` env var).

### 5. Run the frontend (optional)

```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `LINQ_API_TOKEN` | Yes | Bearer token from [dashboard.linqapp.com](https://dashboard.linqapp.com) |
| `LINQ_FROM_NUMBER` | Yes | E.164 phone number provisioned by Linq |
| `LINQ_WEBHOOK_SECRET` | Yes | HMAC signing secret from webhook registration |
| `LINQ_PREFERRED_SERVICE` | No | `iMessage` (default), `RCS`, or `SMS` |
| `WATSONX_API_KEY` | Yes | IBM watsonx API key |
| `WATSONX_PROJECT_ID` | Yes | IBM watsonx project ID |
| `WATSONX_API_URL` | No | Defaults to `https://us-south.ml.cloud.ibm.com` |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `OSU_USERNAME` | For BuckeyeLink | OSU login username |
| `OSU_PASSWORD` | For BuckeyeLink | OSU login password |
| `CANVAS_API_URL` | For Canvas | `https://osu.instructure.com` |
| `CANVAS_API_TOKEN` | For Canvas | Generate at carmen.osu.edu/profile/settings |
| `GRUBHUB_EMAIL` | For Grubhub | Grubhub account email |
| `GRUBHUB_PASSWORD` | For Grubhub | Grubhub account password |

---

## Deployment

### Docker

```bash
docker build -t buckeyeclaw .
docker run -p 5000:5000 --env-file .env buckeyeclaw
```

### IBM Cloud Code Engine (CI/CD)

Pushes to `main` trigger automatic deployment via GitHub Actions:

1. Builds a `linux/amd64` Docker image
2. Pushes to IBM Container Registry (`icr.io/buckeyeclaw/buckeyeclaw:latest`)
3. Updates the Code Engine application

**Required GitHub Secrets:**
- `IBM_API_KEY` — IBM Cloud API key with Code Engine and Container Registry access

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Agent Framework** | [BeeAI Framework](https://framework.beeai.dev) (Linux Foundation) |
| **Intake LLM** | IBM Granite 3 8B via watsonx |
| **Execution LLM** | Anthropic Claude Opus 4.6 |
| **Messaging** | Linq Partner API v3 (iMessage, RCS, SMS) |
| **Backend** | Python 3.11, Flask, httpx (async) |
| **Frontend** | Next.js 16, React 19, Tailwind CSS, Three.js, Framer Motion |
| **Browser Automation** | Playwright, browser-use |
| **Mobile Automation** | Appium (Android emulator) |
| **Canvas** | canvasapi Python SDK |
| **Scheduling** | APScheduler + SQLite |
| **Packaging** | uv, Docker |
| **CI/CD** | GitHub Actions → IBM Cloud Code Engine |

---

## Example Conversations

```
You: What's open for dinner right now?
Bot: 👍 (tapback)
Bot: On it! Give me a sec...
Bot: Scott & Traditions are open until 9pm tonight.
     Scott has grilled chicken, pasta bar, and a taco station.
     Traditions has burgers and a stir-fry bar.

You: When's the next CABS bus on the Campus Loop?
Bot: 👍
Bot: There are 3 Campus Loop (CLS) buses running right now.
     Nearest to you: Bus 4012 heading north on High St,
     arriving at 12th Ave stop in ~3 min.

You: Order me Raising Cane's at 6pm
Bot: 👍
Bot: Scheduling your Cane's order for 6:00 PM today.
     I'll place it automatically — you'll get a confirmation
     when it goes through.

You: What's my GPA this semester?
Bot: 👍
Bot: Your Fall 2025 GPA is 3.67.
     MATH 2153: A (4.0) | CSE 2221: A- (3.7)
     ENGLISH 1110: B+ (3.3) | PHYSICS 1251: A (4.0)
```

---

## Documentation

- [`docs/USECASES.md`](docs/USECASES.md) — Full feature matrix with 80+ use cases, tool names, and example prompts
- [`docs/EVENT-LOOP-PLAN.md`](docs/EVENT-LOOP-PLAN.md) — Event loop architecture design
- [`CLAUDE.md`](CLAUDE.md) — Project conventions and framework reference

---

## License

All rights reserved.
