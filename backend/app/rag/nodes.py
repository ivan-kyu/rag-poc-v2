from __future__ import annotations

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from app.rag.prompts import RAG_PROMPT
from app.rag.retrievers import (
    build_hybrid,
    build_hyde,
    build_multiquery,
    build_naive,
    with_reranker,
)
from app.rag.schemas import AnswerWithCitations, GraphState
from app.settings import settings
from app.stores.factory import get_vector_store


def _format_context(docs: list[Document]) -> str:
    parts = []
    for doc in docs:
        src = doc.metadata.get("source", "unknown")
        score = doc.metadata.get("relevance_score", "")
        score_str = f" (relevance: {score:.2f})" if score else ""
        parts.append(f"[{src}{score_str}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


async def retrieve_naive(state: GraphState) -> GraphState:
    store = get_vector_store()
    retriever = build_naive(store)
    docs = await retriever.ainvoke(state["query"])
    return {**state, "retrieved_chunks": docs}


async def retrieve_hybrid(state: GraphState) -> GraphState:
    store = get_vector_store()
    # Need all docs for BM25 index
    all_docs_result = store.store.get() if hasattr(store.store, "get") else None
    if all_docs_result and "documents" in all_docs_result:
        lc_docs = [
            Document(page_content=c, metadata=m)
            for c, m in zip(all_docs_result["documents"], all_docs_result["metadatas"] or [], strict=False)
        ]
    else:
        # Fallback: use naive retriever docs for BM25
        base = build_naive(store, k=20)
        lc_docs = await base.ainvoke(state["query"])
    retriever = build_hybrid(store, lc_docs)
    docs = await retriever.ainvoke(state["query"])
    return {**state, "retrieved_chunks": docs}


async def retrieve_multiquery(state: GraphState) -> GraphState:
    store = get_vector_store()
    base = build_naive(store)
    retriever = build_multiquery(base)
    docs = await retriever.ainvoke(state["query"])
    return {**state, "retrieved_chunks": docs}


async def retrieve_hyde(state: GraphState) -> GraphState:
    store = get_vector_store()
    retriever, hypothetical = await build_hyde(store, state["query"])
    docs = await retriever.ainvoke(hypothetical)
    return {**state, "retrieved_chunks": docs}


async def rerank_chunks(state: GraphState) -> GraphState:
    store = get_vector_store()
    base = build_naive(store)
    reranker = with_reranker(base)
    # Re-rank the already retrieved chunks by querying through the compressor
    docs = await reranker.ainvoke(state["query"])
    return {**state, "reranked_chunks": docs}


async def generate(state: GraphState) -> GraphState:
    chunks = state.get("reranked_chunks") or state.get("retrieved_chunks", [])
    context = _format_context(chunks)

    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.2,
        api_key=settings.openai_api_key,
        streaming=True,
    )
    structured_llm = llm.with_structured_output(AnswerWithCitations)
    chain = RAG_PROMPT | structured_llm

    result: AnswerWithCitations = await chain.ainvoke({
        "context": context,
        "question": state["query"],
    })

    citations = [c.model_dump() for c in result.citations]
    return {
        **state,
        "context_block": context,
        "answer": result.answer,
        "citations": citations,
        "confidence": result.confidence,
    }
