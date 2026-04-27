import pytest

from app.rag.graph import build_graph
from app.rag.schemas import PipelineConfig


@pytest.mark.parametrize(
    "config",
    [
        PipelineConfig(),
        PipelineConfig(hybrid=True),
        PipelineConfig(multi_query=True),
        PipelineConfig(hyde=True),
        PipelineConfig(rerank=True),
        PipelineConfig(route=True),
        PipelineConfig(hybrid=True, rerank=True),
        PipelineConfig(multi_query=True, rerank=True, route=True),
    ],
)
def test_graph_compiles_for_all_configs(config: PipelineConfig):
    graph = build_graph(config)
    assert graph is not None
    # Graph should have at least start + retrieve + generate nodes
    assert len(graph.nodes) >= 3
