"""`make validate` (docs/PLAN.md, Phase 9): runs both validation gates —
ML metric floors on the frozen split and the canonical brief scenarios —
and exits non-zero if either fails, the same way A2's `make eval` gates
its own PR CI.
"""

from __future__ import annotations

import sys

from validation.canonical_scenarios import check_canonical_scenarios
from validation.metric_floors import check_metric_floors


def main() -> int:
    print("=== ML metric floors (frozen split) ===")
    metric_checks = check_metric_floors()
    for check in metric_checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"[{status}] {check.name} ({check.detail})")

    print("\n=== Canonical brief scenarios ===")
    scenario_checks = check_canonical_scenarios()
    for check in scenario_checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"[{status}] {check.name} ({check.detail})")

    all_checks = metric_checks + scenario_checks
    failed = [c for c in all_checks if not c.passed]
    print(f"\n{len(all_checks) - len(failed)}/{len(all_checks)} validation checks passed")
    if failed:
        print("\nFAILED:")
        for check in failed:
            print(f"  - {check.name}: {check.detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
