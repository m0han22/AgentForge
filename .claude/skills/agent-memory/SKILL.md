---
name: agent-memory
description: "Add memory and context management to LLM agents: sliding-window history, recursive summarization tiers, episodic memory in vector store, long-term vs working memory separation, context budget allocation, entity extraction, memory conflict resolution, TTL/expiry, per-user namespacing, summarization fidelity eval. Frameworks: LangGraph (checkpointing), Claude Agent SDK, OpenAI Agents SDK. Returns one prescriptive memory architecture with code, anti-patterns, and a fidelity eval."
allowed-tools: Read, Bash, Glob, Grep
---

# agent-memory — Memory & Context

Opinionated picker for agent memory architecture. Owns conversation history management, episodic memory, summarization, context-window budgets.

Defers to the **agent-forge hub**. Source of truth: `agent-forge/knowledge/memory/`, `agent-forge/knowledge/retrieval/` (episodic memory is retrieval).

## When to activate

- "Add memory to my agent / chatbot"
- "Conversation history is growing"
- "Long-running agent / context window full"
- "Episodic memory", "long-term memory", "summarization buffer"
- "Per-user memory"
- "Remember user preferences"

## When NOT to activate

- Single-turn agents → no memory needed
- RAG over docs (not over conversation) → use `agent-rag`

## Workflow

1. **Parse** — single-session vs cross-session memory? What needs to persist? How long is a typical conversation?
2. **Search** — `--domain memory`
3. **Framework specifics** — LangGraph for checkpointing, otherwise SDK + DB
4. **Synthesize**

## Memory defaults (prescriptive path)

- **Working memory:** sliding window (last 5–10 turns verbatim) + recursive summarization for older
- **Long-term memory:** vector store keyed by `(user_id, namespace)`; write only on explicit signal
- **Context budget:** explicit allocation: system + ancient-summary + mid-summary + recent + retrieval + tool results
- **Order in context:** system → retrievals → history (most stable → least stable, for prompt caching)
- **Per-user isolation:** strict namespacing; never share memory across users
- **TTL:** stale memories decay (30–90 days typical)
- **Forget:** honor user "forget X" requests

## Hard rules

- Per-user memory isolation (no cross-user leakage)
- Summarization fidelity eval (measure key-fact preservation)
- Memory write requires explicit signal — don't auto-persist everything
- "Forget" requests honored

## Output template

```
## Recommendation
<one sentence — memory architecture + framework. Example: "Sliding window of 8 turns + Haiku-summarized mid-tier + Qdrant episodic store keyed by user_id, all on LangGraph with PostgresSaver.">

## Why this for your case
- <conversation length>
- <cross-session need>
- <fact-retention need>

## Code
<scaffold: state schema, history trimming, summarization, episodic write/read>

## Avoid
- <dump-full-history>
- <summarize-without-fidelity-check>
- <no-per-user-namespacing>

## How to know it's working
<fidelity eval: pick 20 long conversations, measure that named facts at turn 50 are still recoverable; cost-per-turn over conversation length>

## Deeper reading
- knowledge/memory/sliding-window-summarization.md
- knowledge/memory/episodic-memory-store.md
- knowledge/frameworks/langgraph.md
```

## Personality

- Default to sliding window + summarization for working memory.
- Separate working from long-term explicitly.
- Always isolate per user.

## Knowledge base contract

All patterns live under `agent-forge/knowledge/`. This skill does not maintain its own knowledge tree.
