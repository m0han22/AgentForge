---
name: Tool Schema Design
category: tools
difficulty: beginner
when_to_use: designing any tool the LLM will call (function calling, MCP server, agent action)
frameworks: [claude-agent-sdk, langgraph, langchain, llamaindex, openai-agents-sdk, pydantic-ai, crewai]
related: [tool-description-when-not-what, tool-input-validation-server-side, error-as-data]
anti_patterns: [trust-llm-tool-args, loose-tool-schemas]
tags: [tools, function-calling, schema, mcp]
---

# Tool Schema Design

**TL;DR:** Use strict JSON Schema with required fields, enums, and typed values. Write the description to answer "when to use this", not "what this does". Validate inputs server-side. Return errors as structured data.

## When to use

- Any LLM tool / function call / MCP tool
- Any agent that invokes external APIs or internal functions
- When the model picks wrong tools or sends wrong arguments

## How it works

Three things matter for tool reliability:

1. **Strict schemas.** Required fields, narrow types (`string` with `enum`, not `string`), `additionalProperties: false`. The model is more reliable when the schema is restrictive.
2. **Description tells WHEN.** "Use when the user asks about pricing or plan changes" beats "Get pricing info". Include 1–2 example invocations.
3. **Server-side validation.** Re-validate every argument server-side — LLMs hallucinate plausible-but-wrong IDs, dates, enum values.

## Code — Claude Agent SDK

```python
SEARCH_DOCS_TOOL = {
    "name": "search_docs",
    "description": (
        "Search the engineering wiki for technical documentation. "
        "Use when the user asks about: API behavior, error codes, "
        "deployment procedures, internal libraries. "
        "Do NOT use for: HR questions, billing, customer data.\n\n"
        "Example: search_docs(query='gRPC retry behavior', top_k=5)"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "minLength": 3,
                "maxLength": 200,
                "description": "Natural language search query",
            },
            "top_k": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20,
                "default": 5,
            },
            "section": {
                "type": "string",
                "enum": ["api", "deployment", "libraries", "errors"],
                "description": "Optional section filter",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}

def handle_search_docs(args: dict) -> dict:
    # Server-side validation, even after schema
    query = args["query"].strip()
    if len(query) < 3:
        return {"error": "query_too_short", "hint": "Query must be at least 3 characters"}
    top_k = max(1, min(args.get("top_k", 5), 20))
    section = args.get("section")
    if section and section not in {"api", "deployment", "libraries", "errors"}:
        return {"error": "invalid_section", "hint": "Use one of: api, deployment, libraries, errors"}
    # ... actual search ...
    return {"results": [...]}
```

## Tradeoffs

- **Strict schemas + enums** reduce model flexibility but dramatically improve tool-call reliability. Worth it.
- **Long descriptions** crowd the context. Aim for 2–4 sentences plus one example.
- **Server-side validation** is duplicative with the schema but catches the cases where the model violates the schema anyway (it happens).

## Anti-patterns

- Description that only states WHAT: "Searches documents" — model can't disambiguate from other search tools
- `string` type for fields that should be `enum` — model invents values
- `additionalProperties: true` (the default in many libraries) — allows the model to inject extra args
- Returning Python exceptions / stack traces as tool errors — model can't recover from them
- No server-side validation — trusting the model's JSON

## Related

- `tool-description-when-not-what` — write descriptions that disambiguate
- `tool-input-validation-server-side` — re-check args after schema
- `error-as-data` — structured errors the LLM can reason about
- `mcp-over-custom` — prefer MCP for portability + auth reuse
