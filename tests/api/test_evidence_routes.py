from collections.abc import Iterator

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import cohort.api.routes.evidence as evidence_module
from cohort.api.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_subgroup_audit_insufficient_n_renders_nulls_not_nan(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_audit = pd.DataFrame(
        {
            "STRATUM": ["native"],
            "N": [20],
            "SUFFICIENT_N": [False],
            "CALIBRATION_IN_THE_LARGE": [float("nan")],
            "EXPECTED_CALIBRATION_ERROR": [float("nan")],
            "TPR": [float("nan")],
            "TPR_CI_LOWER": [float("nan")],
            "TPR_CI_UPPER": [float("nan")],
            "ENROLMENT_RATE": [float("nan")],
            "ENROLMENT_RATE_CI_LOWER": [float("nan")],
            "ENROLMENT_RATE_CI_UPPER": [float("nan")],
        }
    )
    monkeypatch.setattr(evidence_module, "get_subgroup_audit", lambda version: fake_audit)

    response = client.get("/evidence/subgroup-audit")
    assert response.status_code == 200
    row = response.json()[0]
    assert row["sufficient_n"] is False
    assert row["tpr"] is None
    assert row["calibration_in_the_large"] is None


def test_subgroup_audit_sufficient_n_renders_real_numbers(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_audit = pd.DataFrame(
        {
            "STRATUM": ["white"],
            "N": [1000],
            "SUFFICIENT_N": [True],
            "CALIBRATION_IN_THE_LARGE": [0.01],
            "EXPECTED_CALIBRATION_ERROR": [0.02],
            "TPR": [0.8],
            "TPR_CI_LOWER": [0.75],
            "TPR_CI_UPPER": [0.85],
            "ENROLMENT_RATE": [0.5],
            "ENROLMENT_RATE_CI_LOWER": [0.45],
            "ENROLMENT_RATE_CI_UPPER": [0.55],
        }
    )
    monkeypatch.setattr(evidence_module, "get_subgroup_audit", lambda version: fake_audit)

    response = client.get("/evidence/subgroup-audit?version=v1_cost")
    assert response.status_code == 200
    row = response.json()[0]
    assert row["stratum"] == "white"
    assert row["tpr"] == 0.8


def test_label_choice_returns_the_comparison_table(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_comparison = pd.DataFrame(
        {
            "RACE": ["black", "white"],
            "N": [50, 1000],
            "BURDEN_ENROLMENT_RATE": [0.2, 0.19],
            "COST_ENROLMENT_RATE": [0.14, 0.2],
            "GAP_PERCENTAGE_POINTS": [-6.0, 1.0],
        }
    )
    monkeypatch.setattr(evidence_module, "get_label_choice_comparison", lambda: fake_comparison)

    response = client.get("/evidence/label-choice")
    assert response.status_code == 200
    rows = response.json()
    black_row = next(r for r in rows if r["race"] == "black")
    assert black_row["gap_percentage_points"] == -6.0
