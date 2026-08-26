"""Canonical brief scenarios (docs/PLAN.md, Phase 9): a fixed set of named
clinical vignettes exercising the graph's deterministic, non-LLM parts end
to end — real risk scoring (`load_case`), real tools against a real store,
and the real `no_decision_guard` — against known-correct expected outcomes.

Deliberately does not run the LLM-backed evidence agent or brief writer:
`tests/graph/test_case_review_integration.py` already proves the graph's
*control flow* (including a real interrupt()/resume cycle) with fake
stand-ins for those, and no OpenAI key is available in this build
environment to call the real ones (see D-A12-1). What this module gates
that the pytest suite does not is scenario-level regression: for each named
patient, do the tools and the risk-scoring node actually report what is
really true of that patient's record — not "does the graph wire together."
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from cohort.graph.nodes.load_case import HIGH_RISK_TIER, LOW_RISK_TIER, build_load_case_node
from cohort.graph.state import create_initial_case_review_state
from cohort.guardrails.no_decision_guard import find_decision_language
from cohort.pipeline.features.extract import BINARY_FEATURES, CATEGORICAL_FEATURES, NUMERIC_FEATURES
from cohort.pipeline.models.train import FEATURE_COLUMNS
from cohort.pipeline.registry import ModelMetadata, save_model_artifact
from cohort.schemas.case_brief import CaseBrief
from cohort.store.cohort_store import CohortStore
from cohort.tools.care_gap_lookup import build_care_gap_lookup_tool
from cohort.tools.missing_data_check import build_missing_data_check_tool
from validation.checks import Check
from validation.fixtures.scenario_patients import build_scenario_store

# One extra background patient per class keeps the one-hot encoder and the
# logistic regression well-posed; the scenario patients are what's checked.
HIGH_RISK_IDS = ["p_gap", "p_nogap"]
LOW_RISK_IDS = ["p_low", "p_missing"]
BACKGROUND_IDS = ["bg_high", "bg_low"]


def _scenario_feature_table() -> pd.DataFrame:
    ids = HIGH_RISK_IDS + LOW_RISK_IDS + BACKGROUND_IDS
    data: dict[str, object] = {"PATIENT_ID": ids}
    # A single numeric feature encodes the scenario's intended risk level;
    # every other column is filled with fixed, harmless values so the
    # small model has exactly one real signal to learn.
    signal = [1.0, 1.0, -1.0, -1.0, 1.0, -1.0]
    for i, col in enumerate(NUMERIC_FEATURES):
        data[col] = signal if i == 0 else [0.0] * len(ids)
    for col in CATEGORICAL_FEATURES:
        data[col] = ["A"] * len(ids)
    for col in BINARY_FEATURES:
        data[col] = [False] * len(ids)
    return pd.DataFrame(data)


def _fit_scenario_model(features: pd.DataFrame, registry_dir: Path) -> Path:
    preprocess = ColumnTransformer(
        transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES)],
        remainder="passthrough",
    )
    pipeline = Pipeline(steps=[("preprocess", preprocess), ("model", LogisticRegression())])
    x = features[FEATURE_COLUMNS]
    y = (features[NUMERIC_FEATURES[0]] > 0).astype(int)
    pipeline.fit(x, y)
    metadata = ModelMetadata("v_scenario", "Y_SCENARIO", 0.5, len(x), 0, {}, FEATURE_COLUMNS)
    return save_model_artifact(pipeline, metadata, registry_dir)


def _check_risk_scoring(feature_table: pd.DataFrame, version_dir: Path) -> list[Check]:
    node = build_load_case_node(version_dir, feature_table)
    checks = []
    for patient_id in HIGH_RISK_IDS:
        result = node(create_initial_case_review_state(patient_id))
        checks.append(
            Check(
                f"{patient_id}: scores {HIGH_RISK_TIER} risk",
                result["risk_tier"] == HIGH_RISK_TIER,
                f"risk_score={result['risk_score']:.3f}, tier={result['risk_tier']!r}",
            )
        )
    for patient_id in LOW_RISK_IDS:
        result = node(create_initial_case_review_state(patient_id))
        checks.append(
            Check(
                f"{patient_id}: scores {LOW_RISK_TIER} risk",
                result["risk_tier"] == LOW_RISK_TIER,
                f"risk_score={result['risk_score']:.3f}, tier={result['risk_tier']!r}",
            )
        )
    return checks


def _check_care_gap_tool(store: CohortStore) -> list[Check]:
    tool = build_care_gap_lookup_tool(store)
    gap_result = tool.invoke({"patient_id": "p_gap"})
    nogap_result = tool.invoke({"patient_id": "p_nogap"})
    return [
        Check(
            "p_gap: care gap detected (diabetes, no glucose lab)",
            len(gap_result) == 1 and "glucose" in gap_result[0]["gap_description"].lower(),
            f"got {gap_result!r}",
        ),
        Check(
            "p_nogap: no care gap (diabetes, glucose lab present)",
            len(nogap_result) == 0,
            f"got {nogap_result!r}",
        ),
    ]


def _check_missing_data_tool(store: CohortStore) -> list[Check]:
    tool = build_missing_data_check_tool(store)
    result = tool.invoke({"patient_id": "p_missing"})
    missing = set(result["missing_data_types"])
    expected = {"encounters", "labs", "medications", "conditions"}
    return [
        Check(
            "p_missing: every evidence category reported missing",
            missing == expected,
            f"got {sorted(missing)}",
        )
    ]


def _check_no_decision_guard() -> list[Check]:
    clean = CaseBrief(
        patient_id="p_gap",
        narrative="Risk score is elevated relative to the validation cohort.",
        drivers=[],
        corroborating_evidence=[],
        care_gaps=["No glucose or A1c lab recorded for a patient with diabetes"],
        missing_data=[],
        what_would_change_this="A recent glucose or A1c result would clarify current control.",
    )
    dirty = CaseBrief(
        patient_id="p_gap",
        narrative="This patient should be enrolled in the care-management programme.",
        drivers=[],
        corroborating_evidence=[],
        care_gaps=[],
        missing_data=[],
        what_would_change_this="Nothing — recommend enrolment now.",
    )
    return [
        Check(
            "no_decision_guard: clean brief passes",
            find_decision_language(clean) == [],
            "expected zero violations",
        ),
        Check(
            "no_decision_guard: decision language is caught",
            len(find_decision_language(dirty)) >= 1,
            f"got {find_decision_language(dirty)}",
        ),
    ]


def check_canonical_scenarios() -> list[Check]:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = tmp_path / "scenario_cohort.db"
        build_scenario_store(db_path)
        store = CohortStore(db_path)

        feature_table = _scenario_feature_table()
        version_dir = _fit_scenario_model(feature_table, tmp_path / "registry")

        checks = []
        checks += _check_risk_scoring(feature_table, version_dir)
        checks += _check_care_gap_tool(store)
        checks += _check_missing_data_tool(store)
        checks += _check_no_decision_guard()

        store.close()
        return checks


def main() -> int:
    checks = check_canonical_scenarios()
    failed = [c for c in checks if not c.passed]
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"[{status}] {check.name} ({check.detail})")
    print(f"\n{len(checks) - len(failed)}/{len(checks)} canonical scenario checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
