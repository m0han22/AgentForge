---
name: Multi-Agent Handoff
category: architecture
difficulty: intermediate
when_to_use: tasks with genuinely specialized roles where one agent finishes its work and explicitly passes control to another
frameworks: [openai-agents-sdk, langgraph, crewai, claude-agent-sdk]
related: [orchestrator-worker, plan-execute, agent-as-tool]
anti_patterns: [multi-agent-by-default, implicit-handoff-state]
tags: [architecture, multi-agent, handoff, routing]
---

# Multi-Agent Handoff

**TL;DR:** Specialized agents (triage, researcher, writer, escalator) hand off control explicitly with state. Use when the work genuinely decomposes by role and the handoff boundaries are clear. Justify with measured eval improvement — don't adopt for the metaphor.

## When to use

- Genuinely specialized roles (triage → specialist, research → writer → editor)
- Routing problems (which expert handles this?)
- Stages with different tool sets or different model tiers
- Customer service flows with escalation tiers
- When you've measured that role-specialized prompts outperform one big prompt

## When NOT to use

- Single role decomposed for the sake of the metaphor — single agent works
- Latency-critical paths — handoffs serialize, cost more LLM calls
- When the handoff state is hard to define — implicit state = bugs

## How it works

Two flavors:

1. **Triage → specialist** — first agent routes to one specialist agent based on intent classification.
2. **Sequential pipeline** — agent A produces output, agent B consumes it (research → write → edit).

Critical: **handoff state must be explicit**. When agent A hands off to agent B, B receives a structured payload (not "the conversation so far"). Implicit handoffs (just shared chat history) lose context, leak unintended state, and are hard to debug.

Each agent has:
- Its own system prompt (role + scope)
- Its own tool subset (least privilege)
- Its own budget (iterations, cost)
- A clear contract for what state it accepts and what state it emits

## Code — OpenAI Agents SDK

```python
from agents import Agent, Runner, function_tool, handoff
from pydantic import BaseModel

class TicketContext(BaseModel):
    customer_id: str
    issue_summary: str
    severity: str  # low | medium | high

@function_tool
def search_kb(query: str) -> str: ...

@function_tool
def open_ticket(ctx: TicketContext) -> str: ...

# Specialist: docs search
docs_agent = Agent(
    name="docs_specialist",
    instructions=(
        "You answer customer questions using search_kb. "
        "If you cannot find an answer, hand off to escalation_agent with a structured context."
    ),
    tools=[search_kb],
    model="gpt-4o-mini",
)

# Specialist: escalation
escalation_agent = Agent(
    name="escalation_specialist",
    instructions=(
        "You open support tickets for issues that docs cannot resolve. "
        "Always confirm severity and include the customer_id and summary."
    ),
    tools=[open_ticket],
    model="gpt-4o",
)

# Triage: routes to specialists
triage_agent = Agent(
    name="triage",
    instructions=(
        "Determine whether the user's question is answerable from docs (route to docs_specialist) "
        "or requires opening a ticket (route to escalation_specialist via handoff with structured context)."
    ),
    handoffs=[
        docs_agent,
        handoff(escalation_agent, input_type=TicketContext),
    ],
    model="gpt-4o-mini",
)

result = Runner.run_sync(triage_agent, "My account was charged twice, I need a refund.")
```

## Tradeoffs

- **Clarity:** specialist prompts are tighter and easier to maintain than one mega-prompt
- **Cost:** each handoff = additional LLM call(s); 3-stage pipeline = 3× single agent cost minimum
- **Latency:** sequential handoffs add up; streaming and intermediate UI helps
- **Debuggability:** explicit handoff payloads + per-agent traces make root-cause easier than mega-prompts

## Anti-patterns

- Multi-agent by default for "modularity" — without an eval lift, you're just paying more
- Implicit handoff via shared chat history — context bleed, hard to debug
- Specialists with overlapping responsibilities — handoff loop ("not me, the other guy")
- No per-agent budget — one specialist can blow the whole session's cost
- Same model tier for triage and specialist — triage is cheap; use a small model

## Related

- `orchestrator-worker` — parallel fan-out, not role-specialized sequential
- `plan-execute` — alternative for known-step decomposition
- `agent-as-tool` — when handoff isn't quite the right metaphor
- `handoff-explicit-state` — the hard rule
