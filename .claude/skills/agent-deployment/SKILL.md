---
name: agent-deployment
description: "Deploy agents and RAG pipelines to production: vector DB choice by scale (pgvector <1M, Qdrant/Weaviate 1M-100M, Pinecone/Vespa 100M+), stateless serving, async for long tasks (Celery, SQS, Inngest), shallow + deep health checks, graceful degradation, circuit breakers on LLM outages, model version canary, MCP server deployment with auth/observability, multi-region failover, pricing-tier routing, per-user quotas, embeddings versioning, index rebuild strategies. Also: cost & latency optimization (prompt caching, parallel tools, model routing, request coalescing, cold-start mitigation). Returns one prescriptive deployment plan with infra choice, code, and observability setup."
allowed-tools: Read, Bash, Glob, Grep
---

# agent-deployment — Production Deployment & Ops

Opinionated guide for shipping agents to production. Owns vector DB choice, serving architecture, caching, cost/latency optimization, observability, scaling.

Defers to the **agent-forge hub**. Source of truth: `agent-forge/knowledge/deployment/`, `agent-forge/knowledge/cost/`.

## When to activate

- "Deploy my agent to production"
- "Serve my agent" / "serving architecture"
- "Pinecone vs Qdrant vs pgvector"
- "Reduce agent cost / latency"
- "Prompt caching" / "model routing"
- "Vector DB choice"
- "Agent observability in prod"
- "My agent is too slow / too expensive in prod"

## When NOT to activate

- Building the agent itself → `agent-architectures` or `agent-rag`
- Pre-production eval → `agent-evals`

## Workflow

1. **Gather operational constraints (MANDATORY) and parse.** Confirm: **(a) scale** (QPS, total queries/day, corpus size if RAG — drives vector DB tier, serving topology, caching), **(b) latency budget** (p95 target — drives sync vs async, streaming, model routing), **(c) cost ceiling** (per-query, per-month, or hard cap — drives prompt caching, model routing, batching aggressiveness). ASK ONE clarifying question if any are missing. Also extract: ops capacity (managed vs self-host), deployment target (cloud, on-prem, hybrid), regulatory/data residency constraints.
2. **Search** — `--domain deployment` and `--domain cost`
3. **Synthesize**

## Deployment defaults (prescriptive path)

- **Vector DB:** pgvector for <1M chunks; Qdrant for 1M–100M (self-host if ops capacity, Pinecone if not); Vespa for 100M+
- **Serving:** stateless; agent state in DB/Redis, not process memory
- **Long-running agents (>30s):** async tasks (Celery, SQS, Inngest), NOT sync HTTP
- **Health checks:** shallow (process alive) + deep (LLM reachable)
- **Cost optimization:** prompt caching, parallel tool calls, model routing (Haiku/small for simple, Opus/large for complex), batch embeddings, cache retrievals + final answers
- **Resilience:** circuit-break on sustained LLM errors, graceful degradation to cached/cheaper paths, multi-region LLM failover for prod
- **Observability:** trace every run, p50/p95/p99 latency, cost-per-query, error rate, drift monitoring
- **Rollout:** canary new model versions on 5% traffic before full rollout
- **Quotas:** per-user quota enforcement; degrade or queue when exceeded
- **MCP servers:** behind same auth + observability as main service

## Hard rules

- Stateless serving (no in-memory state)
- Long agents → async
- Prompt caching on stable prefixes (system + retrieved context)
- Model version pinned, canary on changes
- Per-user quotas in place

## Output template

```
## Recommendation
<one sentence — infra stack. Example: "Stateless FastAPI behind Cloudflare, agent runs as Inngest async task, pgvector for retrieval, Anthropic prompt caching, Langfuse for traces, canary on new model versions.">

## Why this for your case
- <scale tier reasoning>
- <ops capacity reasoning>
- <latency/cost constraint reasoning>

## Code
<scaffold: serving endpoint, async task wrapper, health checks, prompt caching setup>

## Avoid
- <sync-http-for-long-agents>
- <pinecone-for-1000-docs>
- <no-prompt-caching>
- <no-canary-on-model-bump>

## How to know it's working
<observability checklist: traces, p95 latency, cost-per-query, error rate dashboards; load test before going live>

## Deeper reading
- knowledge/deployment/vector-db-choice.md
- knowledge/cost/prompt-caching.md
- knowledge/frameworks/<framework>.md
```

## Personality

- Match scale to infra. Don't over-provision.
- Always require prompt caching, async-for-long, traces.
- Default to managed for low ops capacity; self-host only with capacity.

## Knowledge base contract

All patterns live under `agent-forge/knowledge/`. This skill does not maintain its own knowledge tree.
