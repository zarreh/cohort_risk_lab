"""Checks a drafted `CaseBrief` for decision or recommendation language in
its free-text fields — the second half of D-A12-1's enforcement.

`CaseBrief` has no field to put a decision in (see the schema's docstring),
but an LLM asked to "synthesise the evidence" can still write a sentence
like "this patient should be enrolled" inside `narrative` if nothing stops
it. This is that stop: a deterministic check, not a prompt instruction —
the same reasoning as `guardrails/phi_projection.py` (an instruction can be
argued with; a check that runs in code cannot).
"""

from __future__ import annotations

import re

from cohort.schemas.case_brief import CaseBrief

# Verbs and phrases that state or imply a decision rather than describing
# evidence. Deliberately broad — a false positive here costs one extra
# revision loop (cheap); a false negative lets a decision through (not).
DECISION_PATTERNS = [
    r"\bshould be enroll",
    r"\brecommend(?:s|ed|ing)?\b",
    r"\benroll(?:s|ed|ing)?\s+(?:this|the)\s+patient",
    r"\bdo not enroll",
    r"\bdeny\b",
    r"\bdenied\b",
    r"\bapprove(?:s|d|ing)?\b",
    r"\bdecline(?:s|d|ing)?\b",
    r"\breject(?:s|ed|ing)?\b",
    r"\beligible for enrolment\b",
    r"\bineligible for enrolment\b",
]

_COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in DECISION_PATTERNS]


def find_decision_language(brief: CaseBrief) -> list[str]:
    """Returns a list of violation descriptions — empty if the brief is
    clean. Checks every free-text field on the brief, not just `narrative`:
    `what_would_change_this` is meant to be a neutral statement of missing
    evidence, and is just as capable of smuggling in a recommendation."""
    violations: list[str] = []
    text_fields = {
        "narrative": brief.narrative,
        "what_would_change_this": brief.what_would_change_this,
    }

    for field_name, text in text_fields.items():
        for pattern in _COMPILED_PATTERNS:
            match = pattern.search(text)
            if match:
                violations.append(f"{field_name!r} contains decision language: {match.group(0)!r}")

    return violations
