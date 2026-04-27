from __future__ import annotations

from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_openai import ChatOpenAI

from app.settings import settings


def build_naive(store, k: int = 5) -> BaseRetriever:
    return store.as_retriever(search_kwargs={"k": k})


def build_hybrid(store, docs: list[Document], k: int = 5) -> BaseRetriever:
    """BM25 + vector ensemble - requires all docs for BM25 in-memory index."""
    vector_retriever = store.as_retriever(search_kwargs={"k": k})
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = k
    return EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.4, 0.6],
    )


def build_multiquery(base_retriever: BaseRetriever) -> BaseRetriever:
    llm = ChatOpenAI(model=settings.openai_model, temperature=0, api_key=settings.openai_api_key)
    return MultiQueryRetriever.from_llm(retriever=base_retriever, llm=llm)


async def build_hyde(store, query: str, k: int = 5) -> tuple[BaseRetriever, str]:
    """Generate a hypothetical document, embed it, retrieve by it."""
    from langchain_openai import ChatOpenAI

    from app.rag.prompts import HYDE_PROMPT

    llm = ChatOpenAI(model=settings.openai_model, temperature=0.3, api_key=settings.openai_api_key)
    chain = HYDE_PROMPT | llm
    hypothetical = (await chain.ainvoke({"query": query})).content
    retriever = store.as_retriever(search_kwargs={"k": k})
    return retriever, hypothetical


def with_reranker(base_retriever: BaseRetriever) -> BaseRetriever:
    """Wrap retriever with a cross-encoder reranker. Falls back gracefully."""
    try:
        if settings.cohere_api_key:
            from langchain_cohere import CohereRerank

            compressor = CohereRerank(cohere_api_key=settings.cohere_api_key, top_n=3)
        else:
            from langchain.retrievers.document_compressors import CrossEncoderReranker
            from langchain_community.cross_encoders import HuggingFaceCrossEncoder

            model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")
            compressor = CrossEncoderReranker(model=model, top_n=3)
        return ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=base_retriever,
        )
    except Exception:
        return base_retriever
