# RAG Explorer v2

A full-stack RAG (Retrieval-Augmented Generation) learning project built with the modern Python AI stack. Upload documents, ask questions, and watch the entire pipeline execute live - with technique toggles to compare retrieval strategies.

## Architecture

```
frontend/          Next.js 16 + Tailwind + shadcn/ui  →  Vercel
backend/           FastAPI + LangChain + LangGraph      →  Fly.io / Railway
knowledge-base/    Markdown + PDF source documents
infra/             Docker Compose (Postgres, Chroma, Redis)
```

### RAG Pipeline (LangGraph)

```
query → [classify_route] → [retrieve: naive | hybrid | multi-query | HyDE]
      → [rerank (optional)] → [generate with citations] → SSE stream → UI
```

### Techniques (all toggleable in UI)

| Technique | Library | What it does |
|-----------|---------|-------------|
| Naive retrieval | LangChain VectorStore | Plain cosine similarity top-K |
| Hybrid search | EnsembleRetriever (BM25 + vector) | Combines keyword + semantic scores |
| Multi-query | MultiQueryRetriever | Generates query variants, merges results |
| HyDE | HypotheticalDocumentEmbedder | Embeds a hypothetical answer, retrieves by it |
| Reranking | ContextualCompressionRetriever + CrossEncoder | Re-scores retrieved chunks |
| Query routing | LangGraph conditional edge | Classifies query type, picks best retriever |

### Observability

- **LangSmith** - every run traced, filterable by technique config
- **RAGAS** - offline eval: faithfulness, answer relevancy, context precision/recall
- LangSmith trace URL included in each chat response

![LangSmith trace list - runs named and tagged by technique](LangSmith%20demo%201.png)

![LangSmith waterfall - full node-level pipeline trace with latency and token costs](LangSmith%20demo%202.png)

## Quickstart

### Prerequisites

- Python 3.11+, `uv` (`pip install uv`)
- Node 20+, `pnpm` (`npm i -g pnpm`)
- Docker + Docker Compose

### 1. Clone and configure

```bash
cp .env.example .env
# Fill in OPENAI_API_KEY and LANGCHAIN_API_KEY at minimum
```

### 2. Start infrastructure

```bash
docker compose -f infra/docker-compose.yml up -d
```

### 3. Start backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
# API at http://localhost:8000
```

### 4. Ingest knowledge base

```bash
curl -X POST http://localhost:8000/api/ingest
```

### 5. Start frontend

```bash
cd frontend
pnpm install
pnpm dev
# App at http://localhost:3000
```

## Vector Backend

Switch between ChromaDB (local dev) and pgvector (production) via env var:

```bash
VECTOR_BACKEND=chroma    # default - uses ./chroma_data/
VECTOR_BACKEND=pgvector  # uses DATABASE_URL pointing to Postgres+pgvector
```

## Deployment

- **Frontend**: Vercel - connect the `frontend/` directory
- **Backend**: Fly.io or Railway (SSE requires long-lived process - Vercel serverless won't work for streaming)
- **Vector DB**: Set `VECTOR_BACKEND=pgvector` and point `DATABASE_URL` at Supabase

## Project Structure

```
backend/
  app/
    api/          FastAPI routers (chat, ingest, upload, documents, evals)
    rag/          LangGraph pipeline (graph, nodes, retrievers, routing, schemas)
    stores/       Vector store adapters (Chroma, pgvector, factory)
    ingestion/    Document loaders, chunker, ingestion orchestrator
    evals/        RAGAS runner, LangSmith dataset management
    settings.py   Pydantic-settings config
    streaming.py  LangGraph events -> SSE formatter
  tests/
frontend/
  src/
    components/   ChatPanel, PipelinePanel, GraphDiagram, TechniqueToggles, EvalPanel
    lib/          SSE client, API wrappers
knowledge-base/   Source documents (Markdown + PDF)
infra/            Docker Compose, Supabase migrations
PLAN.md           Implementation checklist (resume cursor)
```
