# Tool use with Claude

This guide walks through how **tool use** works on the Claude Messages API: you register tools with JSON schemas, Claude may respond with `tool_use` blocks, your code runs the matching functions, and you send structured `tool_result` blocks back—often in a loop until Claude finishes with plain text.

Examples use the official [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) (`anthropic`). A runnable chain that mirrors this flow lives in [`exercises/01_tool_use_reminder.py`](exercises/01_tool_use_reminder.py).

---

## 1. Introduction

**What tool use is.** Claude stays inside the model; it cannot open databases, call your HTTP APIs, or read private files by itself. Tool use is a contract: you describe capabilities as **named tools** with **input schemas**. Claude returns a structured request (`tool_use`) instead of (or alongside) natural language. Your application executes the tool, then **returns the outcome** in the next message so Claude can continue reasoning.

**Why it matters.** You get grounded actions (queries, mutations, lookups) while keeping the model responsible for *when* and *with what arguments* to call—subject to your schemas and prompts.

**High-level loop.**

1. You send user messages (and prior turns) plus `tools=[...]`.
2. If `stop_reason == "tool_use"`, the model’s last assistant message contains one or more `tool_use` blocks.
3. You run your functions, append a user message whose `content` is a list of `tool_result` blocks (IDs must match).
4. Call the API again. Repeat until `stop_reason == "end_turn"` (or you hit limits you define).

```python
import anthropic

client = anthropic.Anthropic()
# tools: list of {name, description, input_schema} — see §3
# messages: alternating user / assistant turns — see §4–§6

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=messages,
)
# Inspect response.stop_reason and response.content next.
```

**How it works.** The API does not execute your tools. It only emits structured `tool_use` payloads. Your process is the **executor**; that separation is what makes tool use safe and controllable (you can log, validate, rate-limit, or refuse calls).

---

## 2. Tool functions

**Tool functions** are ordinary functions in your language/runtime (here, Python). They should be deterministic where possible, validate inputs, and return data that is easy for the model to consume—often JSON-serializable dicts that you stringify before sending back.

```python
from datetime import datetime, timedelta

def add_duration_to_datetime(datetime_str: str, hours: float, minutes: float) -> dict:
    """Add hours and minutes to an ISO-like datetime string."""
    dt = datetime.fromisoformat(datetime_str)
    result = dt + timedelta(hours=hours, minutes=minutes)
    return {"datetime": result.strftime("%Y-%m-%dT%H:%M:%S")}
```

**How it works.** Claude never imports or calls this function. You map `tool_use.name` → `add_duration_to_datetime` in a small dispatcher. That keeps a clear boundary: the model proposes *intent*; your code enforces *authority* (permissions, side effects, real-world correctness).

```python
import json

def run_tool(name: str, arguments: dict) -> str:
    if name == "add_duration_to_datetime":
        payload = add_duration_to_datetime(**arguments)
    else:
        payload = {"error": f"unknown tool: {name}"}
    return json.dumps(payload)
```

---

## 3. Tool schema

Each tool is declared to the API as metadata the model reads at request time: **`name`** (stable identifier), **`description`** (when/why to use it—this drives routing quality), and **`input_schema`** (JSON Schema for the tool’s arguments).

```python
TOOLS = [
    {
        "name": "add_duration_to_datetime",
        "description": (
            "Adds a duration to a given datetime in ISO 8601 format (YYYY-MM-DDTHH:MM:SS). "
            "Use when the user needs a future or past time relative to a known timestamp."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "Starting datetime, ISO 8601.",
                },
                "hours": {"type": "number", "description": "Hours to add (may be 0)."},
                "minutes": {"type": "number", "description": "Minutes to add (may be 0)."},
            },
            "required": ["datetime_str", "hours", "minutes"],
        },
    },
]
```

**How it works.** The model uses `description` to choose among tools and uses `input_schema` to shape JSON arguments. Vague descriptions or overlapping tools lead to mis-routing; tight schemas reduce invalid inputs. You pass `tools=TOOLS` into `client.messages.create(...)`.

---

## 4. Handling message blocks

A **message** has a `role` (`user` or `assistant`) and `content`. `content` is a **list of blocks**, not necessarily a single string. Assistant replies may include `text`, `tool_use`, and (if enabled) other block types. Your loop should iterate blocks by `type`.

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=TOOLS,
    messages=messages,
)

for block in response.content:
    if block.type == "text":
        print("Assistant text:", block.text)
    elif block.type == "tool_use":
        print("Tool call:", block.name, block.input, "id=", block.id)
```

**How it works.** Treat `response.content` as ordered: the model may interleave short explanations with tool calls. For the **next** API request you must append the **entire** assistant `content` list you received (see §6)—not only the text—so that each `tool_use` block keeps its `id` for pairing with `tool_result`.

---

## 5. Sending tool results

When you execute a tool, you send a **user** message whose `content` contains one `tool_result` per executed call. Each result must reference the corresponding `tool_use` block via **`tool_use_id`**. The `content` field is typically a string (often JSON) the model will read.

```python
tool_results = []
for block in response.content:
    if block.type != "tool_use":
        continue
    output = run_tool(block.name, block.input)
    tool_results.append(
        {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": output,
        }
    )

messages.append({"role": "user", "content": tool_results})
```

**How it works.** IDs tie causes to effects: if the model issued two tools in one turn, you must return two results with matching IDs. If a tool fails, you can still return structured JSON; some clients also set an error flag so the model treats the outcome as a failure (check current API/SDK fields for your version).

---

## 6. Multi-turn conversation with tools

A **multi-turn** tool conversation is the same as a normal chat, except some assistant turns are followed by a **synthetic user turn** that carries only `tool_result` blocks (instead of human text). The transcript grows: user → assistant (maybe `tool_use`) → user (`tool_result`) → assistant → …

```text
Turn A — user:       "What time is it in two hours?"
Turn B — assistant:  [tool_use: get_time]
Turn C — user:       [tool_result for that id]
Turn D — assistant:  [text answer]
```

**How it works.** Claude’s reasoning is stateful across turns as long as you preserve the full sequence. Omitting an assistant `tool_use` block or mismatching IDs breaks the contract and typically causes API errors or confused replies.

---

## 7. Implementing multiple turns

The usual pattern is an **agentic loop**: call the API, append the assistant message, if `stop_reason == "tool_use"` then append tool results and repeat; if `stop_reason == "end_turn"`, stop.

```python
import json
import anthropic

def agent_loop(client: anthropic.Anthropic, user_text: str, tools: list) -> str:
    messages = [{"role": "user", "content": user_text}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            tools=tools,
            messages=messages,
        )

        # Preserve the full assistant message for the next request.
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    return block.text
            return ""

        if response.stop_reason == "tool_use":
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": run_tool(block.name, block.input),
                        }
                    )
            messages.append({"role": "user", "content": results})
            continue

        # Other stop reasons (e.g. max_tokens): handle explicitly in production.
        break

    return ""
```

**How it works.** `stop_reason` is your control signal: **`tool_use`** means “I need execution”; **`end_turn`** means “I’m done for now.” The loop is the minimal orchestration layer between the API and your runtime. For production, add logging, timeouts, max-iteration guards, and explicit handling for truncation.

---

## 8. Using multiple tools

Claude may emit **several `tool_use` blocks in one assistant message** (e.g. fetch two records in parallel). You should execute all requested tools for that turn, then send **one** user message containing **all** `tool_result` blocks.

```python
def handle_tool_use_turn(response, run_tool_fn):
    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": run_tool_fn(block.name, block.input),
                }
            )
    return tool_results

# After response with multiple tool_use blocks:
# messages.append({"role": "user", "content": handle_tool_use_turn(response, run_tool)})
```

**How it works.** Batching results mirrors the batching of requests: one assistant turn with N tools → one user turn with N results. Order is not a substitute for `tool_use_id`; always key by ID. You can choose to run tools in parallel in your app (threads/async) as long as you collect all results before the next `messages.create`.

---

## 9. Fine-grained tool calling

Beyond listing tools, the API exposes **`tool_choice`** to constrain *whether* and *which* tool is used. In the Python SDK, choices include:

- **`{"type": "auto"}`** — Claude decides whether to use a tool or respond with text (default behavior).
- **`{"type": "any"}`** — Claude must use one of the provided tools (useful when you want structured extraction or guaranteed action).
- **`{"type": "tool", "name": "add_duration_to_datetime"}`** — Forces use of a specific tool by name.
- **`{"type": "none"}`** — Disallows tools for that request.

For **parallelism**, tool choice objects support **`disable_parallel_tool_use`**: when `True`, the model is limited to **at most one** `tool_use` block for that request—useful when operations must be sequential or when your executor cannot safely run calls in parallel.

```python
# Force exactly one tool call, and require it to be this tool.
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=TOOLS,
    tool_choice={
        "type": "tool",
        "name": "add_duration_to_datetime",
        "disable_parallel_tool_use": True,
    },
    messages=messages,
)

# Allow tools, but cap at one tool_use block per assistant message.
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=TOOLS,
    tool_choice={"type": "auto", "disable_parallel_tool_use": True},
    messages=messages,
)
```

**How it works.** `tool_choice` shapes exploration vs exploitation: `"auto"` for open Q&A, `"any"` when every user turn should hit your tool layer, forced `"tool"` for rigid pipelines (e.g. always normalize input through a validator tool first). `disable_parallel_tool_use` is the fine-grained switch for single-flight tool execution per model turn.

---

## Summary

| Topic | Takeaway |
|--------|-----------|
| Tool functions | Your code runs them; Claude only requests them via `tool_use`. |
| Tool schema | `name`, `description`, and `input_schema` drive selection and arguments. |
| Message blocks | Assistant `content` may mix `text` and `tool_use`; preserve full lists in history. |
| Tool results | User message with `tool_result` items keyed by `tool_use_id`. |
| Multi-turn | Alternate model turns with tool-result turns until `end_turn`. |
| Multiple tools | One assistant turn may request N tools; reply with N results in one user turn. |
| Fine-grained control | `tool_choice` and `disable_parallel_tool_use` constrain tool behavior per request. |

For a full end-to-end example (three chained tools), run [`exercises/01_tool_use_reminder.py`](exercises/01_tool_use_reminder.py).
