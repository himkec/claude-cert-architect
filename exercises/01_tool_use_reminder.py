"""
Exercise 01: Tool Use — 3-Tool Chain
Study Guide Reference: Domain 1 (Task 1.1, 1.2), Domain 2 (Task 2.1)

Goal: Walk through each step of Claude tool use manually:
  1. Write a tool function
  2. Write a JSON schema
  3. Call Claude with the JSON schema
  4. Run the tool
  5. Add the tool result and call Claude again

The chain: get_current_datetime → add_duration_to_datetime → set_reminder
"""

import json
from datetime import datetime, timedelta
import anthropic
from dotenv import load_dotenv

load_dotenv()  # loads ANTHROPIC_API_KEY from .env

# =============================================================================
# STEP 1: Write a tool function
# =============================================================================
# These are plain Python functions that do the actual work.
# Claude never runs them directly — YOU run them on Claude's behalf.

def get_current_datetime() -> dict:
    """Return the current date and time."""
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    print(f"  [tool] get_current_datetime → {now}")
    return {"datetime": now}


def add_duration_to_datetime(datetime_str: str, hours: float, minutes: float) -> dict:
    """Add hours and minutes to a datetime string and return the result."""
    dt = datetime.fromisoformat(datetime_str)
    result = dt + timedelta(hours=hours, minutes=minutes)
    result_str = result.strftime("%Y-%m-%dT%H:%M:%S")
    print(f"  [tool] add_duration_to_datetime({datetime_str} + {hours}h {minutes}m) → {result_str}")
    return {"datetime": result_str}


def set_reminder(remind_at: str, message: str) -> dict:
    """Schedule a reminder at a given datetime with a message."""
    reminder_id = f"REM-{datetime.now().strftime('%H%M%S')}"
    print(f"  [tool] set_reminder @ {remind_at} | msg='{message}' → id={reminder_id}")
    return {
        "reminder_id": reminder_id,
        "scheduled_at": remind_at,
        "message": message,
        "status": "scheduled",
    }


# =============================================================================
# STEP 2: Write a JSON schema
# =============================================================================
# For each tool function, write a JSON schema that describes:
#   - name:         must match what you'll call in your dispatcher
#   - description:  how Claude decides WHEN to call this tool
#   - input_schema: what arguments the tool accepts (JSON Schema format)
#
# Claude reads these schemas to decide which tool to call and what to pass.

TOOLS = [
    {
        "name": "get_current_datetime",
        "description": (
            "Returns the current date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS). "
            "Call this first when you need to know what time it is right now."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},   # no inputs — tool takes no arguments
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


# =============================================================================
# STEP 3: Call Claude with the JSON schema
# =============================================================================
# Pass the tool schemas to client.messages.create() via the `tools` parameter.
# Claude will reply with stop_reason="tool_use" when it wants to call a tool,
# or stop_reason="end_turn" when it has a final answer.

def call_claude(client: anthropic.Anthropic, messages: list) -> object:
    print(f"\n  Calling Claude (turn {len([m for m in messages if m['role'] == 'user'])})...")
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},  # Claude decides how much to think
        tools=TOOLS,                     # <── schemas registered here
        messages=messages,
    )
    print(f"  stop_reason: {response.stop_reason}")
    return response


# =============================================================================
# STEP 4: Run the tool
# =============================================================================
# When Claude returns stop_reason="tool_use", inspect each content block.
# Find blocks with type="tool_use", extract block.name and block.input,
# then call the matching Python function.

def run_tool(tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call by name and return the result as a JSON string."""
    print(f"\n  Claude requested tool: {tool_name}")
    print(f"  Input: {json.dumps(tool_input, indent=4)}")

    if tool_name == "get_current_datetime":
        result = get_current_datetime()
    elif tool_name == "add_duration_to_datetime":
        result = add_duration_to_datetime(**tool_input)
    elif tool_name == "set_reminder":
        result = set_reminder(**tool_input)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}

    return json.dumps(result)


# =============================================================================
# STEP 5: Add the tool result and call Claude again
# =============================================================================
# After running the tool(s), package each result as a "tool_result" block and
# append them in a new "user" message. Then call Claude again.
# Repeat until stop_reason == "end_turn".
#
# Critical: append the full response.content (not just text) so that
# tool_use blocks are preserved for the next API call.

def run_agentic_loop(user_message: str) -> str:
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": user_message}]

    print(f"\nUser: {user_message}")
    print("=" * 60)

    while True:
        # ── Step 3: call Claude ───────────────────────────────────────────
        response = call_claude(client, messages)

        # Append Claude's full response before doing anything else
        messages.append({"role": "assistant", "content": response.content})

        # ── Done? ─────────────────────────────────────────────────────────
        if response.stop_reason == "end_turn":
            final_text = next(
                (block.text for block in response.content if hasattr(block, "text")),
                "(no text response)",
            )
            print(f"\n{'=' * 60}")
            print(f"Claude's final reply:\n{final_text}")
            return final_text

        # ── Step 4: run each requested tool ──────────────────────────────
        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type != "tool_use":
                    continue

                result_json = run_tool(block.name, block.input)

                # ── Step 5: package tool result to send back ──────────────
                # tool_use_id must match block.id so Claude knows which
                # tool call this result belongs to.
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_json,
                })

            # Add all results as a single user turn, then loop → Step 3
            messages.append({"role": "user", "content": tool_results})

        else:
            print(f"  Unexpected stop_reason: {response.stop_reason}")
            break

    return "(loop exited unexpectedly)"


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    # The prompt leaves all tool-selection decisions to Claude.
    # It will autonomously chain all 3 tools to fulfill the request.
    prompt = (
        "Set a reminder for me in 2 hours and 30 minutes from now. "
        "The reminder should say: 'Time to review the Claude tool-use chapter!'"
    )
    run_agentic_loop(prompt)
