from fastapi import APIRouter

from app.stores.factory import get_vector_store

router = APIRouter()


@router.get("/documents")
async def list_documents():
    store = get_vector_store()
    total = await store.count()
    source_stats = await store.source_stats()
    return {
        "total_chunks": total,
        "sources": [
            {"name": name, "chunks": count}
            for name, count in sorted(source_stats.items())
        ],
    }
