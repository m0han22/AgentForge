# AgentForge

[![MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE) [![Claude Code](https://img.shields.io/badge/Claude%20Code-skill-orange)](https://claude.com/claude-code) [![Skills](https://img.shields.io/badge/skills-7-blue)](.claude/skills) [![Patterns](https://img.shields.io/badge/patterns-30%2B-green)](.claude/skills/agent-forge/knowledge) [![Scaffolds](https://img.shields.io/badge/scaffolds-6-purple)](scaffolds)

**Opinionated Claude Code skill for building production AI agents and RAG systems.** Modeled after [UI/UX Pro Max](https://www.uupm.cc), but for the agentic AI domain.

You ask:

> "Build a RAG over 50k internal wiki pages. Citations required, low latency, Claude."

Vanilla Claude gives you five options. AgentForge first asks for **load, latency, cost**, then gives **one prescriptive path** with code, anti-patterns, and a starter eval — drawn from a curated knowledge base instead of generic LLM advice.

---

## Install

```bash
npx agent-forge install claude-code          # → ./.claude/skills/
npx agent-forge install claude-code --dir ~  # → ~/.claude/skills/ (user-level)
npx agent-forge install cursor               # → .cursor/rules/agent-forge.mdc
npx agent-forge install windsurf             # → .windsurf/rules/agent-forge.md
npx agent-forge install copilot              # → .github/copilot-instructions.md
```

Or clone and copy:
```bash
git clone https://github.com/m0han22/AgentForge.git
cp -r AgentForge/.claude/skills/* ~/.claude/skills/
pip install rank-bm25 pyyaml   # optional, for BM25 search
```

Then in your editor: *"Help me design an agent that reviews pull requests."* The skill auto-activates on agentic / RAG keywords.

---

## What's inside

| Layer | What |
|---|---|
| **7 skills** | 1 hub (`agent-forge`) + 6 focused (`agent-architectures`, `agent-rag`, `agent-tools`, `agent-memory`, `agent-evals`, `agent-deployment`) |
| **Knowledge base** | 10 domains (safety, tools, loop, retrieval, evals, cost, memory, architecture, prompt, deployment) with 200+ inline rules + 30+ pattern docs |
| **Framework profiles** | Claude Agent SDK · LangGraph · LangChain · LlamaIndex · OpenAI Agents SDK · Pydantic AI · CrewAI · Deep Agents |
| **Scaffolds** | 6 runnable starter projects, one per framework |
| **Scripts** | `search.py` (BM25) · `recommend.py` (synthesize) · `eval_harness.py` (generate golden set + Ragas) |
| **CLI** | `cli.js` — installs into Claude Code, Cursor, Windsurf, or Copilot |

---

## Use the scripts directly

```bash
SCRIPTS=.claude/skills/agent-forge/scripts

# Synthesized recommendation (search + framework + scaffold pointer)
python3 $SCRIPTS/recommend.py "RAG over 50k wiki pages" --framework llamaindex

# Drill into one domain
python3 $SCRIPTS/search.py "infinite loop budget" --domain loop

# Generate an eval harness for your task
python3 $SCRIPTS/eval_harness.py --task rag   # → ./eval/{golden_set.csv, eval.py, ci_gate.sh}
```

### Try a scaffold

```bash
cd scaffolds/claude-agent-sdk
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY
python main.py "What is the capital of France?"
```

---

## Design principles

1. **One prescriptive answer.** Never "here are 5 options".
2. **Load / latency / cost first.** Asked before recommending — they drive most downstream decisions.
3. **Markdown knowledge, not CSV.** Patterns are markdown files with YAML frontmatter (richer than tabular).
4. **No decision-rules engine.** Claude reads matched patterns and reasons directly.
5. **Knowledge in files, not prompts.** SKILL.md routes; `knowledge/` holds the IP.
6. **Dual audience.** TL;DR up top for experts, deeper explanation below for beginners.

---

## Adding a pattern

Drop a markdown file into `knowledge/<domain>/` with frontmatter (`name`, `category`, `when_to_use`, `frameworks`, `related`, `anti_patterns`, `tags`) and a body. The search engine picks it up automatically — no registration step.

```bash
cat > .claude/skills/agent-forge/knowledge/retrieval/colbert-late-interaction.md <<'EOF'
---
name: ColBERT Late Interaction
category: retrieval
when_to_use: token-level matching on long technical queries
frameworks: [llamaindex, langchain]
tags: [retrieval, colbert]
---
# ColBERT Late Interaction
**TL;DR:** ...
EOF
```

---

## File layout

```
AgentForge/
├── cli.js                            # CLI installer
├── package.json                      # npm metadata
├── .claude/skills/                   # 7 skills (hub + 6 focused)
│   └── agent-forge/
│       ├── SKILL.md                  # router + embedded Quick Reference
│       ├── knowledge/                # 10 domains + frameworks + anti-patterns
│       └── scripts/                  # search.py, recommend.py, eval_harness.py
├── scaffolds/                        # 6 runnable starter projects
└── templates/                        # CLI install bundles per platform
```

---

## Roadmap

- Publish to npm so `npx agent-forge` works without cloning
- Fill out `reasoning/` (CoT, ToT, self-critique) and grow other domains past 1 pattern each
- Live dogfooding pass — verify auto-activation on real prompts
- Add `scaffolds/deep-agents/` starter

---

## Inspiration

Built after studying [UI/UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (same skill architecture, different domain). Architecture patterns informed by [LangChain's Deep Agents](https://github.com/langchain-ai/deepagents), [FareedKhan-dev/all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures), and Claude Code itself.

PRs welcome — add a pattern, fix a typo, or open an issue for substantive changes.

---

[MIT](LICENSE) © 2026 Sai Mohan Kesapragada
