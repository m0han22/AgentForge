---
name: Hybrid BM25 + Dense Retrieval
category: retrieval
difficulty: intermediate
when_to_use: RAG over technical or mixed-intent corpora where exact-term and semantic queries both matter
frameworks: [llamaindex, langchain, langgraph, claude-agent-sdk]
related: [reranking, query-rewriting, chunking-by-structure]
anti_patterns: [dense-only-retrieval, no-rerank-on-fusion]
tags: [retrieval, search, bm25, hybrid, rrf, fusion]
---

# Hybrid BM25 + Dense Retrieval

**TL;DR:** Run BM25 (lexical) and dense (embedding) retrieval in parallel, fuse with Reciprocal Rank Fusion or weighted scoring, then rerank the top-50 with a cross-encoder. Typical lift: +15–25% recall@10 on technical corpora over dense-only.

## When to use

- Technical documentation with specific terminology (API names, error codes, version numbers, library names)
- Mixed-intent corpora (some queries are keyword-driven, some are conceptual)
- Anywhere you've tried dense-only and found "the right doc is in top-50 but not top-5"

## When NOT to use

- Pure conversational Q&A over narrative text (dense alone is usually fine)
- Latency budget under 50ms with no caching (BM25 + dense + fusion + rerank adds ~30–80ms)
- Corpus under ~1000 docs — overkill; dense or BM25 alone works

## How it works

Parallel retrieval, then fusion:

1. **BM25** retrieves top-N by lexical overlap (great for proper nouns, error codes, API names).
2. **Dense** retrieves top-N by embedding similarity (great for paraphrase, conceptual queries).
3. **Fusion** — combine ranks. Reciprocal Rank Fusion (RRF) is simple and robust:
   `score(doc) = sum over retrievers of 1 / (k + rank(doc))` where k is typically 60.
4. **Rerank** — cross-encoder (Cohere rerank, BGE-reranker) re-orders the fused top-50, returning top-5 to the LLM.

The rerank step matters: fusion alone often surfaces near-duplicates from both retrievers, and the cross-encoder is the only thing that scores query-doc relevance jointly.

## Code — LlamaIndex

```python
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.postprocessor.cohere_rerank import CohereRerank

# Assume `index` is your VectorStoreIndex with embedded chunks
dense_retriever = index.as_retriever(similarity_top_k=20)
bm25_retriever = BM25Retriever.from_defaults(
    docstore=index.docstore,
    similarity_top_k=20,
)

# RRF fusion of both retrievers
fusion = QueryFusionRetriever(
    [dense_retriever, bm25_retriever],
    similarity_top_k=20,        # top-N from fusion
    num_queries=1,              # no query rewriting at this stage
    mode="reciprocal_rerank",   # RRF
    use_async=True,
)

# Cross-encoder rerank top-20 → top-5
reranker = CohereRerank(api_key="...", top_n=5, model="rerank-english-v3.0")

def retrieve(query: str):
    nodes = fusion.retrieve(query)
    reranked = reranker.postprocess_nodes(nodes, query_str=query)
    return reranked
```

## Tradeoffs

- **Latency:** +30–80ms over dense-only. Mitigate with parallel issuance + retrieval caching.
- **Cost:** Cohere rerank is paid per query. Open-source BGE-reranker is free but needs GPU for fast inference.
- **Complexity:** More moving parts (BM25 index + vector index + fusion + reranker). Worth it when measured recall actually improves.

## Anti-patterns

- Dense-only retrieval on technical corpora — misses keyword-precise queries
- Fusion without rerank — surfaces near-duplicate chunks from both retrievers
- Different chunking strategies for BM25 vs dense — fusion compares apples to oranges
- Using BM25 over un-preprocessed text (HTML, code) — tokenize and clean first
- Skipping the eval — without recall@k measurement, you can't tell if hybrid actually helps your corpus

## Related

- `reranking` — cross-encoder details
- `query-rewriting` — pair with hybrid for multi-faceted queries
- `parent-document-retrieval` — combine with hybrid for citation-grounded answers
- `chunking-by-structure` — improves both BM25 and dense quality
