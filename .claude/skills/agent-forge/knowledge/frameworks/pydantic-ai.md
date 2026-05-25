---
name: Pydantic AI
category: frameworks
when_to_use: type-safe agents with structured outputs, Pythonic developer experience, dependency injection
language: [python]
maturity: stable
tags: [framework, pydantic, type-safety, structured-output]
---

# Pydantic AI

**TL;DR:** Type-safe Python agent framework from the Pydantic team. Structured outputs are first-class via Pydantic models. Best when you want strong typing, structured responses, and a Pythonic feel without LangChain-style abstractions.

## Pick this when

- You're a Python shop that values type safety
- Structured outputs (Pydantic models) are central to your responses
- You want dependency injection for context (DB connections, user state)
- You prefer a clean, focused framework over a kitchen-sink ecosystem
- Multi-provider support matters (Pydantic AI is provider-agnostic)

## Don't pick this when

- TypeScript is your stack (Python-only)
- You need pre-built multi-agent orchestration (use CrewAI / Agents SDK)
- You need a stateful graph framework (use LangGraph)
- You're already deep in LangChain and the cost of switching outweighs the benefit

## Strengths

- **Type-safe everything** — agent.run() returns a typed result you can refactor against
- **Structured outputs via Pydantic** — the most ergonomic structured-response API in Python
- **Dependency injection** — pass context (DB, auth, user) to tools cleanly
- **Multi-provider** — Anthropic, OpenAI, Gemini, Groq, Mistral, etc.
- **Lightweight** — small surface area; easy to understand the whole API
- **Streaming + tool use + validation** all work out of the box

## Weaknesses

- **Python-only**
- **Newer ecosystem** — fewer integrations than LangChain
- **No built-in checkpointing** like LangGraph
- **Multi-agent is DIY** — composable but not opinionated like CrewAI

## Key APIs

```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from dataclasses import dataclass

class SearchResult(BaseModel):
    title: str
    snippet: str
    url: str

class Answer(BaseModel):
    text: str
    sources: list[SearchResult]
    confidence: float  # 0.0 - 1.0

@dataclass
class Deps:
    db: "Database"
    user_id: str

agent = Agent[Deps, Answer](
    "anthropic:claude-opus-4-7",
    deps_type=Deps,
    result_type=Answer,
    system_prompt="You are a documentation assistant. Always return sources and a confidence score.",
)

@agent.tool
async def search_docs(ctx: RunContext[Deps], query: str) -> list[SearchResult]:
    """Search the user's accessible docs."""
    return await ctx.deps.db.search(query, user_id=ctx.deps.user_id)

# Use
result = await agent.run("How do I configure retries?", deps=Deps(db=db, user_id="u-123"))
print(result.data.text, result.data.confidence)  # typed!
```

## Patterns that pair well

- **Structured output agents** — anywhere you need typed responses
- **DI for multi-tenant** — `deps` carries the user/tenant context safely
- **Schema-validated tool args** — Pydantic models everywhere

## Patterns that don't fit well

- **Long-running stateful workflows** — use LangGraph
- **Pre-built multi-agent crews** — use CrewAI

## Migration notes

- From OpenAI SDK + manual Pydantic parsing: significant ergonomic upgrade
- From LangChain: gain type safety, lose some integrations
- Pairs well alongside FastAPI (same Pydantic models)
