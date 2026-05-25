# Claude Agent SDK — ReAct Starter

Minimal but real ReAct agent on Claude with one tool, strict budget caps, and prompt caching on the system prompt.

## What it does

User asks a question → agent reasons → calls `web_search` tool if needed → reasons over results → answers. Loop is capped at 10 iterations, 50k tokens, and 60 seconds wall-clock.

## Run

```bash
pip install -r requirements.txt
cp .env.example .env  # then add your ANTHROPIC_API_KEY
python main.py "What is the capital of France?"
python main.py "Find the latest stable Python release and explain what's new."
```

## What's wired up

- **ReAct loop** with `max_iterations`, `max_tokens`, `wall_clock_timeout`
- **Prompt caching** on the system prompt (cache breakpoint)
- **One tool**: `web_search` (stub — wire it to Tavily/Brave/Serper)
- **Structured error handling** — tool failures returned as data, not exceptions
- **Iteration trace** printed to stderr for debugging

## Customize

- Replace `web_search` stub with a real provider in `web_search_impl`
- Add more tools to the `TOOLS` list and handlers to `TOOL_HANDLERS`
- Tune `MAX_ITERATIONS`, `MAX_TOKENS`, `MAX_WALL_SECONDS` for your budget

## Related AgentForge patterns

- `knowledge/architecture/react-agent.md`
- `knowledge/loop/max-iterations-budget.md`
- `knowledge/cost/prompt-caching.md`
- `knowledge/tools/tool-schema-design.md`
