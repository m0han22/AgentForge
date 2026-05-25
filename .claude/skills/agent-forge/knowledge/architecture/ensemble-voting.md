---
name: Ensemble (Voting / Majority)
category: architecture
difficulty: intermediate
when_to_use: high-stakes single-shot decisions where wrong answers are costly and the cost of N calls is acceptable
frameworks: [claude-agent-sdk, langgraph, openai-agents-sdk, langchain]
related: [reflection, llm-as-judge, plan-execute-verify]
anti_patterns: [ensemble-on-everything, same-model-same-temperature-ensemble]
tags: [architecture, ensemble, voting, majority, self-consistency]
---

# Ensemble (Voting / Majority)

**TL;DR:** Run the same query through N agents (different models, temperatures, or prompts), aggregate via majority vote or weighted scoring, return the consensus. Trades N× cost for measurable quality lift on single-shot decisions. Often beats reflection at the same cost budget.

## When to use

- High-stakes classification (fraud detection, content moderation, medical triage)
- Single-shot answers where wrong is expensive (legal, financial recommendations)
- Tasks with measurable correctness — "self-consistency" research shows ensembles beat single-shot on math, code, and reasoning
- When you've measured that single-shot accuracy plateaus below ship threshold

## When NOT to use

- Open-ended generative tasks where "consensus" doesn't apply (creative writing)
- Latency-sensitive paths — N calls in parallel still cost the slowest call's time
- Cost-constrained workloads — N× cost adds up fast
- Tasks where the model isn't capable enough — ensembling weak models doesn't fix weakness

## How it works

Three variants:

1. **Self-consistency** — same model + same prompt, but sample N times with temperature > 0; majority-vote the answers.
2. **Diverse-prompt ensemble** — same model, N different prompts (paraphrases, different framings); vote.
3. **Diverse-model ensemble** — N different models (Opus, Sonnet, Haiku, or cross-provider); vote, optionally weighted by past accuracy.

Aggregation:
- **Hard vote** — pick the most common answer (good for classification)
- **Weighted vote** — weight by per-model historical accuracy or per-call confidence
- **Soft aggregation** — synthesize across answers (LLM-as-judge picks the best, or merges)

## Code — Self-consistency

```python
import asyncio
from collections import Counter
from anthropic import AsyncAnthropic

client = AsyncAnthropic()
N = 5

async def sample_answer(question: str, temperature: float = 0.7) -> str:
    resp = await client.messages.create(
        model="claude-opus-4-7",
        max_tokens=512,
        temperature=temperature,
        messages=[{"role": "user", "content": question}],
    )
    return resp.content[0].text.strip()

async def ensemble(question: str, n: int = N) -> str:
    samples = await asyncio.gather(*[sample_answer(question) for _ in range(n)])
    # Normalize: lowercase, strip punctuation, etc. — domain-specific
    normalized = [s.lower().strip(".!?") for s in samples]
    counts = Counter(normalized)
    most_common, count = counts.most_common(1)[0]
    confidence = count / n
    # Return the original (un-normalized) sample matching the consensus
    for sample, norm in zip(samples, normalized):
        if norm == most_common:
            return {"answer": sample, "confidence": confidence, "n": n}
```

## Code — Cross-model ensemble (diverse)

```python
async def cross_model_ensemble(question: str) -> dict:
    tasks = [
        client.messages.create(model="claude-opus-4-7", messages=[{"role":"user","content":question}], max_tokens=512),
        client.messages.create(model="claude-sonnet-4-6", messages=[{"role":"user","content":question}], max_tokens=512),
        # plus calls to other providers (OpenAI, Gemini) via their SDKs
    ]
    responses = await asyncio.gather(*tasks)
    answers = [r.content[0].text.strip() for r in responses]
    # Use LLM-as-judge to synthesize
    judge_prompt = (
        f"Question: {question}\n"
        f"Candidate answers:\n" + "\n".join(f"{i+1}. {a}" for i, a in enumerate(answers))
        + "\nPick the most-supported answer and explain. Output JSON: {answer, confidence, reasoning}"
    )
    judge = await client.messages.create(model="claude-opus-4-7", messages=[{"role":"user","content":judge_prompt}], max_tokens=512)
    return parse_json(judge.content[0].text)
```

## Tradeoffs

- **Quality:** measurable lift on math, code, classification, reasoning tasks (self-consistency papers)
- **Cost:** N× single-shot; budget hard
- **Latency:** with `asyncio.gather`, latency = slowest call (not N×), but worst-case is still high
- **Diversity matters:** identical temperature + identical prompt + same model = same answer N times = no ensemble benefit
- **Aggregation choice:** wrong aggregation kills the benefit (hard-vote on generative outputs makes no sense)

## Anti-patterns

- Ensembling open-ended generation (creative writing) — no consensus signal
- Same model + temperature 0 + same prompt — N identical answers
- N too small (N=2) — no majority signal; minimum 3, typically 5
- No diversity strategy — ensemble of clones doesn't lift quality
- Ensembling everything — cost balloons; use only on high-stakes subset

## Related

- `reflection` — alternative quality booster; reflect-once often comparable to small ensemble at lower cost
- `llm-as-judge` — useful as the aggregator
- `pairwise-comparison` — measure if ensemble actually helps
- `model-routing` — combine with ensembles by tier (cheap ensemble for routine, expensive for edge cases)
