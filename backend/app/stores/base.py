from typing import Any, Protocol

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore


class VectorStoreAdapter(Protocol):
    """Thin protocol so the app code never depends on a concrete store."""

    @property
    def store(self) -> VectorStore: ...

    async def add_documents(self, docs: list[Document]) -> None: ...

    def as_retriever(self, **kwargs: Any): ...

    async def clear(self) -> None: ...

    async def count(self) -> int: ...

    async def source_stats(self) -> dict[str, int]:
        """Return {source_filename: chunk_count} mapping."""
        ...
