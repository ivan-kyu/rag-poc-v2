from langchain_openai import ChatOpenAI

from app.rag.prompts import ROUTE_PROMPT
from app.rag.schemas import GraphState
from app.settings import settings

VALID_ROUTES = {"factual", "definition", "procedural"}


async def classify_query(state: GraphState) -> GraphState:
    llm = ChatOpenAI(model=settings.openai_model, temperature=0, api_key=settings.openai_api_key)
    chain = ROUTE_PROMPT | llm
    result = await chain.ainvoke({"query": state["query"]})
    route = result.content.strip().lower()
    if route not in VALID_ROUTES:
        route = "factual"
    return {**state, "route": route}


def route_to_retriever(state: GraphState) -> str:
    """LangGraph conditional edge: returns the next node name based on config + route."""
    config = state.get("config", {})
    # HyDE and multi-query take priority over hybrid when both are on
    if config.get("hyde"):
        return "retrieve_hyde"
    if config.get("multi_query"):
        return "retrieve_multiquery"
    if config.get("hybrid"):
        return "retrieve_hybrid"
    return "retrieve_naive"
