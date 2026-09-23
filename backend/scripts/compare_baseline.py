#!/usr/bin/env python3
"""Compare rules recommendations to the one-factor lowest-skill baseline."""

from __future__ import annotations

import argparse
from pathlib import Path
from statistics import quantiles
from time import perf_counter

from app.engine.dataset import load_dataset
from app.engine.recommender import recommend
from app.engine.skills import effective_skills, gaps, resolve_target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", nargs="?", default="data")
    ds = load_dataset(Path(parser.parse_args().data_dir))
    durations: list[float] = []
    differing = 0
    examples: list[str] = []
    for employee_id in sorted(ds.employees):
        started = perf_counter()
        result = recommend(ds, employee_id)
        durations.append((perf_counter() - started) * 1000)
        if not result.recommendations:
            continue
        employee = ds.employees[employee_id]
        levels = effective_skills(ds, employee)
        gap_values = gaps(ds, employee, levels, resolve_target(ds, employee))
        if not gap_values:
            continue
        lowest = min((levels.get(skill_id, 0), skill_id) for skill_id in gap_values)[1]
        top = result.recommendations[0]
        if lowest not in {gain.skill_id for gain in top.expected_gains}:
            differing += 1
            reason = result.not_recommended[0].reason if result.not_recommended else "Weighted score selected another target gap."
            if len(examples) < 5:
                examples.append(f"{employee_id}: {top.event_id} instead of lowest {lowest} — {reason}")
    p95 = quantiles(durations, n=20, method="inclusive")[18] if len(durations) >= 2 else (durations[0] if durations else 0)
    print(f"top-1 differs from lowest-skill baseline: {differing}/{len(ds.employees)}")
    print(f"rules runtime p95: {p95:.2f} ms (target < 50 ms)")
    print("examples:")
    for item in examples:
        print(f"- {item}")


if __name__ == "__main__":
    main()
