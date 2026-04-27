import contextlib
from typing import Any

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.settings import settings

COLLECTION_NAME = "rag_documents"


class ChromaStore:
    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )
        self._store = Chroma(
            client=self._client,
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
        )

    @property
    def store(self) -> Chroma:
        return self._store

    async def add_documents(self, docs: list[Document]) -> None:
        self._store.add_documents(docs)

    def as_retriever(self, **kwargs: Any):
        return self._store.as_retriever(**kwargs)

    async def clear(self) -> None:
        with contextlib.suppress(Exception):
            self._client.delete_collection(COLLECTION_NAME)
        embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )
        self._store = Chroma(
            client=self._client,
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
        )

    async def count(self) -> int:
        collection = self._client.get_collection(COLLECTION_NAME)
        return collection.count()

    async def source_stats(self) -> dict[str, int]:
        collection = self._client.get_collection(COLLECTION_NAME)
        result = collection.get(include=["metadatas"])
        stats: dict[str, int] = {}
        for meta in result["metadatas"] or []:
            src = meta.get("source", "unknown") if meta else "unknown"
            stats[src] = stats.get(src, 0) + 1
        return stats
