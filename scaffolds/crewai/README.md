# CrewAI — Researcher + Writer Crew Starter

Two-agent sequential crew: researcher gathers facts, writer produces the answer. Demonstrates when multi-agent role decomposition actually helps (sequential pipeline with distinct expertise).

## What it does

User question → researcher agent uses `search_docs` to find facts → writer agent consumes the research output and produces a polished, cited answer.

## Run

```bash
pip install -r requirements.txt
cp .env.example .env  # add ANTHROPIC_API_KEY
python main.py "How do I configure retries in gRPC?"
```

## What's wired up

- **Two agents** — `researcher` and `writer` with distinct roles, goals, backstories
- **Sequential process** — writer's task depends on researcher's output via `context`
- **Tool** — `search_docs` stub on the researcher
- **Verbose tracing** — see each agent's reasoning in stdout

## Customize

- Replace `search_docs_impl` with a real retriever
- Add an editor or critic agent (sequential or hierarchical)
- Tune the researcher's `backstory` for stricter sourcing requirements
- Switch to `Process.hierarchical` with a manager agent for delegation

## When NOT to use this pattern

Multi-agent multiplies LLM calls. Justify with eval improvement before adopting. See `knowledge/architecture/multi-agent-handoff.md` and `knowledge/frameworks/crewai.md`.

## Related AgentForge patterns

- `knowledge/frameworks/crewai.md`
- `knowledge/architecture/multi-agent-handoff.md`
