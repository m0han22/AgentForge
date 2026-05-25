---
name: Vector Database Choice by Scale
category: deployment
difficulty: intermediate
when_to_use: picking a vector store for a new RAG pipeline or scaling an existing one
frameworks: [llamaindex, langchain, langgraph, claude-agent-sdk]
related: [embeddings-versioning, index-rebuild-strategy, hybrid-search]
anti_patterns: [pinecone-for-1000-docs, self-host-without-ops-capacity]
tags: [deployment, vector-db, pgvector, pinecone, qdrant, weaviate]
---

# Vector Database Choice by Scale

**TL;DR:** pgvector for <1M chunks (just use Postgres). Qdrant or Weaviate for 1M–100M (self-host or managed). Pinecone or Vespa for 100M+ or strict latency SLAs. Don't pick managed for cost reasons; don't self-host without ops capacity.

## When to use

- Greenfield RAG pipeline — picking your first vector store
- Outgrowing current choice (latency degradation, cost blowup, missing features)
- Multi-tenant RAG with isolation requirements

## How it works

The picker, by scale and constraint:

### <1M chunks → pgvector

- You probably already have Postgres. Add the `pgvector` extension.
- Combine with full-text search (Postgres `tsvector`) for hybrid retrieval in a single query.
- Costs ~$0 incremental.
- Limitation: index size + latency grow super-linearly past ~5M vectors; plan migration before then.

### 1M–10M chunks → Qdrant or Weaviate (self-hosted) or Pinecone (managed)

- Self-host **Qdrant** if you want best price/performance and have ops capacity. Rust, fast, hybrid built-in.
- Self-host **Weaviate** if you want richer schema features (multi-tenancy, modules).
- Managed **Pinecone** if you want zero-ops and fast time-to-launch; cost is real but predictable.

### 10M–100M chunks → Qdrant (sharded), Weaviate (cluster), Pinecone (pod-based), Vespa

- At this scale, ops matter more than features. Pick the one your team can operate.
- **Vespa** is the heavyweight choice — built for Yahoo-scale, hybrid + ranking baked in.

### 100M+ chunks or sub-50ms p99 latency → Vespa, Pinecone (serverless), or specialized

- Read the latency benchmarks for your access pattern.
- Consider sharding by tenant or namespace.

### Multi-tenant with isolation → managed (Pinecone namespaces, Weaviate multi-tenancy)

- Self-hosted multi-tenancy is doable but operationally heavy.

## Code — pgvector (the default for <1M)

```sql
-- Schema
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE chunks (
  id BIGSERIAL PRIMARY KEY,
  doc_id TEXT NOT NULL,
  text TEXT NOT NULL,
  metadata JSONB,
  embedding VECTOR(1024),    -- match your embedding model dim
  tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
);

-- Vector index (HNSW for speed, IVFFlat for lower memory)
CREATE INDEX chunks_embedding_idx
  ON chunks USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Full-text index (for BM25-style retrieval)
CREATE INDEX chunks_tsv_idx ON chunks USING GIN (tsv);

-- Hybrid query (dense + lexical, weighted)
SELECT id, doc_id, text,
  (1 - (embedding <=> $1)) * 0.7 +
  ts_rank(tsv, plainto_tsquery('english', $2)) * 0.3 AS score
FROM chunks
WHERE tsv @@ plainto_tsquery('english', $2)
   OR embedding <=> $1 < 0.5
ORDER BY score DESC
LIMIT 20;
```

```python
# Python client
import psycopg
from openai import OpenAI  # or any embedder

embedder = OpenAI()

def upsert_chunk(conn, doc_id, text, metadata):
    emb = embedder.embeddings.create(model="text-embedding-3-large", input=text).data[0].embedding
    conn.execute(
        "INSERT INTO chunks (doc_id, text, metadata, embedding) VALUES (%s, %s, %s, %s)",
        (doc_id, text, metadata, emb),
    )

def hybrid_search(conn, query, top_k=20):
    emb = embedder.embeddings.create(model="text-embedding-3-large", input=query).data[0].embedding
    rows = conn.execute(
        """SELECT id, doc_id, text, ... FROM chunks ORDER BY score DESC LIMIT %s""",
        (emb, query, top_k),
    ).fetchall()
    return rows
```

## Tradeoffs

| Choice | Pro | Con |
|---|---|---|
| pgvector | $0, one less service, hybrid in-DB | Doesn't scale past ~5–10M |
| Qdrant (self) | Best price/perf at scale, fast, hybrid built-in | Need ops capacity |
| Pinecone | Zero-ops, fast launch, predictable | Costs add up at scale |
| Weaviate | Rich features (multi-tenancy, modules) | Heavier than Qdrant |
| Vespa | Battle-tested at Yahoo scale | Steep learning curve |

## Anti-patterns

- Pinecone for 1000 docs — pgvector is faster and free
- Self-hosting Qdrant without on-call rotation — you'll wake up to a down search at 3am
- Switching vector DBs to "fix" a retrieval problem — usually it's chunking or rerank, not the store
- Mixing embedding models across the corpus — old chunks become invisible to new queries
- Not versioning embeddings — corpus rebuild is painful when you don't tag which model produced what

## Related

- `embeddings-versioning` — tag every chunk with the embedding model + version
- `index-rebuild-strategy` — incremental vs full rebuild
- `hybrid-search` — pair the vector DB with BM25 for technical corpora
