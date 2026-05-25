"""
CrewAI — Sequential researcher + writer crew starter.
"""

import json
import os
import sys

from crewai import Agent, Crew, Process, Task
from crewai.tools import BaseTool


class SearchDocs(BaseTool):
    name: str = "search_docs"
    description: str = (
        "Search engineering docs. Use for technical questions. "
        "Returns a list of doc snippets with sources."
    )

    def _run(self, query: str) -> str:
        # Replace with a real retriever
        return (
            f"[stub] No retriever wired yet. Replace SearchDocs._run with a real implementation. "
            f"Query: {query}"
        )


search_tool = SearchDocs()

researcher = Agent(
    role="Research analyst",
    goal="Find accurate, well-sourced facts to answer the user's question",
    backstory=(
        "You are meticulous and skeptical. You only report facts that you can cite from search_docs. "
        "You never invent information."
    ),
    tools=[search_tool],
    verbose=True,
    allow_delegation=False,
)

writer = Agent(
    role="Technical writer",
    goal="Turn research findings into a clear, accurate answer with inline citations",
    backstory=(
        "You value clarity and precision. You never add facts beyond what the researcher provided."
    ),
    verbose=True,
    allow_delegation=False,
)


def build_crew(question: str) -> Crew:
    research_task = Task(
        description=f"Research the following question: {question}",
        expected_output="A bulleted list of factual claims, each with the source from search_docs.",
        agent=researcher,
    )
    write_task = Task(
        description="Write a clear answer based on the research findings.",
        expected_output="A concise, well-structured answer with inline citations.",
        agent=writer,
        context=[research_task],
    )
    return Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential,
        verbose=True,
    )


def run(question: str) -> dict:
    crew = build_crew(question)
    result = crew.kickoff(inputs={"question": question})
    return {"answer": str(result), "raw": getattr(result, "raw", None)}


if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY (CrewAI defaults to OpenAI)", file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) < 2:
        print('Usage: python main.py "your question"', file=sys.stderr)
        sys.exit(1)

    print(json.dumps(run(" ".join(sys.argv[1:])), indent=2))
