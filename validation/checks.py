"""Shared result type for both validation gates (`metric_floors.py`,
`canonical_scenarios.py`), so `run.py` can combine and report them as one
list without a type union at every call site."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Check:
    name: str
    passed: bool
    detail: str
