"""HIPAA minimum-necessary enforcement, in the tool layer — not the prompt
(PORTFOLIO_PLAN_V3.md §7 A12, G3 domain grounding: "encode which fields
tools may return, enforced in the tool layer, not the prompt").

Every tool in `cohort.tools` returns a Pydantic model from `store/models.py`
that already excludes direct identifiers (`data/deidentify.py` handles
that). `project()` is the second, independent layer: even among the
already-de-identified fields, a given tool should surface only what its
specific evidence-gathering purpose needs. A model instructed via its
prompt to "only mention clinically relevant fields" can be talked out of
that by a sufficiently adversarial or confused conversation; a field that
was never serialised into the tool's output cannot leak, regardless of
what the model is told or asked.

The allowlist mechanism itself is `zarreh_agentkit.guardrails.projection`
(a second occurrence, alongside A3's own state-projection pattern); this
module owns only the per-tool allowlist, which is domain-specific.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from zarreh_agentkit.guardrails.projection import project_fields

# tool name -> allowed field names on that tool's return model. A field not
# listed here is dropped by `project()`, never passed through by default.
TOOL_FIELD_ALLOWLIST: dict[str, frozenset[str]] = {
    "patient_encounters": frozenset({"start", "encounter_class", "description"}),
    "patient_labs": frozenset({"date", "category", "description", "value", "units"}),
    "care_gap_lookup": frozenset({"gap_description", "last_relevant_encounter"}),
    "missing_data_check": frozenset({"missing_data_types"}),
    "feature_attribution": frozenset({"feature_name", "contribution", "direction"}),
}


def project(record: BaseModel, tool_name: str) -> dict[str, Any]:
    """Serialises `record` to a dict containing only the fields allowlisted
    for `tool_name`. Raises if `tool_name` has no registered allowlist —
    a new tool must declare what it may return before it can return
    anything, rather than defaulting to "everything"."""
    if tool_name not in TOOL_FIELD_ALLOWLIST:
        raise ValueError(
            f"No PHI projection allowlist registered for tool {tool_name!r}. "
            "Add one to TOOL_FIELD_ALLOWLIST before this tool can return data."
        )
    return project_fields(record, TOOL_FIELD_ALLOWLIST[tool_name])
