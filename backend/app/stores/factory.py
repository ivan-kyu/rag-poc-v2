from functools import lru_cache

from app.settings import settings


@lru_cache(maxsize=1)
def get_vector_store():
    if settings.vector_backend == "pgvector":
        from app.stores.pgvector_store import PGVectorStore

        return PGVectorStore()
    from app.stores.chroma_store import ChromaStore

    return ChromaStore()
