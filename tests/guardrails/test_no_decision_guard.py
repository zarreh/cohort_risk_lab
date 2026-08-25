from cohort.guardrails.no_decision_guard import find_decision_language
from cohort.schemas.case_brief import CaseBrief


def _brief(narrative: str = "", what_would_change_this: str = "") -> CaseBrief:
    return CaseBrief(
        patient_id="p1",
        narrative=narrative or "The patient has elevated glucose and two active conditions.",
        drivers=[],
        corroborating_evidence=[],
        care_gaps=[],
        missing_data=[],
        what_would_change_this=what_would_change_this or "A recent A1c result would clarify this.",
    )


def test_clean_brief_has_no_violations() -> None:
    assert find_decision_language(_brief()) == []


def test_recommend_in_narrative_is_caught() -> None:
    brief = _brief(narrative="Based on this evidence, we recommend enrolling this patient.")
    violations = find_decision_language(brief)
    assert len(violations) >= 1
    assert any("narrative" in v for v in violations)


def test_decision_language_in_what_would_change_this_is_also_caught() -> None:
    brief = _brief(what_would_change_this="Nothing — this patient should be enrolled regardless.")
    violations = find_decision_language(brief)
    assert any("what_would_change_this" in v for v in violations)


def test_case_insensitive_matching() -> None:
    brief = _brief(narrative="RECOMMEND enrollment immediately.")
    assert len(find_decision_language(brief)) >= 1


def test_neutral_clinical_language_is_not_flagged() -> None:
    brief = _brief(
        narrative=(
            "The patient has diabetes and hypertension, with three emergency "
            "encounters in the lookback window."
        )
    )
    assert find_decision_language(brief) == []
