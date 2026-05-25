---
name: agent-forge
description: "Opinionated agentic-AI architect for building and shipping LLM agents and RAG systems. Covers 10 priority domains (safety & guardrails, tool design, loop control, retrieval, eval & observability, cost & latency, memory, agent architecture, prompt quality, deployment) across 6 frameworks (Claude Agent SDK, LangGraph, LangChain, LlamaIndex, OpenAI Agents SDK, Pydantic AI, CrewAI). Actions: plan, build, design, implement, scaffold, review, audit, fix, optimize, harden, deploy, evaluate, debug, refactor. Problems: RAG pipelines, tool-using agents, multi-agent systems, retrieval quality, chunking, hybrid search, reranking, query rewriting, HyDE, ColBERT, agent loops, ReAct, plan-execute, orchestrator-worker, handoffs, memory, summarization, episodic memory, tool schemas, MCP, parallel tools, error handling, retries, prompt injection, jailbreaks, guardrails, PII redaction, content policy, eval, Ragas, golden sets, LLM-as-judge, regression, drift, traces, observability, LangSmith, Phoenix, prompt caching, model routing, latency budgets, cost budgets, vector DB choice, pgvector, Pinecone, Qdrant, Weaviate, Vespa, agent serving, agent deployment. Returns ONE prescriptive recommendation with runnable code, anti-patterns, and a starter eval."
allowed-tools: Read, Bash, Write, Glob, Grep
---

# AgentForge — Agentic AI Architect

Opinionated reference and decision engine for building production AI agents and RAG systems. Contains 10 priority categories (CRITICAL → LOW), 200+ inline rules, framework-specific guidance for 6 ecosystems (Claude Agent SDK, LangGraph, LlamaIndex, OpenAI Agents SDK, Pydantic AI, CrewAI), and a searchable knowledge base of full pattern docs. Recommends ONE path with code, anti-patterns, and a starter eval — never a menu of options.

## When to Apply

This skill should be used when the task involves **building, designing, hardening, evaluating, or deploying an LLM-based agent or RAG system**.

### Must Use

This skill must be invoked when:

- Designing or building a new agent (single-agent, multi-agent, tool-using, planning, ReAct, orchestrator-worker)
- Designing or building a RAG pipeline (chunking, embedding, retrieval, reranking, generation)
- Choosing or comparing agent frameworks (Claude Agent SDK vs LangGraph vs LlamaIndex vs OpenAI Agents vs Pydantic AI vs CrewAI)
- Designing tool schemas, MCP servers, or function-calling integrations
- Adding memory (short-term, long-term, episodic, summarization buffers) to an agent
- Building agent evaluations (golden sets, Ragas, LLM-as-judge, regression harnesses)
- Adding guardrails (prompt injection defense, PII redaction, output validation, content policy)
- Optimizing agent cost or latency (prompt caching, parallel tools, model routing, batching)
- Picking a vector database, embedding model, or reranker
- Deploying agents to production (serving, scaling, monitoring, observability, traces)
- Reviewing or debugging an existing agent or RAG pipeline

### Recommended

This skill is recommended when:

- The user says "my agent is slow / expensive / hallucinating / looping"
- The user is choosing between two agent architectures or frameworks
- The user is pre-launching an agent and wants a production-readiness review
- The user mentions an agent-related error pattern (infinite loop, tool error, bad retrieval)
- The user is migrating between frameworks (e.g., LangChain → LangGraph, LangChain → Claude Agent SDK)

### Skip

This skill is NOT needed when:

- Pure prompt-engineering with no agent / tool / retrieval dimension
- LLM training, fine-tuning, RLHF, or model architecture internals
- General Python / TypeScript / backend coding unrelated to LLMs
- Frontend, UI/UX, or design questions
- Pure infrastructure or DevOps work
- Single LLM API call with no agentic structure

**Decision criteria**: If the task involves an LLM that **calls tools, retrieves context, loops, plans, holds memory, coordinates with other LLMs, or needs evaluation** — this skill applies.

---

## Rule Categories by Priority

*For Claude/AI reference: follow priority 1→10 to decide which rule category to focus on first; use `--domain <name>` to query details. Scripts do not read this table.*

| # | Category | Impact | Domain Flag | Must Have (Key Checks) | Anti-Patterns (Avoid) |
|---|---|---|---|---|---|
| 1 | **Safety & Guardrails** | CRITICAL | `safety` | Input/output validation, prompt-injection defense, tool allowlist, secrets isolation, audit logging | Treating retrieved content as trusted, auto-executing unvalidated LLM output, secrets in system prompts |
| 2 | **Tool Design & Error Handling** | CRITICAL | `tools` | Strict JSON schemas, idempotency, timeouts, retries, actionable errors, server-side validation | Loose tool schemas, stack traces returned to LLM, trusting LLM-generated tool args, unbounded waits |
| 3 | **Loop Control & Budgets** | CRITICAL | `loop` | Max iterations, step/token/cost budgets, wall-clock timeout, progress detection, circuit breakers | "Run until done", silent stop on cap, no cancel signal, repeated identical tool calls |
| 4 | **Retrieval Quality** | HIGH | `retrieval` | Hybrid + rerank, citations required, recall-floor on golden set, query rewriting, parent-doc retrieval | Fixed-size chunking, dense-only retrieval, no rerank, embedding model mismatch, no negative-result handling |
| 5 | **Eval & Observability** | HIGH | `evals` | Golden set required, regression on every change, traces, p95 latency, cost-per-query, drift monitoring | Mean-only metrics, eval on synthetic data only, no regression gate, untraced prod runs |
| 6 | **Cost & Latency** | HIGH | `cost` | Prompt caching, parallel tools, model routing, streaming, batch embeddings, cache retrievals | Sequential independent tool calls, no caching, always-large-model, embed-at-query-time |
| 7 | **Memory & Context** | MEDIUM | `memory` | Sliding window + recursive summarization, per-user isolation, context priority order, TTLs | Dumping full history every turn, no per-user namespacing, summarization without fidelity eval |
| 8 | **Agent Architecture** | MEDIUM | `architecture` | Single-agent default, ReAct for tools, plan-execute for sub-goals, explicit handoffs, sandboxed code exec | Multi-agent by default, implicit handoff state, agent loop when workflow suffices, unsandboxed code exec |
| 9 | **Prompt & Tool Description Quality** | MEDIUM | `prompt` | Role+goal first, when-not-what tool descs, structured output schemas, prompt version control, temp=0 for tools | Tool descs that only state "what", no few-shot for format, high temperature on tool calls |
| 10 | **Multi-Agent & Deployment** | LOW | `deployment` | Stateless serving, async for long tasks, vector DB matched to scale, model version canary, MCP under same auth | Sync HTTP for >30s agents, full reindex on every change, multi-agent without justification |

---

## Quick Reference

Embedded must-know rules per category. Each rule has a short slug for cross-referencing. Full pattern docs live in `knowledge/<domain>/`.

### 1. Safety & Guardrails (CRITICAL)

- `system-prompt-injection-defense` — Treat ALL retrieved content + tool outputs as untrusted; never let them override system instructions
- `input-validation` — Validate user input against schema before passing to LLM; reject oversized/malformed inputs
- `output-validation` — Validate LLM output against schema before acting; never auto-execute unvalidated outputs
- `pii-redaction` — Redact PII before logging traces and before sending to third-party models
- `secrets-isolation` — Never put API keys, credentials, or secrets in system prompts or tool descriptions
- `tool-allowlist` — Restrict tool access per user/role; default-deny dangerous tools (shell, file write, network)
- `confirmation-for-destructive` — Require human confirmation for destructive tool calls (delete, send, pay, deploy)
- `jailbreak-detection` — Pattern-detect known jailbreak phrases; log and reject suspicious inputs
- `content-policy` — Filter inputs and outputs against content policy (NSFW, illegal, harmful)
- `rate-limiting` — Rate-limit per user/IP to prevent abuse and runaway costs
- `audit-logging` — Log every tool call with user, timestamp, input, output, decision rationale
- `output-sanitization` — Sanitize markdown/HTML in user-facing LLM outputs; prevent XSS
- `data-exfiltration-defense` — Block tool calls that would exfiltrate sensitive data (PII in URLs, external network calls from tools handling secrets)
- `prompt-leakage-prevention` — Refuse requests asking for system prompt, tool list, or internal config
- `model-version-pinning` — Pin model version (e.g., `claude-opus-4-7`); never `latest`. Prevents silent behavior drift breaking guardrails

### 2. Tool Design & Error Handling (CRITICAL)

- `tool-schema-strict` — Use JSON Schema with strict types, required fields, enums; reject loose schemas
- `tool-description-when-not-what` — Tool description must state WHEN to use, not just WHAT it does
- `tool-idempotency` — Side-effecting tools must be idempotent or use idempotency keys
- `tool-retry-policy` — Retry transient failures with exponential backoff; cap at 3 retries
- `tool-timeout` — Set explicit timeouts on every tool call; never wait forever
- `error-surface-actionable` — Return errors the LLM can reason about (specific code + recovery hint), not stack traces
- `partial-success-handling` — Tools that batch operations must return per-item success/failure
- `tool-input-validation-server-side` — Validate tool inputs server-side; never trust LLM-generated args
- `tool-result-truncation` — Truncate large tool outputs to fit context; preserve head + tail + summary marker
- `tool-naming-clarity` — Tool names should be `verb_noun`, snake_case, unambiguous (`search_docs`, not `search`)
- `parallel-tool-isolation` — Parallel tool calls must not share mutable state
- `mcp-over-custom` — Prefer MCP servers over custom tool implementations for portability + auth reuse
- `tool-permission-scopes` — Tools should request narrow scopes (read-only vs read-write); least-privilege default
- `dry-run-mode` — Destructive tools should support dry-run / preview mode
- `tool-result-typed` — Tool results should be typed (JSON Schema), not raw strings
- `error-as-data` — Return errors as structured data inside the tool result, not as exceptions

### 3. Loop Control & Budgets (CRITICAL)

- `max-iterations` — Cap agent loops at N iterations (typically 10–20); error out with diagnostic, don't silently stop
- `step-budget` — Budget LLM calls per session; abort and report when exceeded
- `token-budget` — Track input + output tokens per session; abort when over ceiling
- `cost-budget` — Track $ per session; abort when over user-set ceiling
- `wall-clock-timeout` — Hard timeout per agent invocation (typically 60–300s)
- `progress-detection` — Detect when agent is looping without progress (same state across iterations); abort with diagnostic
- `infinite-loop-guard` — Detect repeated identical tool calls; break and ask user
- `early-termination-signals` — Allow user to cancel mid-execution; check cancel token between steps
- `circuit-breaker` — After N consecutive tool errors, stop and ask user
- `goal-completion-check` — Explicit "are we done?" check at each step, not just running until LLM stops
- `state-checkpoint` — Persist agent state at each step so cancellation/crash is recoverable
- `recursion-depth-limit` — Cap recursion depth in multi-agent handoffs (typically ≤3)
- `degenerate-output-detection` — Detect when LLM output is low-information (repetitive, off-topic); abort
- `human-in-loop-trigger` — Escalate to human when uncertainty/cost/risk exceeds threshold
- `cost-projection-prompt` — Estimate cost before starting long-running agents; confirm with user when over $X

### 4. Retrieval Quality (HIGH)

- `chunking-by-structure` — Chunk on semantic boundaries (paragraphs, sections, code blocks), not fixed token counts
- `chunk-overlap` — 10–20% overlap between chunks to preserve context across boundaries
- `parent-document-retrieval` — Index small chunks, return parent context on retrieval
- `hybrid-search` — Combine BM25 (lexical) + dense (semantic) retrieval; fuse with RRF or weighted score
- `reranking` — Rerank top-50 with cross-encoder before sending top-5 to LLM (Cohere, BGE)
- `query-rewriting` — Rewrite user query for retrieval (expand abbreviations, add context from chat history)
- `multi-query-retrieval` — Generate N query variants, retrieve for each, dedupe results
- `hyde` — Generate hypothetical answer, embed it, retrieve similar docs (when query is short/vague)
- `metadata-filtering` — Pre-filter by metadata (date, source, type) before semantic search
- `embedding-model-match` — Use the same embedding model for query and corpus; never mix
- `embedding-domain-fit` — Use domain-tuned embeddings (legal, medical, code) when available
- `recall-floor` — Measure recall@k on golden set; reject pipelines below threshold (e.g., recall@10 > 0.85)
- `citation-required` — Every LLM answer must cite source chunks; reject uncited answers
- `freshness-aware` — Boost recent docs for time-sensitive queries; penalize stale data
- `negative-results-handling` — When no good matches, say "I don't know"; don't force a low-quality answer
- `chunk-context-prepend` — Prepend doc title / section path to chunk text before embedding
- `query-classification` — Classify query type (factual/conceptual/procedural); route to different retrieval strategies
- `dedup-near-duplicates` — Dedupe chunks with high similarity before sending to LLM
- `colbert-late-interaction` — Use ColBERT-style late interaction for token-level matching on technical text
- `agentic-retrieval` — Let the agent iteratively refine retrieval (search → read → refine query → search again)

### 5. Eval & Observability (HIGH)

- `golden-set-required` — Build a 50–200 example golden set BEFORE optimizing anything
- `regression-on-every-change` — Run golden set on every prompt/model/pipeline change; block on regressions
- `ragas-context-recall` — Measure context-recall (Ragas) for RAG; ship when > 0.85
- `ragas-faithfulness` — Measure answer-faithfulness; ship when > 0.9
- `llm-as-judge` — Use stronger model as judge; calibrate against human labels
- `pairwise-comparison` — When optimizing, compare A/B side-by-side rather than absolute scores
- `trace-every-run` — Log full trace (prompts, tool calls, retrievals, decisions) for every production run
- `observability-platform` — Use LangSmith / Phoenix / Helicone / Langfuse for trace inspection
- `metric-distribution-not-mean` — Look at p50/p95/p99, not just mean; tail latency/quality matters
- `drift-monitoring` — Monitor input/output distributions in prod; alert on drift
- `cost-per-query-tracking` — Track $/query; alert when over budget
- `latency-budget-tracking` — Track p95 latency; alert on regressions
- `error-rate-monitoring` — Track tool error rate, refusal rate, fallback rate
- `user-feedback-loop` — Capture thumbs-up/down on outputs; feed into golden set
- `eval-on-real-data` — Use real production samples in golden set, not synthetic
- `adversarial-eval` — Include jailbreak attempts, edge cases, adversarial inputs in eval set
- `human-spot-check` — Sample 5% of prod outputs for human review weekly
- `staging-shadow-traffic` — Mirror prod traffic to staging for safe testing
- `version-tag-outputs` — Tag every output with model/prompt/pipeline version for debugging

### 6. Cost & Latency (HIGH)

- `prompt-caching` — Cache prompt prefixes (system prompt, retrieved context) to cut cost up to 90%
- `parallel-tool-calls` — Issue independent tool calls in parallel, not serially
- `streaming-output` — Stream output for perceived latency; show first token < 500ms
- `model-routing` — Route simple queries to small model (Haiku), complex to large (Opus/Sonnet)
- `batch-embeddings` — Batch embedding requests (100s per call) instead of one-by-one
- `cache-retrievals` — Cache retrieval results for repeated queries (TTL 1h–24h)
- `cache-final-answers` — Cache final LLM answers for popular queries (with semantic dedup)
- `tool-result-caching` — Cache idempotent tool results within a session
- `truncate-context-aggressively` — Trim retrieved context to what's needed; long context = slow + expensive
- `async-non-critical` — Move non-critical work (logging, eval, indexing) to async queues
- `pre-compute-embeddings` — Embed corpus offline; don't embed at query time
- `cdn-static-prompts` — CDN-cache static prompt templates
- `request-coalescing` — Deduplicate concurrent identical requests
- `early-exit-on-confidence` — Exit early when LLM signals high confidence; don't always run full chain
- `cheap-classifier-first` — Use cheap classifier (BERT, regex) before invoking LLM when applicable
- `cold-start-mitigation` — Keep models warm in serverless deployments

### 7. Memory & Context (MEDIUM)

- `sliding-window-history` — Keep last N turns verbatim; summarize older history
- `recursive-summarization` — Summarize in tiers (recent verbatim → mid summary → ancient meta-summary)
- `episodic-memory-store` — Store named facts/preferences in vector store; retrieve per query
- `long-term-vs-working-memory` — Separate per-session working memory from cross-session long-term memory
- `context-budget-allocation` — Allocate context window: system + history + retrieval + tool results; enforce limits
- `context-priority-order` — System prompt first, then retrievals, then history (most → least stable)
- `memory-conflict-resolution` — When stored memories conflict, prefer recent or ask user
- `memory-expiry` — Set TTL on memories; stale facts should decay
- `entity-extraction-for-memory` — Extract entities (names, dates, preferences) from conversations into structured memory
- `memory-isolation-per-user` — Strict per-user memory namespacing; never leak across users
- `summarization-fidelity-eval` — Validate summaries preserve key facts; eval against original
- `context-injection-from-memory` — Inject memories only when retrieval signals relevance
- `forget-on-request` — Honor user "forget that" requests; delete from memory store
- `memory-write-on-explicit-signal` — Don't auto-write everything to memory; require explicit signal

### 8. Agent Architecture (MEDIUM)

- `single-agent-default` — Default to single agent; only add agents when sub-tasks are truly orthogonal
- `react-for-simple-tools` — Use ReAct (think→act→observe) for multi-step tool tasks
- `plan-execute-for-complex` — Use plan-then-execute when task has clear sub-goals known in advance
- `orchestrator-worker-for-parallel` — Use orchestrator+workers when sub-tasks are independent and parallelizable
- `multi-agent-only-when-justified` — Multi-agent adds complexity; justify with measurable eval improvement
- `handoff-explicit-state` — Agent handoffs must pass explicit state; never rely on implicit context
- `supervisor-with-budget` — Supervisor agent should enforce per-worker budget (steps, cost)
- `reflection-when-cheap` — Add reflection step when single-shot quality is insufficient AND latency budget allows
- `tree-of-thoughts-rare` — ToT is expensive; use only for high-stakes reasoning with clear branching
- `agent-as-tool` — Expose sub-agents as tools to a parent agent for composability
- `code-execution-sandbox` — Code-writing agents must run code in sandbox (e2b, modal, daytona); never on host
- `no-agent-for-deterministic` — Don't use an agent when a deterministic pipeline works
- `streaming-thoughts-for-ux` — Stream agent's intermediate thinking for long-running tasks
- `agent-loop-vs-workflow` — Agent loop for open-ended; workflow for fixed steps

### 9. Prompt & Tool Description Quality (MEDIUM)

- `system-prompt-role-first` — Open system prompt with explicit role and goal in one sentence
- `system-prompt-constraints-explicit` — List hard constraints (do not / must) before nice-to-haves
- `tool-description-when-not-what` — Tool descriptions must answer "when to use this", not just what it does
- `tool-description-examples` — Include 1–2 example invocations in tool description
- `few-shot-for-format` — Use few-shot examples when output format matters; instructions alone are unreliable
- `xml-tags-for-structure` — Use XML tags (`<context>`, `<question>`) to structure prompt sections (esp. for Claude)
- `chain-of-thought-explicit` — Ask for reasoning explicitly before answer when accuracy matters
- `output-format-schema` — Specify output schema (JSON); use structured-output APIs when available
- `negative-examples-when-needed` — Include "do not do X" with example when LLM keeps making a specific mistake
- `prompt-version-control` — Version prompts in git; tag with deployed version
- `prompt-eval-before-deploy` — Run golden set against new prompt before rolling out
- `temperature-low-for-tools` — Use temperature 0 (or low) for tool-calling agents
- `temperature-higher-for-creative` — Higher temperature for creative tasks only
- `system-prompt-shorter-better` — Shorter system prompts often outperform longer; trim ruthlessly

### 10. Multi-Agent & Deployment (LOW)

- `vector-db-choice-by-scale` — pgvector for <1M chunks, Qdrant/Weaviate for 1M–100M, Pinecone/Vespa for 100M+
- `vector-db-managed-vs-self` — Managed (Pinecone) for fast start; self-hosted (Qdrant) for cost at scale
- `serving-stateless` — Keep agent endpoints stateless; persist state in DB/cache
- `agent-as-async-task` — Long-running agents (>30s) should be async tasks (Celery, SQS, Inngest), not sync HTTP
- `health-check-shallow-deep` — Both shallow (process alive) and deep (LLM reachable) health checks
- `graceful-degradation` — Fall back to cached/cheaper paths when LLM unavailable
- `circuit-break-on-llm-outage` — Circuit-break LLM calls; return degraded mode on sustained errors
- `model-version-canary` — Canary new model versions on 5% traffic before full rollout
- `mcp-server-deployment` — Deploy MCP servers behind same auth/observability as main service
- `multi-region-failover` — Multi-region LLM provider failover for production
- `pricing-tier-routing` — Route by user tier (free → small model, paid → large)
- `quota-per-user` — Per-user quota enforcement; degrade or queue when exceeded
- `embeddings-versioning` — Tag corpus embeddings with model version; reindex when changing models
- `index-rebuild-strategy` — Incremental index updates for new docs; full rebuild on embedding model change

---

## Prerequisites

Check if Python is installed:

```bash
python3 --version || python --version
```

If Python is not installed, install based on OS:

**macOS:**
```bash
brew install python3
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install python3 python3-pip
```

**Windows:**
```powershell
winget install Python.Python.3.12
```

Search dependencies (BM25):
```bash
pip install rank-bm25 pyyaml
```

---

## How to Use This Skill

Use this skill when the user requests any of the following:

| Scenario | Trigger Examples | Start From |
|---|---|---|
| **New agent / RAG system** | "Build an agent that does X", "Set up RAG over my docs" | Step 1 → Step 2 (`--recommend`) |
| **New tool / MCP server** | "Add a tool that calls our API", "Build an MCP server" | Step 3 (`--domain tools`) |
| **Choose framework** | "LangGraph or Claude Agent SDK?", "Which agent framework should I use?" | Step 4 (`--framework`) |
| **Choose vector DB / embedder / reranker** | "Pinecone vs Qdrant?", "Which embedding model?" | Step 3 (`--domain retrieval` or `--domain deployment`) |
| **Add guardrails / safety** | "Defend against prompt injection", "Add PII redaction" | Step 3 (`--domain safety`) |
| **Add evals** | "How do I measure if my RAG is good?", "Set up Ragas" | Step 3 (`--domain evals`) |
| **Reduce cost / latency** | "My agent is expensive / slow", "Add caching" | Step 3 (`--domain cost`) |
| **Fix agent bug** | "Agent is looping", "Tool keeps failing", "Bad retrieval" | Quick Reference → relevant section |
| **Production readiness review** | "Is this ready to ship?", "Review my agent before deploy" | Pre-Delivery Checklist below |
| **Migrate framework** | "Move from LangChain to LangGraph", "Port to Claude Agent SDK" | Step 4 (`--framework`) on both, diff |

Follow this workflow:

### Step 1 — Analyze the request

Extract structured constraints from the user's message:

- **Problem type**: agent (single/multi), RAG, tool integration, eval setup, deployment, debugging
- **Domain(s)**: which of the 10 priority categories apply (often 2–3 at once)
- **User level**: beginner (plain English) vs experienced (uses jargon like "RRF fusion", "ToT")
- **Framework preference**: if user named one, use it; else pick in Step 4
- **Constraints**: latency budget, scale (queries/day, docs in corpus), cost ceiling, LLM choice, data sensitivity, deployment target

### Step 2 — Generate Full Recommendation (REQUIRED)

Always start with `--recommend` for a complete, prescriptive recommendation spanning all relevant domains:

```bash
python3 .claude/skills/agent-forge/scripts/search.py "<reconstructed query>" --recommend [-p "Project Name"]
```

This:
1. Searches all 10 domains in parallel with BM25 ranking
2. Applies framework matching from `knowledge/frameworks/`
3. Pulls relevant anti-patterns from `knowledge/anti-patterns/`
4. Returns a complete recommendation: architecture + retrieval (if RAG) + safety + tools + evals + deployment notes

**Example:**
```bash
python3 .claude/skills/agent-forge/scripts/search.py "RAG over 10k engineering docs low latency Claude" --recommend -p "DocsBot"
```

### Step 2b — Persist Recommendation (Master + Feature Pattern)

To save the recommendation for cross-session reuse, add `--persist`:

```bash
python3 .claude/skills/agent-forge/scripts/search.py "<query>" --recommend --persist -p "Project Name"
```

This creates:
- `agent-system/MASTER.md` — Global recommendations with all chosen patterns, guardrails, evals
- `agent-system/features/` — Folder for feature-specific overrides

**With feature-specific override:**
```bash
python3 .claude/skills/agent-forge/scripts/search.py "<query>" --recommend --persist -p "Project Name" --feature "search"
```

Creates `agent-system/features/search.md` with deviations from MASTER.

**Hierarchical retrieval pattern:**
When building a specific feature, first check `agent-system/features/<feature>.md`. If it exists, its rules override `agent-system/MASTER.md`. Otherwise use MASTER exclusively.

### Step 3 — Supplement with Domain Searches (as needed)

After the full recommendation, dig into specific domains:

```bash
python3 .claude/skills/agent-forge/scripts/search.py "<keyword>" --domain <domain> [-n <max_results>]
```

**When to use each domain:**

| Need | Domain | Example |
|---|---|---|
| Guardrails, prompt injection, PII | `safety` | `--domain safety "prompt injection defense"` |
| Tool schemas, MCP, error handling | `tools` | `--domain tools "mcp server design"` |
| Loop control, budgets, infinite loops | `loop` | `--domain loop "agent infinite loop guard"` |
| Chunking, hybrid, rerank, embeddings | `retrieval` | `--domain retrieval "hybrid search rerank"` |
| Ragas, golden sets, LLM judge | `evals` | `--domain evals "golden set construction"` |
| Caching, parallel tools, model routing | `cost` | `--domain cost "prompt caching"` |
| Summarization, episodic, context mgmt | `memory` | `--domain memory "long term episodic memory"` |
| ReAct, plan-execute, multi-agent | `architecture` | `--domain architecture "plan execute"` |
| System prompts, tool descs, few-shot | `prompt` | `--domain prompt "tool description writing"` |
| Vector DB, serving, scaling, observability | `deployment` | `--domain deployment "vector db scale"` |

### Step 4 — Framework Guidelines

Get framework-specific implementation guidance:

```bash
python3 .claude/skills/agent-forge/scripts/search.py "<pattern>" --framework <framework>
```

**Available frameworks:**

| Framework | Best For |
|---|---|
| `claude-agent-sdk` | Anthropic ecosystem, tool use + MCP, computer use, agentic coding |
| `langgraph` | Stateful agent graphs, complex multi-step flows, persistence |
| `langchain` | Broad ecosystem, lots of integrations, prototyping |
| `llamaindex` | RAG-first, sophisticated indexing, document QA |
| `openai-agents-sdk` | OpenAI ecosystem, simple agent loops, handoffs |
| `pydantic-ai` | Type-safe agents in Python, structured outputs |
| `crewai` | Multi-agent role-play, sequential/parallel crews |

---

## Search Reference

### Available Domains

| Domain | Use For | Example Keywords |
|---|---|---|
| `safety` | Guardrails, prompt injection, PII, content policy, audit | injection, jailbreak, redaction, content policy |
| `tools` | Tool schemas, MCP, function calling, error handling | mcp, function calling, tool schema, retries |
| `loop` | Loop control, budgets, termination, circuit breakers | infinite loop, max steps, budget, timeout |
| `retrieval` | RAG patterns: chunking, hybrid, rerank, embeddings | chunking, hybrid, rerank, hyde, colbert |
| `evals` | Eval frameworks, golden sets, observability | ragas, golden set, llm judge, regression |
| `cost` | Cost/latency optimization, caching, routing | prompt caching, parallel tools, model routing |
| `memory` | Memory patterns, summarization, episodic | sliding window, summarization, episodic |
| `architecture` | Agent architectures and reasoning loops | react, plan execute, orchestrator, multi-agent |
| `prompt` | Prompt engineering, system prompts, few-shot | system prompt, few shot, xml tags, structured output |
| `deployment` | Production infra, vector DBs, serving | vector db, async, canary, observability |

### Available Frameworks

| Framework | Language | Stage | Strength |
|---|---|---|---|
| `claude-agent-sdk` | Python, TS | Stable | Anthropic-native, MCP-first, computer use |
| `langgraph` | Python, TS | Stable | Stateful graphs, persistence, debugging |
| `langchain` | Python, TS | Stable | Largest ecosystem, prototyping |
| `llamaindex` | Python, TS | Stable | RAG indexing depth |
| `openai-agents-sdk` | Python | Stable | OpenAI-native, simple loops |
| `pydantic-ai` | Python | Stable | Type safety, structured outputs |
| `crewai` | Python | Stable | Multi-agent role orchestration |

---

## Example Workflow

**User request:** "Build a RAG chatbot over 50k internal engineering wiki pages. Needs to cite sources, be cheap, and answer fast. Using Claude."

### Step 1 — Analyze

- **Problem type**: RAG pipeline
- **Domains**: `retrieval` (primary), `cost`, `evals`, `safety` (citation requirement implies grounding)
- **User level**: experienced (says "RAG", "cite sources", knows what they want)
- **Framework**: not specified — will pick LlamaIndex or Claude Agent SDK
- **Constraints**: 50k docs (medium scale), cost-sensitive, latency-sensitive, Claude as LLM, citation required

### Step 2 — Generate Full Recommendation

```bash
python3 .claude/skills/agent-forge/scripts/search.py "RAG 50k engineering wiki citations Claude cheap fast" --recommend -p "WikiBot"
```

Output (synthesized response Claude produces):

```
## Recommendation
Use LlamaIndex with hierarchical chunking (section-aware) + hybrid BM25/dense retrieval + Cohere rerank-3, Claude Haiku for generation, Anthropic prompt caching on the system prompt + retrieved context. Store chunks in pgvector.

## Why this for your case
- 50k docs = pgvector tier (no need for Pinecone)
- Hierarchical chunking + section-aware preserves wiki structure for accurate citations
- Hybrid + rerank lifts recall@5 by ~20% on technical text vs dense-only
- Haiku + prompt caching gives sub-second latency at ~$0.001/query

## Code
[LlamaIndex scaffold with pgvector, BGE-base embeddings, BM25Retriever, CohereRerank, ChatAnthropic]

## Avoid
- Embedding entire wiki pages (chunk-context-prepend, chunking-by-structure)
- Skipping the reranker on technical text (reranking)
- Mixing embedding models between corpus and query (embedding-model-match)
- Returning answers without citations (citation-required)
- Calling embedding API at query time (pre-compute-embeddings)

## How to know it's working
Build a 30-question golden set from real wiki support tickets. Measure context-recall (Ragas) and citation-precision. Ship when both > 0.85.

## Deeper reading
- knowledge/retrieval/hybrid-search.md — fusion strategy details
- knowledge/retrieval/parent-document-retrieval.md — section-aware citation
- knowledge/cost/prompt-caching.md — Anthropic caching specifics
- knowledge/evals/ragas-setup.md — Ragas golden-set walkthrough
```

### Step 3 — Supplement (if user asks follow-ups)

If user asks "what about citations specifically?":
```bash
python3 .claude/skills/agent-forge/scripts/search.py "citation grounding source attribution" --domain retrieval
```

### Step 4 — Framework Deep-Dive (if user wants code)

```bash
python3 .claude/skills/agent-forge/scripts/search.py "rag hybrid rerank pgvector" --framework llamaindex
```

---

## Output Formats

`--recommend` supports two output formats:

```bash
# Markdown (default) — best for IDE/docs
python3 .claude/skills/agent-forge/scripts/search.py "agentic coding assistant" --recommend

# ASCII (compact) — best for terminal
python3 .claude/skills/agent-forge/scripts/search.py "agentic coding assistant" --recommend -f ascii
```

---

## Tips for Better Results

### Query Strategy

- Use **multi-dimensional keywords** — combine domain + scale + constraints + framework: `"RAG 100k legal docs low latency LlamaIndex"`, not just `"RAG"`
- Try different keywords for the same need: `"agent looping"` → `"infinite loop guard"` → `"max iterations budget"`
- Start with `--recommend` for full picture, then `--domain` to deep-dive any single dimension
- Add `--framework <name>` for implementation-specific code

### Common Sticking Points

| Problem | What to Do |
|---|---|
| Agent loops without finishing | Quick Reference §3: `max-iterations` + `progress-detection` + `infinite-loop-guard` |
| RAG hallucinates / makes things up | Quick Reference §4: `citation-required` + `negative-results-handling` + `reranking` |
| Agent is expensive | Quick Reference §6: `prompt-caching` + `model-routing` + `cache-retrievals` |
| Agent is slow | Quick Reference §6: `parallel-tool-calls` + `streaming-output` + `truncate-context-aggressively` |
| Tool calls keep failing | Quick Reference §2: `error-surface-actionable` + `tool-retry-policy` + `tool-input-validation-server-side` |
| Don't know if RAG is "good enough" | Quick Reference §5: `golden-set-required` + `ragas-context-recall` + `ragas-faithfulness` |
| Prompt injection / jailbreak fears | Quick Reference §1: `system-prompt-injection-defense` + `output-validation` + `tool-allowlist` |
| Can't decide between frameworks | Run `--framework` on each, compare on user's actual constraints |
| Multi-agent feels overcomplicated | Quick Reference §8: `single-agent-default` + `multi-agent-only-when-justified` |
| Memory grows unbounded / costs explode | Quick Reference §7: `sliding-window-history` + `recursive-summarization` + `memory-expiry` |

### Pre-Implementation Checklist

Before writing agent code, confirm:
- [ ] Run `--recommend` and review the full recommendation
- [ ] Quick Reference §1–§3 (CRITICAL) reviewed for relevance to your case
- [ ] Framework choice justified (not picked by familiarity alone)
- [ ] Vector DB choice matches scale (`vector-db-choice-by-scale`)
- [ ] Cost/latency budget defined BEFORE writing code
- [ ] Eval plan exists (`golden-set-required`)

---

## Pre-Delivery Checklist

Before shipping an agent or RAG system to production, verify:

### Safety & Guardrails (CRITICAL)
- [ ] Model version pinned (no `latest`)
- [ ] Input validation on user requests (size, schema)
- [ ] Output validation before any tool execution
- [ ] Prompt-injection defense applied to retrieved content and tool outputs
- [ ] PII redacted from logs and third-party model calls
- [ ] Secrets not in system prompts or tool descriptions
- [ ] Tool allowlist per user/role
- [ ] Destructive actions require confirmation
- [ ] Audit log captures every tool call
- [ ] Rate limiting in place

### Tool Design (CRITICAL)
- [ ] All tool inputs validated server-side (not just LLM-trusted)
- [ ] Tool schemas use strict JSON Schema with required fields and enums
- [ ] Every tool call has an explicit timeout
- [ ] Retries with exponential backoff (cap at 3)
- [ ] Errors returned as structured data, not stack traces
- [ ] Idempotency for side-effecting tools
- [ ] Tool result truncation for large outputs

### Loop Control (CRITICAL)
- [ ] Max iterations cap (typically 10–20)
- [ ] Step budget, token budget, cost budget all enforced
- [ ] Wall-clock timeout per invocation
- [ ] Infinite loop detection (repeated identical tool calls)
- [ ] Cancel signal honored
- [ ] State checkpointed for recovery

### Retrieval Quality (if RAG)
- [ ] Hybrid retrieval + reranker
- [ ] Recall@k > 0.85 on golden set
- [ ] Citations required in every answer
- [ ] Negative-result handling (says "I don't know" when no good match)
- [ ] Embedding model matched between query and corpus

### Eval & Observability
- [ ] Golden set built (50–200 examples)
- [ ] Regression gate on every prompt/model/pipeline change
- [ ] Full traces logged in prod (LangSmith / Phoenix / Langfuse)
- [ ] p95 latency tracked
- [ ] Cost-per-query tracked
- [ ] Error rate + refusal rate monitored
- [ ] User feedback loop (thumbs-up/down)
- [ ] Outputs version-tagged

### Cost & Latency
- [ ] Prompt caching enabled on stable prompt prefixes
- [ ] Independent tool calls run in parallel
- [ ] Streaming output to client
- [ ] Model routing (small for simple, large for complex)
- [ ] Retrieval cached for popular queries
- [ ] Context aggressively truncated to fit

### Memory (if persistent)
- [ ] Per-user memory namespacing strict
- [ ] Sliding window + summarization on long conversations
- [ ] Memory TTL set
- [ ] User "forget" requests honored
- [ ] Context budget allocated explicitly

### Deployment
- [ ] Stateless serving (state in DB/cache, not process memory)
- [ ] Long-running agents are async tasks
- [ ] Shallow + deep health checks
- [ ] Graceful degradation when LLM unavailable
- [ ] Circuit breaker on sustained LLM errors
- [ ] New model versions canaried before full rollout

---

## Common Rules for Production Agents

Frequently overlooked issues that make agents fragile in production.

### Tool Design

| Rule | Standard | Avoid | Why |
|---|---|---|---|
| **Tool description states WHEN** | "Use this when the user asks about X" + 1 example | "Searches the database" (only WHAT) | LLM picks wrong tools when descriptions don't disambiguate |
| **Idempotency keys on writes** | Side-effecting tools accept and honor idempotency-key | Tool blindly creates duplicate records on retry | LLMs retry; non-idempotent tools cause duplicates |
| **Server-side input validation** | Tool validates types, ranges, allowed values BEFORE acting | Trusting LLM-generated JSON args | LLMs hallucinate plausible-but-wrong args (wrong types, made-up IDs) |
| **Errors as structured data** | `{"error": "rate_limited", "retry_after": 30}` returned in tool result | Throwing exception or returning stack trace | LLM can't recover from opaque errors; structured errors guide retry |
| **Tool timeout enforced** | Every tool has explicit timeout (5–30s typical) | "It'll return eventually" | Hanging tools block the agent and exhaust budget |
| **MCP for external tools** | Wrap third-party APIs as MCP servers | Custom inline integrations per agent | MCP gives auth/observability reuse + portability |

### Loop Safety

| Rule | Do | Don't |
|---|----|----|
| **Max iterations** | Hard cap (10–20) + diagnostic error on hit | Run until LLM says "done" |
| **Step budget** | Track + enforce per session | Budget-free agents in prod |
| **Cancel signal** | Check between every step | Ignore until next API boundary |
| **Progress detection** | Compare state across iterations; abort if unchanged | Trust agent to detect its own stuck state |
| **Cost cap** | Estimate before, abort over | Discover cost after the bill |

### Retrieval Quality

| Rule | Do | Don't |
|---|----|----|
| **Hybrid retrieval** | BM25 + dense fused with RRF | Dense-only "because semantic" |
| **Always rerank** | Cross-encoder on top-50 → top-5 to LLM | Send top-k embeddings directly to LLM |
| **Citations required** | Every claim cites a source chunk | Free-form generation over retrieved context |
| **Chunk by structure** | Section/paragraph boundaries | Fixed token-count splits |
| **Eval first** | Golden set + recall floor before shipping | Vibes-based "looks good" review |

### Eval & Observability

| Rule | Do | Don't |
|---|----|----|
| **Golden set first** | 50–200 examples from real data, manually labeled | Optimize before measuring |
| **Regression gate** | Run golden set on every change; block on regressions | Manual spot-checks |
| **Trace everything** | Full prompt + tool calls + retrievals in trace platform | Console logs only |
| **Distribution metrics** | p50/p95/p99 for latency + quality | Mean only |
| **Real data in eval set** | Sample from production | Synthetic eval set only |

### Cost & Latency

| Rule | Do | Don't |
|---|----|----|
| **Prompt caching** | Cache stable system prompts + retrieved context | Pay full price on every request |
| **Parallel tool calls** | Issue concurrent for independent operations | Serial when tools have no dependencies |
| **Model routing** | Haiku/Sonnet for simple, Opus for complex | Always-Opus by default |
| **Stream output** | First token < 500ms perceived latency | Wait for full response |
| **Cache retrievals** | TTL on retrieval results for popular queries | Re-embed and re-retrieve identical queries |

---

## Knowledge Base Contract

- **Source of truth:** `knowledge/` under this skill's directory
- **Format:** one `.md` file per pattern with YAML frontmatter (`name`, `category`, `difficulty`, `when_to_use`, `frameworks`, `related`, `anti_patterns`, `tags`) + body
- **Search entry point:** `scripts/search.py` — always invoke through it; do not grep `knowledge/` directly except to verify a specific file exists
- **Framework profiles:** `knowledge/frameworks/` — one file per supported framework with strengths/weaknesses/when-to-pick
- **Anti-patterns:** `knowledge/anti-patterns/` — cross-cutting, pulled into every recommendation

If you discover a useful pattern that is not in `knowledge/`, do not invent it inline. Tell the user it is missing, give the best recommendation from what exists, and suggest adding it as a new file.

---

## Output Template (mandatory structure for every response)

Every response this skill produces follows this shape exactly:

```
## Recommendation
<one sentence — the prescription. Name the pattern + the framework.>

## Why this for your case
- <bullet tying to a constraint the user stated>
- <bullet tying to another constraint>
- <bullet tying to a third>

## Code
<runnable snippet in the recommended framework, imports included, key knobs labeled>

## Avoid
- <anti-pattern from knowledge/anti-patterns/>
- <anti-pattern>
- <anti-pattern — 3–5 total>

## How to know it's working
<one starter eval: golden set + 1–2 metrics + interpretation rule>

## Deeper reading
- knowledge/<domain>/<file>.md — <one-line why>
- knowledge/<domain>/<file>.md — <one-line why>
```

For beginners (inferred from plain-English phrasing), insert a **What this means** gloss after the **Recommendation** — 2 sentences, no jargon. Skip for experienced users.

---

## Personality Rules

- **Pick one path.** Never say "it depends" unless the user gave genuinely conflicting constraints. If conflicting, ask ONE targeted question and stop.
- **Name the framework.** Don't list options. Pick based on stack, level, and `knowledge/frameworks/` fit.
- **No hedging language** — strike "you might want to consider", "perhaps", "it could be worth". Replace with direct instruction.
- **Cite the knowledge file** when making a claim, so user can verify.
- **One clarifying question maximum** before committing to a recommendation. Don't interrogate.

---

## Boundaries

Do NOT activate or take over for:

- General coding questions unrelated to LLMs / agents
- Pure prompt-engineering questions with no agent/retrieval/tool dimension
- LLM training, fine-tuning, RLHF, model architecture internals
- UI/UX, frontend, or design questions
- Frameworks not in `knowledge/frameworks/`. If asked, say out-of-scope and recommend closest covered alternative.

If a request is in-domain but no pattern in `knowledge/` matches well, say so explicitly — do not fabricate.
