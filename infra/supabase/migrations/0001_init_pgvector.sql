-- Enable pgvector extension
-- LangChain's PGVector creates its own tables (langchain_pg_collection, langchain_pg_embedding)
-- This migration only ensures the extension is available.
CREATE EXTENSION IF NOT EXISTS vector;
