# D-A12-7 — Typed tools instead of text-to-SQL

## Context

The source `healthcare_hitl_assistant.ipynb` notebook has an LLM generate
SQL against the patient database directly, gated by a keyword blocklist
(`UNSAFE_KEYWORDS = ["DROP", "TRUNCATE", ...]`) and a human-in-the-loop
approval step for anything classified as a write. This is the wrong
architecture for two independent reasons:

1. **A keyword blocklist over generated SQL is trivially bypassable** —
   comments, encoding tricks, and semantically-equivalent-but-differently-
   worded statements all evade a fixed keyword list, and the notebook's own
   classifier runs on the *generated SQL text*, not on what the query
   actually does.
2. **It gives the model far more query surface than any evidence-gathering
   task needs.** An agent that can express arbitrary SQL can retrieve
   arbitrary rows and columns — the opposite of HIPAA minimum necessary
   (D-A12-2's cousin concern, enforced here at the tool-design level rather
   than the field-projection level).

## Decision

Every tool the evidence agent can call (`cohort.tools`) is a fixed,
narrow, typed function: `patient_encounters`, `patient_labs`,
`care_gap_lookup`, `missing_data_check`, `feature_attribution`. Each has a
Pydantic args schema (a patient id, occasionally a limit) and a fixed
return shape filtered through `guardrails/phi_projection.py`. None of them
accept a query string, a filter expression, or anything else that could
expand what a single call can retrieve. `cohort.store.CohortStore` is the
only thing that talks SQL, and every query in it is a fixed, parameterised
statement written by hand — never string-built from model output.

## Consequences

- The agent cannot construct a query this app's authors did not
  anticipate. Adding a new capability means adding a new tool with its own
  allowlist entry, not relaxing a filter.
- This does cost flexibility: a clinician asking a question this specific
  tool set cannot answer gets "no evidence available," not a best-effort
  query. That is the correct failure mode for a system operating under
  minimum-necessary, not a limitation to work around.
- Every tool is independently unit-testable against a small fixture
  database (`tests/fixtures/cohort_db.py`) without touching the real
  cohort — the same benefit a fixed API surface gives any typed client.
