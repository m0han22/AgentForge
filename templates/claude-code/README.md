# Claude Code template

The Claude Code install copies the full skill suite (1 hub + 6 focused skills) from `.claude/skills/` in this repo into the target project's (or user's) `.claude/skills/` directory.

Usage:

```bash
npx agent-forge install claude-code            # into ./.claude/skills/
npx agent-forge install claude-code --dir ~    # into ~/.claude/skills/ (user-level)
```

After install, open Claude Code in the target directory. The skill auto-activates on agentic / RAG keywords.

This file is informational only — the actual installed content is at `<repo-root>/.claude/skills/`.
