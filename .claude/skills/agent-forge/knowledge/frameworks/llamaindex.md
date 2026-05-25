---
name: LlamaIndex
category: frameworks
when_to_use: RAG-first systems, sophisticated indexing (hierarchical, knowledge graph, multi-modal), document QA
language: [python, typescript]
maturity: stable
tags: [framework, llamaindex, rag, indexing]
---

# LlamaIndex

**TL;DR:** RAG-first framework with the richest indexing primitives (hierarchical, parent-doc, knowledge graph, multi-modal). Best when your problem is "answer questions from documents" rather than "general agent". Has agent primitives but they're not its core strength.

## Pick this when

- RAG over documents is the primary workload
- You need sophisticated indexing (hierarchical chunking, parent-doc retrieval, knowledge graphs, multi-modal)
- You want first-class evaluation tools (LlamaIndex has built-in eval modules)
- Document loaders + node parsers + retrievers should all "just work" together

## Don't pick this when

- Agent-first with light retrieval (use Claude Agent SDK or LangGraph)
- You only need basic RAG and prefer a smaller dependency (use direct SDK + pgvector)
- Multi-agent orchestration is the goal (use CrewAI / Agents SDK)

## Strengths

- **Best-in-class indexing** — hierarchical, parent-doc, sentence-window, auto-merging retrievers
- **Native query engines** — RouterQueryEngine, SubQuestionQueryEngine, MultiStepQueryEngine
- **Eval modules built in** — faithfulness, relevancy, semantic similarity
- **LlamaParse** — strong PDF/table extraction
- **Vector store + graph store integration** — knowledge graph RAG without leaving the framework

## Weaknesses

- **Agent loops are less polished** than LangGraph
- **Abstractions can be deep** — many similar classes (BaseRetriever, BaseQueryEngine, etc.)
- **API surface is large** — discoverability cost

## Key APIs

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import HierarchicalNodeParser
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.postprocessor.cohere_rerank import CohereRerank

Settings.llm = Anthropic(model="claude-opus-4-7")
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")

# Load and parse hierarchically (section → paragraph → sentence)
docs = SimpleDirectoryReader("./data").load_data()
parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[2048, 512, 128])
nodes = parser.get_nodes_from_documents(docs)

# Build index (use the leaf nodes; parents are stored in docstore)
from llama_index.core.storage.docstore import SimpleDocumentStore
docstore = SimpleDocumentStore()
docstore.add_documents(nodes)

leaf_nodes = [n for n in nodes if not n.child_nodes]
index = VectorStoreIndex(leaf_nodes)

# Auto-merging retriever: hits leaves, returns parent when many leaves of same parent match
base_retriever = index.as_retriever(similarity_top_k=12)
retriever = AutoMergingRetriever(base_retriever, storage_context=index.storage_context)

# Rerank
reranker = CohereRerank(top_n=5)

query_engine = RetrieverQueryEngine(
    retriever=retriever,
    node_postprocessors=[reranker],
)

response = query_engine.query("What is the refund policy?")
print(response, response.source_nodes)
```

## Patterns that pair well

- **Hierarchical chunking + parent-doc retrieval** (this is LlamaIndex's wheelhouse)
- **Knowledge graph RAG** for entity-relationship-heavy domains
- **Multi-step query decomposition** for complex questions
- **Built-in eval module** for faithfulness/relevancy

## Patterns that don't fit well

- **Long agent loops with many tools** — use LangGraph or Claude Agent SDK
- **High-frequency simple lookups** — direct SDK + pgvector has less overhead

## Migration notes

- From LangChain RAG: usually worth it if you need hierarchical retrieval or knowledge graph
- From custom RAG: graduate when you outgrow flat chunking
- To LangGraph: if the agent loop becomes the main complexity, not the retrieval
