import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.ingestion.pipeline import ingest_documents
from app.settings import settings
from app.stores.factory import get_vector_store

router = APIRouter()

UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".md", ".pdf"}


@router.post("/upload")
async def upload_file(file: UploadFile):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    UPLOAD_DIR.mkdir(exist_ok=True)
    dest = UPLOAD_DIR / (file.filename or "upload")
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    store = get_vector_store()
    kb_dir = Path(settings.knowledge_base_dir)
    stats = await ingest_documents(kb_dir, store)
    return {"status": "ok", "filename": file.filename, **stats}
