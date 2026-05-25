---
name: Sub-Agent with Isolated Context
category: architecture
difficulty: advanced
when_to_use: long-horizon agents where intermediate work (research, search, parsing) would bloat the parent's context window
frameworks: [deep-agents, langgraph, claude-agent-sdk, claude-code]
related: [multi-agent-handoff, agent-as-tool, filesystem-as-memory]
anti_patterns: [sub-agent-sharing-parent-context, sub-agent-without-budget]
tags: [architecture, sub-agent, context-isolation, delegation, long-horizon]
---

# Sub-Agent with Isolated Context

**TL;DR:** Spawn a child agent with a fresh, empty context window to do focused work (deep research, long search, big-file parsing). Only the final result returns to the parent — the child's intermediate thinking never pollutes parent context. The pattern that makes long-horizon agents tractable. Used by Claude Code's Task/Agent tool and LangChain's Deep Agents.

## When to use

- Long-running agents that would otherwise exhaust their context window
- "Deep" research / exploration where intermediate thinking is voluminous but the answer is compact
- Tasks the parent agent could do but doesn't need to *witness* (parsing a 10k-line log, summarizing a 200-page PDF, exploring a code repo)
- When you want to parallelize independent investigations across multiple sub-agents
- When the parent should remain focused on orchestration, not detail work

## When NOT to use

- Short, single-step tool calls — direct call is simpler and cheaper
- When the parent needs to see intermediate state (use `multi-agent-handoff` with explicit state instead)
- Tight latency budgets — spawning a sub-agent means waiting for its full loop
- Tasks where sub-agent outputs need to share state with each other (use `blackboard` or `orchestrator-worker`)

## How it differs from multi-agent-handoff

- **Handoff:** agents pass state explicitly; receiver continues the conversation
- **Sub-agent:** child gets a focused prompt + scope; only a structured result returns. Parent's chat history is unaffected.

The isolation is the whole point. The parent says "find me a fact"; the child reads 50 documents and reasons through them; the parent gets one sentence back. The parent's context stays clean.

## How it works

The spawn pattern:

1. Parent agent decides a task is worth delegating (heuristic or explicit decision).
2. Parent constructs a `task_prompt` — self-contained, with all context the child needs.
3. Parent invokes the sub-agent with: prompt, tool subset, budget (iterations / tokens / cost / wall-clock), expected output schema.
4. Child runs its own loop in an isolated context window. Has access to its own tools (often a narrower set).
5. Child returns a structured result.
6. Parent appends only the result to its own context — not the child's trace.

Critical guards:
- **Per-sub-agent budget** — independent from parent's budget; cap iterations + cost
- **Output schema** — child returns structured data, not freeform text
- **Tool subset** — child gets only the tools it needs (least privilege)
- **Failure as data** — child failure returns `{error, partial_result}` to parent, not an exception

## Code — Claude Agent SDK (sub-agent as a tool)

```python
from anthropic import Anthropic
from pydantic import BaseModel

client = Anthropic()

class ResearchResult(BaseModel):
    answer: str
    sources: list[str]
    confidence: float

def run_sub_agent(task: str, tools: list, max_iters: int = 10, max_tokens: int = 20_000) -> dict:
    """Run a child agent with isolated context. Returns structured result."""
    messages = [{"role": "user", "content": task}]
    tokens_used = 0

    for i in range(max_iters):
        if tokens_used >= max_tokens:
            return {"error": "token_budget_exceeded", "partial": messages[-1] if messages else None}

        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",  # cheap model for delegated work
            max_tokens=2048,
            system="You are a focused research agent. Return only the final structured answer.",
            tools=tools,
            messages=messages,
        )
        tokens_used += resp.usage.input_tokens + resp.usage.output_tokens

        if resp.stop_reason == "end_turn":
            return {"result": resp.content[0].text, "tokens": tokens_used, "iterations": i + 1}
        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            tool_results = execute_tools(resp.content, tools)
            messages.append({"role": "user", "content": tool_results})
            continue

    return {"error": "max_iterations", "iterations": max_iters}

# Expose as a tool to the parent agent
DELEGATE_RESEARCH_TOOL = {
    "name": "delegate_research",
    "description": (
        "Delegate a focused research task to a sub-agent with isolated context. "
        "Use for: deep dives, long-document analysis, multi-source synthesis. "
        "The sub-agent has search tools but no write access. "
        "Returns a structured ResearchResult."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "Self-contained task prompt for the sub-agent"},
            "max_iters": {"type": "integer", "default": 10, "maximum": 20},
        },
        "required": ["task"],
        "additionalProperties": False,
    },
}

def handle_delegate_research(args: dict) -> ResearchResult:
    return run_sub_agent(
        task=args["task"],
        tools=[SEARCH_TOOL, READ_DOC_TOOL],
        max_iters=args.get("max_iters", 10),
        max_tokens=20_000,
    )
```

The parent agent calls `delegate_research(task="Find the most recent change to our auth middleware and summarize why it changed.")`. The sub-agent reads 30 commits and 10 PR descriptions in its own context, returns one paragraph. Parent context stays compact.

## Tradeoffs

- **Context efficiency:** parent stays under context limit even on multi-hour tasks
- **Cost:** sub-agents are additional LLM calls — budget them per spawn
- **Latency:** parent waits for the whole child loop; not always parallelizable
- **Debuggability:** sub-agent traces must be logged separately and linkable to parent run id
- **Quality:** child sees only the prompt it gets; if parent's task framing is incomplete, child can't course-correct mid-loop
- **Use a cheaper model for the child** when the work is routine — Haiku/small model + many sub-agents often beats one Opus loop

## Anti-patterns

- Sub-agent reads parent's chat history — defeats isolation, why are you using this pattern
- No per-sub-agent budget — single child loop blows the parent's session budget
- Same-prompt sub-agent — adds latency without changing what's done; just call the tool
- Returning freeform text instead of structured data — parent has to parse loosely-structured strings
- Spawning sub-agents recursively without depth cap — exponential blowup

## Related

- `multi-agent-handoff` — when state must flow between agents
- `agent-as-tool` — the implementation primitive
- `filesystem-as-memory` — pairs well; sub-agent writes findings to a file, parent reads later
- `orchestrator-worker` — parallel sub-agent variant
- `max-iterations-budget` — required for each sub-agent
