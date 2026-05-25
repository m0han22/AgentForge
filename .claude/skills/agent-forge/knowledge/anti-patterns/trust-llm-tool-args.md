---
name: Trusting LLM-Generated Tool Arguments
category: anti-patterns
applies_to: [tools, safety]
severity: critical
tags: [anti-pattern, tools, safety, validation]
---

# Trusting LLM-Generated Tool Arguments

**The trap:** Your tool gets called with `{"user_id": "u_482", "amount": 1000, "currency": "USD"}`. The schema says those are required strings/numbers. You execute. Later you discover the LLM invented `u_482` (the real user is `u_4829`), the amount was supposed to be cents but the LLM sent dollars, and the user actually said "euros".

## Why it happens

- Schema validation feels like "enough"
- LLMs produce confident, well-formatted, plausible-looking JSON
- The LLM is "right" most of the time — the failures are tail risk
- Server-side validation feels duplicative

## How to recognize it

- Bug reports about wrong records being modified
- Currency / unit mismatches in financial flows
- "The agent ran but the wrong thing happened"
- LLM tool calls succeeding with technically-valid-but-wrong args

## What to do instead

Three layers, all required:

1. **Strict JSON Schema** — required fields, enums for fixed values, `additionalProperties: false`. Reduces but doesn't eliminate bad args.
2. **Server-side validation** — re-validate every argument as if it came from an untrusted client. Because it did.
3. **Sanity checks** — does the user ID exist? Is the amount in expected range? Does the currency match the user's account?

For destructive operations, add:

4. **Dry-run / preview mode** — return what would happen, not what happened
5. **Explicit confirmation** — show the proposed action to the user before executing
6. **Idempotency keys** — protect against the LLM retrying and double-acting

See `knowledge/tools/tool-schema-design.md` for the full pattern.

## Real-world examples

- LLM books flight on the wrong date (parsed "next Friday" as the wrong week)
- LLM sends email to wrong recipient (matched the wrong person from address book)
- LLM transfers funds in wrong currency (user said USD, LLM defaulted to account's home currency)
- LLM deletes wrong record (off-by-one in pagination index)

Every one of these has happened in production at companies you've heard of.

## Related

- `tool-schema-design` — strict schemas + server-side validation
- `confirmation-for-destructive` — human approval for risky ops
- `tool-idempotency` — protect against retries
- `audit-logging` — required for forensics when it goes wrong
