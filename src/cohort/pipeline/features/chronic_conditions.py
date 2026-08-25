"""Named chronic-condition flags, matched by keyword against condition
descriptions.

Deliberately named and interpretable rather than one-hot-encoding all ~400
distinct condition descriptions: `explain/` (Phase 3) attributes a
prediction to *these* flags, and "diabetes: yes/no" means something to a
clinician reading a case brief in a way that "condition_code_44054006: yes"
does not.
"""

from __future__ import annotations

CHRONIC_CONDITION_KEYWORDS: dict[str, str] = {
    "HAS_DIABETES": "diabetes",
    "HAS_HYPERTENSION": "hypertension",
    "HAS_OBESITY": "obesity",
    "HAS_ASTHMA": "asthma",
    "HAS_HEART_FAILURE": "heart failure",
    "HAS_CHRONIC_KIDNEY_DISEASE": "chronic kidney",
    "HAS_CORONARY_DISEASE": "coronary",
    "HAS_DEPRESSION": "depress",
    "HAS_ANXIETY": "anxiety",
}
