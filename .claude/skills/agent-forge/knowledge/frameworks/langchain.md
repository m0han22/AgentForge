---
name: LangChain
category: frameworks
when_to_use: prototyping, broad ecosystem integrations, when you need many off-the-shelf retrievers / loaders / parsers
language: [python, typescript]
maturity: stable
tags: [framework, langchain, ecosystem]
---

# LangChain

**TL;DR:** Largest ecosystem of LLM integrations (200+ retrievers, embedders, loaders, vector stores). Best for prototyping and projects that need many off-the-shelf pieces. For agent loops in production, prefer LangGraph (its sibling).

## Pick this when

- Prototyping — speed of trying things matters
- You need many off-the-shelf integrations (loaders, parsers, retrievers, vector stores)
- You want a high-level RetrievalQA / RAG chain to start
- You'll graduate to LangGraph for serious agent work

## Don't pick this when

- Production agent loops (use LangGraph)
- Minimal-overhead Claude work (use Claude Agent SDK)
- RAG-first with sophisticated indexing (use LlamaIndex)
- Multi-agent role orchestration (use CrewAI)

## Strengths

- **Massive ecosystem** — pretty much every embedder, vector DB, loader has a LangChain integration
- **LCEL (LangChain Expression Language)** — composable chains via the `|` operator
- **Easy to prototype** — `RetrievalQA.from_chain_type(...)` in three lines
- **Cross-provider abstractions** — switch LLMs by changing one line

## Weaknesses

- **Abstractions leak** — fine while it works, painful to debug when it doesn't
- **Agent primitives are deprecated** in favor of LangGraph — don't build new agents on `AgentExecutor`
- **Version churn** — breaking changes between minor versions
- **Performance overhead** vs calling SDKs directly

## Key APIs (LCEL)

```python
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

llm = ChatAnthropic(model="claude-opus-4-7")
prompt = ChatPromptTemplate.from_template("Question: {q}\n\nContext: {context}\n\nAnswer:")

def retrieve(q: str) -> str:
    # your retriever
    return "..."

chain = (
    {"q": RunnablePassthrough(), "context": retrieve}
    | prompt
    | llm
    | StrOutputParser()
)

answer = chain.invoke("what is the refund policy?")
```

## Patterns that pair well

- **Quick RAG prototype** — RetrievalQA + a vector store, 10 lines
- **LCEL pipelines** for clear data flow
- **Document loaders + text splitters** ecosystem

## Patterns that don't fit well

- **Stateful agents in production** — use LangGraph
- **Tight performance budgets** — overhead is non-trivial
- **Custom tool calling on Claude** — use Claude Agent SDK directly

## Migration notes

- From LangChain AgentExecutor → LangGraph: officially recommended; rewrite to graph
- From LangChain RAG → LlamaIndex: only if you need sophisticated indexing (parent-doc, hierarchical, knowledge-graph)
- From LangChain → direct SDK: when you find yourself fighting the abstraction
