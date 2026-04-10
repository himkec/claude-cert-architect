# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Study and exercise repository for the **Claude Certified Architect – Foundations** certification exam. It contains:
- `study-guide.md` — domain-by-domain exam notes (5 domains, cheat sheets, out-of-scope topics)
- `tool-use-with-claude.md` — reference guide for the Claude Messages API tool use pattern
- `exercises/` — runnable Python exercises and Jupyter notebooks

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your ANTHROPIC_API_KEY
```

## Running exercises

```bash
# Python scripts
source .venv/bin/activate
python exercises/01_tool_use_reminder.py

# Jupyter notebooks
jupyter notebook exercises/001_tools.ipynb
```

## Architecture

All exercises use the **Anthropic Python SDK** (`anthropic`) with `load_dotenv()` to pull `ANTHROPIC_API_KEY` from `.env`. The canonical agentic loop pattern used throughout:

1. Call `client.messages.create(model=..., tools=TOOLS, messages=messages)`
2. Append the full `response.content` to `messages` (preserves `tool_use` block IDs)
3. If `stop_reason == "tool_use"` → dispatch tools, append `tool_result` blocks as a new user turn, repeat
4. If `stop_reason == "end_turn"` → done

Tool schemas follow `{name, description, input_schema}` where `description` drives Claude's routing decisions — specificity matters.

## Exam domain weights (for prioritizing study)

| Domain | Weight |
|--------|--------|
| Agentic Architecture & Orchestration | 27% |
| Claude Code Configuration & Workflows | 20% |
| Prompt Engineering & Structured Output | 20% |
| Tool Design & MCP Integration | 18% |
| Context Management & Reliability | 15% |
