# BuckeyeClaw

Your entire campus, one text away.

BuckeyeClaw is a locally-hosted AI agent that unifies Ohio State University's fragmented student services into a single messaging interface. Text a phone number from iMessage, RCS, or SMS and the agent handles everything — dining menus, bus tracking, Grubhub orders, class schedules, grades, financial aid, email, and 50+ more campus tools — with typing indicators, read receipts, and tapback reactions that make it feel like you're talking to a person.

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
- **Gated access** — only registered phone numbers reach the agent; unregistered numbers get a signup prompt

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

### BuckeyeMail (Microsoft 365)
- Fetch inbox messages
- Search emails by keyword, sender, or subject
- Get unread count
- Read specific email detail
- OAuth2 via Microsoft Entra ID (Azure AD)
- Per-user token persistence with automatic refresh

### Persistent Memory (pgvector + Voyage AI)
- **User facts** — key-value pairs with semantic embeddings for context-aware responses
- **Task history** — 30-day rolling window categorized into 11 domains (food, transit, canvas, etc.)
- **Scheduled jobs** — recurring tasks detected by Granite and stored as cron expressions
- **Semantic retrieval** — Voyage AI `voyage-3` embeddings (1024 dims) with pgvector cosine similarity
- Memory context injected into agent system prompt before every interaction

### Web Dashboard
- Three.js animated landing page with dithered wave shader
- Real-time agent reasoning split view — see tool calls, intent, and timing as the agent works
- Domain-specific pages for dining, transit, academics, campus, food, and email
- Memory visualization with D3-style force-directed graph
- BuckeyeLink SSO browser session with real-time screenshot streaming
- Phone registration onboarding flow
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
          │  BuckeyeMail (4 tools)       │
          └──────────────┬──────────────┘
                         │
          ┌──────────────▼──────────────┐
          │    Persistent Memory Layer   │
          │  pgvector + Voyage AI        │
          │  facts │ tasks │ jobs        │
          └─────────────────────────────┘
```

### Agent Workflow

1. **Memory Read** — Retrieve top-5 relevant user facts + all scheduled jobs via pgvector semantic search
2. **Granite Intake** — IBM Granite 3 8B (fast, cheap) classifies the user's message into one of 18 intents and extracts parameters. Simple greetings are handled directly.
3. **Claude Execution** — Claude Opus 4.6 (powerful reasoning) selects from 87 tools, executes them, and drafts a response. Skipped for simple queries.
4. **Granite Format** — Granite reformats the response as plain text under 800 characters for SMS delivery.
5. **Memory Write** — Background thread categorizes the task, detects repetition patterns, extracts facts with LLM, embeds with Voyage AI, and stores to Supabase.

### Intent Classification

```
dining_query    bus_query        parking_query     event_query
class_query     library_query    recsports_query   building_query
calendar_query  directory_query  athletics_query   merchant_query
foodtruck_query studentorg_query canvas_query      grubhub_order
buckeyelink_query  email_query  chitchat          unknown
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
│   ├── orchestrator.py                  # 3-step workflow + memory integration
│   ├── factories.py                     # Agent creation (Granite + Claude)
│   └── models.py                        # PipelineState (Pydantic)
│
├── auth/                                # Supabase auth helpers
│   ├── client.py                        # Singleton Supabase client (service role)
│   └── users.py                         # Profile lookup by phone or UUID
│
├── memory/                              # Persistent memory system
│   ├── module.py                        # MemoryModule (read/write orchestration)
│   ├── db.py                            # Supabase CRUD for facts/tasks/jobs
│   └── prompts.py                       # Granite prompts + Voyage AI embedding
│
├── backend/
│   ├── messaging/                       # Linq Partner API v3
│   │   ├── client.py                    # Async HTTP client (httpx)
│   │   ├── sender.py                    # High-level send/typing/react
│   │   ├── webhook.py                   # Flask webhook + OAuth routes
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
│       ├── buckeyelink/                 # Academic services
│       │   ├── tools.py                 # BeeAI tool wrappers (7 tools)
│       │   ├── main.py                  # Interactive CLI
│       │   ├── browser_agent.py         # browser-use Agent wrapper
│       │   ├── auth.py                  # OSU SSO authentication
│       │   ├── enhancer.py              # Claude prompt enhancement
│       │   ├── knowledge.py             # Navigation hints & sitemap
│       │   ├── config.py                # Constants
│       │   └── workflows/               # Task-specific automation
│       │       ├── schedule.py
│       │       ├── grades.py
│       │       ├── financial.py
│       │       ├── enroll.py
│       │       └── holds.py
│       │
│       └── buckeyemail/                 # Microsoft 365 email
│           ├── tools.py                 # BeeAI tool wrappers (4 tools)
│           ├── client.py                # Microsoft Graph API client
│           ├── auth.py                  # MSAL OAuth2 flow
│           └── token_store.py           # SQLite token persistence
│
├── frontend/                            # Next.js 16 + React 19
│   ├── app/
│   │   ├── page.tsx                     # Landing (Three.js wave shader)
│   │   ├── onboarding/page.tsx          # Phone registration flow
│   │   ├── connect/page.tsx             # BuckeyeLink SSO session
│   │   ├── auth/callback/route.ts       # Supabase OAuth callback
│   │   └── app/                         # Dashboard pages
│   │       ├── layout.tsx               # Auth gate + sidebar
│   │       ├── feed/page.tsx            # Real-time agent reasoning split view
│   │       ├── academics/page.tsx       # Schedule, grades, assignments
│   │       ├── campus/page.tsx          # Campus services hub
│   │       ├── dining/page.tsx          # Dining hall menus
│   │       ├── food/page.tsx            # Grubhub interface
│   │       ├── transit/page.tsx         # Bus routes & real-time tracking
│   │       ├── mail/page.tsx            # BuckeyeMail inbox
│   │       └── memory/page.tsx          # Memory graph visualization
│   ├── components/
│   │   ├── Dither.tsx                   # Three.js dithered wave shader
│   │   ├── GlassPanel.tsx               # Glass morphism overlay
│   │   ├── LeftRail.tsx                 # Navigation sidebar
│   │   ├── ScanLine.tsx                 # CRT scanline effect
│   │   ├── SMSMessageRow.tsx            # Message bubble component
│   │   ├── ToolCallCard.tsx             # Tool execution state display
│   │   └── domain/                      # Domain-specific UI components
│   └── lib/supabase/
│       ├── client.ts                    # Browser client (anon key)
│       ├── server.ts                    # Server client (cookie-based auth)
│       └── hooks.ts                     # Real-time subscriptions (messages, runs, events)
│
├── supabase/migrations/                 # Database schema
│   ├── 001_memory.sql                   # Facts, tasks, jobs tables + match_facts RPC
│   └── 002_voyage_embedding.sql         # Voyage AI 1024-dim migration
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
- A Supabase project (for auth, profiles, and memory)

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

### 3. Set up Supabase

Create a Supabase project and run the migrations in `supabase/migrations/` against your database. Then set `SUPABASE_URL` and `SUPABASE_API_KEY` (service role key) in your `.env`.

For the frontend, create `frontend/.env.local`:

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### 4. Register Linq webhook (one-time)

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

### 5. Run the agent

```bash
uv run python main.py
```

The Flask webhook server starts on port 5000 (configurable via `PORT` env var).

### 6. Run the frontend (optional)

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
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_API_KEY` | Yes | Supabase service role key (backend) |
| `VOYAGE_API_KEY` | Yes | Voyage AI API key for `voyage-3` embeddings |
| `OSU_USERNAME` | For BuckeyeLink | OSU login username |
| `OSU_PASSWORD` | For BuckeyeLink | OSU login password |
| `CANVAS_API_URL` | For Canvas | `https://osu.instructure.com` |
| `CANVAS_API_TOKEN` | For Canvas | Generate at carmen.osu.edu/profile/settings |
| `GRUBHUB_EMAIL` | For Grubhub | Grubhub account email |
| `GRUBHUB_PASSWORD` | For Grubhub | Grubhub account password |

---

## Database Schema

BuckeyeClaw uses Supabase (PostgreSQL + pgvector) with the following tables:

| Table | Purpose |
|---|---|
| `profiles` | User accounts — `id` (UUID), `phone` (E.164), `email`, `auth_id` |
| `messages` | Chat messages — `phone`, `role` (user/agent), `text`, `run_id`, `created_at` |
| `agent_runs` | Agent execution history — `status`, `intent`, `user_message`, `final_response`, `error` |
| `agent_events` | Tool-level tracing — `event_type`, `tool_name`, `tool_args`, `tool_result`, `duration_ms` |
| `memory_facts` | User facts with Voyage AI embeddings — `key`, `value`, `embedding` (VECTOR 1024) |
| `memory_tasks` | 30-day task history — `category`, `summary`, `user_id`, `created_at` |
| `memory_jobs` | Recurring scheduled jobs — `name`, `cron_expr`, `params`, `user_id` |

Key features:
- **pgvector** extension for semantic similarity search
- **`match_facts()`** RPC for top-K cosine similarity retrieval
- **Row Level Security** on all tables
- **Real-time subscriptions** for messages, agent runs, and events (used by frontend)

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
| **Embeddings** | Voyage AI `voyage-3` (1024 dims) |
| **Messaging** | Linq Partner API v3 (iMessage, RCS, SMS) |
| **Backend** | Python 3.11, Flask, httpx (async) |
| **Database** | Supabase (PostgreSQL + pgvector + Auth + Realtime) |
| **Frontend** | Next.js 16, React 19, Tailwind CSS, Three.js, Framer Motion |
| **Browser Automation** | Playwright, browser-use |
| **Mobile Automation** | Appium (Android emulator) |
| **Email** | Microsoft Graph API via MSAL |
| **Canvas** | canvasapi Python SDK |
| **Scheduling** | APScheduler + SQLite |
| **Packaging** | uv, Docker |
| **CI/CD** | GitHub Actions → IBM Cloud Code Engine |

---

## Example Conversations

```
You: What's open for dinner right now?
Bot: (tapback)
Bot: Scott & Traditions are open until 9pm tonight.
     Scott has grilled chicken, pasta bar, and a taco station.
     Traditions has burgers and a stir-fry bar.

You: When's the next CABS bus on the Campus Loop?
Bot: (tapback)
Bot: There are 3 Campus Loop (CLS) buses running right now.
     Nearest to you: Bus 4012 heading north on High St,
     arriving at 12th Ave stop in ~3 min.

You: Order me Raising Cane's at 6pm
Bot: (tapback)
Bot: Scheduling your Cane's order for 6:00 PM today.
     I'll place it automatically — you'll get a confirmation
     when it goes through.

You: What's my GPA this semester?
Bot: (tapback)
Bot: Your Fall 2025 GPA is 3.67.
     MATH 2153: A (4.0) | CSE 2221: A- (3.7)
     ENGLISH 1110: B+ (3.3) | PHYSICS 1251: A (4.0)

You: Check my email
Bot: (tapback)
Bot: You have 3 unread emails:
     1. Prof. Smith — "HW5 deadline extended to Friday"
     2. OSU Financial Aid — "Spring aid disbursement posted"
     3. CSE 2221 TA — "Lab 7 graded"
```

---

## Documentation

- [`docs/USECASES.md`](docs/USECASES.md) — Full feature matrix with 80+ use cases, tool names, and example prompts
- [`docs/EVENT-LOOP-PLAN.md`](docs/EVENT-LOOP-PLAN.md) — Event loop architecture design
- [`CLAUDE.md`](CLAUDE.md) — Project conventions and framework reference

---

## License

All rights reserved.
