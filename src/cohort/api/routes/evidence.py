"""Read-only evidence endpoints: the subgroup fairness audit and the
label-choice experiment's divergence table. Both are precomputed by
`make train` — these routes read the results, they never recompute them
per request.
"""

from __future__ import annotations

import math

from fastapi import APIRouter, Query, Request

from cohort.api.deps import get_label_choice_comparison, get_subgroup_audit
from cohort.api.rate_limit import DEFAULT_RATE_LIMIT, limiter
from cohort.api.schemas import LabelChoiceRow, SubgroupAuditRow

router = APIRouter(prefix="/evidence", tags=["evidence"])


def _nullable_float(value: float) -> float | None:
    return None if math.isnan(value) else float(value)


@router.get("/subgroup-audit")
@limiter.limit(DEFAULT_RATE_LIMIT)
def subgroup_audit(
    request: Request, version: str = Query(default="v1_burden")
) -> list[SubgroupAuditRow]:
    audit = get_subgroup_audit(version)
    return [
        SubgroupAuditRow(
            stratum=row["STRATUM"],
            n=int(row["N"]),
            sufficient_n=bool(row["SUFFICIENT_N"]),
            calibration_in_the_large=_nullable_float(row["CALIBRATION_IN_THE_LARGE"]),
            expected_calibration_error=_nullable_float(row["EXPECTED_CALIBRATION_ERROR"]),
            tpr=_nullable_float(row["TPR"]),
            tpr_ci_lower=_nullable_float(row["TPR_CI_LOWER"]),
            tpr_ci_upper=_nullable_float(row["TPR_CI_UPPER"]),
            enrolment_rate=_nullable_float(row["ENROLMENT_RATE"]),
            enrolment_rate_ci_lower=_nullable_float(row["ENROLMENT_RATE_CI_LOWER"]),
            enrolment_rate_ci_upper=_nullable_float(row["ENROLMENT_RATE_CI_UPPER"]),
        )
        for _, row in audit.iterrows()
    ]


@router.get("/label-choice")
@limiter.limit(DEFAULT_RATE_LIMIT)
def label_choice(request: Request) -> list[LabelChoiceRow]:
    comparison = get_label_choice_comparison()
    return [
        LabelChoiceRow(
            race=row["RACE"],
            n=int(row["N"]),
            burden_enrolment_rate=float(row["BURDEN_ENROLMENT_RATE"]),
            cost_enrolment_rate=float(row["COST_ENROLMENT_RATE"]),
            gap_percentage_points=float(row["GAP_PERCENTAGE_POINTS"]),
        )
        for _, row in comparison.iterrows()
    ]
