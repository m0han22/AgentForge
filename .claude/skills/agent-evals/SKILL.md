---
name: agent-evals
description: "Set up evaluation and observability for LLM agents and RAG pipelines. Covers golden set construction (50-200 examples from real data), Ragas metrics (context-recall, faithfulness, answer-correctness), LLM-as-judge, pairwise comparison, regression gates, full trace logging (LangSmith, Phoenix, Langfuse, Helicone), distribution metrics (p50/p95/p99), drift monitoring, cost-per-query tracking, user feedback loops, adversarial eval, human spot checks, staging shadow traffic. Returns one prescriptive eval setup with code, golden-set construction guide, and CI gate."
allowed-tools: Read, Bash, Glob, Grep
---

# agent-evals — Evaluation & Observability

Opinionated guide for measuring whether an agent or RAG pipeline is actually working. Owns golden sets, Ragas, LLM-as-judge, regression gates, traces.

Defers to the **agent-forge hub**. Source of truth: `agent-forge/knowledge/evals/`.

## When to activate

- "How do I evaluate my agent / RAG?"
- "Measure RAG quality" / "Is my RAG good?"
- "Ragas", "golden set", "LLM-as-judge"
- "Set up traces" / "observability for agents"
- "Regression test for my prompt"
- "LangSmith / Phoenix / Langfuse"
- "My agent regressed" / "users complaining about quality drop"

## When NOT to activate

- Building the agent itself → use `agent-architectures` or `agent-rag` first
- Cost/latency optimization → primarily `agent-deployment` (with eval as supporting)

## Workflow

1. **Gather operational constraints (MANDATORY) and parse.** Before designing the eval, confirm: **(a) production load** (drives how much real data is available for golden set, drives sampling rate for human spot-check), **(b) latency budget** (eval can't slow prod past this — drives async vs inline eval), **(c) cost ceiling** (LLM-as-judge calls cost real money at scale — drives judge model tier and eval cadence). ASK ONE clarifying question if any are missing. Also extract: agent type (RAG vs agent vs both), current state (no eval yet vs scaling existing), main quality concern (hallucination, latency, cost).
2. **Search** — `--domain evals`
3. **Synthesize**

## Eval defaults (prescriptive path)

Phase 0 — BEFORE optimizing anything:
- Build a **50–200 example golden set** from real production samples (stratify: 70% common, 20% hard, 10% adversarial)
- Pick **1–3 metrics**:
  - RAG: Ragas context-recall + faithfulness + answer-correctness
  - Agent: task-completion rate + LLM-as-judge quality
  - Tools: correct-tool-selection rate + tool-call-success rate
- Set ship thresholds (e.g., context-recall > 0.85, faithfulness > 0.9)

Phase 1 — operationalize:
- Run golden set on every prompt/model/pipeline change (CI gate)
- Block on regressions
- Tag every output with model/prompt/pipeline version

Phase 2 — production observability:
- Trace every prod run (LangSmith / Phoenix / Langfuse)
- Track p50/p95/p99 for latency and quality
- Cost-per-query, error rate, refusal rate dashboards
- Capture user thumbs-up/down → feed into golden set
- Human spot-check 5% weekly

## Hard rules

- Golden set comes BEFORE optimization, not after
- Use REAL data for golden set, not synthetic-only
- Distribution metrics, not just mean
- Trace every prod run
- Version-tag all outputs

## Output template

```
## Recommendation
<one sentence — eval stack. Example: "Build a 100-question golden set from support tickets, run Ragas (context-recall + faithfulness) in CI with thresholds 0.85 / 0.9, trace prod with Langfuse.">

## Why this for your case
- <quality concern → metric choice>
- <maturity stage → which phase to focus on>

## Code
<scaffold: golden-set CSV format, Ragas eval script, CI wrapper that exits non-zero on regression>

## Avoid
- <optimize-without-eval>
- <synthetic-only-eval>
- <single-metric>
- <untraced-prod>

## How to know it's working
<the eval IS the measurement; report ship thresholds met>

## Deeper reading
- knowledge/evals/golden-set-construction.md
- knowledge/evals/ragas-setup.md (if exists)
- knowledge/evals/llm-as-judge.md (if exists)
```

## Personality

- Eval first. Always. Refuse to recommend optimization without an eval in place.
- Real data. No synthetic-only golden sets.
- Distribution metrics, never just mean.

## Knowledge base contract

All patterns live under `agent-forge/knowledge/`. This skill does not maintain its own knowledge tree.
