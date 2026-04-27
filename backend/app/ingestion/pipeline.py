import logging
from pathlib import Path

from app.ingestion.chunker import chunk_documents
from app.ingestion.loaders import load_directory

logger = logging.getLogger(__name__)


async def ingest_documents(source_dir: Path, store) -> dict:
    """Load, chunk, and upsert all documents from source_dir into store.

    Clears the store first for a clean re-ingest.
    Returns ingestion stats.
    """
    logger.info("Starting ingestion from %s", source_dir)

    docs = load_directory(source_dir)
    if not docs:
        logger.warning("No documents found in %s", source_dir)
        return {"sources": 0, "chunks": 0}

    chunks = chunk_documents(docs)
    logger.info("Loaded %d docs → %d chunks", len(docs), len(chunks))

    await store.clear()
    await store.add_documents(chunks)

    count = await store.count()
    source_stats = await store.source_stats()
    logger.info("Ingested %d chunks from %d sources", count, len(source_stats))

    return {
        "sources": len(source_stats),
        "chunks": count,
        "source_stats": source_stats,
    }
