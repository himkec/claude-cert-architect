## Claude Certified Architect

Study material and hands-on exercises for the Claude Certified Architect – Foundations certification exam.

## Setup

**1. Clone the repo**
```bash
git clone git@github.com:himkec/claude-cert-architect.git
cd claude-cert-architect
```

**2. Create and activate a virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure your API key**
```bash
cp .env.example .env
```
Edit `.env` and replace `your_api_key_here` with your Anthropic API key from [console.anthropic.com](https://console.anthropic.com).

## Running the exercises

```bash
python3 exercises/01_tool_use_reminder.py
```

## Exercises

| File | Topic | Study Guide Domain |
|---|---|---|
| `exercises/01_tool_use_reminder.py` | Tool use — 3-tool chained agentic loop | Domain 1 (Task 1.1, 1.2) |

## Study Guide

See [`study-guide.md`](study-guide.md) for the full breakdown of all 5 exam domains and 26 task statements.
