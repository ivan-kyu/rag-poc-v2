from pathlib import Path

from fastapi import APIRouter

from app.ingestion.pipeline import ingest_documents
from app.settings import settings
from app.stores.factory import get_vector_store

router = APIRouter()


@router.post("/ingest")
async def trigger_ingest():
    store = get_vector_store()
    kb_dir = Path(settings.knowledge_base_dir)
    stats = await ingest_documents(kb_dir, store)
    return {"status": "ok", **stats}
