from typing import Annotated, Any

from langchain_core.documents import Document
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class PipelineConfig(BaseModel):
    hybrid: bool = False
    multi_query: bool = False
    hyde: bool = False
    rerank: bool = False
    route: bool = False


class Citation(BaseModel):
    source: str
    chunk_index: int = 0
    relevance_score: float = 0.0
    snippet: str = ""


class AnswerWithCitations(BaseModel):
    answer: str = Field(description="The answer to the user's question")
    citations: list[Citation] = Field(
        default_factory=list,
        description="Sources used to construct the answer",
    )
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence score for the answer",
    )


def _merge_docs(existing: list[Document], new: list[Document]) -> list[Document]:
    seen = {d.page_content for d in existing}
    return existing + [d for d in new if d.page_content not in seen]


class GraphState(TypedDict):
    query: str
    config: dict[str, Any]
    route: str
    query_variants: list[str]
    retrieved_chunks: Annotated[list[Document], _merge_docs]
    reranked_chunks: list[Document]
    context_block: str
    answer: str
    citations: list[dict]
    confidence: float
    langsmith_url: str
