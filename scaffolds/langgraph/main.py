"""
LangGraph — Stateful agent starter with plan/execute/reason nodes and checkpointing.
"""

import json
import os
import sys
from operator import add
from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

MODEL = "claude-opus-4-7"
MAX_STEPS = 10

llm = ChatAnthropic(model=MODEL, max_tokens=2048)


class State(TypedDict):
    question: str
    plan: list[dict]
    step_idx: int
    results: Annotated[list, add]
    answer: str | None
    iterations: int


def lookup_fact_tool(name: str, args: dict) -> dict:
    """Stub tool. Replace with a real implementation."""
    if name == "lookup_fact":
        return {"fact": f"[stub] fact about '{args.get('topic')}': replace lookup_fact_tool with a real lookup."}
    return {"error": "unknown_tool"}


def plan_node(state: State) -> dict:
    prompt = (
        "Produce a JSON array of steps to answer the question. Each step: "
        '{"step": int, "tool": "lookup_fact", "args": {"topic": "..."}}. '
        "Use minimum number of steps. Max 5 steps.\n\n"
        f"Question: {state['question']}\n\nJSON only:"
    )
    resp = llm.invoke([HumanMessage(content=prompt)])
    try:
        plan = json.loads(resp.content.strip().strip("`"))
    except Exception:
        plan = [{"step": 1, "tool": "lookup_fact", "args": {"topic": state["question"]}}]
    return {"plan": plan, "step_idx": 0, "results": [], "iterations": 0}


def execute_node(state: State) -> dict:
    if state["step_idx"] >= len(state["plan"]):
        return {"iterations": state["iterations"] + 1}
    step = state["plan"][state["step_idx"]]
    result = lookup_fact_tool(step["tool"], step.get("args", {}))
    return {
        "results": [{"step": step, "result": result}],
        "step_idx": state["step_idx"] + 1,
        "iterations": state["iterations"] + 1,
    }


def reason_node(state: State) -> dict:
    prompt = (
        f"Question: {state['question']}\n\n"
        f"Facts gathered: {json.dumps(state['results'])}\n\n"
        "Write a clear, concise answer."
    )
    resp = llm.invoke([HumanMessage(content=prompt)])
    return {"answer": resp.content}


def should_continue(state: State) -> str:
    if state["iterations"] >= MAX_STEPS:
        return "reason"
    if state["step_idx"] >= len(state["plan"]):
        return "reason"
    return "execute"


def build_graph():
    g = StateGraph(State)
    g.add_node("plan", plan_node)
    g.add_node("execute", execute_node)
    g.add_node("reason", reason_node)
    g.set_entry_point("plan")
    g.add_edge("plan", "execute")
    g.add_conditional_edges("execute", should_continue, {"execute": "execute", "reason": "reason"})
    g.add_edge("reason", END)
    return g.compile(checkpointer=MemorySaver())


def run(question: str, thread_id: str = "default") -> dict:
    app = build_graph()
    config = {"configurable": {"thread_id": thread_id}}
    final = app.invoke({"question": question}, config=config)
    return {"answer": final["answer"], "steps_run": final["iterations"], "results": final["results"]}


if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY in .env or environment", file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) < 2:
        print('Usage: python main.py "your question"', file=sys.stderr)
        sys.exit(1)

    result = run(" ".join(sys.argv[1:]))
    print(json.dumps(result, indent=2))
