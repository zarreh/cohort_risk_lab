# Cohort Risk & Review Lab

> The model decides. The agent explains. The human approves. And the fairness
> number is reported per subgroup, not in aggregate.

Portfolio app **A12** (`PORTFOLIO_PLAN_V3.md` §7). Healthcare — population
health / care management, Pillar 2 — Governance & Security. Target URL:
`cohort.zarreh.ai` (not yet deployed — see Status below).

Over a synthetic [Synthea](https://synthetichealth.github.io/synthea/)
population, a calibrated risk model stratifies patients for enrolment in a
care-management programme. A subgroup audit reports calibration and
true-positive-rate parity across age, sex, race and insurance strata — not a
single aggregate AUC. Every flagged patient lands in a clinician review
queue, where an agent assembles the case: which features drove the score,
which encounters and labs corroborate it, what data is missing, and what
would change the answer. **The agent never assigns the risk tier, and it
never enrols anyone** — see
[architecture/decisions](architecture/decisions/index.md) D-A12-1 for how
that is enforced structurally rather than asserted in a prompt.

## Status

**Phase 0 — template shakedown.** Repo scaffold, FastAPI skeleton, a trivial
two-node graph, quality gates (ruff, mypy --strict, import-linter, pytest,
this documentation site) wired and green. No model, no cohort, no agent yet.

> **In one paragraph, for a non-engineer:** this app takes a synthetic
> hospital's worth of patients, uses a statistical model — not a language
> model — to flag who might benefit from a care-management programme, then
> checks whether that model is fair across race, sex and age before anyone
> acts on it. A separate AI assistant then gathers the evidence a clinician
> would want to see, but it never makes the call itself — a person always
> does.

This is a research prototype built entirely on synthetic Synthea data. It is
**not** a medical device, does not diagnose, and does not screen for disease
— see [regulatory-basis.md](regulatory-basis.md).
