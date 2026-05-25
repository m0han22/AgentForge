"""
LlamaIndex — RAG starter with hierarchical chunking, hybrid retrieval, optional Cohere rerank.
"""

import os
import sys
from pathlib import Path

from llama_index.core import (
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.llms.anthropic import Anthropic as LlamaAnthropic
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

DATA_DIR = Path("./data")
STORAGE_DIR = Path("./storage")
MODEL = "claude-opus-4-7"
TOP_K = 20
RERANK_TOP_N = 5


def configure():
    Settings.llm = LlamaAnthropic(model=MODEL, max_tokens=1024)
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")


def build_or_load_index():
    if STORAGE_DIR.exists() and any(STORAGE_DIR.iterdir()):
        print("Loading index from ./storage/", file=sys.stderr)
        return load_index_from_storage(StorageContext.from_defaults(persist_dir=str(STORAGE_DIR)))

    if not DATA_DIR.exists() or not any(DATA_DIR.iterdir()):
        print(f"Put files in {DATA_DIR}/ and rerun", file=sys.stderr)
        sys.exit(1)

    print(f"Loading docs from {DATA_DIR}/...", file=sys.stderr)
    docs = SimpleDirectoryReader(str(DATA_DIR)).load_data()

    parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[2048, 512, 128])
    nodes = parser.get_nodes_from_documents(docs)
    leaves = get_leaf_nodes(nodes)

    storage_ctx = StorageContext.from_defaults()
    storage_ctx.docstore.add_documents(nodes)

    print(f"Indexing {len(leaves)} leaf chunks...", file=sys.stderr)
    index = VectorStoreIndex(leaves, storage_context=storage_ctx)
    storage_ctx.persist(persist_dir=str(STORAGE_DIR))
    return index


def build_retriever(index):
    dense = index.as_retriever(similarity_top_k=TOP_K)
    bm25 = BM25Retriever.from_defaults(docstore=index.docstore, similarity_top_k=TOP_K)
    return QueryFusionRetriever(
        [dense, bm25],
        similarity_top_k=TOP_K,
        num_queries=1,
        mode="reciprocal_rerank",
        use_async=False,
    )


def build_query_engine(retriever):
    postprocessors = []
    if os.getenv("COHERE_API_KEY"):
        from llama_index.postprocessor.cohere_rerank import CohereRerank
        postprocessors.append(CohereRerank(top_n=RERANK_TOP_N, model="rerank-english-v3.0"))
    return RetrieverQueryEngine(retriever=retriever, node_postprocessors=postprocessors)


def run(question: str) -> dict:
    configure()
    index = build_or_load_index()
    retriever = build_retriever(index)
    engine = build_query_engine(retriever)
    resp = engine.query(question)
    return {
        "answer": str(resp),
        "sources": [
            {"text": n.node.text[:200], "score": n.score, "metadata": n.node.metadata}
            for n in (resp.source_nodes or [])[:5]
        ],
    }


if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY in .env or environment", file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) < 2:
        print('Usage: python main.py "your question"', file=sys.stderr)
        sys.exit(1)

    import json
    print(json.dumps(run(" ".join(sys.argv[1:])), indent=2))
