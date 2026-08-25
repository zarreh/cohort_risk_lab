import pandas as pd

from cohort.pipeline.labels.burden_label import build_burden_label


def test_patients_with_no_forward_conditions_get_zero_score() -> None:
    included = pd.Series(["p1", "p2"], name="PATIENT_ID")
    forward_conditions = pd.DataFrame({"PATIENT": ["p1", "p1"]})
    labels = build_burden_label(included, forward_conditions, top_k_percent=0.5)
    scores = labels.set_index("PATIENT_ID")["ILLNESS_BURDEN_SCORE"].to_dict()
    assert scores == {"p1": 2, "p2": 0}


def test_top_k_percent_flags_the_highest_scores() -> None:
    included = pd.Series(["p1", "p2", "p3", "p4"], name="PATIENT_ID")
    forward_conditions = pd.DataFrame(
        {"PATIENT": ["p1"] * 5 + ["p2"] * 3 + ["p3"] * 1}
    )  # p4 has none
    labels = build_burden_label(included, forward_conditions, top_k_percent=0.25)
    flagged = set(labels.loc[labels["Y_BURDEN"] == 1, "PATIENT_ID"])
    assert flagged == {"p1"}
