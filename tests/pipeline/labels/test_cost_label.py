import pandas as pd

from cohort.pipeline.labels.access_gap import AccessGapConfig
from cohort.pipeline.labels.cost_label import build_cost_label

CONFIG: AccessGapConfig = {
    "target_column": "RACE",
    "target_value": "black",
    "access_reduction_factor": 0.5,
    "adjusted_fields": [],  # overridden internally to ["REALISED_COST"]
}


def _fixture() -> tuple[pd.Series, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    included = pd.Series(["p1", "p2", "p3"], name="PATIENT_ID")
    race = pd.DataFrame({"PATIENT_ID": ["p1", "p2", "p3"], "RACE": ["black", "white", "white"]})
    encounters = pd.DataFrame(
        {"PATIENT": ["p1", "p2", "p3"], "TOTAL_CLAIM_COST": [1000.0, 1000.0, 1000.0]}
    )
    medications = pd.DataFrame({"PATIENT": ["p1"], "TOTALCOST": [200.0]})
    return included, race, encounters, medications


def test_realised_cost_sums_encounters_and_medications() -> None:
    included, race, encounters, medications = _fixture()
    labels = build_cost_label(included, race, encounters, medications, CONFIG, top_k_percent=0.5)
    realised = labels.set_index("PATIENT_ID")["REALISED_COST"].to_dict()
    assert realised == {"p1": 1200.0, "p2": 1000.0, "p3": 1000.0}


def test_access_gap_is_applied_to_the_forward_window_total_not_realised_cost() -> None:
    included, race, encounters, medications = _fixture()
    labels = build_cost_label(included, race, encounters, medications, CONFIG, top_k_percent=0.5)
    row = labels.set_index("PATIENT_ID").loc["p1"]
    assert row["REALISED_COST"] == 1200.0
    assert row["ADJUSTED_REALISED_COST"] == 600.0


def test_patient_missing_from_both_event_tables_gets_zero_cost() -> None:
    included = pd.Series(["p1", "p2"], name="PATIENT_ID")
    race = pd.DataFrame({"PATIENT_ID": ["p1", "p2"], "RACE": ["white", "white"]})
    encounters = pd.DataFrame({"PATIENT": ["p1"], "TOTAL_CLAIM_COST": [500.0]})
    medications = pd.DataFrame({"PATIENT": [], "TOTALCOST": []})
    labels = build_cost_label(included, race, encounters, medications, CONFIG, top_k_percent=0.5)
    assert labels.set_index("PATIENT_ID").loc["p2", "REALISED_COST"] == 0.0
