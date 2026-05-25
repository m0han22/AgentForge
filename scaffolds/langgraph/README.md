# LangGraph — Stateful Agent Starter

Stateful agent graph with checkpointing. Demonstrates the right pattern when your agent has more than 2-3 steps and you want persistence / resumability.

## What it does

User asks a question → planner produces a JSON plan → executor runs each step → reasoner synthesizes a final answer. State is checkpointed; rerunning with the same thread_id resumes from where it left off.

## Run

```bash
pip install -r requirements.txt
cp .env.example .env  # add ANTHROPIC_API_KEY
python main.py "Compare the population of Tokyo and Delhi."
```

## What's wired up

- **StateGraph** with explicit nodes: `plan`, `execute`, `reason`
- **MemorySaver** checkpointer (swap for `SqliteSaver` or `PostgresSaver` in prod)
- **Typed State** with `Annotated` + reducer for accumulating tool results
- **Budget enforcement** at the graph level (max 10 iterations)

## Customize

- Add more tools to the `TOOLS` dict
- Swap `MemorySaver` for persistent storage
- Add a `replan` node for failure recovery (see `knowledge/architecture/plan-execute.md`)
- Swap `ChatAnthropic` for any LangChain-compatible LLM

## Related AgentForge patterns

- `knowledge/architecture/plan-execute.md`
- `knowledge/frameworks/langgraph.md`
- `knowledge/loop/max-iterations-budget.md`
