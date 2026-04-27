import os
from contextlib import asynccontextmanager

# Must happen before any langchain/langgraph imports so the SDK picks them up
from app.settings import settings

if settings.langsmith_api_key:
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
if settings.langsmith_tracing:
    os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, documents, evals, ingest, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-ingest on startup if knowledge base dir exists
    from pathlib import Path

    from app.ingestion.pipeline import ingest_documents
    from app.stores.factory import get_vector_store

    kb_dir = Path(settings.knowledge_base_dir)
    if kb_dir.exists():
        store = get_vector_store()
        await ingest_documents(kb_dir, store)
    yield


app = FastAPI(title="RAG Explorer v2", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(evals.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "backend": settings.vector_backend}
