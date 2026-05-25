# Pydantic AI — Type-Safe Agent Starter

Typed agent with Pydantic structured output, dependency injection, and a single tool. Best for Python shops that value type safety.

## What it does

User asks a question → agent runs (with dependency-injected DB context) → tool is called as needed → agent returns a **typed `Answer`** with confidence and sources. The whole flow is `mypy`-clean.

## Run

```bash
pip install -r requirements.txt
cp .env.example .env  # add ANTHROPIC_API_KEY
python main.py "What is our refund policy?"
```

## What's wired up

- **Typed result** — `Answer` Pydantic model (text, sources, confidence 0–1)
- **Dependency injection** — `Deps(db, user_id)` available in tools via `RunContext`
- **One tool** — `search_docs` with typed input/output
- **System prompt** with explicit citation requirement
- **Multi-provider** — point `Agent("anthropic:claude-opus-4-7", ...)` at OpenAI / Gemini / Mistral / etc.

## Customize

- Replace `FakeDB` with a real DB / vector store
- Add more tools — `@agent.tool` decorator
- Use `Agent.run_stream(...)` for streaming responses
- Change `result_type=Answer` to your task-specific schema

## Related AgentForge patterns

- `knowledge/frameworks/pydantic-ai.md`
- `knowledge/prompt/system-prompt-structure.md`
- `knowledge/tools/tool-schema-design.md`
