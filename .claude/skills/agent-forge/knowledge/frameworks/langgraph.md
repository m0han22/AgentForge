---
name: LangGraph
category: frameworks
when_to_use: stateful agent graphs with persistence, complex multi-step flows, human-in-the-loop
language: [python, typescript]
maturity: stable
tags: [framework, langchain, langgraph, state-machine, graph]
---

# LangGraph

**TL;DR:** Stateful agent framework built around explicit graphs (nodes = functions, edges = transitions). Best when your agent has more than 3 logical steps, needs persistence/checkpointing, or has human-in-the-loop. Python and TypeScript.

## Pick this when

- Your agent has >3 logical steps with conditional flow
- You need state persistence (resume after crash, replay traces)
- You need human-in-the-loop interrupts
- You want explicit, debuggable state transitions
- You're already in the LangChain ecosystem

## Don't pick this when

- Simple ReAct loop with 1–2 tools (overkill — use SDK directly)
- RAG-first with no agent loop (use LlamaIndex)
- Anthropic-only and minimal abstraction preferred (use Claude Agent SDK)
- Multi-agent role play with sequential crews (use CrewAI)

## Strengths

- **Explicit state graph** — every transition is visible, debuggable, replayable
- **Checkpointing built-in** — `MemorySaver`, `SqliteSaver`, `PostgresSaver`
- **Human-in-the-loop primitives** — `interrupt()` pauses execution for human input
- **LangSmith integration** — traces are native
- **Cycles and conditionals** — first-class, not bolted on
- **Streaming intermediate state** — UX-friendly for long agents

## Weaknesses

- **Steeper learning curve** than a simple SDK loop
- **Overhead for simple cases** — ReAct in 10 lines becomes ReAct in 50 lines
- **State schema design** is up to you — get it wrong and you'll refactor

## Key APIs

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated
from operator import add

class AgentState(TypedDict):
    messages: Annotated[list, add]
    next_action: str | None

def reason(state: AgentState) -> dict:
    # Call LLM, decide next action
    return {"next_action": "search"}

def act_search(state: AgentState) -> dict:
    # Run search tool
    return {"messages": [{"role": "tool", "content": "..."}]}

def should_continue(state: AgentState) -> str:
    return "act_search" if state["next_action"] == "search" else END

graph = StateGraph(AgentState)
graph.add_node("reason", reason)
graph.add_node("act_search", act_search)
graph.set_entry_point("reason")
graph.add_conditional_edges("reason", should_continue, {"act_search": "act_search", END: END})
graph.add_edge("act_search", "reason")

app = graph.compile(checkpointer=MemorySaver())

# Run with thread_id for resumable session
result = app.invoke({"messages": []}, config={"configurable": {"thread_id": "user-123"}})
```

## Patterns that pair well

- **Plan-execute** — plan node, then a loop of execute nodes
- **Orchestrator-worker** — supervisor node routes to worker subgraphs
- **Human-in-the-loop** — `interrupt()` between sensitive steps
- **Long-running with checkpoints** — Postgres saver for production

## Patterns that don't fit well

- **Pure RAG retrieve-then-answer** — graph is overkill for 2 steps
- **High-frequency low-latency** — graph overhead matters

## Migration notes

- From LangChain AgentExecutor: rewrite to graph nodes; usually clearer afterward
- From custom loops: worth migrating if you have >3 steps + persistence needs
- To Claude Agent SDK: if your graph is just ReAct, consider going simpler
