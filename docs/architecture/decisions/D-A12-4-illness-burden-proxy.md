# D-A12-4 — The illness-burden proxy, and excluding race as a feature

## Context

The label-choice experiment (Phase 4) compares a model trained on realised
cost against one trained on illness burden. Neither label is ground truth —
Synthea has no "true illness severity" field — so both are proxies, and the
choice of proxy for illness burden needs its own justification.

A second question sits next to it: should race be a model input? Obermeyer
et al.'s deployed algorithm did **not** use race as a feature and still
produced a racially disparate outcome, because the label it optimised for
(cost) was itself correlated with access, which is correlated with race.
"Fairness through unawareness" — excluding a protected attribute and calling
it done — is a well-documented failure mode for exactly this reason.

## Decision

**Illness-burden proxy**: count of new conditions recorded in a patient's
forward window (`pipeline/labels/burden_label.py`). Deliberately built from
diagnosis events only, with no cost or utilisation signal anywhere in it —
mixing the two would erase the divergence the experiment exists to show.

**Race and ethnicity are excluded from `pipeline/features/extract.py`'s
feature set.** They are used only as the stratification key in the subgroup
audit (Phase 3), never as a model input. This is a deliberate choice to
demonstrate the *stronger* version of the Obermeyer point: this app's model
doesn't need race as an input to produce a racially disparate outcome when
trained on the wrong label. If it needed race as an input to show that, the
lesson would be weaker and easier to dismiss as "just don't use race as a
feature."

## Consequences

- The label-choice experiment's result (§ evidence, Phase 4) is not an
  artifact of a model peeking at demographics — it survives a genuinely
  blinded model.
- The illness-burden label is itself imperfect (a condition *count* is not
  the same as severity), and the model card says so.
- A future reviewer asking "did you control for race in the model?" has a
  direct, defensible answer: race was never available to the model at all.
