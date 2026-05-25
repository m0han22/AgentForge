---
name: Dense-Only Retrieval (When Hybrid is Cheap)
category: anti-patterns
applies_to: [retrieval]
severity: high
tags: [anti-pattern, retrieval, embeddings]
---

# Dense-Only Retrieval (When Hybrid is Cheap)

**The trap:** "Embeddings are semantic, so they'll capture everything." So you build a pure dense-vector RAG. It works on the demo. Then real users start querying API names, error codes, version numbers — and the right doc is in top-50 but not top-5.

## Why it happens

Embedding models squash text into a vector. Two strings with the same meaning end up close — that's the win. But two strings with identical rare tokens (e.g., `grpcio==1.59.0`, `ERR_TLS_CERT_ALTNAME_INVALID`) can end up further apart than semantically similar but token-different strings. Pure dense retrieval loses on:

- Specific identifiers (API names, error codes, library versions, ticket numbers)
- Numeric values that need exact match
- Rare proper nouns

## How to recognize it

- "Recall@10 is 0.95 but recall@5 is 0.62" — the right doc is being found, just not ranked high enough
- "It works for general questions but fails on specific ones"
- Users start including the specific keyword in their query "to help it find the right doc"

## What to do instead

Hybrid retrieval: BM25 + dense, fused with RRF, then reranked. See `knowledge/retrieval/hybrid-search.md`. Typical lift: +15–25% recall@10 on technical text. Costs ~30–80ms of latency. Almost always worth it on technical corpora.

## When dense-only is fine

- Pure conversational text (chat logs, narrative content)
- Corpus where queries are paraphrases, not keyword lookups
- Latency budget under 50ms with no caching infrastructure

## Related

- `hybrid-search` — the fix
- `reranking` — pairs with hybrid
- `recall-floor` — measure to know if you have this problem
