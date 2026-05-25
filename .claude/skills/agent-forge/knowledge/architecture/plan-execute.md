---
name: Plan-then-Execute
category: architecture
difficulty: intermediate
when_to_use: tasks with sub-goals known up front, where interleaved reasoning would waste context
frameworks: [langgraph, claude-agent-sdk, openai-agents-sdk, crewai]
related: [react-agent, plan-execute-verify, orchestrator-worker]
anti_patterns: [plan-execute-when-react-suffices, no-replan-on-failure]
tags: [architecture, planning, plan-execute]
---

# Plan-then-Execute

**TL;DR:** First call produces a plan (ordered list of steps with tools and args). Subsequent calls execute steps without re-deliberating. Faster and cheaper than ReAct when the plan is knowable in advance. Add a replan step when steps fail.

## When to use

- Tasks with clearly identifiable sub-goals (research → analyze → summarize)
- Multi-step workflows where reasoning about the whole task once is cleaner than reasoning at every step
- Tasks where execution is mechanical once the plan exists (data transformations, sequential API calls)
- When ReAct loops are wasting tokens re-reading the same context every turn

## When NOT to use

- The next step truly depends on observing the previous (ReAct fits better)
- Highly exploratory tasks where the plan would change after every observation
- Tasks with only 1–2 steps — overhead of planning outweighs benefit

## How it works

Two phases:

1. **Plan** — single LLM call: "Given this task, produce a plan as a JSON array of `{step, tool, args, expected_outcome}`."
2. **Execute** — for each step: call the tool, append result to working memory, move to next step.

Three reliability guards:
- **Validate the plan** against a schema (each step has known tool, well-formed args).
- **Replan on failure** — if a step fails or returns unexpected output, kick back to the planner with the failure context.
- **Budget the executor** — same iteration / token / cost caps as ReAct.

## Code — LangGraph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

planner = ChatAnthropic(model="claude-opus-4-7")
executor = ChatAnthropic(model="claude-haiku-4-5-20251001")

class State(TypedDict):
    task: str
    plan: list[dict] | None
    step_idx: int
    results: list[dict]
    final_answer: str | None

def plan(state: State) -> dict:
    prompt = (
        f"Plan the steps to complete this task. Available tools: search, summarize, compute.\n"
        f"Output JSON: [{{step:int, tool:str, args:dict, expected:str}}].\n\nTask: {state['task']}"
    )
    resp = planner.invoke([HumanMessage(content=prompt)])
    plan = parse_plan_json(resp.content)
    return {"plan": plan, "step_idx": 0, "results": []}

def execute_step(state: State) -> dict:
    step = state["plan"][state["step_idx"]]
    try:
        result = call_tool(step["tool"], step["args"])
    except Exception as e:
        return {"results": state["results"] + [{"step": step, "error": str(e)}]}
    return {"results": state["results"] + [{"step": step, "result": result}], "step_idx": state["step_idx"] + 1}

def should_continue(state: State) -> str:
    if state["results"] and "error" in state["results"][-1]:
        return "replan"
    if state["step_idx"] >= len(state["plan"]):
        return "finalize"
    return "execute"

def replan(state: State) -> dict:
    failed = state["results"][-1]
    prompt = f"Plan failed at step {failed['step']}. Error: {failed['error']}. Replan from this point."
    resp = planner.invoke([HumanMessage(content=prompt)])
    new_plan = parse_plan_json(resp.content)
    return {"plan": new_plan, "step_idx": 0, "results": state["results"]}

def finalize(state: State) -> dict:
    summary = executor.invoke([HumanMessage(content=f"Summarize results: {state['results']}")])
    return {"final_answer": summary.content}

graph = StateGraph(State)
graph.add_node("plan", plan)
graph.add_node("execute", execute_step)
graph.add_node("replan", replan)
graph.add_node("finalize", finalize)
graph.set_entry_point("plan")
graph.add_edge("plan", "execute")
graph.add_conditional_edges("execute", should_continue, {"execute": "execute", "replan": "replan", "finalize": "finalize"})
graph.add_edge("replan", "execute")
graph.add_edge("finalize", END)
app = graph.compile()
```

## Tradeoffs

- **Token efficiency:** plan is read once; execute steps use small models on small contexts
- **Latency:** front-loads thinking; execution is faster per-step than ReAct
- **Brittleness:** bad plan = wasted execution. Add a verify step (see `plan-execute-verify`) for safety.
- **Replan overhead:** when steps fail, replanning costs as much as the original plan

## Anti-patterns

- Plan-execute for tasks where the next step truly depends on the previous (use ReAct)
- No replan on failure — execution silently produces garbage
- Single-pass plan with no validation — typo in tool name fails halfway through
- Same model for plan and execute — wastes money; plan needs Opus/Sonnet, execute often works with Haiku
- Plan that's too granular (every action) — the LLM is wasted on trivial mechanics; plan at the right altitude

## Related

- `react-agent` — alternative when steps aren't known in advance
- `plan-execute-verify` — adds verification step (PEV)
- `orchestrator-worker` — parallel variant for independent sub-tasks
- `max-iterations-budget` — required pairing
