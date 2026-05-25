---
name: Prompt Caching (Anthropic / OpenAI)
category: cost
difficulty: beginner
when_to_use: any LLM call with a stable prompt prefix (system prompt, tool descriptions, retrieved context, long instructions)
frameworks: [claude-agent-sdk, langgraph, langchain, llamaindex, openai-agents-sdk]
related: [cache-retrievals, truncate-context-aggressively, model-routing]
anti_patterns: [no-cache-stable-prefix, cache-key-instability]
tags: [cost, caching, latency, prompt-engineering]
---

# Prompt Caching (Anthropic / OpenAI)

**TL;DR:** Mark stable prompt prefixes (system prompt, tool definitions, retrieved context, few-shot examples) as cacheable. Cuts input-token cost by up to 90% and reduces first-token latency. Cache TTL is 5 minutes on Anthropic (with refresh-on-hit).

## When to use

- Any production agent with a stable system prompt
- RAG where the retrieved context for popular queries repeats
- Long few-shot prompts
- Tool-calling agents (tool definitions are large and stable)

## When NOT to use

- Single-shot, never-repeating prompts (no cache benefit)
- Prompts under ~1024 tokens (Anthropic minimum cache size)

## How it works

The provider hashes the prompt prefix at one or more cache boundaries. On a cache hit, the prefix is read from cache at ~10% of normal token cost and dramatically lower latency. Cache misses cost slightly MORE than normal (the write).

Strategy:

1. **Put stable content first.** System prompt → tool definitions → retrieved context → conversation history → user message.
2. **Mark explicit cache breakpoints** on the prefix boundary. Anthropic supports up to 4 breakpoints.
3. **Pin model + prompt version** — any change invalidates the cache.
4. **Measure hit rate.** If <50%, your prompts aren't actually stable. Audit what's changing per request.

## Code — Claude Agent SDK

```python
from anthropic import Anthropic

client = Anthropic()

LARGE_SYSTEM_PROMPT = """You are a support agent for AcmeCorp...
[~3000 tokens of policy, tone, tool guidance, examples]
"""

def answer(user_question: str, retrieved_docs: list[str]) -> str:
    return client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": LARGE_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},  # cache breakpoint
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "\n\n".join(f"<doc>{d}</doc>" for d in retrieved_docs),
                        "cache_control": {"type": "ephemeral"},  # cache retrieved context too
                    },
                    {
                        "type": "text",
                        "text": f"<question>{user_question}</question>",
                        # No cache_control on the question — it changes per request
                    },
                ],
            }
        ],
    )
```

After the first call, repeat calls with the same system + retrieved docs read those tokens from cache at ~10% of input cost. Check `response.usage.cache_read_input_tokens` to confirm.

## Tradeoffs

- **First call is ~25% more expensive** (cache write). Break-even after 2 hits.
- **5-minute TTL on Anthropic** — bursty traffic benefits; sparse traffic doesn't (cache expires between requests).
- **Cache invalidation gotchas:** changing model version, modifying a single character in the cached prefix, switching prompt structure all invalidate. Pin tightly.

## Anti-patterns

- Putting user input or timestamps INSIDE the cached prefix — cache key is unstable, hit rate near zero
- No measurement — running prod for months and only discovering 5% hit rate during a cost audit
- Caching tiny prompts (<1024 tokens) — below the minimum, the cache_control is ignored, you pay full price
- Forgetting to invalidate cache when prompt version bumps — model uses stale instructions
- Cache breakpoint AFTER the variable part — only the prefix BEFORE the breakpoint is cached

## Related

- `cache-retrievals` — cache retrieval results separately from prompt cache
- `cache-final-answers` — for popular queries, skip LLM entirely
- `truncate-context-aggressively` — smaller cached prefix = faster cache reads
- `model-routing` — combine with cheaper models for further cost reduction
