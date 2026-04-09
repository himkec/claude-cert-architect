"""
Exercise 01: Tool Use — 3-Tool Chain
Study Guide Reference: Domain 1 (Task 1.1, 1.2), Domain 2 (Task 2.1)

Goal: Demonstrate the full agentic loop where Claude chains 3 tools:
  get_current_datetime → add_duration_to_datetime → set_reminder

Key concepts practiced:
  - Defining tools with JSON schemas (input_schema)
  - Running the agentic loop: check stop_reason == "tool_use"
  - Executing tool functions and returning results as tool_result blocks
  - Claude autonomously deciding the order and parameters of tool calls
"""

import json
from datetime import datetime, timedelta
import anthropic

# ─── 1. Tool Definitions ────────────────────────────────────────────────────
# Each tool is a dict with: name, description, input_schema (JSON Schema)
# Claude uses description + schema to decide when/how to call the tool.

TOOLS = [
    {
        "name": "get_current_datetime",
        "description": (
            "Returns the current date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS). "
            "Call this first when you need to know what time it is right now."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},          # no inputs needed
            "required": [],
        },
    },
    {
        "name": "add_duration_to_datetime",
        "description": (
            "Adds a duration to a given datetime and returns the resulting datetime "
            "in ISO 8601 format. Use this to calculate a future point in time."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "Starting datetime in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)",
                },
                "hours": {
                    "type": "number",
                    "description": "Hours to add (can be 0)",
                },
                "minutes": {
                    "type": "number",
                    "description": "Minutes to add (can be 0)",
                },
            },
            "required": ["datetime_str", "hours", "minutes"],
        },
    },
    {
        "name": "set_reminder",
        "description": (
            "Schedules a reminder message at a specific datetime. "
            "Returns a confirmation with the reminder ID."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "remind_at": {
                    "type": "string",
                    "description": "When to trigger the reminder, in ISO 8601 format",
                },
                "message": {
                    "type": "string",
                    "description": "The reminder message to display to the user",
                },
            },
            "required": ["remind_at", "message"],
        },
    },
]


# ─── 2. Tool Implementations (mock) ─────────────────────────────────────────
# In production these would call real services. Here we simulate them.

def get_current_datetime() -> dict:
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    print(f"  [tool] get_current_datetime → {now}")
    return {"datetime": now}


def add_duration_to_datetime(datetime_str: str, hours: float, minutes: float) -> dict:
    dt = datetime.fromisoformat(datetime_str)
    result = dt + timedelta(hours=hours, minutes=minutes)
    result_str = result.strftime("%Y-%m-%dT%H:%M:%S")
    print(f"  [tool] add_duration_to_datetime({datetime_str} + {hours}h {minutes}m) → {result_str}")
    return {"datetime": result_str}


def set_reminder(remind_at: str, message: str) -> dict:
    reminder_id = f"REM-{datetime.now().strftime('%H%M%S')}"
    print(f"  [tool] set_reminder @ {remind_at} | msg='{message}' → id={reminder_id}")
    return {
        "reminder_id": reminder_id,
        "scheduled_at": remind_at,
        "message": message,
        "status": "scheduled",
    }


# ─── 3. Tool Dispatcher ──────────────────────────────────────────────────────
# Maps tool names to their Python functions and executes them.

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name and return its result as a JSON string."""
    if tool_name == "get_current_datetime":
        result = get_current_datetime()
    elif tool_name == "add_duration_to_datetime":
        result = add_duration_to_datetime(**tool_input)
    elif tool_name == "set_reminder":
        result = set_reminder(**tool_input)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result)


# ─── 4. Agentic Loop ─────────────────────────────────────────────────────────
# Core pattern (Domain 1.1):
#   request → if stop_reason=="tool_use": run tools, append results → repeat
#   until stop_reason=="end_turn"

def run_agentic_loop(user_message: str) -> str:
    client = anthropic.Anthropic()

    messages = [{"role": "user", "content": user_message}]

    print(f"\nUser: {user_message}\n")
    print("─" * 60)

    turn = 0
    while True:
        turn += 1
        print(f"\n[Turn {turn}] Calling Claude...")

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            thinking={"type": "adaptive"},   # let Claude decide thinking depth
            tools=TOOLS,
            messages=messages,
        )

        print(f"  stop_reason: {response.stop_reason}")

        # ── Append Claude's response to the conversation ──────────────────
        # We must append the full content list (not just text) so tool_use
        # blocks are preserved for the next request.
        messages.append({"role": "assistant", "content": response.content})

        # ── Check termination ─────────────────────────────────────────────
        if response.stop_reason == "end_turn":
            # Extract the final text reply
            final_text = next(
                (block.text for block in response.content if hasattr(block, "text")),
                "(no text response)",
            )
            print(f"\n[Done] Claude's final reply:\n{final_text}")
            return final_text

        # ── Handle tool calls ─────────────────────────────────────────────
        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type != "tool_use":
                    continue

                print(f"\n  Claude wants to call: {block.name}")
                print(f"  Input: {json.dumps(block.input, indent=4)}")

                # Execute the tool
                result_json = execute_tool(block.name, block.input)

                # Build the tool_result block to send back
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,   # must match the tool_use block id
                    "content": result_json,
                })

            # Append all tool results in a single user turn
            messages.append({"role": "user", "content": tool_results})

        else:
            # Unexpected stop_reason — surface it and exit
            print(f"  Unexpected stop_reason: {response.stop_reason}")
            break

    return "(loop exited unexpectedly)"


# ─── 5. Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # The prompt intentionally leaves all decisions to Claude:
    # which tools to call, in what order, and with what parameters.
    prompt = (
        "Set a reminder for me in 2 hours and 30 minutes from now. "
        "The reminder should say: 'Time to review the Claude tool-use chapter!'"
    )
    run_agentic_loop(prompt)
