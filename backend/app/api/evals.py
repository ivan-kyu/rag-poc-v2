from fastapi import APIRouter
from pydantic import BaseModel

from app.rag.schemas import PipelineConfig

router = APIRouter()


class EvalRequest(BaseModel):
    config: PipelineConfig = PipelineConfig()


@router.post("/evals/run")
async def run_evals(req: EvalRequest):
    from app.evals.ragas_runner import run_ragas_eval

    result = await run_ragas_eval(req.config)
    return result
