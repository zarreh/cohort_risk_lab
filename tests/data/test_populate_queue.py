import pandas as pd

from data.populate_queue import living_patient_ids


def test_deceased_patients_are_never_queued() -> None:
    patients = pd.DataFrame(
        {
            "PATIENT_ID": ["alive-1", "dead-1", "alive-2"],
            "DEATHDATE": [None, "2021-06-27", None],
        }
    )

    assert living_patient_ids(patients) == {"alive-1", "alive-2"}
