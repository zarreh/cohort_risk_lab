"""Regenerates every chart under docs/evidence/ from real data or real eval
output — never hand-drawn (PORTFOLIO_PLAN_V3.md §9.4). `make docs-assets`
runs this and CI fails if the committed charts drift from what it produces.

No charts exist yet: the cohort and the trained model this depends on land
in Phases 1-4.
"""

from __future__ import annotations


def main() -> None:
    print("No plots to generate yet — pipeline lands in Phases 1-4.")


if __name__ == "__main__":
    main()
