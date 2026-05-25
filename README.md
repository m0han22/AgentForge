# AgentForge

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Made for Claude Code](https://img.shields.io/badge/Made%20for-Claude%20Code-orange)](https://claude.com/claude-code)
[![Skills](https://img.shields.io/badge/Skills-7-blue)](.claude/skills)
[![Patterns](https://img.shields.io/badge/Patterns-30%2B-green)](.claude/skills/agent-forge/knowledge)

> Opinionated Claude Code skill suite for building production AI agents and RAG systems.

AgentForge turns Claude into an **opinionated agentic-AI architect**. Ask it to build a RAG system, design an agent, pick a framework, or harden one for production — and instead of generic LLM advice, you get **one prescriptive recommendation** with code, anti-patterns, and a starter eval. Modeled after [UI/UX Pro Max](https://www.uupm.cc) but for the agentic AI domain.

---

## What it does

You ask:

> "Build a RAG over 50k internal wiki pages. Citations required, low latency, Claude."

A vanilla LLM gives you 5 options to consider. AgentForge gives you **one path** because it first asks the three questions that matter — *load, latency, cost* — then makes the decision:

```
## Recommendation
LlamaIndex with hierarchical chunking + hybrid BM25/dense retrieval + Cohere
rerank-3, Claude Sonnet generation with Anthropic prompt caching, pgvector for storage.

## Why this for your case
- 50k chunks → pgvector tier (no need for Pinecone)
- Wiki structure → hierarchical chunking preserves citation paths
- Hybrid + rerank lifts recall@5 by ~20% on technical text
- Prompt caching + Sonnet → sub-second p95 at ~$0.001/query

## Code
[LlamaIndex scaffold: load → chunk → embed → hybrid retrieve → rerank → cite]

## Avoid
- Embedding whole wiki pages
- Dense-only retrieval on technical text
- Skipping the reranker
- Mixing embedding models between corpus and query

## How to know it's working
Build a 30-question golden set from real wiki support tickets. Measure
context-recall (Ragas) and citation-precision. Ship when both > 0.85.

## Deeper reading
- knowledge/retrieval/hybrid-search.md
- knowledge/deployment/vector-db-choice.md
- knowledge/evals/golden-set-construction.md
```

---

## What's in the box

**One hub skill + six focused skills**, all under `.claude/skills/`:

| Skill | Owns |
|---|---|
| **`agent-forge`** (hub) | The knowledge base, search engine, cross-cutting workflow. Activates on broad agentic / RAG queries. |
| `agent-architectures` | ReAct, plan-execute, PEV, orchestrator-worker, multi-agent handoff, blackboard, reflection, ensemble, sub-agent with isolated context, filesystem-as-memory |
| `agent-rag` | Chunking, hybrid retrieval, reranking, query rewriting, citation grounding |
| `agent-tools` | Tool schemas, MCP servers, error handling, idempotency, parallel calls |
| `agent-memory` | Sliding window, summarization tiers, episodic memory, per-user isolation |
| `agent-evals` | Golden sets, Ragas, LLM-as-judge, regression gates, traces, observability |
| `agent-deployment` | Vector DB choice by scale, async serving, prompt caching, model routing, canary |

**Knowledge base** at `.claude/skills/agent-forge/knowledge/`:
- 10 priority domains (safety, tools, loop, retrieval, evals, cost, memory, architecture, reasoning, prompt, deployment) with 200+ inline rules in the hub's SKILL.md plus growing pattern docs
- 10 architecture pattern docs (ReAct, reflection, plan-execute, PEV, orchestrator-worker, multi-agent-handoff, blackboard, ensemble, sub-agent-isolated-context, filesystem-as-memory)
- 8 framework profiles (Claude Agent SDK, LangGraph, LangChain, LlamaIndex, OpenAI Agents SDK, Pydantic AI, CrewAI, Deep Agents)
- Cross-cutting anti-patterns

**Search engine** at `.claude/skills/agent-forge/scripts/search.py`:
- BM25 ranking over markdown frontmatter + body
- Three modes: `--recommend` (multi-domain), `--domain <name>`, `--framework <name>`
- Optional `--persist` to save recommendations to `agent-system/MASTER.md` for cross-session reuse
- Falls back gracefully if `rank_bm25` or `pyyaml` aren't installed

---

## Quick start

```bash
# Clone
git clone https://github.com/m0han22/AgentForge.git

# Install at user-level (available across all your projects)
cp -r AgentForge/.claude/skills/* ~/.claude/skills/

# Or project-level (this project only)
cp -r AgentForge/.claude/skills/* /path/to/your/project/.claude/skills/

# Install search dependencies (optional but recommended)
pip install rank-bm25 pyyaml
```

Then in Claude Code, just describe what you're building:

> "Help me design an agent that reviews pull requests."

The skill auto-activates on agentic / RAG keywords, asks for load / latency / cost if missing, then delivers a prescriptive recommendation.

---

## Direct CLI use

You can also drive the search engine yourself:

```bash
# Full multi-domain recommendation
python3 .claude/skills/agent-forge/scripts/search.py \
  "RAG 50k engineering wiki Claude" --recommend -p "WikiBot"

# Drill into one domain
python3 .claude/skills/agent-forge/scripts/search.py \
  "hybrid search rerank" --domain retrieval

# Framework-specific guidance
python3 .claude/skills/agent-forge/scripts/search.py \
  "tool use mcp" --framework claude-agent-sdk

# Persist for cross-session reuse
python3 .claude/skills/agent-forge/scripts/search.py \
  "agentic coding assistant" --recommend --persist -p "CodeBot"
```

---

## Design principles

1. **One prescriptive answer.** Never "here are 5 options" — pick one path and justify it.
2. **Load / latency / cost first.** Every workflow asks for these three constraints before recommending. They drive most downstream decisions.
3. **Markdown knowledge, not CSV.** Each pattern is a markdown file with YAML frontmatter — supports rich code, tradeoffs, and links in a way CSVs can't.
4. **No decision-rules engine.** Claude reads the matched pattern files and reasons directly. Simpler and more flexible than IF-THEN rules.
5. **Knowledge in files, not prompts.** SKILL.md routes; `knowledge/` holds the IP. Adding new patterns doesn't require touching the skill.
6. **Dual audience.** Patterns open with a TL;DR for experts who scan, then expand into how-it-works for beginners.

---

## Adding a pattern

Knowledge is the moat. Adding a new pattern is one markdown file — no registration step, the search engine picks it up automatically:

```bash
cat > .claude/skills/agent-forge/knowledge/retrieval/colbert-late-interaction.md <<'EOF'
---
name: ColBERT Late Interaction
category: retrieval
difficulty: advanced
when_to_use: token-level matching on technical text with long queries
frameworks: [llamaindex, langchain]
related: [hybrid-search, reranking]
anti_patterns: [colbert-on-short-queries]
tags: [retrieval, colbert, late-interaction]
---

# ColBERT Late Interaction

**TL;DR:** ...

## When to use
- ...

## Code — LlamaIndex
```python
...
```

## Tradeoffs
...

## Anti-patterns
...
EOF
```

---

## File layout

```
AgentForge/
├── LICENSE
├── README.md
└── .claude/
    └── skills/
        ├── agent-forge/                       # HUB SKILL
        │   ├── SKILL.md                       # router + embedded Quick Reference
        │   ├── knowledge/                     # source of truth
        │   │   ├── safety/                    # prompt injection, validation, audit
        │   │   ├── tools/                     # schemas, MCP, error handling
        │   │   ├── loop/                      # budgets, infinite-loop guards
        │   │   ├── retrieval/                 # RAG patterns
        │   │   ├── evals/                     # Ragas, golden sets, judge
        │   │   ├── cost/                      # caching, routing
        │   │   ├── memory/                    # summarization, episodic
        │   │   ├── architecture/              # ReAct, plan-execute, multi-agent…
        │   │   ├── reasoning/                 # CoT, reflection, ToT (WIP)
        │   │   ├── prompt/                    # system prompt, tool descriptions
        │   │   ├── deployment/                # vector DBs, serving, observability
        │   │   ├── frameworks/                # one profile per framework
        │   │   └── anti-patterns/             # cross-cutting don'ts
        │   └── scripts/
        │       └── search.py                  # BM25 ranking + CLI
        ├── agent-architectures/SKILL.md
        ├── agent-rag/SKILL.md
        ├── agent-tools/SKILL.md
        ├── agent-memory/SKILL.md
        ├── agent-evals/SKILL.md
        └── agent-deployment/SKILL.md
```

---

## Roadmap

- Fill out `reasoning/` (CoT, reflection, ToT, self-critique) and grow `retrieval/`, `evals/`, `deployment/` past 1 pattern each
- Scaffold directory — runnable starter projects per framework
- `npx agent-forge install <platform>` CLI (Cursor, Windsurf, Copilot templates)
- Live dogfooding pass — verify auto-activation on real prompts; tune triggers
- Contributing guide for adding patterns

---

## Contributing

Patterns and improvements welcome. The contribution flow is intentionally lightweight:

1. Fork the repo
2. Add a new pattern under `.claude/skills/agent-forge/knowledge/<domain>/` following the existing format (YAML frontmatter + TL;DR + when-to-use + code + tradeoffs + anti-patterns)
3. Open a PR

For substantive changes to the workflow or hub SKILL.md, open an issue first to align on approach.

---

## Inspiration

Built after studying [UI/UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) — same skill architecture (hub + focused skills + knowledge directory + Python search), different domain. Architecture patterns informed by [LangChain's Deep Agents](https://github.com/langchain-ai/deepagents), [FareedKhan-dev/all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures), and the production lessons from Claude Code itself.

---

## License

[MIT](LICENSE) © 2026 Sai Mohan Kesapragada
