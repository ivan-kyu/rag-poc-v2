"""Translates LangGraph astream_events v2 output into typed SSE events."""
from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any


def _sse(event_type: str, data: Any) -> str:
    return f"data: {json.dumps({'type': event_type, 'data': data})}\n\n"


async def graph_events_to_sse(
    event_stream: AsyncIterator,
    langsmith_url: str = "",
) -> AsyncIterator[str]:
    answer_tokens: list[str] = []
    final_state: dict = {}

    async for event in event_stream:
        kind = event.get("event", "")
        name = event.get("name", "")
        data = event.get("data", {})

        if kind == "on_chain_start" and name not in ("LangGraph", "__start__"):
            yield _sse("node_start", {"node": name})

        elif kind == "on_chain_end" and name not in ("LangGraph", "__start__"):
            output = data.get("output", {})
            payload: dict[str, Any] = {"node": name}

            if name in ("retrieve_naive", "retrieve_hybrid", "retrieve_multiquery", "retrieve_hyde"):
                chunks = output.get("retrieved_chunks", [])
                payload["chunks"] = [
                    {
                        "content": c.page_content if hasattr(c, "page_content") else str(c),
                        "source": (c.metadata.get("source", "") if hasattr(c, "metadata") else ""),
                        "score": c.metadata.get("relevance_score", 0) if hasattr(c, "metadata") else 0,
                    }
                    for c in chunks
                ]
            elif name == "rerank":
                chunks = output.get("reranked_chunks", [])
                payload["chunks"] = [
                    {
                        "content": c.page_content if hasattr(c, "page_content") else str(c),
                        "source": (c.metadata.get("source", "") if hasattr(c, "metadata") else ""),
                        "score": c.metadata.get("relevance_score", 0) if hasattr(c, "metadata") else 0,
                    }
                    for c in chunks
                ]
            elif name == "classify":
                payload["route"] = output.get("route", "")
            elif name == "generate":
                final_state = output

            yield _sse("node_end", payload)

        elif kind == "on_chat_model_stream":
            chunk = data.get("chunk", {})
            token = ""
            if hasattr(chunk, "content"):
                token = chunk.content
            elif isinstance(chunk, dict):
                token = chunk.get("content", "")
            if token:
                answer_tokens.append(token)
                yield _sse("token", {"token": token})

    yield _sse("done", {
        "answer": final_state.get("answer", "".join(answer_tokens)),
        "citations": final_state.get("citations", []),
        "confidence": final_state.get("confidence", 0.8),
        "langsmith_url": langsmith_url,
    })
