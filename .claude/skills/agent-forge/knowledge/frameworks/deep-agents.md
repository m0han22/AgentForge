---
name: Deep Agents (LangChain)
category: frameworks
when_to_use: long-horizon multi-step tasks (research, coding, deep analysis) where you want production defaults out of the box instead of writing them yourself on LangGraph
language: [python, typescript]
maturity: stable
tags: [framework, langchain, langgraph, deep-agents, harness, long-horizon]
---

# Deep Agents (LangChain)

**TL;DR:** Opinionated harness on top of LangGraph that bundles production agent patterns — sub-agents with isolated context, filesystem-as-memory, summarization, HITL, persistent memory — as defaults. Best when you're building a long-horizon agent (research, coding, multi-hour work) and don't want to rebuild the harness yourself.

## Pick this when

- Long-horizon tasks (research, coding agents, multi-step analysis)
- You want sub-agent delegation, filesystem memory, and context summarization out of the box
- You're already in the LangChain / LangGraph ecosystem
- You want a starting point similar to Claude Code but framework-portable
- You're willing to accept opinionated defaults in exchange for not building the harness

## Don't pick this when

- Single-shot or short agent loops — overkill; use Claude Agent SDK or OpenAI Agents SDK
- You want zero LangChain dependencies — Deep Agents is built on LangGraph
- Latency-critical paths — bundled patterns (summarization, sub-agent spawn) add cost
- You need very custom orchestration — write directly against LangGraph

## Strengths

- **Sub-agents with isolated context** — the right pattern for long-horizon work, built in
- **Filesystem abstraction** — local, sandboxed, or remote backends; agent reads/writes files as memory
- **Automatic context management** — summarization of long threads, tool-output offloading
- **HITL primitives** — approve/reject tool calls before execution, first-class
- **Persistent memory backends** — pluggable, for cross-session recall
- **MCP support** — wire in third-party tools via MCP
- **Skills concept** — reusable agent behaviors invoked on demand

## Weaknesses

- **Opinionated** — if your task doesn't fit the long-horizon harness model, the defaults add overhead
- **LangGraph dependency** — inherits LangGraph's learning curve and version churn
- **Cost** — sub-agents + summarization + HITL all multiply LLM calls; budget tightly
- **TypeScript variant (deepagents.js)** lags Python in features

## When it shines vs alternatives

| Alternative | Pick Deep Agents when |
|---|---|
| **Claude Agent SDK** | Long-horizon work where you'd otherwise reimplement sub-agents, file memory, HITL, summarization |
| **LangGraph (raw)** | You want the bundled production patterns instead of rolling your own |
| **OpenAI Agents SDK** | You need filesystem memory and isolated sub-agents (Agents SDK has handoffs but not isolated-context delegation) |
| **CrewAI** | You want context-isolated delegation (CrewAI's multi-agent is more "role play" than isolated work) |

## Key APIs (sketch)

```python
from deepagents import create_deep_agent
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-opus-4-7")

# Sub-agent the main agent can delegate to
research_subagent = {
    "name": "researcher",
    "description": "Use to delegate focused research with isolated context.",
    "prompt": "You are a research specialist. Read documents and return findings concisely.",
    "tools": ["fs_read", "search_docs"],
}

agent = create_deep_agent(
    model=llm,
    tools=[fs_read, fs_write, fs_list, search_docs, ...],
    instructions="You are a long-horizon assistant. Use files for any output > 500 tokens.",
    subagents=[research_subagent],
    # filesystem backend (local sandbox by default)
    # human-in-the-loop config
    # memory backend
)

result = agent.invoke({"messages": [{"role": "user", "content": "Audit our auth middleware."}]})
```

## Patterns that pair well

- **Sub-agent with isolated context** — the headline pattern; Deep Agents implements this natively
- **Filesystem as memory** — built-in fs primitives, agent uses files for state
- **Recursive summarization** — automatic for long threads
- **HITL on destructive ops** — approve/reject before execution
- **Persistent memory** — pluggable backend for cross-session recall

## Patterns that don't fit well

- **Single-tool quick lookups** — overhead is not justified
- **Tight stateful graphs** with custom logic — use LangGraph directly
- **Pure RAG** without agent loop — use LlamaIndex

## Migration notes

- From a custom LangGraph agent: drop Deep Agents on top, replace your hand-rolled sub-agent / fs / summarization with the bundled defaults
- From Claude Agent SDK: only switch if you genuinely need the long-horizon harness; otherwise SDK stays leaner
- From a coding agent like Claude Code: Deep Agents gives you the same architecture in a framework-portable form
