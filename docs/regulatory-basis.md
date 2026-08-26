# Regulatory and domain basis

This app is a research prototype trained and evaluated entirely on
synthetic [Synthea](https://synthetichealth.github.io/synthea/) patients.
It has never touched a real patient record and is not, and does not claim
to be, a medical device. This page states the actual basis for that claim
against the frameworks that would apply if it ever did touch real data,
rather than asserting it once in a banner and leaving it unexamined.

## HIPAA: minimum-necessary and Safe Harbor de-identification

Two separate controls, doing two separate jobs, both exercised on real
(synthetic) data rather than only described:

**De-identification (`data/deidentify.py`).** Every Synthea patient is
run through HIPAA Safe Harbor-style removal before anything downstream
ever sees it: no name, no address below state level, no SSN, no exact
dates. Every date is shifted by a per-patient, seeded offset — the same
offset applied consistently across every table for that patient, so
relative timing (an encounter three days after a lab) survives while the
absolute calendar does not. Age is never derived by mutating a patient's
birthdate to cap it (an earlier version of this pipeline did that and
produced patients with negative ages — see the model card's discussion of
that bug); it is capped only at the point a feature or a chart computes
it, so no patient's stored record is ever chronologically inconsistent
with itself.

**Minimum-necessary tool design (`guardrails/phi_projection.py`).** Safe
Harbor governs what the *dataset* may contain; minimum-necessary governs
what any single *access* may return. Every read-only tool the evidence
agent can call is bound to a per-tool field allowlist — `patient_encounters`
returns date, care setting, and reason, never a billing or cost field;
no tool returns a field its stated purpose doesn't require. This is
enforced in the tool layer itself, not left to a prompt instruction the
model could be talked out of.

## FDA: why this is Non-Device Clinical Decision Support

The 21st Century Cures Act (and 21 U.S.C. §360j(o)(1)(E)) excludes
software from the device definition when it meets four criteria. This
app's design tracks each one, not by accident:

1. **Does not acquire, process, or analyze a medical image or signal.**
   The risk model's inputs are administrative and utilisation
   features — encounter counts, condition flags, medication counts — never
   imaging, waveform, or device signal data.
2. **Displays or analyzes medical information about a patient.** True by
   design: that is exactly what the case brief does.
3. **Supports, rather than replaces, a clinician's judgment.** This is
   D-A12-1, enforced structurally rather than claimed: `CaseBrief`
   (`schemas/case_brief.py`) has no risk-tier field and no
   enrolment/recommendation field anywhere in its schema, so there is
   nowhere for a recommendation to go even in the fields an LLM authors.
   `guardrails/no_decision_guard.py` additionally scans the one free-text
   field the brief has for decision language ("should be enrolled",
   "recommend", "approve") and fails the brief if it finds any. The human
   reviewer makes the enrolment call at `await_decision`; nothing upstream
   of that node can.
4. **Enables independent review of the basis for a recommendation.** The
   risk score is never presented alone: `graph/nodes/load_case.py`
   attaches the model's own SHAP feature attribution
   (`pipeline/explain/shap_explainer.py`) as `drivers` before any LLM node
   runs, and the evidence agent's job is to corroborate those drivers
   against the patient's actual encounters, labs, and care gaps — a
   reviewer can check the reasoning, not just trust a number.

A tool that assigns a risk tier and stops there would already be a closer
call. Whether this app crosses back into device territory in a real
deployment is a question for the organization deploying it and its own
regulatory counsel, not something a synthetic-data prototype can settle —
this section states the design basis for the non-device argument, not a
determination.

## NCQA/HEDIS: enrolment, not diagnosis

The positioning is deliberate and consistent everywhere in this app:
**care-management programme enrolment**, never screening, never disease
identification, never diagnosis. This matches how NCQA's HEDIS measures
and case/care-management accreditation standards frame risk
stratification: identifying which already-known patients would benefit
from additional care coordination resources, not detecting or diagnosing
a condition. The risk labels (`Y_BURDEN`, `Y_COST`) are both defined over
patients' *existing*, already-recorded chronic conditions and utilisation
— the model never infers an undiagnosed condition, and the frontend and
every prototype banner state the enrolment framing explicitly.

## Obermeyer et al. (Science, 2019): reproduced, not rediscovered

This app's one clickable artifact — the label-choice experiment
(`docs/evidence/label-choice-experiment.md`) — is built to demonstrate the
finding Obermeyer et al. documented: a healthcare risk algorithm trained
to predict cost, rather than illness burden, systematically under-flags
Black patients at equal underlying need, because unequal historical access
to care makes realised cost a biased proxy for need.

Synthea generates utilisation and cost with no differential access baked
in, so training on unmodified synthetic data would show no such
divergence — a null result dressed as a finding. The access gap in this
cohort is therefore **injected, seeded, and disclosed**
([D-A12-2](architecture/decisions/D-A12-2-injected-access-gap.md)): a
published parameter reduces realised utilisation and spend for one
demographic stratum at equal illness burden. Every page that shows the
resulting divergence states this plainly. The claim being demonstrated is
that the subgroup audit *catches* an access-driven label-choice failure —
not that this app discovered one in the wild.

## Positioning guardrails

Every page in this app carries a persistent banner: architectural
demonstration, fully synthetic Synthea data, not a medical device. This is
never deployed against real or re-identifiable patient data.
