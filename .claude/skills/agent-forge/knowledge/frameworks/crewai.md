---
name: CrewAI
category: frameworks
when_to_use: multi-agent role-play orchestration with clear agent roles and sequential or hierarchical task flow
language: [python]
maturity: stable
tags: [framework, crewai, multi-agent, role-play]
---

# CrewAI

**TL;DR:** Opinionated multi-agent framework where you define agents with roles, goals, and tasks, then assemble them into "crews" that execute sequentially or hierarchically. Best when your problem genuinely fits the "team of specialists" mental model.

## Pick this when

- Your problem decomposes naturally into specialist roles (researcher, writer, editor)
- Sequential or hierarchical task flow fits your workflow
- You want opinionated multi-agent primitives (don't want to design them yourself)
- Demo / showcase value matters (the role metaphor is intuitive to stakeholders)

## Don't pick this when

- Single-agent task — CrewAI's overhead isn't justified
- You want stateful graphs / cycles — use LangGraph
- You want minimal abstraction — use Claude Agent SDK or OpenAI Agents SDK
- You're cost-sensitive — multi-agent multiplies LLM calls; budget accordingly

## Strengths

- **Intuitive multi-agent metaphor** — agents have roles, goals, backstories
- **Sequential / hierarchical process** built in
- **Tools and task delegation** primitives
- **Strong community + many examples** — good for learning multi-agent patterns

## Weaknesses

- **Token cost** — multi-agent always costs more than single-agent; verify the eval improvement justifies it
- **Less debuggable** than explicit graphs — agent-to-agent handoff state is implicit
- **Role-play overhead** in prompts can hurt task accuracy vs leaner approaches
- **Justify the choice with eval** — many teams adopt CrewAI for the metaphor, not the measured improvement

## Key APIs

```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(
    role="Research analyst",
    goal="Find relevant facts about the user's question from the docs",
    backstory="You're meticulous and skeptical. You only report what you can cite.",
    tools=[search_docs_tool],
    verbose=True,
)

writer = Agent(
    role="Technical writer",
    goal="Turn research findings into a clear, accurate answer with citations",
    backstory="You value clarity. You never invent facts beyond the research.",
    verbose=True,
)

research_task = Task(
    description="Research: {question}",
    agent=researcher,
    expected_output="Bulleted list of factual claims with citations",
)

write_task = Task(
    description="Write an answer using the research output",
    agent=writer,
    expected_output="Clear answer with inline citations",
    context=[research_task],
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,
)

result = crew.kickoff(inputs={"question": "How do I configure retries?"})
```

## Patterns that pair well

- **Sequential pipelines** (research → write → edit)
- **Hierarchical delegation** (manager → workers)
- **Tasks with explicit dependencies** via `context`

## Patterns that don't fit well

- **Single-agent ReAct** — use Claude Agent SDK
- **Stateful long-running flows with checkpointing** — use LangGraph
- **Latency-critical paths** — multi-agent inflates total LLM time

## Migration notes

- From single-agent: only migrate after measuring that multi-agent improves eval
- From LangGraph: only if you find the graph DSL heavier than role-based decomposition
- General rule: justify multi-agent with a measured quality lift; otherwise stay single-agent
