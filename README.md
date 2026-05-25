# AgentForge

> Opinionated Claude Code skill suite for building production AI agents and RAG systems.

AgentForge is a multi-skill knowledge base + decision engine for the agentic AI domain. Inspired by [UI/UX Pro Max](https://www.uupm.cc), it gives you one prescriptive recommendation — pattern + framework + code + anti-patterns + eval — instead of the generic "here are 5 options" you get from a vanilla LLM.

## What's in the box

**One hub skill + six focused skills**, all under `.claude/skills/`:

| Skill | Owns |
|---|---|
| **agent-forge** (hub) | The knowledge base + search engine + cross-cutting workflow. Activates on broad agentic/RAG queries. |
| **agent-architectures** | ReAct, plan-execute, orchestrator-worker, multi-agent, reflection, ToT |
| **agent-rag** | Chunking, hybrid retrieval, reranking, query rewriting, citation grounding |
| **agent-tools** | Tool schemas, MCP servers, error handling, idempotency, parallel calls |
| **agent-memory** | Sliding window, summarization tiers, episodic memory, per-user isolation |
| **agent-evals** | Golden sets, Ragas, LLM-as-judge, regression gates, traces, observability |
| **agent-deployment** | Vector DB choice, async serving, caching, cost/latency optimization, canary |

**Knowledge base** (`/.claude/skills/agent-forge/knowledge/`):
- 10 priority domains, growing catalog of pattern markdown files
- 7 framework profiles (Claude Agent SDK, LangGraph, LangChain, LlamaIndex, OpenAI Agents SDK, Pydantic AI, CrewAI)
- Cross-cutting anti-patterns

**Search engine** (`/.claude/skills/agent-forge/scripts/search.py`):
- BM25 ranking over markdown frontmatter + body
- Three modes: `--recommend` (full multi-domain), `--domain <name>`, `--framework <name>`
- Optional `--persist` to save recommendations to `agent-system/MASTER.md` for cross-session reuse

## How to use

### Install (plain skill folder — recommended for v0)

Copy the skills into your project's `.claude/skills/` or your user-level `~/.claude/skills/`:

```bash
# Project-level install
cp -r AgentForge/.claude/skills/* /path/to/your/project/.claude/skills/

# Or user-level install (available across all projects)
cp -r AgentForge/.claude/skills/* ~/.claude/skills/
```

Install Python dependencies (search engine):
```bash
pip install rank-bm25 pyyaml
```
The search script falls back to a simpler TF-IDF-ish ranking if `rank_bm25` is missing, and a minimal frontmatter parser if `pyyaml` is missing. Both are optional but recommended.

### Use it

The skills auto-activate when you mention agentic/RAG topics in Claude Code. Try:

```
Build me a RAG over 50k engineering wiki pages. Citations required, low latency, Claude.
```

Claude will:
1. Recognize agentic/RAG keywords → activate `agent-forge` (and possibly `agent-rag`)
2. Run `search.py "...--recommend"` against the knowledge base
3. Read the top pattern files
4. Synthesize a prescriptive response: **recommendation → why → code → anti-patterns → eval → deeper reading**

### Direct CLI use

You can also invoke the search engine yourself:

```bash
# Full recommendation across all domains
python3 .claude/skills/agent-forge/scripts/search.py "RAG 50k engineering wiki Claude" --recommend -p "WikiBot"

# Drill into one domain
python3 .claude/skills/agent-forge/scripts/search.py "hybrid search rerank" --domain retrieval

# Framework-specific guidance
python3 .claude/skills/agent-forge/scripts/search.py "tool use mcp" --framework claude-agent-sdk

# Persist for cross-session reuse
python3 .claude/skills/agent-forge/scripts/search.py "agentic coding assistant" --recommend --persist -p "CodeBot"
```

## Adding new patterns

Knowledge is the moat. Adding a pattern is a single markdown file:

```bash
# Add a new retrieval pattern
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
EOF
```

Then the search engine picks it up automatically — no registration step.

## File layout

```
AgentForge/
├── README.md                                          # this file
└── .claude/
    └── skills/
        ├── agent-forge/                               # HUB SKILL
        │   ├── SKILL.md                               # full router + embedded quick reference
        │   ├── knowledge/                             # source of truth
        │   │   ├── safety/                            # prompt injection, validation, audit
        │   │   ├── tools/                             # schemas, MCP, error handling
        │   │   ├── loop/                              # budgets, infinite-loop guards
        │   │   ├── retrieval/                         # RAG patterns
        │   │   ├── evals/                             # Ragas, golden sets
        │   │   ├── cost/                              # caching, routing
        │   │   ├── memory/                            # summarization, episodic
        │   │   ├── architecture/                      # ReAct, plan-execute, multi-agent
        │   │   ├── reasoning/                         # CoT, reflection, ToT
        │   │   ├── prompt/                            # system prompt, tool descriptions
        │   │   ├── deployment/                        # vector DBs, serving, observability
        │   │   ├── frameworks/                        # one profile per framework
        │   │   └── anti-patterns/                     # cross-cutting don'ts
        │   └── scripts/
        │       └── search.py                          # BM25 ranking + CLI
        ├── agent-architectures/SKILL.md               # focused: pick + implement architecture
        ├── agent-rag/SKILL.md                         # focused: RAG pipeline design
        ├── agent-tools/SKILL.md                       # focused: tool / MCP design
        ├── agent-memory/SKILL.md                      # focused: memory architecture
        ├── agent-evals/SKILL.md                       # focused: eval & observability
        └── agent-deployment/SKILL.md                  # focused: production deployment
```

## Design principles

1. **One prescriptive answer.** Never "here are 5 options" — pick one path and justify it.
2. **CSVs → markdown.** UUPM uses CSVs because their data is tabular; agentic patterns need code + tradeoffs, so we use markdown with frontmatter.
3. **No decision-rules engine.** Claude reads the matched pattern files and reasons directly. Simpler, more flexible.
4. **Knowledge in files, not in prompts.** The SKILL.md is the router; `knowledge/` is the IP. Adding new patterns doesn't require touching the skill.
5. **Dual audience.** Patterns open with a TL;DR for experts who scan, then expand into how-it-works for beginners.

## Inspiration

Built after studying [UI/UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) — same skill architecture (hub + focused skills + knowledge directory + Python search), different domain (agentic AI vs UI/UX).

## Status

V0. The skeleton and seed patterns are in place. The knowledge base is the moat — it grows by accretion. Add a new pattern every time you discover one in production.

## License

TBD.
