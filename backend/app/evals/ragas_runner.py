"""RAGAS offline evaluation runner."""
from __future__ import annotations

import asyncio
import functools
import logging
import os

from app.evals.datasets import EVAL_DATASET
from app.rag.schemas import PipelineConfig
from app.settings import settings

logger = logging.getLogger(__name__)


async def run_ragas_eval(config: PipelineConfig, sample_size: int = 5) -> dict:
    """
    Run RAGAS metrics on a sample of the eval dataset using the given pipeline config.
    Returns scores and a LangSmith experiment URL if tracing is enabled.
    """
    try:
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        from ragas import evaluate
        from ragas.dataset_schema import EvaluationDataset, SingleTurnSample
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from ragas.llms import LangchainLLMWrapper
        from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

        from app.rag.graph import build_graph
        from app.rag.schemas import GraphState
    except ImportError as e:
        return {"error": f"Missing dependency: {e}"}

    if settings.openai_api_key:
        os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

    ragas_llm = LangchainLLMWrapper(
        ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key)
    )
    ragas_embeddings = LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(model=settings.openai_embedding_model, api_key=settings.openai_api_key)
    )

    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    for metric in metrics:
        metric.llm = ragas_llm
        if hasattr(metric, "embeddings"):
            metric.embeddings = ragas_embeddings

    graph = build_graph(config)
    samples_data = EVAL_DATASET[:sample_size]
    eval_samples = []

    for item in samples_data:
        initial_state: GraphState = {
            "query": item["question"],
            "config": config.model_dump(),
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
        try:
            result = await graph.ainvoke(initial_state)
            chunks = result.get("reranked_chunks") or result.get("retrieved_chunks", [])
            eval_samples.append(SingleTurnSample(
                user_input=item["question"],
                response=result.get("answer", ""),
                retrieved_contexts=[c.page_content for c in chunks],
                reference=item["ground_truth"],
            ))
        except Exception as exc:
            logger.warning("Eval sample failed: %s", exc)

    if not eval_samples:
        return {"error": "All eval samples failed"}

    dataset = EvaluationDataset(samples=eval_samples)

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            functools.partial(evaluate, dataset=dataset, metrics=metrics),
        )
        scores_df = result.to_pandas()
        scores = {
            metric: round(float(scores_df[metric].mean()), 3)
            for metric in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
            if metric in scores_df.columns
        }
    except Exception as exc:
        return {"error": f"RAGAS evaluation failed: {exc}"}

    return {
        "config": config.model_dump(),
        "sample_size": len(eval_samples),
        "scores": scores,
    }
