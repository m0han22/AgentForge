# OpenAI Agents SDK — Triage + Specialist Starter

Two-agent system: a triage agent routes incoming questions to a docs specialist via handoff. Demonstrates the right way to do specialist routing with explicit, typed handoff state.

## What it does

User asks a question → triage agent classifies → if docs-answerable, hands off to docs specialist (which uses a search tool) → docs specialist answers with citations.

## Run

```bash
pip install -r requirements.txt
cp .env.example .env  # add OPENAI_API_KEY
python main.py "How do I configure retries in gRPC?"
```

## What's wired up

- **Two agents** — `triage_agent` (gpt-4o-mini) and `docs_agent` (gpt-4o)
- **Handoff** with typed Pydantic input (`DocsRequest`)
- **Tool** — `search_docs` stub
- **Input guardrail** — blocks off-topic requests (weather, sports, etc.)

## Customize

- Wire `search_docs_impl` to a real retriever (your LlamaIndex / pgvector / Pinecone setup)
- Add more specialists for billing, account, escalation
- Tune the triage agent's instructions for your routing rules
- Add output guardrails for sensitive content

## Related AgentForge patterns

- `knowledge/architecture/multi-agent-handoff.md`
- `knowledge/frameworks/openai-agents-sdk.md`
- `knowledge/safety/prompt-injection-defense.md`
