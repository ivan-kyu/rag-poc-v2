# Plan: rag-poc-v2 (Python + LangChain + LangSmith)

## Context

`rag-poc` is a polished TypeScript/Next.js RAG explorer with a live pipeline visualization (Supabase pgvector, OpenAI, NDJSON streaming, hybrid search). The user wants `rag-poc-v2` rebuilt around the modern Python AI stack as a serious learning + portfolio project that:

- Uses **LangChain + LangGraph** for the RAG pipeline.
- Has **LangSmith** observability + evals (online + RAGAS offline).
- Demonstrates **ChromaDB** experience while keeping a path to deploy on **Vercel + Supabase (pgvector)**.
- Showcases multiple modern RAG techniques (hybrid, reranking, multi-query, HyDE, routing) toggleable from the UI to compare results.
- Visualizes the full pipeline live, like v1 but richer (LangGraph node-level events).

The rebuild lives in a new sibling directory `rag-poc-v2/`; v1 is left untouched.

## High-Level Architecture

```
rag-poc-v2/
├── backend/                        # Python (uv-managed)
│   ├── app/
│   │   ├── main.py                 # FastAPI entry, CORS, SSE endpoints
│   │   ├── api/
│   │   │   ├── chat.py             # POST /api/chat - SSE stream of LangGraph events
│   │   │   ├── ingest.py           # POST /api/ingest - re-ingest knowledge base
│   │   │   ├── upload.py           # POST /api/upload - file upload (Supabase Storage)
│   │   │   ├── documents.py        # GET /api/documents - KB stats
│   │   │   └── evals.py            # POST /api/evals/run - trigger RAGAS eval
│   │   ├── rag/
│   │   │   ├── graph.py            # LangGraph StateGraph definition
│   │   │   ├── nodes.py            # Individual nodes (embed, retrieve, rerank, generate)
│   │   │   ├── retrievers.py       # Hybrid (BM25+vector), MultiQuery, HyDE, Compression
│   │   │   ├── routing.py          # Query classifier → branches
│   │   │   ├── prompts.py          # Prompt templates (LangChain Hub or local)
│   │   │   └── schemas.py          # Pydantic models: AnswerWithCitations, GraphState
│   │   ├── stores/
│   │   │   ├── base.py             # VectorStoreAdapter protocol
│   │   │   ├── chroma_store.py     # ChromaDB impl (default local)
│   │   │   └── pgvector_store.py   # Supabase pgvector impl (prod)
│   │   ├── ingestion/
│   │   │   ├── loaders.py          # PyPDFLoader, UnstructuredMarkdownLoader
│   │   │   ├── chunker.py          # RecursiveCharacterTextSplitter (+ semantic option)
│   │   │   └── pipeline.py         # ingest_documents() orchestrator
│   │   ├── evals/
│   │   │   ├── ragas_runner.py     # RAGAS metrics (faithfulness, answer_relevancy, context_precision/recall)
│   │   │   ├── datasets.py         # LangSmith dataset push/pull
│   │   │   └── online.py           # LangSmith online eval feedback hooks
│   │   ├── observability.py        # LangSmith client setup, run tagging
│   │   ├── settings.py             # Pydantic-settings (env config)
│   │   └── streaming.py            # SSE event formatter (LangGraph → SSE)
│   ├── tests/                      # pytest-asyncio
│   ├── pyproject.toml              # uv + Ruff + pytest
│   └── Dockerfile
├── frontend/                       # Next.js 16 (mirrors v1 layout)
│   ├── src/app/
│   │   ├── page.tsx                # Main 3-panel layout
│   │   └── api/                    # (proxy if needed; mostly direct backend calls)
│   ├── src/components/
│   │   ├── ChatPanel.tsx
│   │   ├── PipelinePanel.tsx       # Now shows LangGraph node graph + per-node data
│   │   ├── KnowledgeBasePanel.tsx
│   │   ├── TechniqueToggles.tsx    # NEW: enable/disable multi-query, HyDE, rerank, routing
│   │   ├── EvalPanel.tsx           # NEW: trigger RAGAS, show scores, link to LangSmith
│   │   └── GraphDiagram.tsx        # NEW: live LangGraph visualization (react-flow)
│   ├── package.json                # pnpm
│   └── next.config.ts
├── knowledge-base/                 # Same 5 markdown docs from v1, copied over (+ a couple PDFs to test)
├── infra/
│   ├── docker-compose.yml          # postgres+pgvector, chroma, redis, langsmith optional
│   └── supabase/migrations/        # pgvector init (port from v1)
├── .env.example
└── README.md
```

## Key Decisions

### Vector DB - swappable adapter

`stores/base.py` defines a thin `VectorStoreAdapter` protocol. Both implementations wrap LangChain's native `Chroma` and `PGVector` classes so we get `EnsembleRetriever`/reranker compatibility for free. Selection via `VECTOR_BACKEND=chroma|pgvector` env var.

- **Local dev default**: ChromaDB (persistent client, runs in-process or via docker-compose).
- **Production**: Supabase pgvector (uses LangChain's `langchain_postgres.PGVector`).
- Same ingestion pipeline writes to whichever is configured; switching backends just re-ingests.

### RAG techniques (full showcase, all in LangChain/LangGraph)

| Technique | LangChain primitive |
|-----------|---------------------|
| Naive vector retrieval | `vectorstore.as_retriever()` |
| Hybrid (BM25 + vector) | `EnsembleRetriever([BM25Retriever, vector_retriever])` |
| Multi-query rewriting | `MultiQueryRetriever.from_llm(...)` |
| HyDE | `HypotheticalDocumentEmbedder` + custom retriever |
| Reranking | `ContextualCompressionRetriever` with `CrossEncoderReranker` (default `BAAI/bge-reranker-base`); optional Cohere rerank if API key present |
| Query routing | LangGraph conditional edge: classifier node decides which retriever to use |
| Corrective RAG (stretch) | LangGraph cycle: grade retrieved chunks, re-query if low-grade |

Each technique is a toggle in the UI; the backend builds the LangGraph dynamically from the toggle set so users can compare answers/traces side-by-side.

### Pipeline = LangGraph StateGraph

```
classify_query → [retrieve_naive | retrieve_hybrid | retrieve_multiquery | retrieve_hyde]
              → rerank (optional) → grade_chunks (optional) → generate → emit_citations
```

`GraphState` is a Pydantic model: `query`, `query_embedding`, `route`, `retrieved_chunks`, `reranked_chunks`, `prompt`, `answer`, `citations`. Each node `astream_events()` emits SSE events to the frontend. LangGraph's structure matches the UI's pipeline visualization 1:1.

### Streaming

FastAPI endpoint returns `text/event-stream`. Subscribes to `graph.astream_events(version="v2")` and re-emits a typed event stream:

- `node_start` / `node_end` (with payload) for each LangGraph node
- `token` for streaming LLM output
- `done` with full structured answer

Frontend `EventSource`-style consumer feeds the pipeline panel, mirroring v1's NDJSON design but with richer node-level granularity.

### Structured output + citations

LangChain's `with_structured_output(AnswerWithCitations)` on the generation LLM (Pydantic model: `answer: str`, `citations: list[Citation]`, `confidence: float`). Stream tokens during draft, then validate final structure.

### Observability (LangSmith)

- `LANGCHAIN_TRACING_V2=true` + project name `rag-poc-v2`. Every LangGraph run auto-traced.
- Tag runs with technique-toggle metadata so traces are filterable by configuration.
- Online evaluators in LangSmith for hallucination / answer relevance.
- UI links each chat turn to its LangSmith trace URL.

### Evals (RAGAS + LangSmith datasets)

- Curated eval dataset (~20 Q/A pairs from the knowledge base) stored as a LangSmith dataset.
- `evals/ragas_runner.py` runs `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall` over the dataset for each technique config.
- `EvalPanel.tsx` triggers eval runs and renders a comparison table; results posted back to LangSmith.

### Tooling

- **uv** for Python deps + virtualenvs
- **Ruff** (lint + format)
- **pytest + pytest-asyncio + httpx** for backend tests
- **Pydantic v2** + `pydantic-settings` for config
- **pnpm** for frontend (per global instructions)
- **Docker Compose**: postgres+pgvector, chroma server, redis (optional cache)

### Caching (lightweight)

LangChain `set_llm_cache(SQLiteCache(...))` for LLM responses + `CacheBackedEmbeddings` for embeddings. SQLite local, swap to Redis in docker-compose later.

### Deployment path

- **Frontend**: Vercel (Next.js). Already aligns with global preferences.
- **Backend**: FastAPI does **not** stream cleanly on Vercel Python serverless (response buffering). Recommended targets: **Fly.io** or **Railway** (long-lived process, SSE works). Note this in README; document Vercel Functions as a non-streaming fallback.
- **Vector DB**: Supabase (pgvector) for prod via the swappable adapter; ChromaDB stays the local dev default.
- **Storage**: Supabase Storage (port v1's bucket logic).

## Files to create/port

**Port from v1 (logic, not code):**
- `knowledge-base/*.md` → copy verbatim
- `supabase/migrations/20260223000000_init_pgvector.sql` → adapt for `langchain_pg_embedding` schema
- Hybrid-search merging logic → replaced by `EnsembleRetriever`
- NDJSON event shape → translate to SSE events in `streaming.py`
- Frontend visual layout from `src/components/{ChatPanel,PipelinePanel,KnowledgeBasePanel}.tsx`

**Net new:**
- LangGraph definition + nodes
- Technique toggle wiring (backend dynamic graph builder + frontend toggles)
- Eval panel + RAGAS runner
- LangSmith trace links in UI
- React-flow LangGraph visualization

## Verification

1. **Local bring-up**: `docker compose up` then `cd backend && uv run uvicorn app.main:app --reload` and `cd frontend && pnpm dev`. Visit `http://localhost:3000`.
2. **Ingestion**: Hit `/api/ingest`, then `/api/documents` returns chunk counts matching `knowledge-base/`.
3. **Smoke chat**: Ask "What is RAG?" - SSE stream shows each LangGraph node firing in the pipeline panel; final answer cites at least one source.
4. **Backend swap**: Set `VECTOR_BACKEND=pgvector`, re-ingest, repeat smoke chat - identical UX, different store.
5. **Technique toggles**: Run the same query with naive vs hybrid+rerank+multi-query - pipeline panel shows different node sequences; LangSmith traces are tagged accordingly.
6. **LangSmith**: Confirm runs appear in the LangSmith project, traces link from the UI.
7. **Evals**: Trigger RAGAS run from EvalPanel - scores render in UI and post to LangSmith dataset feedback.
8. **Tests**: `uv run pytest` covers chunker, retriever assembly, graph wiring, schema validation.
9. **Lint**: `uv run ruff check . && uv run ruff format --check .` clean.

## Open follow-ups (not in initial scope)

- Corrective/self-RAG cycle (LangGraph already supports; add after baseline works)
- Semantic chunking via `SemanticChunker`
- Per-document permissions/multi-tenancy
- Production deploy automation (one-shot Fly.io + Vercel + Supabase)

---

## Implementation TODO (resumable checklist)

Each phase is independently testable. Mark items `[x]` as you complete them. If context fills, just re-read this file and the last completed item to resume.

### Phase 0 - Bootstrap

- [ ] Create `rag-poc-v2/` next to `rag-poc/`
- [ ] `git init` (parent already initialized 2026-04-27)
- [ ] Copy `rag-poc/knowledge-base/*.md` → `rag-poc-v2/knowledge-base/`
- [ ] Add 1-2 sample PDFs to `knowledge-base/` for PDF-path testing
- [ ] Create top-level `README.md` (architecture diagram + quickstart)
- [ ] Create `.env.example` with: `OPENAI_API_KEY`, `LANGCHAIN_API_KEY`, `LANGCHAIN_TRACING_V2`, `LANGCHAIN_PROJECT`, `VECTOR_BACKEND`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `COHERE_API_KEY` (optional), `CHROMA_PERSIST_DIR`
- [ ] Add `.gitignore` (Python: `.venv`, `__pycache__`, `.env`; Node: `node_modules`, `.next`)

### Phase 1 - Backend skeleton

- [ ] `cd backend && uv init --package` (uv-managed project)
- [ ] Add deps: `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `python-multipart`, `sse-starlette`, `langchain`, `langchain-openai`, `langchain-community`, `langchain-chroma`, `langchain-postgres`, `langgraph`, `langsmith`, `chromadb`, `pypdf`, `unstructured[md]`, `rank-bm25`, `sentence-transformers`, `ragas`, `redis`, `httpx`
- [ ] Dev deps: `ruff`, `pytest`, `pytest-asyncio`, `pytest-cov`
- [ ] Configure `pyproject.toml` with Ruff rules + pytest config
- [ ] `app/settings.py` - Pydantic-settings reading `.env`
- [ ] `app/main.py` - FastAPI app with CORS for `http://localhost:3000`
- [ ] Health endpoint `GET /health` returning `{status: "ok", backend: settings.vector_backend}`
- [ ] **Verify**: `uv run uvicorn app.main:app --reload` and `curl localhost:8000/health` → 200

### Phase 2 - Vector store adapter

- [ ] `app/stores/base.py` - `VectorStoreAdapter` Protocol (`add_documents`, `as_retriever`, `clear`, `count`)
- [ ] `app/stores/chroma_store.py` - wraps `langchain_chroma.Chroma` with persistent client
- [ ] `app/stores/pgvector_store.py` - wraps `langchain_postgres.PGVector`
- [ ] `app/stores/factory.py` - `get_vector_store()` reading `VECTOR_BACKEND`
- [ ] `infra/docker-compose.yml` - services: `postgres` (with pgvector image `pgvector/pgvector:pg16`), `chroma` (`chromadb/chroma`), `redis`
- [ ] `infra/supabase/migrations/0001_init_pgvector.sql` - enable pgvector extension (LangChain creates the table on first write)
- [ ] **Verify**: `docker compose up -d`, then a tiny script that adds 2 docs and queries with each backend

### Phase 3 - Ingestion pipeline

- [ ] `app/ingestion/loaders.py` - dispatch by extension: `.md` → `UnstructuredMarkdownLoader`, `.pdf` → `PyPDFLoader`
- [ ] `app/ingestion/chunker.py` - `RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)` (matches v1 numbers)
- [ ] `app/ingestion/pipeline.py` - `ingest_documents(source_dir, vector_store)`: load → split → embed → upsert; clear before re-ingest
- [ ] `CacheBackedEmbeddings` wrapping `OpenAIEmbeddings(model="text-embedding-3-small")` with local file store
- [ ] `app/api/ingest.py` - `POST /api/ingest` triggers pipeline; `GET /api/documents` returns per-source chunk counts
- [ ] `app/api/upload.py` - multipart upload, validates ext (md/pdf only), saves to Supabase Storage (or local `uploads/` if no Supabase configured), then re-ingests
- [ ] **Verify**: `curl -X POST localhost:8000/api/ingest`, then `GET /api/documents` shows expected sources/chunks for both backends

### Phase 4 - LangGraph pipeline (naive baseline)

- [ ] `app/rag/schemas.py` - `GraphState` (TypedDict or Pydantic), `Citation`, `AnswerWithCitations`
- [ ] `app/rag/prompts.py` - system prompt + context-block template (port v1's wording)
- [ ] `app/rag/nodes.py` - functions: `embed_query`, `retrieve`, `build_prompt`, `generate`
- [ ] `app/rag/graph.py` - `build_graph(config)` returns a compiled `StateGraph`; baseline = naive retrieval only
- [ ] `app/rag/schemas.py` - structured output `AnswerWithCitations` via `with_structured_output`
- [ ] `app/api/chat.py` - `POST /api/chat`: builds graph, runs `astream_events(version="v2")`, formats SSE
- [ ] `app/streaming.py` - LangGraph event → SSE event translator (`node_start`, `node_end`, `token`, `done`, `error`)
- [ ] **Verify**: `curl -N -X POST localhost:8000/api/chat -H "Content-Type: application/json" -d '{"question":"What is RAG?"}'` shows streaming SSE events with citations

### Phase 5 - Advanced retrieval techniques

- [ ] `app/rag/retrievers.py::build_hybrid()` - `EnsembleRetriever([BM25Retriever, vector_retriever], weights=[0.4, 0.6])`
- [ ] `app/rag/retrievers.py::build_multiquery()` - `MultiQueryRetriever.from_llm`
- [ ] `app/rag/retrievers.py::build_hyde()` - `HypotheticalDocumentEmbedder` + custom retriever
- [ ] `app/rag/retrievers.py::with_reranker()` - `ContextualCompressionRetriever` with `CrossEncoderReranker(BAAI/bge-reranker-base)`; opt Cohere if `COHERE_API_KEY` set
- [ ] `app/rag/routing.py` - LLM classifier node (`factual` vs `definition` vs `procedural`) → conditional edge to retriever
- [ ] Extend `build_graph(config: PipelineConfig)` so toggles compose nodes dynamically (multiquery → hyde → hybrid → rerank → generate)
- [ ] `PipelineConfig` schema accepted in `/api/chat` body: `{question, config: {hybrid, multi_query, hyde, rerank, route}}`
- [ ] **Verify**: Run same query with each toggle combo; confirm distinct retrieved-chunk sets and SSE node sequences

### Phase 6 - Observability (LangSmith)

- [ ] Set `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_PROJECT=rag-poc-v2` via env
- [ ] Tag every run with `metadata={"config": pipeline_config_dict}` so traces are filterable
- [ ] Include LangSmith run URL in the SSE `done` event payload
- [ ] **Verify**: Chat once → run appears in LangSmith with correct tags; URL opens trace

### Phase 7 - Evals (RAGAS + LangSmith datasets)

- [ ] `app/evals/datasets.py` - hand-curate 15-20 Q/A pairs from `knowledge-base/`; push as LangSmith dataset on first run
- [ ] `app/evals/ragas_runner.py` - run `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall` for a given `PipelineConfig`
- [ ] `app/api/evals.py` - `POST /api/evals/run` accepts config, returns scores + LangSmith run URL
- [ ] **Verify**: Trigger eval for naive vs full-stack configs; scores differ as expected; results visible in LangSmith

### Phase 8 - Frontend (Next.js)

- [ ] `cd frontend && pnpm create next-app@latest .` (App Router, TS, Tailwind, ESLint)
- [ ] Install shadcn/ui, lucide-react, react-hook-form, zod, react-flow (`@xyflow/react`), `eventsource-parser`
- [ ] Port v1 layout: `ChatPanel.tsx`, `PipelinePanel.tsx`, `KnowledgeBasePanel.tsx` (visual structure only - rewire APIs)
- [ ] `lib/sseClient.ts` - SSE consumer using `fetch` + `eventsource-parser`
- [ ] `components/TechniqueToggles.tsx` - switches for hybrid / multi-query / HyDE / rerank / route; sends `config` with each chat request
- [ ] `components/GraphDiagram.tsx` - react-flow renderer; nodes light up on `node_start` / `node_end` SSE events
- [ ] `components/EvalPanel.tsx` - trigger eval, render score table, link to LangSmith
- [ ] LangSmith trace link button on each chat turn
- [ ] **Verify (UI test in browser)**: ingestion → ask question → pipeline visualization animates → answer renders with citations → toggle a technique and re-ask → graph + answer change → trigger eval → scores render

### Phase 9 - Tests + tooling polish

- [ ] `tests/test_chunker.py` - chunk count + overlap invariants
- [ ] `tests/test_stores.py` - parametrized over chroma + pgvector
- [ ] `tests/test_graph.py` - graph compiles for all toggle combos; mocked LLM
- [ ] `tests/test_api.py` - SSE endpoint returns expected event sequence
- [ ] `uv run ruff check . && uv run ruff format --check .` clean
- [ ] `uv run pytest --cov=app` ≥ 70% on `app/rag/` and `app/ingestion/`

### Phase 10 - Deploy

- [ ] `backend/Dockerfile` (uv-based multi-stage)
- [ ] Fly.io or Railway config (long-lived process for SSE)
- [ ] Vercel project for `frontend/`; set `NEXT_PUBLIC_BACKEND_URL` to deployed FastAPI URL
- [ ] Switch `VECTOR_BACKEND=pgvector` and point at Supabase prod
- [ ] Smoke test prod URL end-to-end

---

## Resume hints

- Plan file is the source of truth. The checkbox state above is the resume cursor.
- If unsure where you left off: `cd rag-poc-v2 && ls -R` and compare against the file paths in this plan.
- Each phase's **Verify** step is the gate before moving on.
- Whenever you swap configurations or providers, re-run Phase 7 evals to catch regressions.
