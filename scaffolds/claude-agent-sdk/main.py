"""
Claude Agent SDK — ReAct agent starter.

Implements:
- ReAct loop (reason → tool → observe → reason)
- Iteration / token / wall-clock budgets with abort-on-cap
- Prompt caching on the system prompt
- Structured error returns from tools
"""

import os
import sys
import json
import time
from anthropic import Anthropic

MODEL = "claude-opus-4-7"
MAX_ITERATIONS = 10
MAX_TOKENS = 50_000
MAX_WALL_SECONDS = 60.0

SYSTEM_PROMPT = """You are a focused research assistant. Use the `web_search` tool
when a question requires current information you don't have. Be concise. Always
cite the source URL when you use a search result.
"""

TOOLS = [
    {
        "name": "web_search",
        "description": (
            "Search the web for current information. Use when the user asks about "
            "recent events, current versions, prices, or anything time-sensitive. "
            "Example: web_search(query='latest Python release 2026')"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 3, "maxLength": 200},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    }
]


def web_search_impl(query: str, top_k: int = 5) -> dict:
    """Replace this with a real search provider (Tavily, Brave, Serper, etc.)."""
    return {
        "results": [
            {
                "title": f"Stub result {i+1} for '{query}'",
                "url": f"https://example.com/r{i+1}",
                "snippet": f"This is a placeholder. Replace web_search_impl with your provider.",
            }
            for i in range(min(top_k, 3))
        ]
    }


def handle_tool(name: str, args: dict) -> dict:
    try:
        if name == "web_search":
            return web_search_impl(query=args["query"], top_k=args.get("top_k", 5))
        return {"error": "unknown_tool", "hint": f"No handler for tool '{name}'"}
    except Exception as e:
        return {"error": "tool_failed", "hint": str(e)}


def run(user_question: str) -> dict:
    client = Anthropic()
    messages = [{"role": "user", "content": user_question}]
    tokens_used = 0
    started = time.monotonic()

    for i in range(MAX_ITERATIONS):
        if tokens_used >= MAX_TOKENS:
            return {"status": "budget_exceeded", "reason": f"tokens {tokens_used}/{MAX_TOKENS}"}
        if time.monotonic() - started >= MAX_WALL_SECONDS:
            return {"status": "timeout", "reason": f"wall_clock {MAX_WALL_SECONDS}s"}

        resp = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=TOOLS,
            messages=messages,
        )
        tokens_used += resp.usage.input_tokens + resp.usage.output_tokens
        print(f"[iter {i+1}] stop_reason={resp.stop_reason} tokens_used={tokens_used}", file=sys.stderr)

        if resp.stop_reason == "end_turn":
            text = "".join(b.text for b in resp.content if b.type == "text")
            return {"status": "ok", "answer": text, "iterations": i + 1, "tokens": tokens_used}

        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    result = handle_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        return {"status": "unexpected_stop", "stop_reason": resp.stop_reason}

    return {"status": "max_iterations", "iterations": MAX_ITERATIONS, "tokens": tokens_used}


if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY in .env or environment", file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) < 2:
        print('Usage: python main.py "your question"', file=sys.stderr)
        sys.exit(1)

    result = run(" ".join(sys.argv[1:]))
    print(json.dumps(result, indent=2))
