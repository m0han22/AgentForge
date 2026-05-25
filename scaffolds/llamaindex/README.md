# LlamaIndex — RAG Pipeline Starter

End-to-end RAG over a local docs directory: load → hierarchical chunk → embed → hybrid retrieve → rerank → answer with citations.

## What it does

Drop markdown / text / PDF files into `./data/` and run. The script builds a vector index, retrieves hybrid (BM25 + dense), reranks the top-20 with Cohere, and answers your question with source citations.

## Run

```bash
pip install -r requirements.txt
cp .env.example .env  # add ANTHROPIC_API_KEY and COHERE_API_KEY (optional)
mkdir -p data && cp /path/to/your/docs/*.md data/
python main.py "What is our refund policy?"
```

## What's wired up

- **Hierarchical chunking** (section → paragraph → sentence) via `HierarchicalNodeParser`
- **Hybrid retrieval** — BGE embeddings (open-source) + BM25, fused by `QueryFusionRetriever`
- **Reranker** — Cohere rerank-3 if key present, else skip
- **Citation** — every answer includes `source_nodes`
- **Storage** — local persistent storage in `./storage/`; rebuild only when data changes

## Customize

- Swap `BAAI/bge-base-en-v1.5` for a paid embedder (OpenAI / Voyage) if you prefer
- Replace local `./data/` with cloud loaders (`LlamaIndex S3Reader`, `GoogleDriveReader`, etc.)
- Persist to pgvector / Qdrant / Pinecone for production (see `knowledge/deployment/vector-db-choice.md`)

## Related AgentForge patterns

- `knowledge/retrieval/hybrid-search.md`
- `knowledge/frameworks/llamaindex.md`
- `knowledge/deployment/vector-db-choice.md`
- `knowledge/evals/golden-set-construction.md`
