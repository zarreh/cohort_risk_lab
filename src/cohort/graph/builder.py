from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from cohort.graph.nodes.done import done_node
from cohort.graph.nodes.echo import echo_node
from cohort.graph.state import SkeletonState

SkeletonGraph = CompiledStateGraph[SkeletonState, None, SkeletonState, SkeletonState]


def build_skeleton_graph() -> SkeletonGraph:
    """The only function that wires nodes and edges. Phase 0: echo -> done.

    The real case-review graph (`load_case -> assemble_evidence -> ... ->
    await_decision -> record_decision`) is wired here in Phase 6, once a
    trained model, a cohort store and the evidence tools it depends on exist
    (docs/PLAN.md §Phases).
    """
    workflow = StateGraph(SkeletonState)
    workflow.add_node("echo", echo_node)
    workflow.add_node("done", done_node)
    workflow.set_entry_point("echo")
    workflow.add_edge("echo", "done")
    workflow.add_edge("done", END)
    return workflow.compile()
