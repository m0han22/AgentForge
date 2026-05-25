#!/usr/bin/env python3
"""
AgentForge recommendation synthesizer.

Wraps search.py with framework + scaffold awareness. Given a query and optionally
a chosen framework, emits a structured recommendation that:

1. Searches all 10 domains via search.py logic (BM25)
2. Picks (or accepts) a framework and reads its profile
3. Points to a runnable scaffold under scaffolds/ if one fits
4. Suggests an eval harness via eval_harness.py

Usage:
    recommend.py "RAG over 50k wiki pages with citations" --framework llamaindex
    recommend.py "build a coding agent" --task agent
    recommend.py "tool use mcp" --top-k 3
"""

import argparse
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCAFFOLDS_DIR = SKILL_DIR.parents[2] / "scaffolds"  # repo-root/scaffolds/

# Import search module from the same dir
sys.path.insert(0, str(Path(__file__).resolve().parent))
import search  # noqa: E402

FRAMEWORK_TO_SCAFFOLD = {
    "claude-agent-sdk": "claude-agent-sdk",
    "langgraph": "langgraph",
    "langchain": "langgraph",          # nearest scaffold; LangChain users typically migrate to LangGraph
    "llamaindex": "llamaindex",
    "openai-agents-sdk": "openai-agents",
    "pydantic-ai": "pydantic-ai",
    "crewai": "crewai",
}

# Map query keywords to scaffold hints when no framework is specified
KEYWORD_TO_FRAMEWORK = [
    (["rag", "retrieval", "embedding", "chunk", "rerank", "vector"], "llamaindex"),
    (["langgraph", "stateful", "checkpoint", "graph", "plan-execute"], "langgraph"),
    (["claude", "anthropic", "mcp", "computer use"], "claude-agent-sdk"),
    (["openai", "gpt-4", "handoff", "triage"], "openai-agents-sdk"),
    (["pydantic", "structured output", "typed"], "pydantic-ai"),
    (["crew", "multi-agent", "role"], "crewai"),
]


def infer_framework(query: str) -> str | None:
    q = query.lower()
    for keywords, framework in KEYWORD_TO_FRAMEWORK:
        if any(k in q for k in keywords):
            return framework
    return None


def detect_task_type(query: str) -> str | None:
    q = query.lower()
    if any(t in q for t in ["rag", "retrieval", "rerank", "chunk", "embed", "vector"]):
        return "rag"
    if any(t in q for t in ["tool", "function call", "mcp"]) and not any(t in q for t in ["agent", "loop"]):
        return "tools"
    if any(t in q for t in ["agent", "loop", "react", "plan", "multi-agent"]):
        return "agent"
    return None


def render(query, results, framework, scaffold_rel, eval_task, project=None):
    out = []
    out.append(f"# AgentForge Recommendation{' — ' + project if project else ''}")
    out.append("")
    out.append(f"**Query:** `{query}`")
    out.append("")

    if framework:
        out.append(f"**Framework:** `{framework}`")
        fw_profile = SKILL_DIR / "knowledge" / "frameworks" / f"{framework}.md"
        if fw_profile.exists():
            out.append(f"**Framework profile:** [`knowledge/frameworks/{framework}.md`]({fw_profile.relative_to(SKILL_DIR)})")
        out.append("")

    if scaffold_rel:
        out.append(f"**Runnable scaffold:** `scaffolds/{scaffold_rel}/` — clone, install, set API key, run.")
        out.append("")

    if eval_task:
        out.append(f"**Generate eval harness:**")
        out.append(f"```bash")
        out.append(f"python3 .claude/skills/agent-forge/scripts/eval_harness.py --task {eval_task}")
        out.append(f"```")
        out.append("")

    out.append("## Matched patterns")
    out.append("")
    if not results:
        out.append("_No matches in the knowledge base._")
    else:
        for domain, hits in results.items():
            out.append(f"### {domain}")
            for doc, score in hits:
                rel = doc["path"].relative_to(SKILL_DIR)
                name = doc["meta"].get("name") or doc["path"].stem
                when = doc["meta"].get("when_to_use", "")
                out.append(f"- **{name}** (`{rel}`)" + (f" — {when}" if when else ""))
            out.append("")

    out.append("---")
    out.append("")
    out.append("## Next steps")
    out.append("1. Read the matched pattern files in full")
    out.append(f"2. Open the scaffold ({'scaffolds/' + scaffold_rel + '/' if scaffold_rel else 'choose one in scaffolds/'}) and adapt")
    if eval_task:
        out.append(f"3. Generate the eval harness and start building a golden set from real data")
    out.append("")
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description="AgentForge recommendation synthesizer")
    p.add_argument("query", help="What you're trying to build")
    p.add_argument("--framework", choices=list(FRAMEWORK_TO_SCAFFOLD.keys()),
                   help="Force a framework choice. If omitted, inferred from the query.")
    p.add_argument("--task", choices=["rag", "agent", "tools"],
                   help="Force task type for eval suggestion. If omitted, inferred from the query.")
    p.add_argument("--top-k", "-n", type=int, default=3)
    p.add_argument("-p", "--project", help="Project name")
    args = p.parse_args()

    # 1. Search all domains via search.py
    results = search.search_all(args.query, top_k_per_domain=args.top_k)

    # 2. Pick framework
    framework = args.framework or infer_framework(args.query)

    # 3. Map to scaffold
    scaffold_rel = FRAMEWORK_TO_SCAFFOLD.get(framework) if framework else None

    # 4. Suggest eval task
    eval_task = args.task or detect_task_type(args.query)

    print(render(args.query, results, framework, scaffold_rel, eval_task, args.project))
    return 0


if __name__ == "__main__":
    sys.exit(main())
