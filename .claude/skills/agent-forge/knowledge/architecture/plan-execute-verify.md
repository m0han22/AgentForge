---
name: Plan-Execute-Verify (PEV)
category: architecture
difficulty: advanced
when_to_use: high-stakes tasks where executing a wrong plan has real cost (financial actions, code deploys, data mutations)
frameworks: [langgraph, claude-agent-sdk, openai-agents-sdk]
related: [plan-execute, reflection, dry-run-mode]
anti_patterns: [pev-without-rollback, verify-with-same-model]
tags: [architecture, plan-execute-verify, pev, safety, verification]
---

# Plan-Execute-Verify (PEV)

**TL;DR:** Plan, then verify the plan against constraints BEFORE executing, then execute, then verify the outcome AFTER. Distinct from reflection (which revises outputs) — PEV gates dangerous actions on satisfying a verification check. The default architecture for any agent that takes consequential actions.

## When to use

- Actions with real-world consequences (financial, communicational, deploys, data writes)
- Code agents that modify production systems
- Multi-step workflows where step N depends on step N-1 being correct
- Anywhere a wrong execution is more expensive than a slow execution

## When NOT to use

- Read-only / informational agents (just plan-execute is enough)
- Latency-critical paths (verify adds 2 extra LLM calls minimum)
- When the verification model isn't better than the planner — adds cost without signal

## How it works

Four phases, gated:

1. **Plan** — generate the structured action plan
2. **Verify-plan** — separate model checks the plan against explicit invariants ("does this transfer money?", "does this delete user data?", "does any step contradict the user's stated constraint?"). If verify fails, replan or escalate to human.
3. **Execute** — run the plan (preferably with dry-run on the destructive steps)
4. **Verify-outcome** — confirm post-conditions hold. If not, rollback or escalate.

What makes PEV different from reflection:
- Reflection revises outputs after generation; PEV blocks execution before it happens
- Reflection optimizes quality; PEV enforces safety
- Reflection can be same-model; PEV's verifier should be a different (or stronger) model

## Code — LangGraph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict
from langchain_anthropic import ChatAnthropic

planner = ChatAnthropic(model="claude-opus-4-7")
verifier = ChatAnthropic(model="claude-opus-4-7")  # different instance / could be different model
executor = ChatAnthropic(model="claude-haiku-4-5-20251001")

INVARIANTS = """
- Steps must not modify user data without explicit user consent in the original request.
- Steps must not exceed $100 in any financial transaction.
- Steps must not delete production resources.
- Each step must list a rollback action.
"""

class State(TypedDict):
    task: str
    plan: list[dict] | None
    plan_verdict: dict | None
    execution: list[dict]
    outcome_verdict: dict | None

def plan(state: State) -> dict:
    resp = planner.invoke(f"Plan steps for: {state['task']}. Output JSON: [{{step, action, args, rollback}}]")
    return {"plan": parse_json(resp.content)}

def verify_plan(state: State) -> dict:
    prompt = f"INVARIANTS:\n{INVARIANTS}\n\nPLAN:\n{state['plan']}\n\nReport JSON: {{passes: bool, violations: [...]}}"
    resp = verifier.invoke(prompt)
    return {"plan_verdict": parse_json(resp.content)}

def route_after_plan_verify(state: State) -> str:
    if state["plan_verdict"]["passes"]:
        return "execute"
    return "escalate"  # human-in-loop

def execute(state: State) -> dict:
    results = []
    for step in state["plan"]:
        try:
            r = call_action(step["action"], step["args"], dry_run=is_destructive(step))
            results.append({"step": step, "result": r, "status": "ok"})
        except Exception as e:
            # Run rollback for previously-succeeded steps
            rollback_all(results)
            return {"execution": results + [{"step": step, "error": str(e), "status": "rolled_back"}]}
    return {"execution": results}

def verify_outcome(state: State) -> dict:
    prompt = (
        f"Task: {state['task']}\n"
        f"Executed: {state['execution']}\n"
        f"Confirm the user's goal is met. JSON: {{satisfied: bool, gaps: [...]}}"
    )
    resp = verifier.invoke(prompt)
    return {"outcome_verdict": parse_json(resp.content)}

def escalate(state: State) -> dict:
    return {"execution": [{"escalated_to_human": True, "reason": state["plan_verdict"]["violations"]}]}

graph = StateGraph(State)
graph.add_node("plan", plan)
graph.add_node("verify_plan", verify_plan)
graph.add_node("execute", execute)
graph.add_node("verify_outcome", verify_outcome)
graph.add_node("escalate", escalate)
graph.set_entry_point("plan")
graph.add_edge("plan", "verify_plan")
graph.add_conditional_edges("verify_plan", route_after_plan_verify, {"execute": "execute", "escalate": "escalate"})
graph.add_edge("execute", "verify_outcome")
graph.add_edge("verify_outcome", END)
graph.add_edge("escalate", END)
app = graph.compile()
```

## Tradeoffs

- **Safety:** the primary win. Catches dangerous plans before they execute.
- **Cost:** at least 3× single-agent (plan + verify + execute + verify-outcome); often 4–5×.
- **Latency:** verification is sequential — adds full LLM round-trips.
- **False positives:** strict verifiers reject legitimate plans, escalating to humans needlessly. Tune the invariants carefully.

## Anti-patterns

- PEV without rollback in execute — partial failures leave the system in a bad state
- Verifier is the same model and same instance — it agrees with the planner; no real check
- Vague invariants — verifier emits vague verdicts
- No human-in-loop on escalate — system stalls when verification fails
- Verify-outcome that just summarizes — must check post-conditions against original task

## Related

- `plan-execute` — base pattern without verification
- `reflection` — revises outputs; PEV gates actions
- `dry-run-mode` — pair with PEV for destructive steps
- `confirmation-for-destructive` — fallback when verifier is uncertain
