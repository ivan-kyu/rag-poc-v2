import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.rag.graph import build_graph
from app.rag.schemas import GraphState, PipelineConfig
from app.settings import settings
from app.streaming import graph_events_to_sse

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    config: PipelineConfig = PipelineConfig()


@router.post("/chat")
async def chat(req: ChatRequest):
    graph = build_graph(req.config)
    run_id = str(uuid.uuid4())

    active_techniques = [k for k, v in req.config.model_dump().items() if v]
    tags = active_techniques if active_techniques else ["naive"]

    initial_state: GraphState = {
        "query": req.question,
        "config": req.config.model_dump(),
        "route": "",
        "query_variants": [],
        "retrieved_chunks": [],
        "reranked_chunks": [],
        "context_block": "",
        "answer": "",
        "citations": [],
        "confidence": 0.8,
        "langsmith_url": "",
    }

    run_config = {
        "run_id": run_id,
        "run_name": f"RAG: {req.question[:60]}{'...' if len(req.question) > 60 else ''}",
        "tags": tags,
        "metadata": {
            "question": req.question,
            "techniques": tags,
            **req.config.model_dump(),
        },
    }

    langsmith_url = (
        f"https://smith.langchain.com/o/~/projects/p/{settings.langsmith_project}/r/{run_id}"
        if settings.langsmith_tracing
        else ""
    )

    async def event_stream() -> AsyncIterator[str]:
        event_iter = graph.astream_events(initial_state, version="v2", config=run_config)
        async for chunk in graph_events_to_sse(event_iter, langsmith_url=langsmith_url):
            yield chunk

    return StreamingResponse(event_stream(), media_type="text/event-stream")
