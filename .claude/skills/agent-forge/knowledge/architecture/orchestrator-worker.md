---
name: Orchestrator-Worker
category: architecture
difficulty: intermediate
when_to_use: sub-tasks are independent and parallelizable (research over N sources, transform N records)
frameworks: [langgraph, claude-agent-sdk, openai-agents-sdk, crewai]
related: [plan-execute, multi-agent-handoff, agent-as-tool]
anti_patterns: [orchestrator-for-serial-deps, no-worker-budget]
tags: [architecture, orchestrator, worker, parallel, fan-out]
---

# Orchestrator-Worker

**TL;DR:** A coordinator agent decomposes the task into independent sub-tasks, fans them out to worker agents running in parallel, then aggregates results. The right pattern when work is genuinely parallel — not just when you have multiple agents.

## When to use

- Independent sub-tasks (research 10 papers, summarize 50 emails, transform 100 records)
- Map-reduce-shaped problems
- Per-document or per-entity processing where each instance is isolated
- When total wall-clock time is the constraint and tasks are I/O-bound (LLM calls)

## When NOT to use

- Sub-tasks have dependencies — use sequential plan-execute instead
- Aggregation step is the actual hard part — orchestrator-worker doesn't help
- Single-document tasks — overhead isn't justified
- Cost-sensitive workloads — fanning out multiplies LLM calls

## How it works

Three roles:

1. **Orchestrator** (1 instance) — receives the task, decides on the split, fans out to workers, aggregates results.
2. **Workers** (N instances, parallel) — each handles one sub-task independently. Same prompt and tools, different inputs.
3. **Aggregator** — usually the orchestrator, post-fan-out. Synthesizes worker outputs.

Critical guards:
- **Per-worker budget** — each worker has its own iteration / token / cost cap.
- **Worker isolation** — workers must not share mutable state.
- **Timeout per worker** — a slow worker shouldn't stall the whole job.
- **Partial-success handling** — aggregate must handle "5 of 10 workers succeeded" cleanly.

## Code — LangGraph (parallel fan-out)

```python
import asyncio
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from operator import add
from langchain_anthropic import ChatAnthropic

orchestrator_llm = ChatAnthropic(model="claude-opus-4-7")
worker_llm = ChatAnthropic(model="claude-haiku-4-5-20251001")

class State(TypedDict):
    task: str
    sub_tasks: list[dict]
    results: Annotated[list, add]  # reducer accumulates from parallel branches
    final: str

async def split(state: State) -> dict:
    prompt = f"Decompose into independent sub-tasks. Output JSON array. Task: {state['task']}"
    resp = await orchestrator_llm.ainvoke(prompt)
    return {"sub_tasks": parse_json(resp.content)}

async def worker(sub_task: dict) -> dict:
    prompt = f"Complete: {sub_task['description']}"
    try:
        async with asyncio.timeout(30):
            resp = await worker_llm.ainvoke(prompt)
        return {"sub_task_id": sub_task["id"], "output": resp.content, "status": "ok"}
    except (asyncio.TimeoutError, Exception) as e:
        return {"sub_task_id": sub_task["id"], "error": str(e), "status": "failed"}

async def fan_out(state: State) -> dict:
    # Launch all workers in parallel
    results = await asyncio.gather(*[worker(st) for st in state["sub_tasks"]])
    return {"results": results}

async def aggregate(state: State) -> dict:
    successful = [r for r in state["results"] if r["status"] == "ok"]
    failed = [r for r in state["results"] if r["status"] != "ok"]
    prompt = (
        f"Original task: {state['task']}\n"
        f"Worker outputs (success): {successful}\n"
        f"Worker failures: {failed}\n"
        f"Synthesize a final answer. Note any gaps from failed sub-tasks."
    )
    resp = await orchestrator_llm.ainvoke(prompt)
    return {"final": resp.content}

graph = StateGraph(State)
graph.add_node("split", split)
graph.add_node("fan_out", fan_out)
graph.add_node("aggregate", aggregate)
graph.set_entry_point("split")
graph.add_edge("split", "fan_out")
graph.add_edge("fan_out", "aggregate")
graph.add_edge("aggregate", END)
app = graph.compile()
```

## Tradeoffs

- **Wall-clock latency:** drops dramatically when N is large (parallelism wins)
- **Cost:** total cost = N workers + 1 orchestrator + 1 aggregator. Inflates linearly with N.
- **Aggregation quality:** the aggregator is the bottleneck for final quality. Use a stronger model here.
- **Failure modes:** partial success is the norm at scale; design the aggregator to handle it gracefully

## Anti-patterns

- Orchestrator-worker for serial-dependent tasks — adds complexity without parallelism benefit
- No per-worker timeout — one stuck worker blocks the whole job
- Workers share state — defeats isolation, introduces race conditions
- No budget per worker — runaway costs at scale
- Aggregator that ignores failures — silent quality drops when workers error

## Related

- `plan-execute` — sequential variant for dependent steps
- `multi-agent-handoff` — for role-specialized work, not parallelism
- `agent-as-tool` — workers can be agents themselves
- `circuit-breaker` — pair with worker fan-out for resilience
