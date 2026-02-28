# BuckeyeLink Automation

Hybrid browser automation for OSU's BuckeyeLink portal using **Browser Use** (AI agent) + **Playwright** (deterministic scripts).

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  main.py (CLI)                   │
│         Choose workflow → run it                 │
├─────────────────────────────────────────────────┤
│                                                  │
│  auth.py          → Playwright (deterministic)   │
│  ├─ Fill creds                                   │
│  ├─ Wait for Duo MFA (human approves push)       │
│  └─ Confirm post-auth landing                    │
│                                                  │
│  workflows/                                      │
│  ├─ enroll.py     → AI agent (dynamic forms)     │
│  ├─ grades.py     → Hybrid (navigate + extract)  │
│  └─ financial.py  → Hybrid (navigate + extract)  │
│                                                  │
├─────────────────────────────────────────────────┤
│  Browser Use + Playwright (shared browser)       │
└─────────────────────────────────────────────────┘
```

## Setup

### 1. Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### 2. Install

```bash
# Clone or copy this project
cd buckeyelink-automation

# Using uv (recommended)
uv venv --python 3.11
source .venv/bin/activate   # Mac/Linux
# .venv\Scripts\activate    # Windows

uv pip install browser-use playwright python-dotenv
uv run playwright install chromium

# Or using pip
pip install browser-use playwright python-dotenv
playwright install chromium
```

### 3. Configure

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
OSU_USERNAME=lastname.123
OSU_PASSWORD=your_password
ANTHROPIC_API_KEY=sk-ant-...    # or use OPENAI_API_KEY
```

### 4. Run

```bash
python main.py
```

You'll be prompted to choose a workflow. When Duo MFA is triggered, you'll see a console message — approve the push on your phone, and the script continues automatically.

## Workflows

### 1. Class Enrollment (`enroll`)
- AI agent navigates the Student Center → Enrollment
- Searches for classes by subject/catalog number
- Handles dynamic dropdowns, section selection
- You confirm before final enrollment

### 2. Check Grades (`grades`)
- Deterministic navigation to grades page
- AI extracts and formats your grades/GPA
- Optionally exports to JSON/CSV

### 3. Financial Aid / Billing (`financial`)
- Navigates to financial center
- AI extracts current balance, aid status, charges
- Summarizes everything in a clean format

## Customization

### Adding a new workflow
1. Create `workflows/my_workflow.py`
2. Define either a deterministic Playwright function or an AI agent task
3. Register it in `main.py`

### Switching LLM provider
In `.env`, set one of:
```
ANTHROPIC_API_KEY=...   # Uses Claude
OPENAI_API_KEY=...      # Uses GPT-4
```

Then update `config.py` accordingly.
