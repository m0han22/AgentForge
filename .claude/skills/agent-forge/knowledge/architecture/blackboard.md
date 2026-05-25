---
name: Blackboard (Shared Workspace)
category: architecture
difficulty: advanced
when_to_use: long-running multi-agent collaboration where agents incrementally contribute to a shared artifact (research, design, code review)
frameworks: [langgraph, crewai, custom]
related: [orchestrator-worker, multi-agent-handoff, agent-as-tool]
anti_patterns: [blackboard-without-locks, blackboard-for-simple-pipelines]
tags: [architecture, blackboard, shared-state, multi-agent, collaboration]
---

# Blackboard (Shared Workspace)

**TL;DR:** Agents (specialists) read from and write to a shared structured workspace. A controller schedules which agent runs next based on the current workspace state. Best for long-running collaborative tasks where each agent contributes a section, not for simple pipelines.

## When to use

- Long-running research / authoring tasks where multiple specialists contribute incrementally
- Tasks where the order of contributions is dynamic, not predetermined
- Iterative design where each pass refines existing content (code review, document editing, scientific writing)
- When you need an inspectable artifact-in-progress that humans can also edit

## When NOT to use

- Simple sequential pipelines — multi-agent-handoff is cleaner
- Parallel independent work — orchestrator-worker is cleaner
- Short tasks (under 10 steps) — overhead of the shared state isn't justified
- Latency-critical paths — the scheduler adds turns

## How it works

Four components:

1. **Blackboard** — structured workspace (typically JSON or sectioned markdown) with named slots ("research_notes", "draft", "critique", "final"). Versioned, with locks per slot.
2. **Knowledge sources** (agents) — each agent declares what it reads from and writes to. E.g., "Researcher reads task, writes research_notes." "Writer reads research_notes, writes draft." "Critic reads draft, writes critique."
3. **Controller / Scheduler** — picks the next agent based on workspace state. Can be a rule engine ("if draft exists and critique is empty, run Critic") or an LLM ("given the workspace, who should run next?").
4. **Termination condition** — explicit (workspace has final, scheduler emits done) or budget-based (max controller iterations).

Critical: per-slot locks. Two agents writing the same slot simultaneously corrupts state.

## Code — Custom (LangGraph-style)

```python
from dataclasses import dataclass, field
from threading import Lock

@dataclass
class Blackboard:
    task: str
    research_notes: str | None = None
    draft: str | None = None
    critique: str | None = None
    final: str | None = None
    history: list[dict] = field(default_factory=list)
    locks: dict[str, Lock] = field(default_factory=lambda: {
        k: Lock() for k in ["research_notes", "draft", "critique", "final"]
    })

    def write(self, slot: str, value: str, agent: str):
        with self.locks[slot]:
            setattr(self, slot, value)
            self.history.append({"agent": agent, "slot": slot})

def researcher(bb: Blackboard) -> None:
    notes = llm.invoke(f"Research notes for: {bb.task}")
    bb.write("research_notes", notes, "researcher")

def writer(bb: Blackboard) -> None:
    draft = llm.invoke(f"Write a draft using: {bb.research_notes}")
    bb.write("draft", draft, "writer")

def critic(bb: Blackboard) -> None:
    critique = llm.invoke(f"Critique this draft: {bb.draft}")
    bb.write("critique", critique, "critic")

def finalizer(bb: Blackboard) -> None:
    final = llm.invoke(f"Revise draft addressing critique. Draft: {bb.draft}. Critique: {bb.critique}")
    bb.write("final", final, "finalizer")

AGENTS = {
    "researcher": (researcher, lambda bb: bb.research_notes is None),
    "writer":     (writer,     lambda bb: bb.research_notes and not bb.draft),
    "critic":     (critic,     lambda bb: bb.draft and not bb.critique),
    "finalizer":  (finalizer,  lambda bb: bb.critique and not bb.final),
}

def schedule(bb: Blackboard, max_iters: int = 10) -> Blackboard:
    for _ in range(max_iters):
        ready = [(name, fn) for name, (fn, cond) in AGENTS.items() if cond(bb)]
        if not ready:
            return bb  # done or stalled
        name, fn = ready[0]
        fn(bb)
    raise RuntimeError("Blackboard scheduler exceeded iterations")
```

## Tradeoffs

- **Inspectability:** the workspace IS the audit log; humans can read intermediate state
- **Flexibility:** agents can be added/removed without rewiring the whole pipeline
- **Complexity:** schedulers, locks, slot conventions — significant overhead
- **Latency:** LLM-driven scheduler adds an extra call per step; rule-driven is faster but rigid
- **Debugging:** "why didn't this agent run?" requires inspecting scheduler logic + workspace state

## Anti-patterns

- Blackboard without locks — concurrent writes corrupt state
- Blackboard for short pipelines — overkill; use handoff
- LLM scheduler with no budget — controller loops while no agent's preconditions hold
- Implicit slot schemas — agents disagree about field names; subtle bugs
- No termination condition — system runs until budget exhausted

## Related

- `orchestrator-worker` — for parallel fan-out instead of shared workspace
- `multi-agent-handoff` — for predictable sequential pipelines
- `agent-as-tool` — agents can be tools the controller invokes
- `max-iterations-budget` — required for the scheduler
