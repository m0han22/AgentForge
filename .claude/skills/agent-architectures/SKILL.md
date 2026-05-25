---
name: agent-architectures
description: "Pick and implement the right agent architecture: ReAct, plan-execute, orchestrator-worker, multi-agent, handoffs, reflection, tree-of-thoughts. Covers when to use single-agent vs multi-agent, supervisor patterns, reasoning loops, agent-as-tool composition, code-execution sandboxing. Frameworks: Claude Agent SDK, LangGraph, OpenAI Agents SDK, Pydantic AI, CrewAI. Returns one prescriptive architecture with code, loop budgets, and failure-mode anti-patterns."
allowed-tools: Read, Bash, Glob, Grep
---

# agent-architectures — Architecture Picker

Opinionated picker for agent architecture. Hub of all things "how should the agent be structured": ReAct, plan-execute, orchestrator-worker, multi-agent, reflection, ToT, agent-as-tool.

This skill defers to the **agent-forge hub** for the knowledge base and search. The hub's `knowledge/architecture/`, `knowledge/reasoning/`, `knowledge/loop/`, and `knowledge/frameworks/` are the source of truth. Use the hub's `scripts/search.py`.

## When to activate

- "Build me an agent that..."
- "Should I use ReAct or plan-execute?"
- "Multi-agent or single-agent for X?"
- "How do I structure an agent loop?"
- "Orchestrator-worker", "handoff", "supervisor", "swarm"
- "Reflection", "tree of thoughts", "self-critique"
- "My agent keeps looping" / "agent doesn't finish"

## When NOT to activate

- Pure RAG with no agent loop → use `agent-rag`
- Tool schema design without architecture concerns → use `agent-tools`
- Evaluation of an existing agent → use `agent-evals`

## Workflow

1. **Gather operational constraints (MANDATORY) and parse the request.** Before recommending, confirm: **(a) load / scale** (users, QPS, total queries/day), **(b) latency budget** (interactive / near-interactive / batch / specific p95), **(c) cost ceiling** (per-query / per-month / "minimize with hard cap"). If any of these three are missing from the user's message, ASK ONE focused clarifying question before proceeding. These determine framework, model tier, sub-agent vs monolithic, and sync vs async. Recommending without them is guessing. Also extract task shape (known steps vs open-ended?), tool count, parallelism opportunity, framework preference.
2. **Search** — `python3 .claude/skills/agent-forge/scripts/search.py "<query>" --domain architecture` and `--domain loop`
3. **Pick framework** — `python3 .claude/skills/agent-forge/scripts/search.py "<query>" --framework <name>`
4. **Synthesize** — use the output template below

## Architecture picker (decision rules)

| Task shape | Pick |
|---|---|
| 1–3 tool calls, simple chain | Direct SDK call, no loop |
| Multi-step, next step depends on previous | **ReAct** |
| Plan known in advance, just execute | **Plan-execute** |
| Independent parallel sub-tasks | **Orchestrator-worker** |
| Specialist roles (research → write → edit) | **Multi-agent sequential** (justify with eval) |
| Quality matters > latency | Add **reflection** step |
| High-stakes reasoning with branching | **Tree of Thoughts** (rare; expensive) |
| Long-running, resumable, human-in-loop | **LangGraph** state machine |

**Default:** single-agent ReAct. Add complexity only when you can measure a quality improvement.

## Hard rules (always)

- **Max iterations cap** (10–20) — never `while True`
- **Step / token / cost / wall-clock budget** — see `knowledge/loop/max-iterations-budget.md`
- **Infinite loop guard** — detect repeated identical tool calls
- **Circuit breaker** — N consecutive tool errors → ask user
- **Code-writing agents in sandbox** (e2b, modal, daytona) — never on host

## Output template

```
## Recommendation
<one sentence — architecture + framework. Example: "Use single-agent ReAct on Claude Agent SDK with a 15-iteration cap and $1 cost budget.">

## Why this for your case
- <task-shape reasoning>
- <complexity vs need tradeoff>
- <framework fit>

## Code
<runnable scaffold including the loop, the budget, the tool handlers>

## Avoid
- <anti-pattern, e.g., run-until-done>
- <anti-pattern>
- <anti-pattern>

## How to know it's working
<eval suggestion: golden set + completion-rate + cost-per-task + p95 latency>

## Deeper reading
- knowledge/architecture/<pattern>.md
- knowledge/loop/max-iterations-budget.md
- knowledge/frameworks/<framework>.md
```

## Personality

- Default to single-agent. Multi-agent must be justified with measured eval improvement.
- Always pair architecture choice with explicit budgets.
- Name one framework. Don't list.

## Knowledge base contract

All patterns live under `agent-forge/knowledge/`. This skill does not maintain its own knowledge tree.
