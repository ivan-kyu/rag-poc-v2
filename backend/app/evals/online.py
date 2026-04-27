"""LangSmith online eval feedback hooks."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def submit_feedback(run_id: str, score: float, comment: str = "") -> None:
    """Post a thumbs-up/down feedback score to LangSmith for a given run."""
    try:
        from langsmith import Client

        client = Client()
        client.create_feedback(
            run_id=run_id,
            key="user_rating",
            score=score,
            comment=comment,
        )
    except Exception as exc:
        logger.warning("Failed to submit LangSmith feedback: %s", exc)
