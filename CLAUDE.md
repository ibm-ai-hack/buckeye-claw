# BuckeyeBot — Unified OSU Student Agent

## Project Overview

A locally-hosted AI agent that unifies several endpoints used by Ohio State University students into a single messaging interface. Users text a Linq-provisioned phone number (iMessage, RCS, or SMS) and the agent autonomously handles requests across campus services, food ordering, and academic tools — with typing indicators, read receipts, and tapback reactions that make it feel alive.

**Core capabilities:**
- **Campus Services** — dining, bus tracking, parking, events, libraries, rec sports, and 50+ OSU APIs via the Ohio State MCP server
- **Food Ordering** — place Grubhub orders through Android emulation scripts
- **Academic Tools** — access BuckeyeLink services (scheduling, financial aid, grades) via browser automation
- **Messaging Interface** — iMessage (blue bubbles), RCS, and SMS via Linq Partner API with typing indicators, read receipts, and emoji reactions

## Architecture

### Agent Layer — BeeAI Framework

Built on the **BeeAI Framework** (Linux Foundation) for multi-agent orchestration in Python.

- **Docs**: https://framework.beeai.dev
- **GitHub**: https://github.com/i-am-bee/beeai-framework

Use `RequirementAgent` as the default agent type with declarative rule-based constraints:

```python
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.backend import ChatModel
from beeai_framework.memory import TokenMemory
```

Key conventions:
- Prefer `ChatModel.from_name()` for backend initialization
- Use `TokenMemory` for production; `UnconstrainedMemory` for prototyping
- Use `@tool` decorator for custom tools
- Wrap agent runs in `try/except FrameworkError`

### Messaging Interface — Linq Partner API

- **Linq Partner API v3** — native iMessage, RCS, and SMS messaging
- Users text the Linq-provisioned phone number; iMessage is preferred with automatic SMS fallback
- **Alive features:**
  - Typing indicators — dots appear while the agent processes
  - Read receipts — messages marked as read on receipt
  - Tapback reactions — auto-acknowledges messages with a thumbs-up
  - Rich media — supports images, videos, and file attachments
- **Architecture:** Flask webhook at `/webhook` receives JSON events from Linq, returns `200 OK` immediately, processes in background thread, sends replies via separate API call
- **Modules:** `messaging/client.py` (HTTP client), `messaging/sender.py` (high-level send/typing/react), `messaging/webhook.py` (Flask handler), `messaging/verify.py` (HMAC signature verification), `messaging/events.py` (event parsing), `messaging/chat_store.py` (phone-to-chat-ID cache)

### Campus APIs — Ohio State MCP Server

The [ohio-state-mcp-server](https://mcpmarket.com/server/ohio-state) provides 50+ tools across 14 categories:

| Category | Key Tools |
|---|---|
| **Dining** | `get_dining_locations`, `get_dining_menu`, `get_dining_locations_with_menus` |
| **Bus Transportation** | `get_bus_routes`, `get_bus_stops`, `get_bus_vehicles` (real-time) |
| **Parking** | `get_parking_availability` (real-time garage availability) |
| **Classes** | `search_classes` (by keyword, subject, instructor) |
| **Campus Events** | `get_campus_events`, `search_campus_events`, `get_events_by_date_range` |
| **Libraries** | `get_library_locations`, `get_library_rooms`, `get_rooms_by_capacity` |
| **Rec Sports** | `get_recsports_facilities`, `get_facility_hours`, `get_facility_events` |
| **BuckID Merchants** | `get_buckid_merchants`, `get_merchants_with_meal_plan` |
| **Athletics** | `get_upcoming_games`, `search_sports` |
| **Buildings** | `get_buildings`, `search_buildings`, `find_room_type` |
| **Food Trucks** | `get_foodtruck_events`, `search_foodtrucks` |
| **Student Orgs** | `get_student_organizations`, `search_student_orgs` |
| **Calendar** | `get_academic_calendar`, `get_university_holidays` |
| **Directory** | `search_people` |

### Food Ordering — Grubhub via Android Emulation

Android emulation scripts to automate Grubhub ordering on behalf of the user. This handles the full order flow (restaurant selection, menu browsing, cart, checkout) through scripted UI interactions on an emulated Android device.

### Academic Tools — BuckeyeLink via Browser Automation

Browser automation (e.g., Playwright/Selenium) to access tools within http://buckeyelink.osu.edu/ including:
- Class scheduling and registration
- Financial aid status
- Grade and transcript access
- Student account and billing

## Environment

- Linq and LLM credentials stored in `.env` (gitignored)
- MCP servers configured per-project in Claude Code's local config
- Ohio State MCP server: `ohio-state-mcp-server`

### Required Environment Variables

```
# Linq Partner API
LINQ_API_TOKEN=           # Bearer token from dashboard.linqapp.com
LINQ_FROM_NUMBER=         # E.164 phone number provisioned by Linq
LINQ_WEBHOOK_SECRET=      # HMAC signing secret (from webhook registration)
LINQ_PREFERRED_SERVICE=iMessage  # iMessage | RCS | SMS

# IBM watsonx
WATSONX_API_KEY=
WATSONX_PROJECT_ID=
WATSONX_API_URL=https://us-south.ml.cloud.ibm.com
```

## Setup

1. Copy `.env.example` to `.env` and fill in credentials
2. Install Python dependencies: `pip install beeai-framework`
3. Install the Ohio State MCP server: `npx ohio-state-mcp-server` (or configure in MCP settings)
4. (Optional) Install Ollama and pull a model: `ollama pull granite3.3`
5. Register your Linq webhook (one-time):
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

## BeeAI Framework Quick Reference

### Agent Types

| Agent | When to Use |
|---|---|
| **RequirementAgent** | Default — declarative constraints, predictable execution (Python only) |
| **ReActAgent** | Fallback — classic reasoning + acting loop (Python & TypeScript) |

### Core Modules

| Module | Purpose |
|---|---|
| **Agents** | Core reasoning loop |
| **Backend** | Unified LLM provider interface (`ChatModel`) |
| **Tools** | Built-in + custom tools via `@tool` decorator |
| **Memory** | `TokenMemory` (production), `UnconstrainedMemory` (prototyping) |
| **Workflows** | Multi-agent orchestration via `@workflow.step()` |
| **Cache** | `SlidingCache`, `UnconstrainedCache` |
| **Errors** | `FrameworkError` hierarchy with `.explain()` |

### LLM Providers

```python
ChatModel.from_name("ollama:granite3.3")       # Local
ChatModel.from_name("anthropic:claude-sonnet-4") # Anthropic
ChatModel.from_name("openai:gpt-5-mini")        # OpenAI
ChatModel.from_name("watsonx:ibm/granite-3-8b-instruct")  # IBM watsonx
```

### Custom Tools

```python
from beeai_framework.tools import StringToolOutput, tool

@tool
def my_tool(param: str) -> StringToolOutput:
    """Tool description for the agent."""
    return StringToolOutput(result)
```

### Workflows (Multi-Agent)

```python
from beeai_framework.workflows import Workflow
from pydantic import BaseModel

class State(BaseModel):
    query: str
    result: str | None = None

workflow = Workflow(State)

@workflow.step()
async def handle(state: State) -> None:
    response = await agent.run(state.query)
    state.result = response.last_message.text
```

## Useful Commands

```bash
# Run the agent
uv run python main.py

# Start Ollama (if using local LLM)
ollama serve

# Install dependencies
pip install beeai-framework
```
