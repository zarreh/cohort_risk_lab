import pytest

from cohort.guardrails.phi_projection import project
from cohort.store.models import LabObservation


def _lab() -> LabObservation:
    return LabObservation(
        patient_id="p1",
        date="2023-01-01T00:00:00",  # type: ignore[arg-type]
        category="laboratory",
        description="Glucose",
        value="95",
        units="mg/dL",
    )


def test_project_keeps_only_allowlisted_fields() -> None:
    result = project(_lab(), "patient_labs")
    assert set(result.keys()) == {"date", "category", "description", "value", "units"}


def test_project_drops_patient_id_even_though_present_on_the_model() -> None:
    result = project(_lab(), "patient_labs")
    assert "patient_id" not in result


def test_unregistered_tool_name_raises() -> None:
    with pytest.raises(ValueError, match="No PHI projection allowlist"):
        project(_lab(), "some_new_tool_nobody_registered")
