---
name: Reflection (Self-Critique Loop)
category: architecture
difficulty: intermediate
when_to_use: quality-critical tasks where a second pass can catch errors and the latency / cost budget allows
frameworks: [claude-agent-sdk, langgraph, openai-agents-sdk, pydantic-ai]
related: [react-agent, plan-execute-verify, llm-as-judge]
anti_patterns: [reflection-on-every-call, reflection-without-eval]
tags: [architecture, reflection, self-critique, quality]
---

# Reflection (Self-Critique Loop)

**TL;DR:** After producing a candidate answer, have the model (same or stronger) critique it against explicit criteria, then revise. Trades 2–3× latency and cost for measurable quality lift on hard tasks. Worth it only when single-shot quality has a measurable floor you can't reach otherwise.

## When to use

- High-stakes outputs (legal, medical, financial summaries)
- Code generation where correctness matters more than throughput
- Agent plans before execution (catch obvious mistakes before acting)
- Anywhere your golden-set eval shows single-shot quality plateauing below ship threshold

## When NOT to use

- Interactive chat with a tight latency budget (reflection adds seconds)
- Tasks where the model isn't actually capable enough — reflection doesn't fix capability gaps
- Without an eval — you cannot tell if reflection is actually helping
- Routine, low-risk outputs — the cost isn't justified

## How it works

Three-step loop:

1. **Generate** — model produces a candidate answer.
2. **Critique** — same or stronger model reviews against an explicit rubric ("Are the facts grounded in the retrieved context? Are there factual claims without citations? Is the code syntactically valid? Does it solve the stated problem?").
3. **Revise** — model produces a new answer addressing the critique.

Variants:
- **Self-reflection** — same model does all three steps.
- **Cross-model reflection** — Opus critiques Sonnet's output (stronger critic).
- **N-pass reflection** — repeat until the critique is empty (cap iterations).

Pair with prompt caching for the rubric + context; only the candidate changes per pass.

## Code — Claude Agent SDK

```python
from anthropic import Anthropic

client = Anthropic()
MAX_REFLECT_ITERS = 2

CRITIQUE_PROMPT = """Critique the candidate answer against these criteria:
1. Every factual claim must cite a source from <context>.
2. No claims that contradict the context.
3. No hedging that fails to answer the question.
4. Code (if any) must compile.

Output JSON: {"issues": [...], "must_revise": true|false}
"""

def reflect_and_revise(system: str, context: str, question: str) -> str:
    # Step 1: generate
    candidate = client.messages.create(
        model="claude-opus-4-7",
        system=system,
        messages=[{"role": "user", "content": f"<context>{context}</context>\n<question>{question}</question>"}],
        max_tokens=2048,
    ).content[0].text

    for i in range(MAX_REFLECT_ITERS):
        # Step 2: critique
        critique = client.messages.create(
            model="claude-opus-4-7",
            system=CRITIQUE_PROMPT,
            messages=[{"role": "user", "content": f"<context>{context}</context>\n<question>{question}</question>\n<candidate>{candidate}</candidate>"}],
            max_tokens=512,
        ).content[0].text

        import json
        try:
            verdict = json.loads(critique)
        except Exception:
            return candidate  # critique malformed; ship the candidate

        if not verdict.get("must_revise"):
            return candidate

        # Step 3: revise
        candidate = client.messages.create(
            model="claude-opus-4-7",
            system=system,
            messages=[
                {"role": "user", "content": f"<context>{context}</context>\n<question>{question}</question>"},
                {"role": "assistant", "content": candidate},
                {"role": "user", "content": f"Revise to address: {verdict['issues']}"},
            ],
            max_tokens=2048,
        ).content[0].text

    return candidate
```

## Tradeoffs

- **Cost:** 2–3× a single-shot call. Budget accordingly.
- **Latency:** sequential by nature — each step waits for the prior. Streaming the final answer mitigates UX.
- **Diminishing returns:** 1 reflection pass captures most of the lift; 2+ rarely helps and sometimes degrades (over-revision).
- **Same-model critique** has blind spots — the model misses its own systematic errors. Cross-model critique catches more.

## Anti-patterns

- Adding reflection without measuring — you're paying 2–3× without knowing it helps
- Reflecting on every call — pick the high-stakes subset; route others to single-shot
- No iteration cap — model can chase its tail revising forever
- Vague critique prompt ("is this good?") — model produces vague critique; rubric must be specific
- Reflection as substitute for retrieval / tools — it's a quality booster, not a knowledge source

## Related

- `react-agent` — pair reflection with action sequences
- `plan-execute-verify` — reflection on the plan, not the output
- `llm-as-judge` — same primitive used for eval
- `pairwise-comparison` — to measure if reflection actually helps your task
