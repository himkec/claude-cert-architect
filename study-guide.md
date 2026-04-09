# Claude Certified Architect – Foundations Study Guide

## Exam Overview

- **Format:** Multiple choice, 4 options per question (1 correct, 3 distractors)
- **Scoring:** 100–1,000 scaled score; minimum passing score **720**
- **Scenarios:** 4 of 6 scenarios presented at random per exam
- **No penalty** for guessing — answer every question

---

## Domain Weightings

| Domain | Weight |
|--------|--------|
| Domain 1: Agentic Architecture & Orchestration | 27% |
| Domain 2: Tool Design & MCP Integration | 18% |
| Domain 3: Claude Code Configuration & Workflows | 20% |
| Domain 4: Prompt Engineering & Structured Output | 20% |
| Domain 5: Context Management & Reliability | 15% |

---

## Exam Scenarios (6 total, 4 appear on exam)

| # | Scenario | Primary Domains |
|---|----------|----------------|
| 1 | Customer Support Resolution Agent | D1, D2, D5 |
| 2 | Code Generation with Claude Code | D3, D5 |
| 3 | Multi-Agent Research System | D1, D2, D5 |
| 4 | Developer Productivity with Claude | D2, D3, D1 |
| 5 | Claude Code for Continuous Integration | D3, D4 |
| 6 | Structured Data Extraction | D4, D5 |

---

## Domain 1: Agentic Architecture & Orchestration (27%)

### 1.1 Agentic Loops for Autonomous Task Execution

**Know:**
- Agentic loop lifecycle: request → inspect `stop_reason` → execute tools → return results → repeat
- `stop_reason: "tool_use"` → continue; `stop_reason: "end_turn"` → terminate
- Tool results appended to conversation history between iterations
- Model-driven decision-making vs pre-configured decision trees

**Avoid (anti-patterns):**
- Parsing natural language to determine loop termination
- Arbitrary iteration caps as primary stopping mechanism
- Checking assistant text content as completion indicator

---

### 1.2 Multi-Agent Systems: Coordinator-Subagent Patterns

**Know:**
- Hub-and-spoke architecture: coordinator manages all inter-subagent communication
- Subagents have **isolated context** — they do NOT inherit coordinator's history
- Coordinator responsibilities: task decomposition, delegation, result aggregation
- Risk: overly narrow decomposition → incomplete topic coverage

**Skills:**
- Coordinator dynamically selects subagents based on query (not always full pipeline)
- Partition research scope to minimize duplication across subagents
- Iterative refinement: coordinator evaluates gaps → re-delegates → re-synthesizes
- Route all subagent communication through coordinator for observability

---

### 1.3 Subagent Invocation, Context Passing, and Spawning

**Know:**
- `Task` tool spawns subagents; `allowedTools` must include `"Task"` for coordinator
- Subagent context must be **explicitly provided** in the prompt
- `AgentDefinition`: descriptions, system prompts, tool restrictions per subagent
- Fork-based session management for divergent approaches from shared baseline

**Skills:**
- Include complete findings from prior agents directly in subagent prompt
- Use structured data to separate content from metadata (source URLs, page numbers)
- Spawn parallel subagents: emit **multiple Task tool calls in a single response**
- Coordinator prompts specify goals/quality criteria, not step-by-step instructions

---

### 1.4 Multi-Step Workflows with Enforcement and Handoff Patterns

**Know:**
- Programmatic enforcement (hooks, prerequisite gates) vs prompt-based guidance
- Prompt instructions alone have non-zero failure rate for deterministic compliance
- Structured handoff protocols: customer details + root cause + recommended actions

**Skills:**
- Programmatic prerequisites block downstream tools until prerequisites complete
  - e.g., block `process_refund` until `get_customer` returns verified customer ID
- Decompose multi-concern requests → investigate in parallel → unified resolution
- Compile structured handoff summaries when escalating to human agents

---

### 1.5 Agent SDK Hooks for Tool Call Interception and Data Normalization

**Know:**
- `PostToolUse` hooks: intercept tool results for transformation before model processes them
- Hook patterns to intercept outgoing tool calls and enforce compliance rules
- Hooks = deterministic guarantees; prompts = probabilistic compliance

**Skills:**
- `PostToolUse` to normalize heterogeneous data formats (Unix timestamps, ISO 8601, numeric status codes)
- Interception hooks to block policy-violating actions (e.g., refunds > $500) and redirect to escalation
- Choose hooks over prompt-based enforcement when guaranteed compliance is required

---

### 1.6 Task Decomposition Strategies for Complex Workflows

**Know:**
- Fixed sequential pipelines (prompt chaining) vs dynamic adaptive decomposition
- Prompt chaining: break reviews into sequential steps (per-file → cross-file integration pass)
- Adaptive investigation: generate subtasks based on what is discovered at each step

**Skills:**
- Prompt chaining for predictable multi-aspect reviews
- Dynamic decomposition for open-ended investigation tasks
- Split large code reviews: per-file local passes + separate cross-file integration pass
- Open-ended tasks: map structure → identify high-impact areas → prioritized adaptive plan

---

### 1.7 Session State, Resumption, and Forking

**Know:**
- `--resume <session-name>` to continue a specific prior conversation
- `fork_session` for independent branches from a shared analysis baseline
- Inform agent about file changes when resuming after code modifications
- New session + structured summary is more reliable than resuming with stale tool results

**Skills:**
- Use `--resume` for named investigation sessions across work sessions
- Use `fork_session` to compare approaches (e.g., two testing strategies)
- Choose resumption (prior context valid) vs fresh session with injected summaries (stale results)

---

## Domain 2: Tool Design & MCP Integration (18%)

### 2.1 Effective Tool Interface Design

**Know:**
- Tool descriptions = primary mechanism LLMs use for tool selection
- Minimal descriptions → unreliable selection among similar tools
- Include: input formats, example queries, edge cases, boundary explanations
- Ambiguous/overlapping descriptions cause misrouting
- System prompt wording can create unintended tool associations

**Skills:**
- Write descriptions that differentiate purpose, inputs, outputs, and when to use vs alternatives
- Rename tools + update descriptions to eliminate functional overlap
- Split generic tools into purpose-specific tools with defined input/output contracts
- Review system prompts for keyword-sensitive instructions that override tool descriptions

---

### 2.2 Structured Error Responses for MCP Tools

**Know:**
- `isError` flag pattern for communicating tool failures to agent
- Error types: transient (timeouts), validation (invalid input), business (policy violations), permission
- Generic "Operation failed" → prevents appropriate recovery decisions
- Retryable vs non-retryable errors

**Skills:**
- Return structured error metadata: `errorCategory`, `isRetryable` boolean, human-readable description
- Include `retriable: false` + customer-friendly explanation for business rule violations
- Local recovery within subagents for transient failures; propagate only unresolvable errors
- Distinguish access failures (retry decisions) from valid empty results (successful query, no matches)

---

### 2.3 Tool Distribution Across Agents and Tool Choice Configuration

**Know:**
- Too many tools (e.g., 18 instead of 4–5) degrades tool selection reliability
- Agents with out-of-scope tools tend to misuse them
- Scoped tool access: give agents only the tools needed for their role
- `tool_choice` options: `"auto"`, `"any"`, forced `{"type": "tool", "name": "..."}`

**Skills:**
- Restrict each subagent's tool set to role-relevant tools
- Replace generic tools with constrained alternatives (e.g., `fetch_url` → `load_document`)
- Provide scoped cross-role tools for high-frequency needs; route complex cases through coordinator
- Use forced `tool_choice` to ensure a specific tool is called first
- Use `tool_choice: "any"` to guarantee model calls a tool (not conversational text)

---

### 2.4 MCP Server Integration into Claude Code and Agent Workflows

**Know:**
- Project-level: `.mcp.json` (shared via version control)
- User-level: `~/.claude.json` (personal/experimental)
- Environment variable expansion in `.mcp.json` (e.g., `${GITHUB_TOKEN}`)
- All MCP server tools discovered at connection time and available simultaneously
- MCP resources: expose content catalogs to reduce exploratory tool calls

**Skills:**
- Configure shared MCP servers in `.mcp.json` with env var expansion for auth tokens
- Configure personal servers in `~/.claude.json`
- Enhance MCP tool descriptions to prevent agent from preferring built-ins (e.g., Grep)
- Choose community MCP servers over custom for standard integrations (e.g., Jira)
- Expose content catalogs as MCP resources for visibility without exploratory calls

---

### 2.5 Built-in Tools: Read, Write, Edit, Bash, Grep, Glob

**Know:**
- `Grep`: content search (function names, error messages, import statements)
- `Glob`: file path pattern matching (by name or extension)
- `Read`/`Write`: full file operations
- `Edit`: targeted modifications using unique text matching
- When `Edit` fails (non-unique match) → use `Read` + `Write` as fallback

**Skills:**
- Use `Grep` for searching code content across codebase
- Use `Glob` for finding files matching naming patterns (e.g., `**/*.test.tsx`)
- Build codebase understanding incrementally: `Grep` entry points → `Read` to trace flows
- Trace function usage across wrapper modules: identify exported names → search each

---

## Domain 3: Claude Code Configuration & Workflows (20%)

### 3.1 CLAUDE.md Configuration Hierarchy, Scoping, and Modular Organization

**Know:**
- Hierarchy: user-level (`~/.claude/CLAUDE.md`) → project-level (`.claude/CLAUDE.md` or root) → directory-level
- User-level settings are NOT shared via version control
- `@import` syntax for referencing external files (modular CLAUDE.md)
- `.claude/rules/` directory for topic-specific rule files as alternative to monolithic CLAUDE.md

**Skills:**
- Diagnose hierarchy issues (e.g., new team member missing instructions → user-level vs project-level)
- Use `@import` to selectively include standards files per package
- Split large CLAUDE.md into focused files: `testing.md`, `api-conventions.md`, `deployment.md`
- Use `/memory` command to verify which memory files are loaded

---

### 3.2 Custom Slash Commands and Skills

**Know:**
- Project-scoped commands: `.claude/commands/` (shared via version control)
- User-scoped commands: `~/.claude/commands/` (personal)
- Skills: `.claude/skills/` with `SKILL.md` files + frontmatter: `context: fork`, `allowed-tools`, `argument-hint`
- `context: fork`: runs skill in isolated sub-agent context, prevents polluting main conversation
- Personal skill variants: `~/.claude/skills/` with different names (doesn't affect teammates)

**Skills:**
- Create project-scoped slash commands in `.claude/commands/` for team-wide availability
- Use `context: fork` for verbose/exploratory skills to isolate from main session
- Use `allowed-tools` in frontmatter to restrict tool access during skill execution
- Use `argument-hint` to prompt for required parameters when invoked without arguments
- Choose: skills (on-demand, task-specific) vs CLAUDE.md (always-loaded, universal)

---

### 3.3 Path-Specific Rules for Conditional Convention Loading

**Know:**
- `.claude/rules/` files with YAML frontmatter `paths` field containing glob patterns
- Path-scoped rules load **only when editing matching files** → reduces irrelevant context
- Glob patterns better than directory-level CLAUDE.md for cross-directory conventions

**Skills:**
- Create `.claude/rules/` files with YAML path scoping (e.g., `paths: ["terraform/**/*"]`)
- Use glob patterns for file-type conventions regardless of location (e.g., `**/*.test.tsx`)
- Choose path-specific rules over subdirectory CLAUDE.md when conventions span directories

---

### 3.4 Plan Mode vs Direct Execution

**Know:**
- **Plan mode:** large-scale changes, multiple valid approaches, architectural decisions, multi-file modifications
- **Direct execution:** simple, well-scoped changes (single function, clear stack trace)
- Plan mode enables safe exploration before committing → prevents costly rework
- `Explore` subagent: isolates verbose discovery output, returns summaries to preserve main context

**Skills:**
- Plan mode for: microservice restructuring, library migrations (45+ files), infrastructure decisions
- Direct execution for: single-file bug fixes, adding a date validation conditional
- Use `Explore` subagent for verbose discovery phases
- Combine: plan mode for investigation → direct execution for implementation

---

### 3.5 Iterative Refinement Techniques

**Know:**
- Concrete input/output examples = most effective for communicating expected transformations
- Test-driven iteration: write tests first → iterate by sharing test failures
- Interview pattern: have Claude ask questions to surface considerations before implementing
- Interacting problems → single message; independent problems → sequential iteration

**Skills:**
- Provide 2–3 concrete input/output examples when natural language produces inconsistent results
- Write test suites (expected behavior, edge cases, performance) before implementation
- Use interview pattern to surface design considerations (cache invalidation, failure modes)
- Provide specific test cases with input/expected output for edge case handling

---

### 3.6 Claude Code Integration into CI/CD Pipelines

**Know:**
- `-p` / `--print` flag: non-interactive mode for automated pipelines
- `--output-format json` + `--json-schema`: structured output for CI
- CLAUDE.md provides project context (testing standards, fixture conventions, review criteria)
- Session context isolation: same session that generated code is less effective at reviewing it

**Skills:**
- Run Claude Code in CI with `-p` flag to prevent interactive input hangs
- Use `--output-format json` + `--json-schema` for machine-parseable PR comments
- Include prior review findings on re-runs; instruct to report only new/unaddressed issues
- Provide existing test files in context to avoid duplicate test suggestions
- Document testing standards, criteria, and fixtures in CLAUDE.md for better test generation

---

## Domain 4: Prompt Engineering & Structured Output (20%)

### 4.1 Explicit Criteria to Improve Precision and Reduce False Positives

**Know:**
- Explicit criteria > vague instructions (e.g., "flag only when claimed behavior contradicts code" vs "check accuracy")
- General instructions ("be conservative", "only high-confidence") don't improve precision
- High false positive categories undermine trust in accurate categories

**Skills:**
- Write specific review criteria: define what to report (bugs, security) vs skip (minor style)
- Temporarily disable high false-positive categories to restore trust while improving prompts
- Define explicit severity criteria with concrete code examples for each severity level

---

### 4.2 Few-Shot Prompting for Output Consistency

**Know:**
- Few-shot examples = most effective technique for consistently formatted, actionable output
- Examples demonstrate ambiguous-case handling; model generalizes to novel patterns
- Effective for reducing hallucination in extraction tasks

**Skills:**
- Create 2–4 targeted few-shot examples for ambiguous scenarios with reasoning
- Include examples showing desired output format (location, issue, severity, suggested fix)
- Provide examples distinguishing acceptable patterns from genuine issues
- Use examples for varied document structures (inline citations vs bibliographies)

---

### 4.3 Structured Output via Tool Use and JSON Schemas

**Know:**
- `tool_use` + JSON schemas = most reliable approach for schema-compliant output (eliminates syntax errors)
- `tool_choice: "auto"` → model may return text; `"any"` → must call a tool; forced → specific tool
- Strict JSON schemas eliminate syntax errors but NOT semantic errors (e.g., values in wrong fields)
- Schema design: required vs optional fields, enum + `"other"` + detail string for extensibility

**Skills:**
- Define extraction tools with JSON schemas; extract structured data from `tool_use` response
- Set `tool_choice: "any"` when multiple extraction schemas exist and document type is unknown
- Force specific tool: `tool_choice: {"type": "tool", "name": "extract_metadata"}`
- Design nullable fields when source documents may not contain the information
- Add `"unclear"` enum values and `"other"` + detail fields for extensible categorization
- Include format normalization rules in prompts alongside strict output schemas

---

### 4.4 Validation, Retry, and Feedback Loops for Extraction Quality

**Know:**
- Retry-with-error-feedback: append specific validation errors to prompt on retry
- Retries are ineffective when required information is absent from the source document
- `detected_pattern` field tracks which constructs trigger findings → enables dismissal pattern analysis
- Semantic validation errors vs schema syntax errors (eliminated by tool use)

**Skills:**
- Follow-up requests: include original document + failed extraction + specific validation errors
- Identify when retries will succeed (format mismatches) vs fail (information absent from source)
- Add `detected_pattern` fields to enable analysis of false positive patterns
- Design self-correction flows: `calculated_total` alongside `stated_total` to flag discrepancies

---

### 4.5 Efficient Batch Processing Strategies

**Know:**
- Message Batches API: **50% cost savings**, up to **24-hour** processing window, no guaranteed latency SLA
- Appropriate for: overnight reports, weekly audits, nightly test generation (non-blocking, latency-tolerant)
- NOT appropriate for: blocking workflows (pre-merge checks)
- Batch API does NOT support multi-turn tool calling within a single request
- `custom_id` fields for correlating request/response pairs

**Skills:**
- Match API to latency requirements: synchronous API for blocking checks, batch for overnight
- Calculate batch submission frequency based on SLA constraints
- Handle failures: resubmit only failed documents (by `custom_id`) with modifications
- Refine prompts on sample set before batch-processing large volumes

---

### 4.6 Multi-Instance and Multi-Pass Review Architectures

**Know:**
- Self-review limitation: model retains reasoning context → less likely to question its own decisions
- Independent review instances (no prior context) more effective at catching subtle issues
- Multi-pass: per-file local analysis + cross-file integration passes → avoids attention dilution

**Skills:**
- Use second independent Claude instance to review generated code without generator's context
- Split large reviews: focused per-file passes (local issues) + integration passes (cross-file data flow)
- Run verification passes where model self-reports confidence alongside each finding

---

## Domain 5: Context Management & Reliability (15%)

### 5.1 Preserve Critical Information Across Long Interactions

**Know:**
- Progressive summarization risk: loses numerical values, dates, percentages, customer expectations
- "Lost in the middle" effect: models reliably process start/end of long inputs, may miss middle
- Tool results accumulate and consume tokens disproportionate to relevance
- Must pass complete conversation history in subsequent API requests

**Skills:**
- Extract transactional facts (amounts, dates, order numbers) into persistent "case facts" block
- Trim verbose tool outputs to only relevant fields before they accumulate in context
- Place key findings summaries at the **beginning** of aggregated inputs; use section headers
- Require subagents to include metadata (dates, source locations) in structured outputs
- Modify upstream agents to return structured data instead of verbose reasoning chains

---

### 5.2 Effective Escalation and Ambiguity Resolution Patterns

**Know:**
- Escalate when: customer explicitly requests human, policy exceptions/gaps, unable to make progress
- Escalate **immediately** when customer explicitly demands it (don't attempt investigation first)
- Sentiment-based escalation and self-reported confidence scores are unreliable
- Multiple customer matches → request additional identifiers (don't heuristic-select)

**Skills:**
- Add explicit escalation criteria with few-shot examples to system prompt
- Honor explicit customer requests for human agents immediately
- Acknowledge frustration + offer resolution; escalate only if customer reiterates preference
- Escalate when policy is ambiguous or silent on the specific request
- Instruct agent to ask for additional identifiers when tool returns multiple matches

---

### 5.3 Error Propagation Strategies Across Multi-Agent Systems

**Know:**
- Structured error context (failure type, attempted query, partial results, alternatives) enables recovery
- Access failures (timeouts) ≠ valid empty results (successful query, no matches)
- Generic error statuses hide valuable context from coordinator
- Anti-patterns: silently suppressing errors OR terminating entire workflow on single failure

**Skills:**
- Return structured error context: failure type, what was attempted, partial results, alternatives
- Distinguish access failures from valid empty results in error reporting
- Subagents: implement local recovery for transient failures; propagate only unresolvable errors
- Structure synthesis output with coverage annotations (well-supported vs gap due to unavailable sources)

---

### 5.4 Context Management in Large Codebase Exploration

**Know:**
- Context degradation in extended sessions: inconsistent answers, references to "typical patterns"
- Scratchpad files persist key findings across context boundaries
- Subagent delegation isolates verbose exploration output
- Structured state persistence for crash recovery: agents export state; coordinator loads manifest on resume

**Skills:**
- Spawn subagents for specific investigations while main agent preserves high-level coordination
- Maintain scratchpad files with key findings; reference them for subsequent questions
- Summarize key findings before spawning next-phase subagents; inject summaries into initial context
- Design crash recovery using structured agent state exports (manifests)
- Use `/compact` to reduce context usage during extended exploration sessions

---

### 5.5 Human Review Workflows and Confidence Calibration

**Know:**
- Aggregate accuracy (e.g., 97% overall) may mask poor performance on specific document types/fields
- Stratified random sampling: measures error rates in high-confidence extractions, detects novel patterns
- Field-level confidence scores calibrated using labeled validation sets
- Validate accuracy by document type and field before automating high-confidence extractions

**Skills:**
- Implement stratified random sampling of high-confidence extractions for ongoing measurement
- Analyze accuracy by document type and field before reducing human review
- Have models output field-level confidence scores; calibrate review thresholds with labeled data
- Route low-confidence or ambiguous/contradictory extractions to human review

---

### 5.6 Information Provenance and Uncertainty in Multi-Source Synthesis

**Know:**
- Source attribution is lost during summarization when findings compressed without claim-source mappings
- Structured claim-source mappings must be preserved through synthesis
- Conflicting statistics: annotate conflicts with source attribution, don't arbitrarily select one value
- Temporal data: require publication/collection dates to prevent misinterpreting differences as contradictions

**Skills:**
- Require subagents to output structured claim-source mappings (source URLs, names, excerpts)
- Structure reports with sections distinguishing well-established from contested findings
- Include conflicting values with explicit annotation; let coordinator reconcile before synthesis
- Require publication/collection dates in structured outputs for temporal interpretation
- Render different content types appropriately (financial data as tables, news as prose)

---

## Key Technologies & Concepts Cheat Sheet

| Technology | Key Concepts |
|-----------|--------------|
| **Claude Agent SDK** | `stop_reason`, hooks (`PostToolUse`, interception), `Task` tool, `allowedTools`, `AgentDefinition` |
| **MCP** | `isError` flag, `.mcp.json` (project), `~/.claude.json` (user), env var expansion, resources vs tools |
| **Claude Code** | CLAUDE.md hierarchy, `.claude/rules/` (YAML glob), `.claude/commands/`, `.claude/skills/` (SKILL.md), plan mode, `/compact`, `--resume`, `fork_session` |
| **Claude Code CLI** | `-p`/`--print`, `--output-format json`, `--json-schema` |
| **Claude API** | `tool_use`, `tool_choice` (`auto`/`any`/forced), `stop_reason` (`tool_use`/`end_turn`), `max_tokens` |
| **Message Batches API** | 50% cost savings, 24hr window, `custom_id`, no multi-turn tool calling |
| **JSON Schema** | Required vs optional, nullable, enum + `"other"` + detail, strict mode |

---

## Out-of-Scope (Will NOT Appear on Exam)

- Fine-tuning or training custom models
- API authentication, billing, account management
- Deploying/hosting MCP servers (infrastructure)
- Claude's internal architecture, training, or model weights
- Constitutional AI, RLHF, safety training
- Embedding models or vector databases
- Computer use (browser/desktop automation)
- Vision/image analysis
- Streaming API / server-sent events
- Rate limiting, quotas, API pricing calculations
- OAuth, API key rotation
- Specific cloud provider configs (AWS, GCP, Azure)
- Prompt caching implementation details
- Token counting algorithms

---

## Preparation Exercises

| # | Exercise | Domains |
|---|----------|---------|
| 1 | Build a multi-tool agent with escalation logic | D1, D2, D5 |
| 2 | Configure Claude Code for team development workflow | D3, D2 |
| 3 | Build a structured data extraction pipeline | D4, D5 |
| 4 | Design and debug a multi-agent research pipeline | D1, D2, D5 |

---

## Exam Preparation Checklist

- [ ] Build a complete agentic loop with tool calling, error handling, session management
- [ ] Spawn subagents and practice passing context between them
- [ ] Configure CLAUDE.md hierarchy + path-specific rules + custom skills with frontmatter
- [ ] Integrate at least one MCP server
- [ ] Write tool descriptions that differentiate similar tools; implement structured error responses
- [ ] Build a structured data extraction pipeline with tool_use + JSON schemas + validation-retry loops
- [ ] Practice batch processing with the Message Batches API
- [ ] Write few-shot examples for ambiguous scenarios
- [ ] Define explicit review criteria to reduce false positives
- [ ] Design multi-pass review architecture for large code reviews
- [ ] Practice context management: structured facts extraction, scratchpad files, subagent delegation
- [ ] Design human review workflows with confidence-based routing
- [ ] Complete the practice exam (link provided separately)
