"""Picks the operating point by cost, not by a default 0.5 cutoff.

A care-management programme has an asymmetric cost structure: missing a
patient who would have benefited (a false negative) costs a preventable bad
outcome; enrolling someone who didn't need it (a false positive) costs a
programme slot and a clinician's review time. Optimising accuracy at 0.5
optimises for neither of the costs that actually matter to the programme
owner.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CostMatrix:
    cost_false_negative: float
    cost_false_positive: float


def optimize_threshold(
    y_true: np.ndarray, y_proba: np.ndarray, cost_matrix: CostMatrix, n_candidates: int = 200
) -> float:
    """Sweeps candidate thresholds and returns the one minimising total
    expected cost on the given (validation) set."""
    candidates = np.linspace(0.0, 1.0, n_candidates + 1)
    best_threshold = 0.5
    best_cost = float("inf")

    for threshold in candidates:
        predicted_positive = y_proba >= threshold
        false_negatives = int(((y_true == 1) & ~predicted_positive).sum())
        false_positives = int(((y_true == 0) & predicted_positive).sum())
        total_cost = (
            false_negatives * cost_matrix.cost_false_negative
            + false_positives * cost_matrix.cost_false_positive
        )
        if total_cost < best_cost:
            best_cost = total_cost
            best_threshold = float(threshold)

    return best_threshold
