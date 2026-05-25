---
name: Sliding Window + Recursive Summarization
category: memory
difficulty: intermediate
when_to_use: conversational agents whose history grows beyond the context window
frameworks: [langgraph, langchain, claude-agent-sdk, openai-agents-sdk]
related: [episodic-memory-store, context-budget-allocation, summarization-fidelity-eval]
anti_patterns: [dump-full-history, summarize-without-fidelity-check]
tags: [memory, summarization, conversation, context-window]
---

# Sliding Window + Recursive Summarization

**TL;DR:** Keep the last N turns verbatim (sliding window). Summarize older history in tiers (recent → mid summary → ancient meta-summary). Re-summarize when each tier exceeds budget. Validate summaries preserve key facts.

## When to use

- Chatbots, copilots, voice agents — any agent with multi-turn conversation
- Long-running coding agents that exceed context budget
- Any case where naively concatenating history blows the context window

## When NOT to use

- Single-turn agents (no history)
- Agents where exact history fidelity matters (legal, medical transcripts) — use full retrieval over history instead

## How it works

Three tiers, each with a token budget:

1. **Recent (verbatim):** last N turns kept exactly. Typical N = 5–10 turns.
2. **Mid (summary):** turns N+1 to N+M summarized into ~500 tokens. When mid exceeds budget, condense + push oldest to ancient.
3. **Ancient (meta-summary):** highly compressed running summary, ~200 tokens, updated periodically.

At each turn:
- Build context = system + ancient_summary + mid_summary + recent_turns + new_user_message
- If `len(recent) > N`: pop oldest, append to mid; if `len(mid) > budget`: re-summarize and bump to ancient

Pair with episodic memory for named-fact retrieval (e.g., "the user said their company is AcmeCorp 50 turns ago" should be retrievable, not lost in compression).

## Code — LangGraph

```python
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

llm = ChatAnthropic(model="claude-opus-4-7")
RECENT_TURNS = 8
MID_TOKEN_BUDGET = 1500
SUMMARIZER = ChatAnthropic(model="claude-haiku-4-5-20251001")

def summarize(text: str, target_tokens: int) -> str:
    prompt = (
        f"Compress the following conversation to ~{target_tokens} tokens. "
        f"Preserve: named entities, decisions made, open questions, user preferences. "
        f"Drop: pleasantries, repeated context.\n\n{text}"
    )
    return SUMMARIZER.invoke([HumanMessage(content=prompt)]).content

def trim_history(state: dict) -> dict:
    recent = state.get("recent", [])
    mid_summary = state.get("mid_summary", "")
    ancient = state.get("ancient_summary", "")

    if len(recent) > RECENT_TURNS:
        # Pop oldest turn, fold into mid
        oldest = recent.pop(0)
        mid_text = mid_summary + f"\n[turn] {oldest.type}: {oldest.content}"
        if len(mid_text.split()) > MID_TOKEN_BUDGET:
            # Mid is full — fold mid into ancient
            ancient = summarize(ancient + "\n\n" + mid_text, target_tokens=200)
            mid_summary = ""
        else:
            mid_summary = mid_text

    return {**state, "recent": recent, "mid_summary": mid_summary, "ancient_summary": ancient}

def build_messages(state, new_user_msg):
    return [
        SystemMessage(content="You are an assistant. Memory context:"),
        SystemMessage(content=f"[Ancient context]\n{state['ancient_summary']}"),
        SystemMessage(content=f"[Recent context]\n{state['mid_summary']}"),
        *state["recent"],
        HumanMessage(content=new_user_msg),
    ]
```

## Tradeoffs

- **Summarization adds a cheap-model call per N turns.** Use Haiku/small model to keep cost negligible.
- **Information loss is real.** Critical facts get summarized away. Pair with episodic memory store for facts you can't afford to lose.
- **Latency:** summarization is async-friendly — do it after responding, not before.

## Anti-patterns

- Dumping full history every turn — works for 20 turns, breaks at 200 with huge cost spike
- Summarizing without fidelity eval — silent quality degradation over long conversations
- Single-tier truncation (drop oldest N) — loses context cliff-style; user notices
- Synchronous summarization on the hot path — adds latency every turn instead of just compaction turns
- Same model for summarization and answering — wastes money; summarization is a simpler task

## Related

- `episodic-memory-store` — vector store for named-fact recall
- `context-budget-allocation` — explicit token budgets per context slot
- `summarization-fidelity-eval` — measure key-fact preservation
- `memory-isolation-per-user` — per-user namespacing for stored summaries
