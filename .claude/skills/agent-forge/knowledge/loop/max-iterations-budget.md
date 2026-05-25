---
name: Max Iterations + Step / Token / Cost Budgets
category: loop
difficulty: beginner
when_to_use: every production agent loop, every multi-step LLM workflow
frameworks: [claude-agent-sdk, langgraph, langchain, openai-agents-sdk, pydantic-ai, crewai]
related: [infinite-loop-guard, progress-detection, circuit-breaker]
anti_patterns: [run-until-done, budget-free-agents]
tags: [loop, budget, safety, cost-control]
---

# Max Iterations + Step / Token / Cost Budgets

**TL;DR:** Every agent loop needs hard caps on iterations, total LLM calls, tokens, dollars, and wall-clock time. Aborting with a diagnostic is always better than silently looping forever or running up an unbounded bill.

## When to use

- Every production agent. No exceptions.
- Especially: agents with tools that can fail or hang, agents called by users (not just internal scripts), agents over expensive models.

## When NOT to use

- Trivial single-call LLM features with no loop. (But you still want a cost cap globally.)

## How it works

Four orthogonal budgets, each with its own enforcement:

1. **Max iterations** — hard cap on loop count (10–20 typical). Abort with diagnostic on hit.
2. **Token budget** — sum input + output tokens across the session. Abort when exceeded.
3. **Cost budget** — translate tokens to $ at current model pricing. Abort when exceeded. Confirm with user before starting if estimated cost > threshold.
4. **Wall-clock timeout** — hard time limit per invocation (60–300s typical). Async-friendly: check between steps, return partial state on timeout.

The pattern: at each step boundary, check ALL budgets. Fail fast with a structured error the caller can render.

## Code — Claude Agent SDK

```python
from dataclasses import dataclass, field
from time import monotonic

@dataclass
class AgentBudget:
    max_iterations: int = 15
    max_tokens: int = 100_000
    max_cost_usd: float = 1.0
    max_wall_seconds: float = 120.0

    iterations: int = 0
    tokens_used: int = 0
    cost_used: float = 0.0
    start: float = field(default_factory=monotonic)

    def check(self) -> tuple[bool, str | None]:
        if self.iterations >= self.max_iterations:
            return False, f"max_iterations exceeded ({self.max_iterations})"
        if self.tokens_used >= self.max_tokens:
            return False, f"token budget exceeded ({self.tokens_used}/{self.max_tokens})"
        if self.cost_used >= self.max_cost_usd:
            return False, f"cost budget exceeded (${self.cost_used:.2f}/${self.max_cost_usd:.2f})"
        if monotonic() - self.start >= self.max_wall_seconds:
            return False, f"wall-clock timeout ({self.max_wall_seconds}s)"
        return True, None

def run_agent(client, system, user_msg, tools, budget: AgentBudget):
    messages = [{"role": "user", "content": user_msg}]
    while True:
        ok, reason = budget.check()
        if not ok:
            return {"status": "budget_exceeded", "reason": reason, "messages": messages}
        budget.iterations += 1

        resp = client.messages.create(
            model="claude-opus-4-7",
            system=system,
            tools=tools,
            messages=messages,
            max_tokens=4096,
        )
        budget.tokens_used += resp.usage.input_tokens + resp.usage.output_tokens
        budget.cost_used += estimate_cost(resp)

        if resp.stop_reason == "end_turn":
            return {"status": "ok", "result": resp, "iterations": budget.iterations}

        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            tool_results = execute_tools(resp.content, tools)
            messages.append({"role": "user", "content": tool_results})
            continue

        return {"status": "unexpected_stop", "reason": resp.stop_reason}
```

## Tradeoffs

- **Tight budgets** abort some legitimate long sessions — accept this; the upside (no runaway cost / no infinite loops) is worth the rare false stop.
- **Cost estimation** requires keeping per-model pricing in code. Worth maintaining a small pricing table.
- **Wall-clock** is the only budget that works against tools that hang — others don't catch tool-side hangs.

## Anti-patterns

- "Run until LLM says done" — LLMs can loop forever or never emit a `stop_turn`
- Only iteration cap, no token/cost cap — single long iteration can blow budget
- Silent stop on cap hit — caller has no idea why the agent quit
- Checking budget AFTER the LLM call instead of before — overshoots by one expensive call
- No `wall_seconds` cap — agent can hang indefinitely on a stuck tool

## Related

- `infinite-loop-guard` — detect repeated identical tool calls
- `progress-detection` — abort when state doesn't change across iterations
- `circuit-breaker` — stop on N consecutive tool errors
- `cost-projection-prompt` — confirm with user when estimated cost > threshold
