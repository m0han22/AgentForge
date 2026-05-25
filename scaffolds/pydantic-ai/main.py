"""
Pydantic AI — Type-safe agent with structured output and DI.
"""

import asyncio
import json
import os
import sys
from dataclasses import dataclass
from typing import Iterable

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext


class Source(BaseModel):
    title: str
    snippet: str
    url: str | None = None


class Answer(BaseModel):
    text: str
    sources: list[Source] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class FakeDB:
    """Stub. Replace with a real retriever (pgvector / Qdrant / LlamaIndex)."""

    def search(self, query: str, user_id: str) -> Iterable[Source]:
        return [
            Source(
                title=f"[stub] Doc about '{query[:30]}'",
                snippet=f"Replace FakeDB.search with a real retriever. (user={user_id})",
                url="https://example.com/stub",
            )
        ]


@dataclass
class Deps:
    db: FakeDB
    user_id: str


agent = Agent(
    "anthropic:claude-opus-4-7",
    deps_type=Deps,
    output_type=Answer,
    system_prompt=(
        "You are a documentation assistant. Use search_docs to find relevant material. "
        "Always cite at least one source. Confidence reflects how well the sources "
        "directly answer the question (1.0 = perfect grounding, 0.2 = weak)."
    ),
)


@agent.tool
async def search_docs(ctx: RunContext[Deps], query: str) -> list[Source]:
    """Search the user's accessible docs. Use for any factual question."""
    return list(ctx.deps.db.search(query, ctx.deps.user_id))


async def run(question: str) -> Answer:
    result = await agent.run(
        question,
        deps=Deps(db=FakeDB(), user_id="demo-user"),
    )
    return result.output


if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY in .env or environment", file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) < 2:
        print('Usage: python main.py "your question"', file=sys.stderr)
        sys.exit(1)

    answer = asyncio.run(run(" ".join(sys.argv[1:])))
    print(json.dumps(answer.model_dump(), indent=2))
