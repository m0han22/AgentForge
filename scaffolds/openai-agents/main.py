"""
OpenAI Agents SDK — Triage agent that hands off to a docs specialist.
"""

import json
import os
import sys

from agents import (
    Agent,
    GuardrailFunctionOutput,
    Runner,
    function_tool,
    handoff,
    input_guardrail,
)
from pydantic import BaseModel


class DocsRequest(BaseModel):
    question: str
    user_role: str = "developer"


@function_tool
def search_docs(query: str) -> str:
    """Search engineering docs. Use for technical questions about our products."""
    # Replace with a real retriever. See scaffolds/llamaindex/ for an example.
    return (
        f"[stub] No docs index wired up yet. Replace search_docs with a real retriever. "
        f"Query was: {query}"
    )


@input_guardrail
async def topic_guardrail(ctx, agent, user_input):
    off_topic_terms = ("weather", "sports", "stock price", "horoscope")
    is_off = any(t in user_input.lower() for t in off_topic_terms)
    return GuardrailFunctionOutput(
        output_info={"off_topic": is_off},
        tripwire_triggered=is_off,
    )


docs_agent = Agent(
    name="docs_specialist",
    instructions=(
        "You answer technical questions using search_docs. "
        "Cite the source for every claim. If no relevant doc is found, "
        "say 'I don't have that information' — do not guess."
    ),
    tools=[search_docs],
    model="gpt-4o",
)

triage_agent = Agent(
    name="triage",
    instructions=(
        "Route the user to the right specialist. "
        "Technical / docs / how-to questions → hand off to docs_specialist with a structured DocsRequest. "
        "Everything else → answer directly that you cannot help with that topic."
    ),
    handoffs=[handoff(docs_agent, input_type=DocsRequest)],
    input_guardrails=[topic_guardrail],
    model="gpt-4o-mini",
)


def run(question: str) -> dict:
    result = Runner.run_sync(triage_agent, question)
    return {
        "final_agent": result.final_agent.name if result.final_agent else None,
        "answer": result.final_output,
    }


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY in .env or environment", file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) < 2:
        print('Usage: python main.py "your question"', file=sys.stderr)
        sys.exit(1)

    print(json.dumps(run(" ".join(sys.argv[1:])), indent=2))
