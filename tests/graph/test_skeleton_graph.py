from cohort.graph.builder import build_skeleton_graph
from cohort.graph.state import create_initial_skeleton_state


def test_skeleton_graph_runs_end_to_end() -> None:
    graph = build_skeleton_graph()
    result = graph.invoke(create_initial_skeleton_state("hello"))
    assert result["echoed"] == "echo: hello"
    assert result["done"] is True
