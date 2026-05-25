---
name: ReAct (Reason + Act) Agent
category: architecture
difficulty: beginner
when_to_use: multi-step tool-use tasks where the steps are not known in advance
frameworks: [langgraph, claude-agent-sdk, openai-agents-sdk, langchain, pydantic-ai]
related: [plan-execute-for-complex, reflection-when-cheap, max-iterations-budget]
anti_patterns: [react-when-deterministic-would-work, no-loop-budget]
tags: [architecture, react, agent-loop, tool-use]
---

# ReAct (Reason + Act) Agent

**TL;DR:** Single agent loop: model reasons about what to do → calls a tool → observes the result → reasons again → continues until done. Default agent architecture for tool-using LLMs. Pair with strict budgets.

## When to use

- Multi-step tasks involving tools (search, calculate, look up, file ops)
- Tasks where the next step depends on previous tool output
- When you don't know the full plan in advance
- Default choice when you don't have a specific reason to use something else

## When NOT to use

- Tasks with fixed, known steps — use a workflow (deterministic graph) instead
- Tasks needing parallel exploration of multiple branches — use orchestrator-worker
- Multi-step tasks where the plan IS known upfront — use plan-then-execute (avoids interleaved reasoning overhead)
- Single-tool, single-call interactions — just call the tool directly

## How it works

The loop:

```
1. Model receives: system prompt + user query + tools available
2. Model emits: either a final answer (stop) or a tool call (continue)
3. If tool call: execute tool, append result to messages
4. Loop to step 2
```

The model interleaves "reasoning" (which tool? what args?) with "acting" (tool call) implicitly — no separate planning step.

Critical guards:
- **Max iterations** (10–20)
- **Token / cost budget**
- **Infinite loop detection** (same tool + same args repeated)
- **Tool error circuit breaker** (3 consecutive errors → ask user)

## Code — Claude Agent SDK

```python
from anthropic import Anthropic

client = Anthropic()
MAX_ITERS = 15

def react_agent(system: str, user_query: str, tools: list, tool_handlers: dict):
    messages = [{"role": "user", "content": user_query}]
    for i in range(MAX_ITERS):
        resp = client.messages.create(
            model="claude-opus-4-7",
            system=system,
            tools=tools,
            messages=messages,
            max_tokens=4096,
        )

        if resp.stop_reason == "end_turn":
            return resp.content[0].text

        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    try:
                        result = tool_handlers[block.name](block.input)
                    except Exception as e:
                        result = {"error": "tool_failed", "detail": str(e)}
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        raise RuntimeError(f"Unexpected stop_reason: {resp.stop_reason}")

    raise RuntimeError(f"Agent exceeded {MAX_ITERS} iterations without completing")
```

## Tradeoffs

- **Simple to implement and debug** — single loop, easy to trace.
- **Latency:** each step is a round-trip. N-step task = N×LLM latency. Stream intermediate thinking to mitigate UX impact.
- **Token cost** grows quadratically with steps (full history sent each turn). Mitigate with prompt caching + history compression.
- **Quality:** good for ≤10 steps; degrades for longer tasks — switch to plan-execute or multi-agent.

## Anti-patterns

- ReAct loop when a deterministic workflow would work — adds nondeterminism without benefit
- No iteration cap — single bad query can run for hours
- Re-sending full history every turn without prompt caching — costs explode
- Tool errors as exceptions thrown to the caller — LLM can't recover
- "Just one more tool" patterns — model keeps adding tools instead of answering

## Related

- `max-iterations-budget` — required pairing
- `plan-execute-for-complex` — alternative for known-plan tasks
- `streaming-thoughts-for-ux` — show reasoning during long loops
- `reflection-when-cheap` — quality booster when accuracy matters
