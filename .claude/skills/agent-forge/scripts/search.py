#!/usr/bin/env python3
"""
AgentForge knowledge base search.

BM25 ranking over markdown pattern files in knowledge/. Used by the SKILL to
surface relevant patterns for a user query.

Usage:
    search.py "<query>" --recommend [-p "Project"] [--persist] [--feature "name"] [-f markdown|ascii]
    search.py "<query>" --domain <name>
    search.py "<query>" --framework <name>
    search.py "<query>" [--top-k N]

Domains: safety, tools, loop, retrieval, evals, cost, memory, architecture, prompt, deployment, reasoning
Frameworks: claude-agent-sdk, langgraph, langchain, llamaindex, openai-agents-sdk, pydantic-ai, crewai

Falls back to a simple TF-IDF-ish ranking if rank_bm25 is not installed.
Falls back to a minimal frontmatter parser if PyYAML is not installed.
"""

import argparse
import re
import sys
from pathlib import Path
from collections import Counter

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


SKILL_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = SKILL_DIR / "knowledge"
FRAMEWORKS_DIR = KNOWLEDGE_DIR / "frameworks"

DOMAINS = [
    "safety", "tools", "loop", "retrieval", "evals", "cost",
    "memory", "architecture", "prompt", "deployment", "reasoning",
]
FRAMEWORKS = [
    "claude-agent-sdk", "langgraph", "langchain", "llamaindex",
    "openai-agents-sdk", "pydantic-ai", "crewai",
]


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def parse_frontmatter(content):
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---", 4)
    if end == -1:
        return {}, content
    raw_meta = content[4:end].strip()
    body = content[end + 4:].lstrip("\n")
    if HAS_YAML:
        try:
            meta = yaml.safe_load(raw_meta) or {}
        except Exception:
            meta = {}
    else:
        meta = _minimal_yaml(raw_meta)
    return meta, body


def _minimal_yaml(raw):
    """Tiny fallback parser. Handles `key: value` and `key: [a, b, c]`."""
    out = {}
    for line in raw.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            items = [s.strip().strip("'\"") for s in v[1:-1].split(",") if s.strip()]
            out[k] = items
        else:
            out[k] = v.strip("'\"")
    return out


def load_corpus(paths):
    corpus = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        meta, body = parse_frontmatter(text)
        tags = meta.get("tags", []) or []
        frameworks = meta.get("frameworks", []) or []
        if not isinstance(tags, list):
            tags = [str(tags)]
        if not isinstance(frameworks, list):
            frameworks = [str(frameworks)]
        searchable = " ".join([
            str(meta.get("name", "")),
            str(meta.get("category", "")),
            str(meta.get("when_to_use", "")),
            " ".join(str(t) for t in tags),
            " ".join(str(f) for f in frameworks),
            body,
        ])
        corpus.append({
            "path": path,
            "meta": meta,
            "body": body,
            "tokens": tokenize(searchable),
        })
    return corpus


def rank(corpus, query, top_k=5):
    if not corpus:
        return []
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    if HAS_BM25:
        bm25 = BM25Okapi([doc["tokens"] for doc in corpus])
        scores = bm25.get_scores(query_tokens)
    else:
        doc_freq = Counter()
        for doc in corpus:
            for term in set(doc["tokens"]):
                doc_freq[term] += 1
        n_docs = len(corpus)
        scores = []
        for doc in corpus:
            tf = Counter(doc["tokens"])
            score = 0.0
            for term in query_tokens:
                if doc_freq.get(term, 0) == 0:
                    continue
                idf = (n_docs / max(doc_freq[term], 1)) ** 0.5
                score += tf.get(term, 0) * idf
            scores.append(score)
    ranked = sorted(zip(corpus, scores), key=lambda x: -x[1])
    return [(doc, float(score)) for doc, score in ranked[:top_k] if score > 0]


def list_paths(root):
    if not root.exists():
        return []
    return [p for p in root.glob("**/*.md") if p.is_file()]


def search_domain(query, domain, top_k=5):
    return rank(load_corpus(list_paths(KNOWLEDGE_DIR / domain)), query, top_k)


def search_framework(query, framework, top_k=3):
    paths = list(FRAMEWORKS_DIR.glob(f"{framework}*.md"))
    return rank(load_corpus(paths), query, top_k)


def search_all(query, top_k_per_domain=3):
    results = {}
    for domain in DOMAINS:
        hits = search_domain(query, domain, top_k_per_domain)
        if hits:
            results[domain] = hits
    return results


def render_hit(doc, score, fmt="markdown"):
    meta = doc["meta"]
    rel = doc["path"].relative_to(SKILL_DIR)
    name = meta.get("name") or doc["path"].stem
    when = meta.get("when_to_use", "")
    frameworks = meta.get("frameworks", [])
    if isinstance(frameworks, list):
        frameworks = ", ".join(str(f) for f in frameworks)
    if fmt == "ascii":
        line1 = f"[{score:.2f}] {name}"
        line2 = f"  path: {rel}"
        line3 = f"  when: {when}" if when else ""
        line4 = f"  frameworks: {frameworks}" if frameworks else ""
        return "\n".join(s for s in [line1, line2, line3, line4] if s)
    when_str = f" — {when}" if when else ""
    return f"- **{name}** (`{rel}`){when_str}"


def render(query, results, project=None, fmt="markdown"):
    out = []
    if fmt == "ascii":
        out.append("=" * 70)
        out.append(f"AGENTFORGE{' — ' + project if project else ''}")
        out.append(f"Query: {query}")
        out.append("=" * 70)
    else:
        title = f"# AgentForge Recommendation{' — ' + project if project else ''}"
        out.append(title)
        out.append("")
        out.append(f"**Query:** `{query}`")
        out.append("")

    if not results:
        out.append("")
        out.append("No matching patterns found. The knowledge base may not cover this query yet.")
        out.append("Consider adding a new pattern under knowledge/<domain>/.")
        return "\n".join(out)

    for domain, hits in results.items():
        if fmt == "ascii":
            out.append("")
            out.append(f"--- {domain.upper()} ---")
            for doc, score in hits:
                out.append(render_hit(doc, score, fmt))
        else:
            out.append(f"## {domain}")
            out.append("")
            for doc, score in hits:
                out.append(render_hit(doc, score, fmt))
            out.append("")

    if fmt == "markdown":
        out.append("---")
        out.append("")
        out.append("**Next:** read the matched files in full, then synthesize a prescriptive response per the SKILL.md output template.")
    return "\n".join(out)


def persist(content, project, feature=None):
    base = Path.cwd() / "agent-system"
    if feature:
        target = base / "features" / f"{feature}.md"
    else:
        target = base / "MASTER.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def main():
    p = argparse.ArgumentParser(description="AgentForge knowledge search (BM25 over knowledge/)")
    p.add_argument("query", help="Search query")
    p.add_argument("--recommend", action="store_true", help="Full multi-domain recommendation")
    p.add_argument("--domain", choices=DOMAINS, help="Search within one domain")
    p.add_argument("--framework", choices=FRAMEWORKS, help="Framework-specific guidance")
    p.add_argument("--top-k", "-n", type=int, default=5, help="Max results per domain")
    p.add_argument("--persist", action="store_true", help="Save recommendation to ./agent-system/")
    p.add_argument("-p", "--project", help="Project name (for persistence)")
    p.add_argument("--feature", help="Feature name (writes to ./agent-system/features/<name>.md)")
    p.add_argument("-f", "--format", choices=["markdown", "ascii"], default="markdown")
    args = p.parse_args()

    if args.domain:
        hits = search_domain(args.query, args.domain, args.top_k)
        results = {args.domain: hits} if hits else {}
    elif args.framework:
        hits = search_framework(args.query, args.framework, args.top_k)
        results = {f"frameworks/{args.framework}": hits} if hits else {}
    else:
        results = search_all(args.query, top_k_per_domain=args.top_k)

    content = render(args.query, results, args.project, args.format)
    print(content)

    if args.persist:
        if not args.project:
            print("\n[warn] --persist without -p/--project; using 'Untitled'", file=sys.stderr)
        target = persist(content, args.project or "Untitled", args.feature)
        print(f"\n[persisted] {target}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
