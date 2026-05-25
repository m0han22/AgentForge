---
name: Golden Set Construction
category: evals
difficulty: beginner
when_to_use: before optimizing any prompt, model, retrieval, or agent pipeline
frameworks: [langsmith, ragas, phoenix, langfuse]
related: [ragas-context-recall, regression-on-every-change, eval-on-real-data]
anti_patterns: [optimize-without-eval, synthetic-only-eval]
tags: [evals, golden-set, regression, measurement]
---

# Golden Set Construction

**TL;DR:** Build a 50–200 example dataset of `(input, expected_output)` pairs from real production data BEFORE you start optimizing. Run it on every change. Without it, every "improvement" is a guess.

## When to use

- Before tuning any prompt, swapping any model, changing any retrieval setting
- Before shipping any agent or RAG pipeline to production
- After any production incident — add the failing case to the golden set

## When NOT to use

- One-shot scripts that won't change
- Pure exploration / hackweek prototypes (but build one before promoting to prod)

## How it works

The golden set is a tiny, hand-curated dataset that captures what "good" looks like for your specific task. Process:

1. **Source from real data.** Pull 50–200 real user queries (or real document scenarios) from logs / tickets / interviews.
2. **Stratify.** Include the boring common cases (~70%), the known hard cases (~20%), the adversarial cases (~10% — jailbreak attempts, edge cases).
3. **Label.** For each input, write the expected output (full text for generation, expected chunk IDs for retrieval, expected tool calls for agents).
4. **Add metrics.** Pair the dataset with 1–3 metrics: exact match, context-recall, faithfulness, LLM-as-judge score.
5. **Version it.** Check the dataset into git. Tag with the date you last refreshed.
6. **Gate on it.** Every prompt/model/pipeline change runs the golden set; regressions block the merge.

The set grows by accretion: every production incident adds a new row. After 6 months you have a real safety net.

## Code — Ragas + a CSV

```python
# golden_set.csv:
# question,ground_truth_answer,ground_truth_context_ids,category
import csv
from ragas import evaluate
from ragas.metrics import context_recall, faithfulness, answer_correctness
from datasets import Dataset

def load_golden(path="golden_set.csv"):
    rows = []
    with open(path) as f:
        for row in csv.DictReader(f):
            rows.append({
                "question": row["question"],
                "ground_truth": row["ground_truth_answer"],
                "category": row["category"],
            })
    return rows

def run_pipeline(question: str) -> dict:
    """Your RAG pipeline. Returns: {answer, contexts}."""
    ...

def evaluate_pipeline():
    golden = load_golden()
    results = [run_pipeline(g["question"]) for g in golden]
    ds = Dataset.from_list([
        {
            "question": g["question"],
            "answer": r["answer"],
            "contexts": r["contexts"],
            "ground_truth": g["ground_truth"],
        }
        for g, r in zip(golden, results)
    ])
    scores = evaluate(ds, metrics=[context_recall, faithfulness, answer_correctness])
    return scores

if __name__ == "__main__":
    scores = evaluate_pipeline()
    print(scores)
    # Ship rule: context_recall > 0.85, faithfulness > 0.9
    assert scores["context_recall"] > 0.85
    assert scores["faithfulness"] > 0.9
```

## Tradeoffs

- **Manual labeling is tedious** — 50 examples take 2–4 hours. Worth it. Pay yourself once; benefit forever.
- **Synthetic golden sets are tempting** but produce optimistic-biased metrics. Use synthetic only to supplement, never as the primary set.
- **Size:** smaller than 50 is noise-dominated; larger than 200 is diminishing returns until you have specific subsegments to evaluate.

## Anti-patterns

- "We'll add the eval later" — you won't. Build it first.
- Synthetic dataset from the LLM itself — measures LLM's confidence, not correctness
- Single metric (just exact match, or just LLM-judge) — different metrics catch different failure modes
- Golden set in a doc / spreadsheet, not in git — gets stale, no versioning
- Never updating after incidents — the set decays into "tests for last month's problems"

## Related

- `regression-on-every-change` — CI gates on golden set
- `ragas-context-recall` — primary RAG metric to put in the gate
- `pairwise-comparison` — A/B for optimization, golden set for absolute floor
- `adversarial-eval` — the 10% hard-case slice
