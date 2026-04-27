from langgraph.graph import END, START, StateGraph

from app.rag.nodes import (
    generate,
    rerank_chunks,
    retrieve_hybrid,
    retrieve_hyde,
    retrieve_multiquery,
    retrieve_naive,
)
from app.rag.routing import classify_query, route_to_retriever
from app.rag.schemas import GraphState, PipelineConfig


def build_graph(config: PipelineConfig):
    """Compile a LangGraph StateGraph based on enabled technique toggles."""
    g = StateGraph(GraphState)

    # Always present nodes
    g.add_node("retrieve_naive", retrieve_naive)
    g.add_node("retrieve_hybrid", retrieve_hybrid)
    g.add_node("retrieve_multiquery", retrieve_multiquery)
    g.add_node("retrieve_hyde", retrieve_hyde)
    g.add_node("rerank", rerank_chunks)
    g.add_node("generate", generate)

    if config.route:
        g.add_node("classify", classify_query)
        g.add_edge(START, "classify")
        g.add_conditional_edges("classify", route_to_retriever, {
            "retrieve_naive": "retrieve_naive",
            "retrieve_hybrid": "retrieve_hybrid",
            "retrieve_multiquery": "retrieve_multiquery",
            "retrieve_hyde": "retrieve_hyde",
        })
    else:
        # Direct edge from start to the appropriate retriever
        if config.hyde:
            g.add_edge(START, "retrieve_hyde")
        elif config.multi_query:
            g.add_edge(START, "retrieve_multiquery")
        elif config.hybrid:
            g.add_edge(START, "retrieve_hybrid")
        else:
            g.add_edge(START, "retrieve_naive")

    retriever_nodes = ["retrieve_naive", "retrieve_hybrid", "retrieve_multiquery", "retrieve_hyde"]
    next_node = "rerank" if config.rerank else "generate"
    for node in retriever_nodes:
        g.add_edge(node, next_node)

    if config.rerank:
        g.add_edge("rerank", "generate")

    g.add_edge("generate", END)

    return g.compile()
