# D-A12-1 — The LLM is not the risk model, and how that is structurally enforced

## Context

A12's tagline is "the model decides, the agent explains, the human
approves." That sentence is easy to assert in a README and easy to violate
by accident the first time an LLM prompt is tweaked to be more helpful.
The question this ADR answers is not *whether* the agent should decide —
that was always the design intent — but *what actually stops it from
drifting into deciding* as the system evolves.

The answer this app settled on: don't rely on the prompt at all. Every
enforcement point below works even if every prompt in this repo were
deleted and replaced with "be helpful."

## Decision — four independent structural controls

1. **The risk score and tier are set once, before any LLM runs, directly
   from the deployed model.** `graph/nodes/load_case.py` calls
   `pipeline.predict_proba` and writes `risk_score`/`risk_tier` into
   `CaseReviewState`. No node downstream of it — not the evidence agent,
   not the brief writer — can reach those fields; nothing after
   `load_case` has a reason to import the trained model at all except
   `feature_attribution`, which only reads its explanation, never its
   score.

2. **`CaseBrief` has no field to hold a decision.** No `risk_tier`, no
   `enrol` boolean, no recommendation field of any kind — see the
   schema's own docstring in `schemas/case_brief.py`. An LLM prompted to
   "assess this patient" has nowhere in the *structure* to put an
   assessment.

3. **Free text is checked, not trusted.** The one place a decision could
   still hide is prose — `narrative` and `what_would_change_this`.
   `guardrails/no_decision_guard.py` pattern-matches both fields for
   decision language after every draft, deterministically, and
   `graph/nodes/verify_brief.py` routes a violation back to
   `assemble_evidence` with specific feedback rather than letting it
   through. This is a real revision loop, not a warning: `route_after_verify`
   only reaches `await_decision` once the brief is clean or
   `MAX_REVISIONS` is exhausted — verified directly in
   `tests/graph/nodes/test_verify_brief.py`.

4. **The decision itself comes from `interrupt()`, not from a node.**
   `graph/nodes/await_decision.py` suspends the graph and returns the
   brief to a human; `decision` and `override_notes` are only ever set from
   the `Command(resume=...)` payload a clinician supplies. Verified against
   the real langgraph checkpointer runtime in
   `tests/graph/nodes/test_hitl_loop.py` — an interrupt/resume cycle, not a
   mocked one.

## Consequences

- A future contributor who wants the agent to "just recommend enrolment
  when it's obvious" cannot do it by editing a prompt. They would have to
  add a field to `CaseBrief`, delete a guard, or bypass `interrupt()`
  outright — all visible, reviewable code changes, not a prompt diff that
  looks like a wording tweak.
- The cost is real: a model that drafts a very well-reasoned implicit
  recommendation in neutral-sounding prose that doesn't match any pattern
  in `DECISION_PATTERNS` could still get through. The guard is a regex
  list, not a semantic judge — deliberately, so its behaviour is fully
  predictable and testable, at the cost of not catching cleverly-worded
  evasions. This is a known limitation, not an oversight.
- Every one of these four controls is independently unit-tested without a
  live LLM call (`tests/graph/`, `tests/guardrails/`) — the enforcement
  does not depend on catching a bad LLM response in the wild, because it
  does not depend on the LLM's behaviour at all.
