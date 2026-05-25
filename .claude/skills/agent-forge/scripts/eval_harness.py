#!/usr/bin/env python3
"""
AgentForge eval harness generator.

Emits starter eval files for a given task type into ./eval/:
- golden_set.csv — empty skeleton with header + 3 example rows
- eval.py       — runnable Ragas (RAG) or task-completion (agent) eval script
- ci_gate.sh    — CI wrapper that exits non-zero on threshold failure
- README.md     — short doc

Usage:
    eval_harness.py --task rag    [--out ./eval]
    eval_harness.py --task agent  [--out ./eval]
    eval_harness.py --task tools  [--out ./eval]
"""

import argparse
import sys
from pathlib import Path


GOLDEN_SET_RAG = """question,ground_truth_answer,ground_truth_context_ids,category
"What is our refund policy for annual plans?","Annual plans are refundable pro-rata within 30 days.","POL-23","common"
"Where do I find the API rate limit settings?","API rate limits are configured per workspace under Settings → API.","DOC-API-12","common"
"What happens if I exceed my rate limit?","Requests are queued for up to 5 seconds then return 429.","DOC-API-13","hard"
"""

GOLDEN_SET_AGENT = """task,expected_tools,expected_outcome,category
"Look up the user's last 3 orders and summarize","[get_orders]","Summary mentions all 3 orders with dates","common"
"Find the most-cited paper on attention mechanisms","[web_search]","Returns 'Attention Is All You Need' or similar","common"
"Delete user 482's account","[]","Refuses without explicit confirmation","adversarial"
"""

GOLDEN_SET_TOOLS = """tool_call_input,expected_tool,expected_args_subset,category
"Search for 'gRPC retries'","search_docs","{""query"": ""gRPC retries""}","common"
"Get my orders from last week","get_orders","{""from"": ""last_week""}","common"
"Delete all my data","escalate_to_human","{}","adversarial"
"""

EVAL_PY_RAG = '''"""
RAG eval — Ragas context-recall + faithfulness on golden_set.csv.

Replace `run_pipeline` with your actual RAG. Outputs PASS/FAIL based on thresholds.
"""

import csv
import sys
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import answer_correctness, context_recall, faithfulness

THRESHOLDS = {"context_recall": 0.85, "faithfulness": 0.90}


def run_pipeline(question: str) -> dict:
    """Replace this with your actual RAG pipeline. Must return {answer, contexts}."""
    raise NotImplementedError("Wire run_pipeline to your RAG. Returns dict(answer=..., contexts=[...])")


def load_golden(path="golden_set.csv"):
    with open(path) as f:
        return list(csv.DictReader(f))


def main():
    golden = load_golden()
    rows = []
    for g in golden:
        out = run_pipeline(g["question"])
        rows.append({
            "question": g["question"],
            "answer": out["answer"],
            "contexts": out["contexts"],
            "ground_truth": g["ground_truth_answer"],
        })
    ds = Dataset.from_list(rows)
    scores = evaluate(ds, metrics=[context_recall, faithfulness, answer_correctness])
    print(scores)

    failed = []
    for metric, threshold in THRESHOLDS.items():
        if scores[metric] < threshold:
            failed.append(f"{metric}={scores[metric]:.3f} < {threshold}")
    if failed:
        print("FAIL:", "; ".join(failed), file=sys.stderr)
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
'''

EVAL_PY_AGENT = '''"""
Agent eval — task completion + correct-tool-selection on golden_set.csv.

Replace `run_agent` with your actual agent. Outputs PASS/FAIL based on thresholds.
"""

import csv
import json
import sys

PASS_THRESHOLD = 0.80


def run_agent(task: str) -> dict:
    """Replace this with your actual agent run. Must return {tools_called, final_output}."""
    raise NotImplementedError("Wire run_agent to your agent. Returns dict(tools_called=[...], final_output='...')")


def load_golden(path="golden_set.csv"):
    with open(path) as f:
        return list(csv.DictReader(f))


def evaluate_row(g: dict, result: dict) -> bool:
    expected_tools = json.loads(g["expected_tools"])
    if expected_tools and not all(t in result["tools_called"] for t in expected_tools):
        return False
    # Simple substring check; replace with LLM-as-judge for richer scoring
    return any(token.lower() in result["final_output"].lower()
               for token in g["expected_outcome"].split()[:3])


def main():
    golden = load_golden()
    passes = []
    for g in golden:
        try:
            r = run_agent(g["task"])
            passes.append(evaluate_row(g, r))
        except Exception as e:
            print(f"ERROR on '{g['task']}': {e}", file=sys.stderr)
            passes.append(False)

    rate = sum(passes) / len(passes) if passes else 0.0
    print(f"completion_rate={rate:.3f} ({sum(passes)}/{len(passes)})")
    if rate < PASS_THRESHOLD:
        print(f"FAIL: rate < {PASS_THRESHOLD}", file=sys.stderr)
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
'''

EVAL_PY_TOOLS = '''"""
Tool eval — correct-tool-selection rate on golden_set.csv.

Tests that your agent picks the right tool with approximately the right args.
"""

import csv
import json
import sys

PASS_THRESHOLD = 0.90


def predict_tool_call(input_text: str) -> dict:
    """Replace this with your actual tool-picker (LLM call with tools)."""
    raise NotImplementedError("Wire predict_tool_call to your LLM+tools call")


def load_golden(path="golden_set.csv"):
    with open(path) as f:
        return list(csv.DictReader(f))


def args_subset_match(expected: dict, actual: dict) -> bool:
    for k, v in expected.items():
        if k not in actual:
            return False
        if isinstance(v, str) and v.lower() not in str(actual[k]).lower():
            return False
    return True


def main():
    golden = load_golden()
    correct = 0
    for g in golden:
        try:
            pred = predict_tool_call(g["tool_call_input"])
            expected_args = json.loads(g["expected_args_subset"])
            if pred["tool"] == g["expected_tool"] and args_subset_match(expected_args, pred["args"]):
                correct += 1
        except Exception as e:
            print(f"ERROR on '{g['tool_call_input']}': {e}", file=sys.stderr)

    rate = correct / len(golden) if golden else 0.0
    print(f"tool_selection_accuracy={rate:.3f} ({correct}/{len(golden)})")
    if rate < PASS_THRESHOLD:
        print(f"FAIL: rate < {PASS_THRESHOLD}", file=sys.stderr)
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
'''

CI_GATE = """#!/usr/bin/env bash
# CI gate — runs the golden-set eval and exits non-zero on regression.
# Wire this into your CI (.github/workflows/eval.yml or equivalent).
set -euo pipefail

cd "$(dirname "$0")"
python3 eval.py
"""

README_RAG = """# RAG eval starter

Generated by `agent-forge/scripts/eval_harness.py --task rag`.

## What's here
- `golden_set.csv` — 50–200 examples of (question, ground_truth_answer, ground_truth_context_ids). 3 starter rows included; **grow this with real production queries**.
- `eval.py` — runnable Ragas eval (context-recall + faithfulness + answer-correctness). Wire `run_pipeline` to your RAG.
- `ci_gate.sh` — CI wrapper that exits non-zero on threshold failure.

## First run
1. Fill out 50+ rows in `golden_set.csv` from real user queries (not synthetic).
2. Replace `run_pipeline` in `eval.py` with your actual RAG.
3. `pip install ragas datasets` and run `python eval.py`.
4. Tune thresholds in `eval.py` for your acceptable floor (defaults: context_recall > 0.85, faithfulness > 0.9).
5. Wire `ci_gate.sh` into CI so every prompt/model/pipeline change runs the eval.

## Related
- `knowledge/evals/golden-set-construction.md`
"""

README_AGENT = """# Agent eval starter

Generated by `agent-forge/scripts/eval_harness.py --task agent`.

## What's here
- `golden_set.csv` — examples of (task, expected_tools, expected_outcome, category)
- `eval.py` — runs your agent against the golden set, measures completion rate
- `ci_gate.sh` — CI wrapper

## First run
1. Fill out 50+ rows from real production tasks.
2. Replace `run_agent` in `eval.py` with your agent invocation. Must return `{tools_called, final_output}`.
3. Run `python eval.py`. Default threshold: 80% completion rate.

## Related
- `knowledge/evals/golden-set-construction.md`
"""

README_TOOLS = """# Tool-selection eval starter

Generated by `agent-forge/scripts/eval_harness.py --task tools`.

## What's here
- `golden_set.csv` — examples of (input, expected_tool, expected_args_subset, category)
- `eval.py` — runs your tool-picker, measures correct-tool-selection rate
- `ci_gate.sh` — CI wrapper

## First run
1. Add real prod tool-call examples to `golden_set.csv`.
2. Wire `predict_tool_call` in `eval.py` to your LLM-with-tools call.
3. Run `python eval.py`. Default threshold: 90% selection accuracy.

## Related
- `knowledge/tools/tool-schema-design.md`
- `knowledge/evals/golden-set-construction.md`
"""

CONTENT = {
    "rag":   (GOLDEN_SET_RAG,   EVAL_PY_RAG,   README_RAG),
    "agent": (GOLDEN_SET_AGENT, EVAL_PY_AGENT, README_AGENT),
    "tools": (GOLDEN_SET_TOOLS, EVAL_PY_TOOLS, README_TOOLS),
}


def main():
    p = argparse.ArgumentParser(description="Generate AgentForge eval harness starter files")
    p.add_argument("--task", required=True, choices=list(CONTENT.keys()))
    p.add_argument("--out", default="./eval", help="Output directory (default: ./eval)")
    p.add_argument("--force", action="store_true", help="Overwrite if files exist")
    args = p.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    golden, evalpy, readme = CONTENT[args.task]
    files = {
        "golden_set.csv": golden,
        "eval.py": evalpy,
        "ci_gate.sh": CI_GATE,
        "README.md": readme,
    }

    skipped = []
    for name, content in files.items():
        target = out / name
        if target.exists() and not args.force:
            skipped.append(str(target))
            continue
        target.write_text(content)
        if name == "ci_gate.sh":
            target.chmod(0o755)

    print(f"Wrote eval harness to {out}/", file=sys.stderr)
    if skipped:
        print("Skipped existing files (use --force to overwrite):", file=sys.stderr)
        for s in skipped:
            print(f"  {s}", file=sys.stderr)
    print(f"\nNext steps:", file=sys.stderr)
    print(f"  1. Fill {out}/golden_set.csv with 50+ real production examples", file=sys.stderr)
    print(f"  2. Wire {out}/eval.py to your pipeline", file=sys.stderr)
    print(f"  3. Run: cd {out} && python eval.py", file=sys.stderr)


if __name__ == "__main__":
    main()
