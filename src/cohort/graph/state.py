from typing import TypedDict


class SkeletonState(TypedDict):
    """Phase 0 walking-skeleton state — kept as the template's trivial proof graph.

    The real `CaseReviewState` (case brief assembly + HITL decision) lands in
    Phase 6 (docs/PLAN.md §Phases) alongside the evidence agent and tools it
    depends on. Building it before there is a model, a case, or a tool to
    call would just be typed scaffolding with nothing behind it.
    """

    message: str
    echoed: str
    done: bool


def create_initial_skeleton_state(message: str) -> SkeletonState:
    return SkeletonState(message=message, echoed="", done=False)
