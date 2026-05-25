---
name: Claude Agent SDK
category: frameworks
when_to_use: building agents in the Anthropic ecosystem, especially tool use + MCP + computer use
language: [python, typescript]
maturity: stable
tags: [framework, anthropic, claude, agent-sdk, mcp]
---

# Claude Agent SDK

**TL;DR:** Anthropic's first-party SDK for building agents on Claude. Best fit when you want tight integration with Claude features (prompt caching, MCP, computer use, agentic coding) and minimal framework overhead. Python and TypeScript.

## Pick this when

- You're building on Claude (not multi-provider)
- You want first-class MCP support
- You want computer-use or agentic-coding patterns
- You prefer minimal abstraction — write your own loop, use SDK primitives
- You need prompt caching with explicit control

## Don't pick this when

- You need multi-provider abstraction out of the box (use LangChain / LiteLLM)
- You want a stateful graph framework with persistence (use LangGraph)
- You're RAG-first with no agent loop (use LlamaIndex)
- You need pre-built multi-agent orchestration (use CrewAI / Agents SDK)

## Strengths

- **Native Claude features:** prompt caching, extended thinking, computer use, large context (1M tokens on Opus 4.7)
- **MCP-first:** tools as MCP servers compose cleanly
- **Minimal magic:** you write the loop, you control the budget — easy to debug
- **TypeScript parity:** real cross-language support, not afterthought
- **Streaming, tool use, structured output** are all stable and well-documented

## Weaknesses

- **Single-provider:** no built-in OpenAI / Gemini routing
- **No built-in graph orchestration** — write your own state machine
- **No built-in eval harness** — pair with Ragas / LangSmith / Phoenix

## Key APIs

```python
from anthropic import Anthropic

client = Anthropic()

# Basic message
resp = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=1024,
    system="You are an assistant.",
    messages=[{"role": "user", "content": "Hello"}],
)

# Tool use
resp = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=4096,
    tools=[TOOL_DEFINITION],
    messages=messages,
)

# Streaming
with client.messages.stream(...) as stream:
    for text in stream.text_stream:
        print(text, end="")

# Prompt caching (cache_control breakpoints)
client.messages.create(
    model="claude-opus-4-7",
    system=[{"type": "text", "text": LONG_PROMPT, "cache_control": {"type": "ephemeral"}}],
    ...
)

# MCP client connection
from anthropic.mcp import MCPClient
mcp = MCPClient.connect("stdio:///path/to/mcp-server")
tools = mcp.list_tools()
```

## Patterns that pair well

- **ReAct loop:** write your own — ~30 lines, easy to budget
- **Prompt caching:** mark stable prefixes (system + tool defs + retrieved context)
- **MCP servers:** wrap external tools as MCP for reuse across agents
- **Output validation:** parse tool calls against schema before executing

## Patterns that don't fit well

- **Complex stateful graphs:** doable but painful — consider LangGraph if your state machine has >5 nodes
- **Pre-built multi-agent role play:** not built in — use CrewAI if you need it out of the box

## Migration notes

- From OpenAI SDK: message format is similar; tool format differs (input_schema vs parameters)
- From LangChain: drop the wrappers, call SDK directly — usually less code
- From LangGraph: keep LangGraph if state graph is doing real work; switch if you've just been using it for ReAct loops
