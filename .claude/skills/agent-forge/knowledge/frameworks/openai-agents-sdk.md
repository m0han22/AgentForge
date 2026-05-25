---
name: OpenAI Agents SDK
category: frameworks
when_to_use: OpenAI ecosystem, simple agent loops, handoffs between specialized agents
language: [python]
maturity: stable
tags: [framework, openai, agents-sdk, handoffs]
---

# OpenAI Agents SDK

**TL;DR:** OpenAI's first-party agent SDK. Lightweight Python framework with clean primitives for agents, tools, handoffs, and guardrails. Best in the OpenAI ecosystem when you want minimal abstraction with built-in multi-agent handoff.

## Pick this when

- You're on OpenAI models (GPT-4o, o1, o3)
- You want a simple loop with built-in handoff between specialized agents
- You want built-in guardrails primitives
- You prefer official tooling over LangChain abstractions

## Don't pick this when

- Multi-provider abstraction needed (use LangChain / LiteLLM)
- Anthropic ecosystem (use Claude Agent SDK)
- Complex stateful graphs (use LangGraph)

## Strengths

- **Official OpenAI tooling** — well-supported, mirrors API additions quickly
- **Handoffs first-class** — agent A → agent B is a primitive, not a hack
- **Guardrails built-in** — input/output validation as first-class concepts
- **Lightweight** — minimal abstraction; you can still see what's happening
- **Tracing built-in** — integrates with OpenAI's trace viewer

## Weaknesses

- **OpenAI-only** — switching providers means rewriting
- **Python-only** at the moment (no first-party TypeScript)
- **No built-in graph/checkpointing** like LangGraph

## Key APIs

```python
from agents import Agent, Runner, function_tool, GuardrailFunctionOutput, input_guardrail

@function_tool
def search_docs(query: str) -> str:
    """Search the engineering wiki. Use when the user asks technical questions."""
    return "..."  # actual search

# Input guardrail to block off-topic
@input_guardrail
async def topic_guardrail(ctx, agent, user_input):
    if "weather" in user_input.lower():
        return GuardrailFunctionOutput(output_info="off-topic", tripwire_triggered=True)
    return GuardrailFunctionOutput(output_info="ok", tripwire_triggered=False)

# Specialized agents
docs_agent = Agent(
    name="docs",
    instructions="Answer technical questions using search_docs.",
    tools=[search_docs],
    model="gpt-4o",
)

triage_agent = Agent(
    name="triage",
    instructions=(
        "Route the user to the right specialist. "
        "If it's a docs/technical question, hand off to the docs agent."
    ),
    handoffs=[docs_agent],
    input_guardrails=[topic_guardrail],
    model="gpt-4o-mini",
)

# Run
result = Runner.run_sync(triage_agent, "How do I configure gRPC retries?")
print(result.final_output)
```

## Patterns that pair well

- **Handoff-based multi-agent** — triage → specialist routing
- **Guardrails on inputs and outputs** — schema and content checks
- **Simple ReAct loops** with the built-in Runner

## Patterns that don't fit well

- **Stateful long-running workflows** with checkpointing — use LangGraph
- **Multi-provider work** — Agents SDK is OpenAI-only

## Migration notes

- From `assistants` API: Agents SDK is the recommended successor
- From LangChain agents: simpler model; rewrite straightforward
- To Claude Agent SDK: when switching providers
