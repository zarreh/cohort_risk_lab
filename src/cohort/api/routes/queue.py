"""The review queue: list flagged patients, start a review, stream its
progress, and record the clinician's decision.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from cohort.api.deps import get_case_review_graph, get_queue_store, settings_dependency
from cohort.api.rate_limit import DEFAULT_RATE_LIMIT, limiter
from cohort.api.run_executor import resume_review, start_review
from cohort.api.schemas import (
    CaseDetailResponse,
    DecisionRequest,
    QueueEntryResponse,
    StartReviewResponse,
)
from cohort.api.streaming import stream_review_events
from cohort.graph.builder import CaseReviewGraph
from cohort.settings import Settings
from cohort.store.queue_store import QueueStore

router = APIRouter(prefix="/queue", tags=["queue"])

QueueStoreDep = Annotated[QueueStore, Depends(get_queue_store)]
GraphDep = Annotated[CaseReviewGraph, Depends(get_case_review_graph)]
SettingsDep = Annotated[Settings, Depends(settings_dependency)]


@router.get("")
@limiter.limit(DEFAULT_RATE_LIMIT)
def list_queue(
    request: Request, queue_store: QueueStoreDep, status: str | None = None
) -> list[QueueEntryResponse]:
    cases = queue_store.list_queue(status=status)
    return [
        QueueEntryResponse(
            patient_id=c.patient_id,
            risk_score=c.risk_score,
            risk_tier=c.risk_tier,
            status=c.status,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in cases
    ]


@router.get("/{patient_id}")
@limiter.limit(DEFAULT_RATE_LIMIT)
def get_case(request: Request, patient_id: str, queue_store: QueueStoreDep) -> CaseDetailResponse:
    case = queue_store.get_case(patient_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found in the review queue")
    return CaseDetailResponse(
        patient_id=case.patient_id,
        risk_score=case.risk_score,
        risk_tier=case.risk_tier,
        status=case.status,
        decision=case.decision,
        override_notes=case.override_notes,
        decided_at=case.decided_at,
    )


@router.post("/{patient_id}/start", status_code=202)
@limiter.limit(DEFAULT_RATE_LIMIT)
def start_case_review(
    request: Request,
    patient_id: str,
    background_tasks: BackgroundTasks,
    queue_store: QueueStoreDep,
    graph: GraphDep,
    settings: SettingsDep,
) -> StartReviewResponse:
    case = queue_store.get_case(patient_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found in the review queue")
    if case.status != "pending":
        raise HTTPException(status_code=409, detail=f"Case is already {case.status!r}")

    background_tasks.add_task(start_review, patient_id, graph, queue_store, settings)
    return StartReviewResponse(patient_id=patient_id, status="in_review")


@router.get("/{patient_id}/events")
@limiter.limit(DEFAULT_RATE_LIMIT)
def case_events(
    request: Request, patient_id: str, queue_store: QueueStoreDep
) -> EventSourceResponse:
    return EventSourceResponse(stream_review_events(queue_store, patient_id))


@router.post("/{patient_id}/decision", status_code=202)
@limiter.limit(DEFAULT_RATE_LIMIT)
def submit_decision(
    request: Request,
    patient_id: str,
    body: DecisionRequest,
    background_tasks: BackgroundTasks,
    queue_store: QueueStoreDep,
    graph: GraphDep,
    settings: SettingsDep,
) -> StartReviewResponse:
    case = queue_store.get_case(patient_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found in the review queue")
    if case.status != "awaiting_decision":
        raise HTTPException(
            status_code=409, detail=f"Case is {case.status!r}, not awaiting a decision"
        )

    background_tasks.add_task(
        resume_review, patient_id, body.decision, body.notes, graph, queue_store, settings
    )
    return StartReviewResponse(patient_id=patient_id, status="deciding")
