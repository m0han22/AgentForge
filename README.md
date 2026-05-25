# AgentForge

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Made for Claude Code](https://img.shields.io/badge/Made%20for-Claude%20Code-orange)](https://claude.com/claude-code)
[![Skills](https://img.shields.io/badge/Skills-7-blue)](.claude/skills)
[![Patterns](https://img.shields.io/badge/Patterns-30%2B-green)](.claude/skills/agent-forge/knowledge)
[![Scaffolds](https://img.shields.io/badge/Scaffolds-6-purple)](scaffolds)
[![CLI](https://img.shields.io/badge/CLI-npx%20agent--forge-black)](cli.js)

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

**Scripts** at `.claude/skills/agent-forge/scripts/`:
- `search.py` — BM25 ranking over knowledge/ with `--recommend`, `--domain`, `--framework`, `--persist` modes
- `recommend.py` — wraps search.py with framework inference and scaffold pointers; emits a complete recommendation
- `eval_harness.py` — generates `golden_set.csv` + Ragas eval script + CI gate for RAG / agent / tools tasks
- Search falls back gracefully if `rank_bm25` or `pyyaml` aren't installed

**Runnable scaffolds** at `scaffolds/` — minimal but real starter projects:
- `claude-agent-sdk/` — ReAct agent with budgets + prompt caching
- `langgraph/` — Stateful plan/execute/reason graph with checkpointing
- `llamaindex/` — RAG: hierarchical chunking + hybrid + Cohere rerank, with citations
- `openai-agents/` — Triage agent with typed handoff to specialist
- `pydantic-ai/` — Type-safe agent with Pydantic-structured output + DI
- `crewai/` — Sequential researcher + writer crew

**CLI installer** at `cli.js` — `npx agent-forge install <platform>` for Claude Code, Cursor, Windsurf, or GitHub Copilot.

---

## Quick start

### Install via CLI (recommended)

```bash
# In your project directory:
npx agent-forge install claude-code            # → .claude/skills/

# Or for Cursor / Windsurf / Copilot:
npx agent-forge install cursor                 # → .cursor/rules/agent-forge.mdc
npx agent-forge install windsurf               # → .windsurf/rules/agent-forge.md
npx agent-forge install copilot                # → .github/copilot-instructions.md

# Install at user-level (available across all projects):
npx agent-forge install claude-code --dir ~
```

### Or clone + copy

```bash
git clone https://github.com/m0han22/AgentForge.git
cp -r AgentForge/.claude/skills/* ~/.claude/skills/
pip install rank-bm25 pyyaml  # optional; for the BM25 search engine
```

Then in Claude Code (or your editor), just describe what you're building:

> "Help me design an agent that reviews pull requests."

The skill auto-activates on agentic / RAG keywords, asks for load / latency / cost if missing, then delivers a prescriptive recommendation pointing to a runnable scaffold.

---

## Direct CLI use (Python scripts)

You can drive the knowledge tools yourself:

```bash
SCRIPTS=.claude/skills/agent-forge/scripts

# Synthesized recommendation (search + framework + scaffold pointer)
python3 $SCRIPTS/recommend.py "RAG over 50k engineering wiki Claude" --framework llamaindex

# Raw BM25 search across all domains
python3 $SCRIPTS/search.py "hybrid search rerank" --recommend

# Drill into one domain
python3 $SCRIPTS/search.py "infinite loop budget" --domain loop

# Framework-specific guidance
python3 $SCRIPTS/search.py "tool use mcp" --framework claude-agent-sdk

# Generate an eval harness for your task (RAG / agent / tools)
python3 $SCRIPTS/eval_harness.py --task rag        # → ./eval/{golden_set.csv, eval.py, ci_gate.sh}
python3 $SCRIPTS/eval_harness.py --task agent
python3 $SCRIPTS/eval_harness.py --task tools

# Persist a recommendation for cross-session reuse
python3 $SCRIPTS/search.py "agentic coding assistant" --recommend --persist -p "CodeBot"
```

### Try a scaffold

```bash
cd scaffolds/claude-agent-sdk
pip install -r requirements.txt
cp .env.example .env  # add ANTHROPIC_API_KEY
python main.py "What is the capital of France?"
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
├── package.json                         # npm metadata for `npx agent-forge`
├── cli.js                               # CLI installer (claude-code, cursor, windsurf, copilot)
├── .gitignore
├── .claude/
│   └── skills/
│       ├── agent-forge/                 # HUB SKILL
│       │   ├── SKILL.md                 # router + embedded Quick Reference
│       │   ├── knowledge/               # 10 domains + frameworks + anti-patterns
│       │   │   ├── safety/
│       │   │   ├── tools/
│       │   │   ├── loop/
│       │   │   ├── retrieval/
│       │   │   ├── evals/
│       │   │   ├── cost/
│       │   │   ├── memory/
│       │   │   ├── architecture/        # 10 pattern docs
│       │   │   ├── reasoning/           # WIP
│       │   │   ├── prompt/
│       │   │   ├── deployment/
│       │   │   ├── frameworks/          # 8 profiles
│       │   │   └── anti-patterns/
│       │   └── scripts/
│       │       ├── search.py            # BM25 ranking + CLI
│       │       ├── recommend.py         # search + framework + scaffold synthesis
│       │       └── eval_harness.py      # generate golden_set + eval.py + CI gate
│       ├── agent-architectures/SKILL.md
│       ├── agent-rag/SKILL.md
│       ├── agent-tools/SKILL.md
│       ├── agent-memory/SKILL.md
│       ├── agent-evals/SKILL.md
│       └── agent-deployment/SKILL.md
├── scaffolds/                           # 6 runnable starter projects
│   ├── claude-agent-sdk/
│   ├── langgraph/
│   ├── llamaindex/
│   ├── openai-agents/
│   ├── pydantic-ai/
│   └── crewai/
└── templates/                           # CLI installer source templates
    ├── claude-code/
    ├── cursor/
    ├── windsurf/
    └── copilot/
```

---

## Roadmap

- Fill out `reasoning/` (CoT, ToT, self-critique) and grow `retrieval/`, `evals/`, `deployment/` past 1 pattern each
- Publish to npm (`npm publish` so `npx agent-forge` works without the GitHub clone)
- Live dogfooding pass — verify auto-activation on real prompts; tune triggers
- Contributing guide for adding patterns
- Add a `scaffolds/deep-agents/` starter once Deep Agents stabilizes

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
