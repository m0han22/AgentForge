---
name: "Run Until Done" (No Loop Budget)
category: anti-patterns
applies_to: [loop, cost, deployment]
severity: critical
tags: [anti-pattern, loop, budget, safety]
---

# "Run Until Done" (No Loop Budget)

**The trap:** Your agent loop is `while True: step()`. It terminates "when the LLM says it's done." It works in testing. In production, a single bad query loops 200 times, racks up a $50 bill, and times out only because the load balancer killed it.

## Why it happens

- Demo code becomes prod code without budget retrofit
- Tools that occasionally hang make the LLM keep retrying
- LLM goes into a degenerate "let me try one more search" loop
- Prompts encourage thoroughness without bounds ("keep going until you have a complete answer")

## How to recognize it

- Cost alerts firing on single-user sessions
- Latency p99 spikes that are 100× p50
- Logs showing the same tool called with the same args repeatedly
- Wall-clock timeouts from the load balancer (not the agent)

## What to do instead

Four budgets, always:

1. **Max iterations** (10–20)
2. **Token budget** per session
3. **Cost budget** per session
4. **Wall-clock timeout** per invocation

Plus structural defenses:

- **Infinite loop guard:** detect identical tool calls and break
- **Progress detection:** abort when state doesn't change across iterations
- **Circuit breaker:** stop after N consecutive tool errors

See `knowledge/loop/max-iterations-budget.md` for code.

## What about legitimately long tasks?

Use async patterns. Long tasks should not be sync agent loops. They should be:

- Async background jobs with checkpoints (LangGraph + Postgres saver)
- Workflows with human-in-the-loop pauses
- Decomposed into many short agent calls, not one long one

## Related

- `max-iterations-budget` — the fix
- `infinite-loop-guard` — detection
- `circuit-breaker` — error-driven termination
- `agent-as-async-task` — for legitimately long work
