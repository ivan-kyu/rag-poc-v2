from typing import Any

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from app.settings import settings

COLLECTION_NAME = "rag_documents"


class PGVectorStore:
    def __init__(self) -> None:
        embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )
        self._store = PGVector(
            embeddings=embeddings,
            collection_name=COLLECTION_NAME,
            connection=settings.database_url,
            use_jsonb=True,
        )

    @property
    def store(self) -> PGVector:
        return self._store

    async def add_documents(self, docs: list[Document]) -> None:
        self._store.add_documents(docs)

    def as_retriever(self, **kwargs: Any):
        return self._store.as_retriever(**kwargs)

    async def clear(self) -> None:
        self._store.delete_collection()
        self._store.create_collection()

    async def count(self) -> int:
        with self._store._make_sync_session() as session:
            collection = self._store.get_collection(session)
            if collection is None:
                return 0
            from langchain_postgres.vectorstores import EmbeddingStore
            from sqlalchemy import func, select

            result = session.execute(
                select(func.count()).where(
                    EmbeddingStore.collection_id == collection.uuid
                )
            )
            return result.scalar() or 0

    async def source_stats(self) -> dict[str, int]:
        with self._store._make_sync_session() as session:
            collection = self._store.get_collection(session)
            if collection is None:
                return {}
            from langchain_postgres.vectorstores import EmbeddingStore

            rows = session.execute(
                __import__("sqlalchemy").select(EmbeddingStore.cmetadata).where(
                    EmbeddingStore.collection_id == collection.uuid
                )
            ).fetchall()
            stats: dict[str, int] = {}
            for (meta,) in rows:
                src = (meta or {}).get("source", "unknown")
                stats[src] = stats.get(src, 0) + 1
            return stats
