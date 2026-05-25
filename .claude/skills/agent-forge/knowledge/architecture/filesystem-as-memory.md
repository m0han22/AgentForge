---
name: Filesystem as Memory (Context Offloading)
category: architecture
difficulty: intermediate
when_to_use: long-running agents that produce or consume more data than fits in the context window
frameworks: [deep-agents, claude-agent-sdk, claude-code, langgraph]
related: [sub-agent-isolated-context, episodic-memory-store, recursive-summarization]
anti_patterns: [stream-everything-into-context, no-file-cleanup]
tags: [architecture, filesystem, memory, context-offloading, long-horizon]
---

# Filesystem as Memory (Context Offloading)

**TL;DR:** Treat a sandboxed filesystem (real or virtual) as the agent's working memory. Big tool outputs, intermediate research, scratchpads — all written to files. The agent reads only the files relevant to its current step. Sidesteps the context window as the binding constraint on long-horizon work. Used by Claude Code, Deep Agents, and any serious coding agent.

## When to use

- Agents that process more data than fits in context (large codebases, document corpora, log archives)
- Multi-step research / synthesis tasks where intermediate findings accumulate
- Coding agents — files ARE the natural state
- Long-running tasks where you want resumability across sessions
- Anywhere you'd otherwise summarize-then-throw-away valuable intermediate state

## When NOT to use

- Short single-shot tasks — overhead isn't justified
- No sandbox available — never give an agent a real filesystem without isolation
- Streaming/real-time tasks where files add latency
- When the data has structure better served by a DB (use vector store or KV instead)

## How it works

Three primitives:

1. **`write(path, content)`** — agent writes intermediate or final state to a file
2. **`read(path)`** — agent fetches content back when needed
3. **`list_dir(path)`, `search(pattern)`** — agent discovers what exists without reading everything

The agent's prompt encourages this pattern explicitly: "Use files for any output longer than a few hundred tokens. Don't keep large content in your reasoning."

Common workflow:
- Tool returns 50k tokens → agent writes it to `findings/api_docs.md` instead of keeping inline
- Sub-agent produces a report → writes to `reports/auth_audit.md`, returns just the path
- Agent revisits old findings → reads the relevant file, not the entire conversation
- Final answer → composed from reading only the files that matter

Pair with isolation:
- Files in a project-scoped sandbox (`/tmp/agent-run-{run_id}/`)
- Read/write permissions limited to the sandbox
- Cleanup hook on session end (or retain for resumability if checkpointing)

## Code — Claude Agent SDK with sandboxed filesystem

```python
from pathlib import Path
import shutil, tempfile, uuid

class AgentSandbox:
    def __init__(self, run_id: str | None = None):
        self.run_id = run_id or uuid.uuid4().hex[:8]
        self.root = Path(tempfile.gettempdir()) / f"agent-{self.run_id}"
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe(self, path: str) -> Path:
        p = (self.root / path).resolve()
        if not str(p).startswith(str(self.root)):
            raise ValueError("path escapes sandbox")
        return p

    def write(self, path: str, content: str) -> dict:
        p = self._safe(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return {"path": str(p.relative_to(self.root)), "bytes": len(content)}

    def read(self, path: str, max_chars: int = 50_000) -> dict:
        p = self._safe(path)
        if not p.exists():
            return {"error": "not_found"}
        text = p.read_text()
        if len(text) > max_chars:
            return {"content": text[:max_chars], "truncated": True, "total_chars": len(text)}
        return {"content": text}

    def list_dir(self, path: str = ".") -> dict:
        p = self._safe(path)
        return {"entries": [str(e.relative_to(self.root)) for e in p.iterdir()]}

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)

# Expose as agent tools
sandbox = AgentSandbox()

FS_TOOLS = [
    {
        "name": "fs_write",
        "description": (
            "Write content to a file in the sandbox. Use for any output longer than ~500 tokens "
            "instead of keeping it in your reasoning. Returns the path."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "fs_read",
        "description": "Read a file's content. Use to recall earlier findings.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "fs_list",
        "description": "List files in the sandbox to see what's been written.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "default": "."}},
            "additionalProperties": False,
        },
    },
]

HANDLERS = {
    "fs_write": lambda args: sandbox.write(args["path"], args["content"]),
    "fs_read":  lambda args: sandbox.read(args["path"]),
    "fs_list":  lambda args: sandbox.list_dir(args.get("path", ".")),
}
```

The system prompt then nudges the agent: "When a tool returns more than ~500 tokens, write the output to a file and continue with the file path as a reference. Read files back when you need their content."

## Tradeoffs

- **Context economy:** the primary win — agents can operate on more data than fits in the window
- **Resumability:** the sandbox is the durable state; checkpoint = serialize the sandbox
- **Sandboxing complexity:** need real filesystem isolation (sandbox, container, jail) for safety
- **Latency:** each read/write is a tool round-trip; not free
- **Discoverability:** agent has to remember (or list) what it wrote — give it `list_dir` early in the prompt
- **Cleanup:** orphan sandboxes leak disk; cap retention or scope to session

## Anti-patterns

- Streaming every tool result into context regardless of size — defeats the whole pattern
- No `list_dir` tool — agent loses track of what files exist
- Real filesystem, no sandbox — agent can write anywhere; security and stability nightmare
- No cleanup hook — disk fills with abandoned sandboxes
- File paths with no project convention — agent invents arbitrary paths, can't find them later
- Files used for state that should be in structured memory (entity facts → use vector store, not filenames)

## Related

- `sub-agent-isolated-context` — sub-agents write findings to files; parent reads paths back
- `episodic-memory-store` — for structured facts (vector DB), not for blob storage
- `recursive-summarization` — when files grow too large; summarize old files
- `tool-result-truncation` — even with files, truncate the in-context preview
